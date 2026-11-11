"""Validation gate (challenge C04). Each check returns a list of reason codes; empty means it passed.
Nothing downstream runs on an input that produced an E_ code."""
import math

import pandas as pd

from verify.rules import RULES


def _out(value, bounds) -> bool:
    lo, hi = bounds
    return value is None or not isinstance(value, (int, float)) or math.isnan(value) or value < lo or value > hi


def _missing(value) -> bool:
    return value is None or (isinstance(value, float) and math.isnan(value)) or value in RULES["fill_values"]


def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def check_location(lat, lon, sites: pd.DataFrame) -> list[str]:
    if _out(lat, RULES["lat_range"]) or _out(lon, RULES["lon_range"]):
        return ["E_COORD_RANGE"]
    near = any(_haversine_km(lat, lon, s.lat, s.lon) <= RULES["site_radius_km"] for s in sites.itertuples())
    return [] if near else ["E_SITE_UNKNOWN"]


def _fy_end(period: str) -> str:
    # FY2025 runs Jul 2024 - Jun 2025 (Pakistan fiscal year)
    return f"{int(period[2:]):04d}-06"


def check_period(period: str, last_month: str) -> list[str]:
    try:
        if period.upper().startswith("FY"):
            end = _fy_end(period.upper())
            start = f"{int(period[2:]) - 1:04d}-07"
        else:
            pd.Period(period, freq="M")
            start = end = period
    except (ValueError, TypeError):
        return ["E_DATE_RANGE"]
    if end < RULES["date_min"] or start > last_month or end > last_month:
        return ["E_DATE_RANGE"]
    return []


def check_weather(wind_speed=None, wind_dir=None, solar_irradiance=None, temperature=None) -> list[str]:
    pairs = [
        (wind_speed, RULES["wind_speed_range"]),
        (wind_dir, RULES["wind_dir_range"]),
        (solar_irradiance, RULES["irradiance_range"]),
        (temperature, RULES["temperature_range"]),
    ]
    bad = any(not _missing(v) and _out(v, b) for v, b in pairs)
    return ["E_WEATHER_RANGE"] if bad else []


def check_no2(value) -> list[str]:
    return ["E_NO2_RANGE"] if _out(value, RULES["no2_range"]) else []


def check_cloud(value) -> list[str]:
    return ["E_SAT_RANGE"] if _out(value, RULES["cloud_range"]) else []


def check_generation(generation_gwh, capacity_mw, days) -> list[str]:
    if generation_gwh is None or generation_gwh < 0:
        return ["E_CLAIM_RANGE"]
    max_gwh = capacity_mw * 24 * days / 1000 * RULES["cf_tolerance"]
    return ["E_CF_OVER_100"] if generation_gwh > max_gwh else []


def check_claim(claim: dict, page_text: str | None) -> list[str]:
    ctype, value = claim.get("claim_type"), claim.get("value")
    if ctype not in RULES["claim_types"]:
        return ["E_CLAIM_TYPE"]
    if value is None or not isinstance(value, (int, float)) or math.isnan(value) or value < 0:
        return ["E_CLAIM_RANGE"]
    if ctype == "reduction_pct" and value > 100:
        return ["E_REDUCTION_OVER_100"]
    if claim.get("entry_mode") == "extracted":
        raw = claim.get("raw_text") or ""
        if not raw or page_text is None or raw not in page_text:
            return ["E_CLAIM_NOT_IN_SOURCE"]
    return []


def check_ndvi(value) -> list[str]:
    return ["E_NDVI_RANGE"] if _out(value, RULES["ndvi_range"]) else []


def check_tree_density(trees, acres) -> list[str]:
    if not trees or trees <= 0 or not acres or acres <= 0 or trees / acres > RULES["max_trees_per_acre"]:
        return ["E_TREE_DENSITY"]
    return []


def check_share(share) -> list[str]:
    if share is None or not isinstance(share, (int, float)) or not (0 < share <= 1):
        return ["E_SHARE_RANGE"]
    return []


def check_confidence(valid_overpasses, features: dict, train_ranges: dict, interval_width, max_monthly_gwh) -> list[str]:
    codes = []
    if not valid_overpasses or valid_overpasses < RULES["min_overpasses"]:
        codes.append("W_FEW_OBS")
    for name, value in features.items():
        if name not in train_ranges:
            continue
        lo, hi = train_ranges[name]
        pad = (hi - lo) * RULES["ood_margin"]
        if value is None or math.isnan(value) or value < lo - pad or value > hi + pad:
            codes.append("W_OUT_OF_DISTRIBUTION")
            break
    if interval_width is not None and max_monthly_gwh and interval_width > RULES["max_interval_frac"] * max_monthly_gwh:
        codes.append("W_WIDE_INTERVAL")
    return codes


def _sahiwal_sites() -> pd.DataFrame:
    return pd.DataFrame([{"site_id": "sahiwal", "lat": 30.7142, "lon": 73.2380}])


# The eight live demo cases (spec section 8). Cases 1-5 are the five out-of-bounds injections C04 asks for.
GUARD_CASES = [
    {"id": 1, "name": "Impossible location", "input": "A plant at latitude 124.5 (no such place exists)",
     "expected_status": "REJECTED", "expected_code": "E_COORD_RANGE",
     "run": lambda: check_location(124.5, 73.2, _sahiwal_sites())},
    {"id": 2, "name": "Negative wind speed", "input": "A weather reading of -8 m/s wind at the plant",
     "expected_status": "REJECTED", "expected_code": "E_WEATHER_RANGE",
     "run": lambda: check_weather(wind_speed=-8.0)},
    {"id": 3, "name": "200% emissions cut", "input": "The company claims it cut emissions by 200%",
     "expected_status": "REJECTED", "expected_code": "E_REDUCTION_OVER_100",
     "run": lambda: check_claim({"claim_type": "reduction_pct", "value": 200.0, "entry_mode": "manual"}, None)},
    {"id": 4, "name": "Over 100% of capacity", "input": "Sahiwal (1,320 MW) reports 1,380 GWh in a 30-day month, a 145% capacity factor",
     "expected_status": "REJECTED", "expected_code": "E_CF_OVER_100",
     "run": lambda: check_generation(1380.0, 1320.0, 30)},
    {"id": 5, "name": "Broken greenness sensor", "input": "A tree plot reports a greenness (NDVI) of 1.8; the maximum possible is 1",
     "expected_status": "REJECTED", "expected_code": "E_NDVI_RANGE",
     "run": lambda: check_ndvi(1.8)},
    {"id": 6, "name": "Monsoon month, few clear days", "input": "A valid August with only 2 cloud-free satellite passes",
     "expected_status": "LOW_CONFIDENCE", "expected_code": "W_FEW_OBS",
     "run": lambda: check_confidence(2, {}, {}, None, None)},
    {"id": 7, "name": "Figure not in the report", "input": "An extracted figure of 4,100 GWh that does not appear on the cited page",
     "expected_status": "REJECTED", "expected_code": "E_CLAIM_NOT_IN_SOURCE",
     "run": lambda: check_claim({"claim_type": "generation", "value": 4100.0, "raw_text": "4,100", "entry_mode": "extracted"},
                                "The plant delivered 4,255 GWh of net generation in FY2025.")},
    {"id": 8, "name": "Control: normal sensor noise", "input": "An NO2 reading of -0.00002 mol/m2, normal noise near zero",
     "expected_status": "OK", "expected_code": None,
     "run": lambda: check_no2(-0.00002)},
]
