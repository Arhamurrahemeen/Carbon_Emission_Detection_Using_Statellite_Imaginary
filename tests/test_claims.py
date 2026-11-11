"""C12: declared figures vs text claims vs satellite and metered evidence."""
import pandas as pd
import pytest

from verify.claims import claim_verdict, cross_check, extract_claims, make_synthetic_claims, parse_number

EV = {"nepra_gwh": 4255.0, "nepra_prev_gwh": 3800.0, "sat": {"low": 3900.0, "high": 4600.0, "status": "OK"},
      "sat_prev": {"low": 3400.0, "high": 4100.0, "status": "OK"}, "ef": (0.80, 0.95), "verified_trees": 30500}


def _claim(ctype, value, modality="table", raw=None):
    return {"claim_type": ctype, "value": value, "modality": modality, "raw_text": raw or str(value),
            "entry_mode": "manual", "source_page": 1, "source_quote": "q"}


def _pair(checks, pair):
    return [c for c in checks if c["pair"] == pair]


def test_parse_number():
    assert parse_number("4,255") == 4255.0
    assert parse_number("25%") == 25.0
    assert parse_number("3.5 million") == 3_500_000.0


def test_extract_generation_from_table_like_line():
    pages = [{"page": 12, "text": "In FY2025 the plant dispatched 4,100 GWh to the national grid."}]
    c = extract_claims(pages, "hub_ar_2025")[0]
    assert (c["claim_type"], c["value"], c["source_page"], c["raw_text"]) == ("generation", 4100.0, 12, "4,100")
    assert c["entry_mode"] == "extracted" and c["source"] == "hub_ar_2025"


def test_extract_reduction_and_trees_from_narrative():
    pages = [{"page": 3, "text": "We reduced our carbon emissions by 25% compared to last year. "
                                 "Under our green drive we planted 50,000 trees across Sindh."}]
    got = {c["claim_type"]: c for c in extract_claims(pages, "r")}
    assert got["reduction_pct"]["value"] == 25.0 and got["reduction_pct"]["modality"] == "text"
    assert got["trees_planted"]["value"] == 50000.0


def test_extract_co2_in_million_tonnes():
    pages = [{"page": 7, "text": "Scope 1 emissions were 3.5 million tonnes of CO2 in FY2025."}]
    c = extract_claims(pages, "r")[0]
    assert c["claim_type"] == "co2_total" and c["value"] == 3_500_000.0


def test_x1_declared_vs_metered():
    assert _pair(cross_check("sahiwal", "FY2025", [_claim("generation", 4100.0)], EV), "X1")[0]["result"] == "AGREE"
    assert _pair(cross_check("sahiwal", "FY2025", [_claim("generation", 3000.0)], EV), "X1")[0]["result"] == "CONTRADICT"


def test_x2_cannot_compare_when_satellite_thin():
    ev = {**EV, "sat": {**EV["sat"], "status": "LOW_CONFIDENCE"}}
    assert _pair(cross_check("sahiwal", "FY2025", [_claim("generation", 4100.0)], ev), "X2")[0]["result"] == "CANNOT_COMPARE"


def test_x3_x4_co2_vs_ranges():
    checks = cross_check("sahiwal", "FY2025", [_claim("co2_total", 1_000_000.0)], EV)
    assert _pair(checks, "X3")[0]["result"] == "CONTRADICT"
    assert _pair(checks, "X4")[0]["result"] == "CONTRADICT"


def test_x5_text_reduction_vs_rising_generation():
    checks = cross_check("sahiwal", "FY2025", [_claim("reduction_pct", 25.0, "text")], EV)
    x5 = _pair(checks, "X5")
    assert x5 and all(c["result"] == "CONTRADICT" for c in x5)


def test_x6_tree_claim_vs_verified():
    checks = cross_check("sahiwal", "FY2025", [_claim("trees_planted", 50000.0, "text")], EV)
    assert _pair(checks, "X6")[0]["result"] == "CONTRADICT"
    ok = cross_check("sahiwal", "FY2025", [_claim("trees_planted", 31000.0, "text")], EV)
    assert _pair(ok, "X6")[0]["result"] == "AGREE"


def test_x7_table_vs_narrative_same_metric():
    checks = cross_check("sahiwal", "FY2025", [_claim("generation", 4100.0, "table"), _claim("generation", 4300.0, "text")], EV)
    assert _pair(checks, "X7")[0]["result"] == "CONTRADICT"


def test_claim_verdict():
    assert claim_verdict([{"pair": "X1", "result": "CONTRADICT"}, {"pair": "X2", "result": "AGREE"}]) == "INCONSISTENT"
    assert claim_verdict([{"pair": "X1", "result": "AGREE"}, {"pair": "X2", "result": "AGREE"}]) == "CONSISTENT"
    assert claim_verdict([{"pair": "X2", "result": "CANNOT_COMPARE"}]) == "CANNOT_VERIFY"
    assert claim_verdict([{"pair": "X7", "result": "CONTRADICT"}, {"pair": "X1", "result": "AGREE"}]) == "CONSISTENT"


def test_synthetic_claims_are_labelled_with_scale():
    gen = pd.DataFrame({"site_id": ["sahiwal"] * 3, "month": ["2025-01", "2025-02", "2025-03"], "generation_gwh": [600.0, 0.0, 363.0]})
    s = make_synthetic_claims(gen)
    assert (s["data_flags"].str.contains("synthetic")).all()
    assert set(s["scale"]) >= {0.8, 0.6, 0.4, 1.0}
    assert {"site_id", "period", "claim_type", "value", "scale"} <= set(s.columns)
