"""Verdict engine: compare a disclosed figure with the satellite-supported range and write one record.
CONSISTENT = inside the 80% interval. INCONSISTENT = outside (a reason to ask questions, not proof).
CANNOT_VERIFY = evidence too thin, or no claim."""
import math

import pandas as pd

from verify.gate import check_claim, check_confidence, check_generation
from verify.records import make_record, status_for
from verify.rules import RULES

MESSAGES = {
    "low": "Disclosed {metric} is {gap}% below the lowest value the satellite evidence supports. Refer for review.",
    "high": "Disclosed {metric} is {gap}% above the highest value the satellite evidence supports. Refer for review.",
    "consistent": "Disclosed {metric} is within the range the satellite evidence supports.",
    "thin": "Not enough clear satellite evidence for this period to check the claim.",
    "no_claim": "Satellite estimate shown. No company figure was supplied to check.",
    "rejected": "The input is impossible or unsupported, so no estimate was produced.",
}
METRIC = {"generation": "generation", "co2_total": "CO2 emissions"}


def compare(value: float, low: float, high: float) -> tuple[str, float | None]:
    if low <= value <= high:
        return "CONSISTENT", None
    edge = low if value < low else high
    return "INCONSISTENT", round((value - edge) / edge * 100, 1)


def co2_range(gen_low_gwh: float, gen_high_gwh: float, ef_low: float, ef_high: float) -> tuple[float, float]:
    return (round(gen_low_gwh * 1000 * ef_low, 1), round(gen_high_gwh * 1000 * ef_high, 1))


def _days(period: str) -> int:
    if period.upper().startswith("FY"):
        return 365
    return pd.Period(period, freq="M").days_in_month


def _judge(claim: dict | None, est: dict, site: dict, status: str) -> dict:
    out = {}
    if claim is None:
        return {"verdict": "CANNOT_VERIFY", "message": MESSAGES["no_claim"]}
    out.update(claim_type=claim["claim_type"], claim_value=claim["value"],
               claim_source_page=claim.get("source_page"), claim_quote=claim.get("source_quote"))
    if status != "OK" or claim["claim_type"] not in METRIC:
        return {**out, "verdict": "CANNOT_VERIFY", "message": MESSAGES["thin"]}
    if claim["claim_type"] == "generation":
        lo, hi = est["interval_low"], est["interval_high"]
    else:
        lo, hi = est["co2_low_t"], est["co2_high_t"]
    verdict, gap = compare(claim["value"], lo, hi)
    metric = METRIC[claim["claim_type"]]
    if verdict == "CONSISTENT":
        msg = MESSAGES["consistent"].format(metric=metric)
    else:
        msg = MESSAGES["low" if gap < 0 else "high"].format(metric=metric, gap=abs(gap))
    return {**out, "verdict": verdict, "gap_pct": gap, "message": msg}


def _claim_codes(claim: dict | None, site: dict, period: str) -> list[str]:
    if claim is None:
        return []
    codes = check_claim(claim, claim.get("page_text"))
    if not codes and claim["claim_type"] == "generation":
        codes += check_generation(claim["value"], site["capacity_mw"], _days(period))
    return codes


def _flags(row, claim) -> list[str]:
    flags = []
    if row is not None and row.get("synthetic"):
        flags.append("synthetic")
    if claim is not None:
        flags += [f for f in str(claim.get("data_flags") or "").split(";") if f]
        if claim.get("entry_mode") == "manual":
            flags.append("manual_entry")
    return sorted(set(flags))


def emissions_record(site: dict, month_row: dict | None, pred: dict | None, claim: dict | None, model: dict) -> dict:
    period = month_row["month"] if month_row else (claim or {}).get("period", "")
    n = int(month_row["valid_overpasses"]) if month_row and not pd.isna(month_row.get("valid_overpasses")) else 0
    codes = _claim_codes(claim, site, period) if period else []
    est = {}
    if pred is not None:
        est = {k: round(float(pred[k]), 1) for k in ("estimate_gwh", "interval_low", "interval_high")}
        est["co2_low_t"], est["co2_high_t"] = co2_range(est["interval_low"], est["interval_high"], site["ef_low"], site["ef_high"])
        feats = {f: month_row[f] for f in model["train_ranges"] if month_row and f in month_row}
        codes += check_confidence(n, feats, model["train_ranges"], est["interval_high"] - est["interval_low"], model["max_monthly_gwh"])
    else:
        codes.append("W_FEW_OBS")
    codes = sorted(set(codes))
    status = status_for(codes)
    judged = {"message": MESSAGES["rejected"]} if status == "REJECTED" else _judge(claim, est, site, status)
    message = judged.pop("message")
    return make_record("emissions", codes, message, site_id=site["site_id"], period=period,
                       valid_overpasses=n, max_monthly_gwh=model.get("max_monthly_gwh"), **est, **judged,
                       data_flags=_flags(month_row, claim))


def fy_months(fy: str) -> list[str]:
    end = int(fy[2:])
    return [str(p) for p in pd.period_range(f"{end - 1}-07", f"{end}-06", freq="M")]


def fiscal_rollup(records: list[dict], fy: str, site: dict, claim: dict | None = None, inflate: float = 1.0) -> dict:
    """inflate > 1 widens the year for positively autocorrelated monthly errors (effective sample size)."""
    months = set(fy_months(fy))
    recs = [r for r in records if r.get("period") in months and r["status"] != "REJECTED" and "estimate_gwh" in r]
    # A month that is only "too wide on its own" still counts: the year's width is re-checked below.
    thin = sum(any(c != "W_WIDE_INTERVAL" for c in r["reason_codes"]) for r in recs)
    codes = _claim_codes(claim, site, fy)
    if len(recs) < len(months) or thin > RULES["fy_low_conf_max"]:
        codes.append("W_FEW_OBS")
    est = {}
    if recs:
        # Independent monthly errors add in quadrature, so a year is much tighter than 12 x the monthly band.
        total = sum(r["estimate_gwh"] for r in recs)
        lo_half = math.sqrt(inflate * sum((r["estimate_gwh"] - r["interval_low"]) ** 2 for r in recs))
        hi_half = math.sqrt(inflate * sum((r["interval_high"] - r["estimate_gwh"]) ** 2 for r in recs))
        est = {"estimate_gwh": round(total, 1), "interval_low": round(max(0.0, total - lo_half), 1),
               "interval_high": round(total + hi_half, 1)}
        est["co2_low_t"], est["co2_high_t"] = co2_range(est["interval_low"], est["interval_high"], site["ef_low"], site["ef_high"])
        max_year = 12 * max((r.get("max_monthly_gwh") or 0) for r in recs) if any(r.get("max_monthly_gwh") for r in recs) else None
        if max_year and est["interval_high"] - est["interval_low"] > RULES["max_interval_frac"] * max_year:
            codes.append("W_WIDE_INTERVAL")
    codes = sorted(set(codes))
    status = status_for(codes)
    judged = {"message": MESSAGES["rejected"]} if status == "REJECTED" else _judge(claim, est, site, status)
    message = judged.pop("message")
    flags = sorted({f for r in recs for f in r.get("data_flags", [])} | set(_flags(None, claim)))
    return make_record("emissions", codes, message, site_id=site["site_id"], period=fy,
                       months_used=len(recs), months_low_confidence=thin, **est, **judged, data_flags=flags)
