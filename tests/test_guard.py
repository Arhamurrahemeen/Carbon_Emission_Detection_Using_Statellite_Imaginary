"""C04: out-of-bounds and hallucination guard. These are the cases injected live on Day 3."""
import pytest

from verify.gate import (
    GUARD_CASES,
    check_claim,
    check_confidence,
    check_generation,
    check_location,
    check_ndvi,
    check_no2,
    check_period,
    check_share,
    check_tree_density,
    check_weather,
)
from verify.records import make_record, status_for


@pytest.mark.parametrize("case", GUARD_CASES, ids=lambda c: c["name"])
def test_guard_case(case):
    codes = case["run"]()
    assert status_for(codes) == case["expected_status"]
    if case["expected_code"]:
        assert case["expected_code"] in codes
    else:
        assert codes == []


def test_five_out_of_bounds_cases_are_rejected():
    rejected = [c for c in GUARD_CASES if c["expected_status"] == "REJECTED"]
    assert len(rejected) >= 5


def test_rejected_record_has_no_estimate():
    r = make_record("emissions", ["E_COORD_RANGE"], "x", estimate_gwh=500, verdict="CONSISTENT")
    assert r["status"] == "REJECTED"
    assert "estimate_gwh" not in r and "verdict" not in r


def test_status_for_warning_and_ok():
    assert status_for(["W_FEW_OBS"]) == "LOW_CONFIDENCE"
    assert status_for(["W_FEW_OBS", "E_NO2_RANGE"]) == "REJECTED"
    assert status_for([]) == "OK"


def test_location(sites):
    assert check_location(124.5, 67.1, sites) == ["E_COORD_RANGE"]
    assert check_location(30.72, 73.24, sites) == []
    assert check_location(25.0, 70.0, sites) == ["E_SITE_UNKNOWN"]


def test_period():
    assert check_period("2025-01", "2026-10") == []
    assert check_period("2017-12", "2026-10") == ["E_DATE_RANGE"]
    assert check_period("2027-03", "2026-10") == ["E_DATE_RANGE"]
    assert check_period("FY2025", "2026-10") == []
    assert check_period("FY2028", "2026-10") == ["E_DATE_RANGE"]


def test_weather():
    assert check_weather(wind_speed=-8) == ["E_WEATHER_RANGE"]
    assert check_weather(solar_irradiance=-50) == ["E_WEATHER_RANGE"]
    assert check_weather(solar_irradiance=-999) == []  # NASA POWER fill value = missing, not a reading
    assert check_weather(wind_speed=4, wind_dir=370) == ["E_WEATHER_RANGE"]
    assert check_weather(wind_speed=4, wind_dir=90) == []


def test_no2_noise_passes_but_impossible_rejects():
    assert check_no2(-0.00002) == []
    assert check_no2(-0.002) == ["E_NO2_RANGE"]
    assert check_no2(0.5) == ["E_NO2_RANGE"]


def test_generation_capacity_factor():
    assert "E_CF_OVER_100" in check_generation(1300, 1320, 30)  # max ~950 GWh in 30 days
    assert check_generation(900, 1320, 30) == []
    assert check_generation(-5, 1320, 30) == ["E_CLAIM_RANGE"]


def test_claims():
    assert check_claim({"claim_type": "reduction_pct", "value": 200, "entry_mode": "manual"}, None) == ["E_REDUCTION_OVER_100"]
    assert check_claim({"claim_type": "colour", "value": 1, "entry_mode": "manual"}, None) == ["E_CLAIM_TYPE"]
    assert check_claim({"claim_type": "co2_total", "value": -1, "entry_mode": "manual"}, None) == ["E_CLAIM_RANGE"]
    extracted = {"claim_type": "generation", "value": 4100, "raw_text": "4,100", "entry_mode": "extracted"}
    assert check_claim(extracted, "net generation of 4,255 GWh") == ["E_CLAIM_NOT_IN_SOURCE"]
    assert check_claim(extracted, "the plant dispatched 4,100 GWh") == []


def test_trees_and_share():
    assert check_ndvi(1.8) == ["E_NDVI_RANGE"]
    assert check_ndvi(0.6) == []
    assert check_share(2.0) == ["E_SHARE_RANGE"]
    assert check_share(0.5) == []
    assert check_tree_density(5000, 2) == ["E_TREE_DENSITY"]
    assert check_tree_density(500, 2) == []


def test_confidence():
    assert check_confidence(2, {}, {}, 10, 1000) == ["W_FEW_OBS"]
    assert check_confidence(12, {"flux_proxy": 5.0}, {"flux_proxy": (0.0, 1.0)}, 10, 1000) == ["W_OUT_OF_DISTRIBUTION"]
    assert check_confidence(12, {"flux_proxy": 1.05}, {"flux_proxy": (0.0, 1.0)}, 10, 1000) == []  # inside 10% margin
    assert check_confidence(12, {}, {}, 600, 1000) == ["W_WIDE_INTERVAL"]
