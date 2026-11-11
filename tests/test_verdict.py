import pytest

from verify.rules import BANNED_WORDS
from verify.value import exposure
from verify.verdict import MESSAGES, co2_range, compare, emissions_record, fiscal_rollup

SITE = {"site_id": "sahiwal", "capacity_mw": 1320, "ef_low": 0.80, "ef_high": 0.95}
MODEL = {"train_ranges": {"flux_proxy": (0.0, 1e-3)}, "max_monthly_gwh": 700.0, "q80": 80.0}


def _row(month="2025-01", n=15, flux=5e-4):
    return {"site_id": "sahiwal", "month": month, "valid_overpasses": n, "flux_proxy": flux, "synthetic": False}


def _pred(est=510.0):
    return {"estimate_gwh": est, "interval_low": est - 80, "interval_high": est + 80}


def test_compare():
    assert compare(300, 430, 590) == ("INCONSISTENT", -30.2)
    assert compare(650, 430, 590) == ("INCONSISTENT", 10.2)
    assert compare(500, 430, 590) == ("CONSISTENT", None)


def test_co2_range_in_tonnes():
    assert co2_range(400, 500, 0.8, 0.95) == (320000.0, 475000.0)


def test_inconsistent_claim_record():
    claim = {"claim_type": "generation", "value": 300.0, "entry_mode": "manual"}
    r = emissions_record(SITE, _row(), _pred(), claim, MODEL)
    assert r["status"] == "OK" and r["verdict"] == "INCONSISTENT" and r["gap_pct"] == -30.2
    assert "below the lowest value" in r["message"]
    assert r["co2_low_t"] == pytest.approx(430 * 1000 * 0.80)


def test_low_confidence_month_cannot_verify_but_shows_estimate():
    claim = {"claim_type": "generation", "value": 300.0, "entry_mode": "manual"}
    r = emissions_record(SITE, _row(n=2), _pred(), claim, MODEL)
    assert r["status"] == "LOW_CONFIDENCE" and r["verdict"] == "CANNOT_VERIFY"
    assert "W_FEW_OBS" in r["reason_codes"] and "estimate_gwh" in r


def test_month_with_no_overpasses_does_not_crash():
    r = emissions_record(SITE, None, None, None, MODEL)
    assert r["status"] == "LOW_CONFIDENCE" and "W_FEW_OBS" in r["reason_codes"]
    assert r["verdict"] == "CANNOT_VERIFY"


def test_impossible_claim_is_rejected_with_no_estimate():
    claim = {"claim_type": "generation", "value": 1400.0, "entry_mode": "manual"}
    r = emissions_record(SITE, _row(), _pred(), claim, MODEL)
    assert r["status"] == "REJECTED" and "E_CF_OVER_100" in r["reason_codes"]
    assert "estimate_gwh" not in r and "verdict" not in r


def test_co2_claim_compared_with_co2_range():
    claim = {"claim_type": "co2_total", "value": 100000.0, "entry_mode": "manual"}
    r = emissions_record(SITE, _row(), _pred(), claim, MODEL)
    assert r["verdict"] == "INCONSISTENT" and r["gap_pct"] < 0


def test_fiscal_rollup_low_confidence_when_too_many_thin_months():
    months = ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
              "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    recs = [emissions_record(SITE, _row(m, n=2 if i < 4 else 15), _pred(400), None, MODEL) for i, m in enumerate(months)]
    fy = fiscal_rollup(recs, "FY2025", SITE)
    assert fy["status"] == "LOW_CONFIDENCE" and fy["estimate_gwh"] == pytest.approx(4800)
    ok = fiscal_rollup([emissions_record(SITE, _row(m), _pred(400), None, MODEL) for m in months], "FY2025", SITE,
                       claim={"claim_type": "generation", "value": 4800.0, "entry_mode": "manual"})
    assert ok["status"] == "OK" and ok["verdict"] == "CONSISTENT"


def test_fiscal_rollup_adds_monthly_errors_in_quadrature_and_rechecks_width():
    months = ["2024-07", "2024-08", "2024-09", "2024-10", "2024-11", "2024-12",
              "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06"]
    narrow_max = {**MODEL, "max_monthly_gwh": 200.0}  # a 160 GWh monthly interval is "too wide" for one month
    recs = [emissions_record(SITE, _row(m), _pred(400), None, narrow_max) for m in months]
    assert all(r["reason_codes"] == ["W_WIDE_INTERVAL"] for r in recs)
    fy = fiscal_rollup(recs, "FY2025", SITE)
    half = 80 * 12 ** 0.5
    assert fy["status"] == "OK"
    assert fy["interval_low"] == pytest.approx(4800 - half, abs=0.2)
    assert fy["interval_high"] == pytest.approx(4800 + half, abs=0.2)
    assert fy["months_low_confidence"] == 0


def test_messages_never_use_banned_words():
    for text in MESSAGES.values():
        assert not any(w in text.lower() for w in BANNED_WORDS)


def test_exposure_ranges():
    a = {"carbon_price_low": 5.0, "carbon_price_high": 80.0}
    e = exposure(300000, 400000, a, declared_t=250000)
    assert e["carbon_cost_usd"] == (1_500_000.0, 32_000_000.0)
    assert e["misstatement_usd"] == (250_000.0, 12_000_000.0)
    assert exposure(300000, 400000, a)["misstatement_usd"] is None
