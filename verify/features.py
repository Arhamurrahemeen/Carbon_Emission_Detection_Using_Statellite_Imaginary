"""Per-overpass cleaning (gate 1) and monthly plume features.
For a fixed emission, the column enhancement falls as wind rises (dilution), so enhancement x wind speed
(flux_proxy) is the quantity that scales with what the plant burns."""
import numpy as np
import pandas as pd

from verify.gate import check_cloud, check_no2, check_weather
from verify.rules import RULES


def _codes(row) -> list[str]:
    codes = []
    for col in ("no2_down", "no2_up", "no2_raw"):
        codes += check_no2(row[col])
    codes += check_cloud(row["cloud_fraction"])
    codes += check_weather(wind_speed=row["wind_speed"], wind_dir=row["wind_dir"])
    return sorted(set(codes))


def clean_overpasses(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (kept, rejected). Calm overpasses (no plume direction) are dropped from both."""
    df = df.copy()
    df["reason_codes"] = [_codes(r) for r in df.to_dict("records")]
    bad = df["reason_codes"].map(bool)
    rejected = df[bad]
    ok = df[~bad]
    kept = ok[ok["wind_speed"] >= RULES["calm_wind"]].drop(columns="reason_codes")
    return kept.reset_index(drop=True), rejected.reset_index(drop=True)


def monthly_features(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["month"] = d["date"].astype(str).str[:7]
    d["enh"] = d["no2_down"] - d["no2_up"]
    d["flux"] = d["enh"] * d["wind_speed"]
    flags = d["data_flags"] if "data_flags" in d else pd.Series("", index=d.index)
    d["is_synth"] = flags.fillna("").astype(str).str.contains("synthetic")
    g = d.groupby(["site_id", "month"])
    out = pd.DataFrame({
        "enh_mean": g["enh"].mean(),
        "flux_proxy": g["flux"].mean(),
        "raw_mean": g["no2_raw"].mean(),
        "valid_overpasses": g.size(),
        "wind_mean": g["wind_speed"].mean(),
        "synthetic": g["is_synth"].any(),
    }).reset_index()
    m = out["month"].str[5:7].astype(int)
    out["month_sin"] = np.sin(2 * np.pi * m / 12)
    out["month_cos"] = np.cos(2 * np.pi * m / 12)
    return out
