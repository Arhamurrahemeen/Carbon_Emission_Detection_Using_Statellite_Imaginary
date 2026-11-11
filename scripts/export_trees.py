"""Tree data from Earth Engine straight to CSV (same method as gee/c07_tree_samples.js and gee/plots_export.js).

Run:  python scripts/export_trees.py [--project gen-lang-client-0940311971] [--only c07|plots]
Out:  data/raw/c07_samples.csv   tree / not-tree points, lower Sindh, 2021 Sentinel-2 features, WorldCover labels
      data/raw/plot_passes.csv   quarterly readings + annual classifier features for each plot in data/manual/plots.csv
Network access happens only here."""
import argparse
import csv
import math
from pathlib import Path

import ee

FEATURES = ["ndvi_p10", "ndvi_p25", "ndvi_p50", "ndvi_p75", "ndvi_p90", "ndvi_stdDev", "mean",
            "B2", "B3", "B4", "B8", "B11", "B12", "ndmi"]
QUARTERS = ["q1", "q2", "q3", "q4"]
PASS_DATES = ["2025-02-10", "2025-05-12", "2025-08-10", "2025-11-03",
              "2026-02-10", "2026-05-12", "2026-08-10", "2026-11-03"]


def _s2(region, start, end):
    def prep(i):
        scl = i.select("SCL")
        clear = scl.neq(3).And(scl.neq(8)).And(scl.neq(9)).And(scl.neq(10)).And(scl.neq(11))
        return (i.select(["B2", "B3", "B4", "B8", "B11", "B12"]).divide(10000)
                .addBands(i.normalizedDifference(["B8", "B4"]).rename("ndvi"))
                .addBands(i.normalizedDifference(["B8", "B11"]).rename("ndmi"))
                .updateMask(clear).copyProperties(i, ["system:time_start"]))
    return ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(region).filterDate(start, end).map(prep)


def _annual(col, start=None):
    ndvi = col.select("ndvi")
    img = (ndvi.reduce(ee.Reducer.percentile([10, 25, 50, 75, 90]))
           .addBands(ndvi.reduce(ee.Reducer.stdDev()))
           .addBands(ndvi.mean().rename("mean"))
           .addBands(col.select(["B2", "B3", "B4", "B8", "B11", "B12", "ndmi"]).median()))
    if start is not None:
        for q in range(4):
            img = img.addBands(ndvi.filterDate(start.advance(3 * q, "month"), start.advance(3 * q + 3, "month")).median().rename(f"q{q + 1}"))
    return img


def c07_samples(dest: Path):
    region = ee.Geometry.Rectangle([66.8, 24.0, 69.5, 26.0])
    start = ee.Date.fromYMD(2021, 1, 1)
    feats = _annual(_s2(region, start, start.advance(1, "year")), start)
    wc = ee.ImageCollection("ESA/WorldCover/v200").first().select("Map")
    label = wc.eq(10).rename("label").updateMask(wc.neq(80).And(wc.neq(95)))
    cols = FEATURES + QUARTERS

    def balanced(seed, n):
        pts = label.sampleRegions(collection=ee.FeatureCollection.randomPoints(region, 25000, seed), scale=10, geometries=True)
        pick = pts.filter(ee.Filter.eq("label", 1)).limit(n).merge(pts.filter(ee.Filter.eq("label", 0)).limit(n))
        return (feats.sampleRegions(collection=pick, properties=["label"], scale=10, geometries=True, tileScale=4)
                .filter(ee.Filter.notNull(cols)))

    rows = []
    for split, seed, n in (("train_test", 7, 1200), ("hand", 99, 100)):
        fc = balanced(seed, n)
        if split == "train_test":
            fc = fc.randomColumn("r", 11)
        for f in fc.getInfo()["features"]:
            p = f["properties"]
            lon, lat = f["geometry"]["coordinates"]
            s = split if split == "hand" else ("train" if p["r"] < 0.7 else "test")
            rows.append({"label": p["label"], "split": s, **{c: p[c] for c in cols}, "lon": lon, "lat": lat})
        print(f"c07 {split}: {sum(r['split'] in (split, 'train', 'test') for r in rows)} rows so far")
    _write(dest, ["label", "split"] + cols + ["lon", "lat"], rows)


def plot_passes(plots_csv: Path, dest: Path):
    plots = list(csv.DictReader(plots_csv.open(encoding="utf-8")))
    cloud_score = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    rows = []
    for p in plots:
        geom = ee.Geometry.Point([float(p["lon"]), float(p["lat"])]).buffer(math.sqrt(float(p["acres"]) * 4047 / math.pi))
        for d in PASS_DATES:
            date = ee.Date(d)
            col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterBounds(geom)
                   .filterDate(date.advance(-15, "day"), date.advance(15, "day")).linkCollection(cloud_score, ["cs"]))

            def score(img):
                clear = img.select("cs").gte(0.6)
                cloud = ee.Number(1).subtract(clear.reduceRegion(ee.Reducer.mean(), geom, 10).get("cs"))
                ndvi = img.normalizedDifference(["B8", "B4"]).updateMask(clear).reduceRegion(ee.Reducer.mean(), geom, 10).get("nd")
                return img.set({"cloud": cloud, "ndvi": ndvi})

            best = col.map(score).sort("cloud")
            obs = ee.Dictionary(ee.Algorithms.If(best.size().gt(0),
                                                 ee.Dictionary({"ndvi": best.first().get("ndvi"), "cloud": best.first().get("cloud")}),
                                                 ee.Dictionary({})))
            annual = _annual(_s2(geom, date.advance(-1, "year"), date)).reduceRegion(ee.Reducer.mean(), geom, 10)
            info = obs.combine(annual).getInfo()
            rows.append({"plot_id": p["plot_id"], "date": d, "ndvi": info.get("ndvi"), "cloud": info.get("cloud"),
                         **{c: info.get(c) for c in FEATURES}})
        print(f"plot {p['plot_id']} done")
    _write(dest, ["plot_id", "date", "ndvi", "cloud"] + FEATURES, rows)


def _write(dest: Path, cols, rows):
    with dest.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {dest}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="gen-lang-client-0940311971")
    ap.add_argument("--only", choices=["c07", "plots"])
    a = ap.parse_args()
    ee.Initialize(project=a.project)
    if a.only in (None, "plots"):
        plot_passes(Path("data/manual/plots.csv"), Path("data/raw/plot_passes.csv"))
    if a.only in (None, "c07"):
        c07_samples(Path("data/raw/c07_samples.csv"))
