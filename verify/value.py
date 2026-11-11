"""Financial value model (rubric: transparent financial assumptions). Always ranges, never a single figure.
Assumptions live in data/manual/assumptions.csv with their source and a demo flag."""
import csv
from pathlib import Path


def load_assumptions(path: Path) -> dict:
    with Path(path).open(newline="", encoding="utf-8") as fh:
        return {r["key"]: float(r["value"]) for r in csv.DictReader(fh)}


def exposure(co2_low_t: float, co2_high_t: float, assumptions: dict, declared_t: float | None = None) -> dict:
    lo_p, hi_p = assumptions["carbon_price_low"], assumptions["carbon_price_high"]
    out = {"carbon_cost_usd": (round(co2_low_t * lo_p, 1), round(co2_high_t * hi_p, 1)), "misstatement_usd": None}
    if declared_t is not None:
        out["misstatement_usd"] = (round(max(0.0, co2_low_t - declared_t) * lo_p, 1),
                                   round(max(0.0, co2_high_t - declared_t) * hi_p, 1))
    return out
