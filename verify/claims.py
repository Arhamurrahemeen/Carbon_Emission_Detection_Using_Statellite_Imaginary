"""Challenge C12: claim extraction and multi-source cross-check.
Extraction is rule-based (no LLM): every extracted value keeps its page, sentence and the number exactly as printed,
and the gate rejects it (E_CLAIM_NOT_IN_SOURCE) if that string is not on the cited page. A person confirms each
claim before it is used. Cross-checks X1-X7 follow design spec section 7.3."""
import re

import numpy as np
import pandas as pd

from verify.rules import RULES

NUM = r"(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)(\s*(?:million|mn|billion))?"
PATTERNS = {
    "generation": re.compile(NUM + r"\s*(GWh|MWh|million units|million kWh)", re.I),
    "co2_total": re.compile(NUM + r"\s*(?:tonnes|tons|t)\s*(?:of\s+)?CO2e?|" + NUM + r"\s*tCO2e?", re.I),
    "trees_planted": re.compile(NUM + r"\s+(?:\w+\s+){0,2}trees", re.I),
    "reduction_pct": re.compile(r"(?:reduc|cut|lower)\w*[^.%]{0,60}?(\d+(?:\.\d+)?)\s?%", re.I),
}
CONTEXT = {"generation": re.compile(r"generat|dispatch|deliver|produc", re.I),
           "trees_planted": re.compile(r"plant", re.I)}
INDEPENDENT = {"X1", "X2", "X3", "X4", "X5", "X6"}


def parse_number(s: str) -> float:
    s = s.strip().lower().replace(",", "").replace("%", "")
    mult = 1.0
    for word, m in (("billion", 1e9), ("million", 1e6), ("mn", 1e6)):
        if s.endswith(word):
            s, mult = s[: -len(word)].strip(), m
    return float(s) * mult


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if s.strip()]


def _modality(sentence: str) -> str:
    return "table" if len(re.findall(r"\d[\d,.]*", sentence)) >= 3 else "text"


def extract_claims(pages: list[dict], source: str) -> list[dict]:
    out = []
    for page in pages:
        for sent in _sentences(page["text"]):
            for ctype, pat in PATTERNS.items():
                if ctype in CONTEXT and not CONTEXT[ctype].search(sent):
                    continue
                m = pat.search(sent)
                if not m:
                    continue
                groups = [g for g in m.groups() if g is not None]
                raw = groups[0]
                value = parse_number(raw + (groups[1] if len(groups) > 1 and re.match(r"\s*(million|mn|billion)", groups[1] or "", re.I) else ""))
                unit = m.group(0)[len(raw):].strip()
                if ctype == "generation" and unit.lower().startswith("mwh"):
                    value /= 1000  # store generation in GWh
                out.append({"claim_type": ctype, "value": value, "unit": unit, "period": None,
                            "source_page": page["page"], "source_quote": sent, "raw_text": raw,
                            "modality": "text" if ctype in ("reduction_pct", "trees_planted") else _modality(sent),
                            "entry_mode": "extracted", "source": source})
    return out


def _rel(a: float, b: float) -> float:
    return abs(a - b) / b if b else float("inf")


def _inside(v, lo, hi) -> bool:
    return lo <= v <= hi


def _check(pair, left, right, ok, reason):
    return {"pair": pair, "left": left, "right": right, "result": "AGREE" if ok else "CONTRADICT", "reason": reason}


def _na(pair, left, right, reason):
    return {"pair": pair, "left": left, "right": right, "result": "CANNOT_COMPARE", "reason": reason}


