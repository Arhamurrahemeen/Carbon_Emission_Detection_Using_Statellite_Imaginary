"""Labelled synthetic stand-ins so the pipeline, tests and app run before real exports land.
Every row carries data_flags="synthetic". Never mixed silently with real data (see verify/io.py)."""
import numpy as np
import pandas as pd

from verify.rules import SITE_PLANTS

SYNTH_CAPACITY_MW = {"sahiwal": 1320, "hub": 2612}
_MONSOON = (7, 8, 9)
# Real events the synthetic series imitates so the chart shows what to look for: 2020 lockdown, 2026 Sahiwal outage.
_DIPS = {"2020-03": 0.6, "2020-04": 0.6, "2026-01": 0.3, "2026-02": 0.5, "2026-03": 0.6}
_K = 1.6e-7  # mol/m2 of column enhancement per GWh/month at 1 m/s wind (sets ~2e-5 at 500 GWh, 4 m/s)


def _plant_factor(month: str, rng) -> float:
    m = int(month[5:7])
    seasonal = 0.15 * np.sin(2 * np.pi * (m - 3) / 12)  # summer peak demand
    pf = 0.55 + seasonal + rng.normal(0, 0.08)
    return float(np.clip(pf * _DIPS.get(month, 1.0), 0.03, 0.95))


def _hours(month: str) -> int:
    return pd.Period(month, freq="M").days_in_month * 24


def make_nepra(site_id: str, months: list[str], capacity_mw: float, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    plants = SITE_PLANTS[site_id]
    rows = []
    for month in months:
        total = capacity_mw * _hours(month) * _plant_factor(month, rng)  # MWh
        for plant in plants:
            rows.append({"plant": plant, "month": month, "net_generation_mwh": round(total / len(plants), 1),
                         "source_pdf": "synthetic", "page": 0, "data_flags": "synthetic"})
    return pd.DataFrame(rows)


def make_overpasses(site_id: str, months: list[str], seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed + 1000)
    gen = make_nepra(site_id, months, SYNTH_CAPACITY_MW[site_id], seed).groupby("month")["net_generation_mwh"].sum() / 1000
    rows = []
    for month in months:
        n = int(rng.integers(2, 5)) if int(month[5:7]) in _MONSOON else int(rng.integers(12, 21))
        days = rng.choice(pd.Period(month, freq="M").days_in_month, size=n, replace=False) + 1
        for day in sorted(days):
            speed = float(rng.uniform(1.5, 8.0))
            direction = float(rng.uniform(0, 360))
            up = float(rng.normal(3e-5, 5e-6))
            enh = _K * gen[month] / speed + float(rng.normal(0, 6e-6))
            raw = up + 0.6 * enh + float(rng.normal(0, 1.2e-5))  # no wind or background correction: noisier
            rows.append({
                "site_id": site_id, "date": f"{month}-{day:02d}",
                "no2_down": up + enh, "no2_up": up, "no2_raw": raw,
                "wind_u": speed * np.sin(np.radians(direction)), "wind_v": speed * np.cos(np.radians(direction)),
                "wind_speed": speed, "wind_dir": direction,
                "cloud_fraction": float(rng.uniform(0, 0.3)), "n_pixels": int(rng.integers(15, 25)),
                "data_flags": "synthetic",
            })
    return pd.DataFrame(rows)


# Real Sentinel-2 NDVI for the Shajar demo plots (Earth Engine export by the Shajar team, 2026-11-11).
# Used until gee/plots_export.js output lands. No classifier features, so the build falls back to the NDVI
# threshold and flags those passes "threshold_fallback".
SHAJAR_NDVI = {
    "m1": [0.43, 0.405, 0.486, 0.49], "m2": [0.666, 0.632, 0.741, 0.633],
    "s1": [0.186, 0.143, 0.0889, 0.104], "s2": [0.233, 0.173, 0.142, 0.151],
    "s3": [0.592, 0.203, 0.308, 0.29], "s4": [0.0603, 0.0395, 0.0246, 0.0414],
}
SHAJAR_DATES = ["2026-02-10", "2026-05-12", "2026-08-10", "2026-11-03"]


def shajar_plot_passes() -> pd.DataFrame:
    rows = [{"plot_id": p, "date": d, "ndvi": v, "cloud": 0.0, "data_flags": "shajar_export"}
            for p, vals in SHAJAR_NDVI.items() for d, v in zip(SHAJAR_DATES, vals)]
    rows += [{"plot_id": p, "date": "2027-02-10", "ndvi": None, "cloud": None, "data_flags": "shajar_export"} for p in SHAJAR_NDVI]
    return pd.DataFrame(rows)


def make_c07_samples(n: int = 600, seed: int = 0) -> pd.DataFrame:
    """Synthetic tree / not-tree samples: trees stay green all year; crops are green in one quarter only."""
    from verify.c07 import TREE_FEATURES
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        tree = i % 2 == 0
        crop_q = rng.integers(0, 4)
        q = [rng.uniform(0.45, 0.7) if tree else (rng.uniform(0.5, 0.8) if k == crop_q else rng.uniform(0.1, 0.25)) for k in range(4)]
        row = {f: rng.normal(0.2, 0.05) for f in TREE_FEATURES}
        row.update({"label": int(tree), "ndvi_p10": rng.uniform(0.35, 0.5) if tree else rng.uniform(0.05, 0.2),
                    "mean": float(np.mean(q)), "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3],
                    "split": "train" if i < int(n * 0.7) else "test", "lon": 67 + i * 1e-3, "lat": 25.0,
                    "data_flags": "synthetic"})
        rows.append(row)
    return pd.DataFrame(rows)
