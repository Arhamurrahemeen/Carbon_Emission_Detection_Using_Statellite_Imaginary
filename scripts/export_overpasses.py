"""Per-overpass NO2 plume features, pulled from Earth Engine straight to CSV (same method as gee/overpass_export.js).

One-time login:  earthengine authenticate
Run:             python scripts/export_overpasses.py [--project shajar-514406] [--start 2018-07-01] [--sites sahiwal hub]
Output:          data/raw/overpasses_<site_id>.csv

Network access happens only here; the pipeline reads the saved CSVs."""
import argparse
import csv
import math
from datetime import date
from pathlib import Path

import ee

SITES = {
    "sahiwal": (30.7142, 73.2380),
    "hub": (24.9147, 66.6888),  # CPHGC coal + Hub Power RFO ~1 km apart: one combined plume
}
NO2 = "tropospheric_NO2_column_number_density"
SCALE = 1113
COLUMNS = ["site_id", "date", "no2_down", "no2_up", "no2_raw", "wind_u", "wind_v",
           "wind_speed", "wind_dir", "cloud_fraction", "n_pixels"]
DOWN_KM, UP_KM, RADIUS_M, RAW_RADIUS_M = 10, 20, 7000, 5000  # starting values, tune


def _offset(lat, lon, km, bearing_deg):
    b = ee.Number(bearing_deg).multiply(math.pi / 180)
    dlat = ee.Number(km).multiply(b.cos()).divide(111.32)
    dlon = ee.Number(km).multiply(b.sin()).divide(111.32 * math.cos(math.radians(lat)))
    return ee.Geometry.Point([dlon.add(lon), dlat.add(lat)])


def _rows(site_id, lat, lon, start, end):
    pt = ee.Geometry.Point([lon, lat])
    era = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY").select(["u_component_of_wind_10m", "v_component_of_wind_10m"])

    def mean_in(img, band, geom):
        return img.select(band).reduceRegion(ee.Reducer.mean(), geom, SCALE).get(band)

    def per_image(img):
        t = img.date()
        hour = ee.Date(t.millis().divide(3600000).round().multiply(3600000))
        w = era.filterDate(hour, hour.advance(1, "hour"))
        uv = ee.Dictionary(ee.Algorithms.If(
            w.size().gt(0),
            ee.Image(w.first()).rename(["u", "v"]).reduceRegion(ee.Reducer.mean(), pt.buffer(15000), 11132),
            ee.Dictionary({"u": -9999, "v": -9999})))
        u, v = ee.Number(uv.get("u")), ee.Number(uv.get("v"))
        direction = u.atan2(v).multiply(180 / math.pi).add(360).mod(360)  # towards, degrees from north
        down = _offset(lat, lon, DOWN_KM, direction).buffer(RADIUS_M)
        up = _offset(lat, lon, UP_KM, direction.add(180)).buffer(RADIUS_M)
        on_site = pt.buffer(RAW_RADIUS_M)
        return ee.Feature(None, {
            "site_id": site_id, "date": t.format("YYYY-MM-dd"),
            "no2_down": mean_in(img, NO2, down), "no2_up": mean_in(img, NO2, up), "no2_raw": mean_in(img, NO2, on_site),
            "wind_u": u, "wind_v": v, "wind_speed": u.hypot(v), "wind_dir": direction,
            "cloud_fraction": mean_in(img, "cloud_fraction", on_site),
            "n_pixels": img.select(NO2).reduceRegion(ee.Reducer.count(), on_site, SCALE).get(NO2),
        })

    col = (ee.ImageCollection("COPERNICUS/S5P/OFFL/L3_NO2")
           .filterBounds(pt.buffer(60000).bounds()).filterDate(start, end).map(per_image)
           .filter(ee.Filter.notNull(["no2_raw", "no2_down", "no2_up"]))
           .filter(ee.Filter.gt("wind_u", -9000)))
    return [f["properties"] for f in col.getInfo()["features"]]


def _half_years(start: date, end: date):
    cur = start
    while cur < end:
        nxt = date(cur.year + (cur.month >= 7), 1 if cur.month >= 7 else 7, 1)
        yield cur.isoformat(), min(nxt, end).isoformat()
        cur = nxt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default="shajar-514406")
    ap.add_argument("--start", default="2018-07-01")
    ap.add_argument("--sites", nargs="+", default=list(SITES))
    args = ap.parse_args()
    ee.Initialize(project=args.project)
    for site_id in args.sites:
        lat, lon = SITES[site_id]
        dest = Path("data/raw") / f"overpasses_{site_id}.csv"
        n = 0
        with dest.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
            w.writeheader()
            for a, b in _half_years(date.fromisoformat(args.start), date.today()):
                rows = sorted(_rows(site_id, lat, lon, a, b), key=lambda r: r["date"])
                w.writerows(rows)
                n += len(rows)
                print(f"{site_id} {a}..{b}: {len(rows)} overpasses")
        print(f"{site_id}: {n} rows -> {dest}")


if __name__ == "__main__":
    main()