def cross_check(site_id: str, period: str, claims: list[dict], evidence: dict) -> list[dict]:
    ev, out = evidence, []
    sat, ef = ev.get("sat"), ev.get("ef", (None, None))
    sat_ok = sat is not None and sat.get("status") == "OK"
    for c in claims:
        t, v, lbl = c["claim_type"], float(c["value"]), f"{c['modality']} claim {c['value']:,.0f}"
        if t == "generation":
            if ev.get("nepra_gwh") is not None:
                d = _rel(v, ev["nepra_gwh"])
                out.append(_check("X1", lbl + " GWh", f"metered {ev['nepra_gwh']:,.0f} GWh", d <= RULES["nepra_match_tol"],
                                  f"Differs from metered generation by {d * 100:.1f}% (tolerance {RULES['nepra_match_tol'] * 100:.0f}%)."))
            if sat_ok:
                out.append(_check("X2", lbl + " GWh", f"satellite {sat['low']:,.0f}-{sat['high']:,.0f} GWh",
                                  _inside(v, sat["low"], sat["high"]), "Compared with the satellite 80% range."))
            else:
                out.append(_na("X2", lbl + " GWh", "satellite range", "Satellite evidence too thin for this period."))
        elif t == "co2_total":
            if ev.get("nepra_gwh") is not None and ef[0]:
                lo, hi = ev["nepra_gwh"] * 1000 * ef[0], ev["nepra_gwh"] * 1000 * ef[1]
                out.append(_check("X3", lbl + " t", f"metered x factor {lo:,.0f}-{hi:,.0f} t", _inside(v, lo, hi),
                                  "Compared with metered generation x emission factor range."))
            if sat_ok and ef[0]:
                lo, hi = sat["low"] * 1000 * ef[0], sat["high"] * 1000 * ef[1]
                out.append(_check("X4", lbl + " t", f"satellite CO2 {lo:,.0f}-{hi:,.0f} t", _inside(v, lo, hi),
                                  "Compared with the satellite-derived CO2 range (derived, not measured)."))
            elif ef[0]:
                out.append(_na("X4", lbl + " t", "satellite CO2 range", "Satellite evidence too thin for this period."))
        elif t == "reduction_pct":
            claimed = -v
            if ev.get("nepra_gwh") is not None and ev.get("nepra_prev_gwh"):
                actual = (ev["nepra_gwh"] / ev["nepra_prev_gwh"] - 1) * 100
                out.append(_check("X5", f"text: cut of {v:.0f}%", f"metered change {actual:+.1f}%", actual <= claimed / 2,
                                  "Emissions follow coal burned; metered generation should fall by at least half the claimed cut."))
            sp = ev.get("sat_prev")
            if sat_ok and sp and sp.get("status") == "OK":
                lo, hi = (sat["low"] / sp["high"] - 1) * 100, (sat["high"] / sp["low"] - 1) * 100
                out.append(_check("X5", f"text: cut of {v:.0f}%", f"satellite change {lo:+.0f}% to {hi:+.0f}%",
                                  _inside(claimed, lo, hi), "Claimed change compared with the satellite year-on-year range."))
        elif t == "trees_planted":
            vt = ev.get("verified_trees")
            if vt is None:
                out.append(_na("X6", lbl + " trees", "verified trees", "No tree plots linked to this company."))
            else:
                out.append(_check("X6", lbl + " trees", f"satellite-verified {vt:,} trees", v <= vt * (1 + RULES["tree_claim_tol"]),
                                  f"Trees on plots whose latest satellite check passed (tolerance {RULES['tree_claim_tol'] * 100:.0f}%)."))
    by_type = {}
    for c in claims:
        by_type.setdefault(c["claim_type"], {}).setdefault(c["modality"], c)
    for t, mods in by_type.items():
        if "table" in mods and "text" in mods and t != "reduction_pct":
            a, b = float(mods["table"]["value"]), float(mods["text"]["value"])
            out.append(_check("X7", f"table {a:,.0f}", f"narrative {b:,.0f}", _rel(b, a) <= RULES["internal_match_tol"],
                              "The same figure stated twice in the report should match."))
    return out


def claim_verdict(checks: list[dict]) -> str:
    indep = [c for c in checks if c["pair"] in INDEPENDENT and c["result"] != "CANNOT_COMPARE"]
    if any(c["result"] == "CONTRADICT" for c in indep):
        return "INCONSISTENT"
    return "CONSISTENT" if indep else "CANNOT_VERIFY"


def make_synthetic_claims(gen: pd.DataFrame, scales=(0.8, 0.6, 0.4, 1.0)) -> pd.DataFrame:
    """Labelled synthetic generation claims built from real metered months: scaled down to test detection,
    scale 1.0 to measure false alarms."""
    rows = []
    for r in gen.dropna(subset=["generation_gwh"]).itertuples():
        for s in scales:
            rows.append({"site_id": r.site_id, "period": r.month, "claim_type": "generation",
                         "value": round(r.generation_gwh * s, 1), "scale": s, "modality": "table",
                         "entry_mode": "synthetic", "raw_text": "", "source_page": None,
                         "source_quote": f"Synthetic claim: metered generation x {s}", "data_flags": "synthetic"})
    return pd.DataFrame(rows)
