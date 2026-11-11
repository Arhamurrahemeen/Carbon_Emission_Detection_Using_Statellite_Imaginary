"""One command rebuilds every output:  python -m verify.build [--root .]
Reads data/, writes outputs/. The app reads outputs/ only."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import zlib

import numpy as np
import pandas as pd

from verify import c07, claims as claims_mod, trees
from verify.features import clean_overpasses, monthly_features
from verify.gate import GUARD_CASES, check_tree_density
from verify.io import SATELLITE_MONTHS, load_inputs
from verify.model import evaluate, fit, join_labels, loo_predictions, predict, window_detection
from verify.records import make_record
from verify.rules import RULES, SITE_PLANTS
from verify.synthetic import make_nepra
from verify.value import exposure, load_assumptions
from verify.verdict import emissions_record, fiscal_rollup, fy_months

DEMO_FY, PREV_FY = "FY2026", "FY2025"


def claim_detection(records: list[dict]) -> dict:
    ok = [r for r in records if r.get("status") == "OK" and r.get("claim_scale") is not None]
    mis = [r for r in ok if r["claim_scale"] < 1]
    true = [r for r in ok if r["claim_scale"] == 1]
    rate = lambda rs: float(np.mean([r["verdict"] == "INCONSISTENT" for r in rs])) if rs else None
    scales = sorted({r["claim_scale"] for r in mis})
    return {"detection_rate": rate(mis), "false_alarm_rate": rate(true), "n_misstated": len(mis), "n_true": len(true),
            "by_scale": {str(s): rate([r for r in mis if r["claim_scale"] == s]) for s in scales}}


def _site_labels(inputs, site_id, capacity, real_overpasses):
    """Train on real labels only when the NO2 features are real too; never pair synthetic NO2 with real labels."""
    if real_overpasses and inputs["real_labels"] is not None:
        return inputs["real_labels"], "real"
    return make_nepra(site_id, SATELLITE_MONTHS, capacity, seed=zlib.crc32(site_id.encode()) % 100), "synthetic"


def _fy_sum(labels: pd.DataFrame, site_id: str, fy: str) -> float | None:
    gen = join_labels(pd.DataFrame({"site_id": site_id, "month": fy_months(fy)}), labels, SITE_PLANTS)["generation_gwh"]
    return float(gen.sum()) if gen.notna().all() else None


def _pollution(inputs, site, metrics, records, monthly_rows, synth_claim_recs):
    sid, cap = site["site_id"], site["capacity_mw"]
    real_ov = inputs["sources"][f"overpasses_{sid}"] == "real"
    kept, rejected = clean_overpasses(inputs["overpasses"][sid])
    feats = monthly_features(kept)
    labels, label_source = _site_labels(inputs, sid, cap, real_ov)
    data = join_labels(feats, labels, SITE_PLANTS).sort_values("month").reset_index(drop=True)
    if inputs["real_labels"] is not None:
        real = join_labels(feats[["site_id", "month"]], inputs["real_labels"], SITE_PLANTS)
        data["metered_gwh"] = real["generation_gwh"].to_numpy()
    lab = data.dropna(subset=["generation_gwh"])
    holdout = max(3, min(12, len(lab) // 3))
    metrics[sid] = evaluate(data, holdout, cap, RULES["fleet_pf_imported_coal"]) | {"label_source": label_source,
                                                                                 "overpasses_rejected": int(len(rejected))}
    annual = window_detection(lab) if len(lab) >= 15 else None
    metrics[sid]["annual"] = annual
    model = fit(lab)
    pred = predict(model, data)
    pred["estimate_source"] = "full_model"
    # Months with a known answer show a leave-one-out estimate, so no shown number was fitted to its own answer.
    loo, q80_loo, _ = loo_predictions(lab)
    idx = lab.sort_values("month").index
    pred.loc[idx, "estimate_gwh"] = loo
    pred.loc[idx, "interval_low"] = np.clip(loo - q80_loo, 0, None)
    pred.loc[idx, "interval_high"] = loo + q80_loo
    pred.loc[idx, "estimate_source"] = "leave_one_out"
    month_recs = []
    for row, p in zip(data.to_dict("records"), pred.to_dict("records")):
        rec = emissions_record(site, row, p, None, model)
        month_recs.append(rec)
        monthly_rows.append({**row, **p, "status": rec["status"], "reason_codes": ";".join(rec["reason_codes"])})
    records.extend(month_recs)
    # Detection test: labelled synthetic claims on held-out months, scored by a model that never saw them.
    train, test = lab.iloc[:-holdout], lab.iloc[-holdout:]
    m_train = fit(train)
    p_test = predict(m_train, test)
    synth = claims_mod.make_synthetic_claims(test[["site_id", "month", "generation_gwh"]])
    by_month = {r["month"]: (r, pp) for r, pp in zip(test.to_dict("records"), p_test.to_dict("records"))}
    for c in synth.to_dict("records"):
        row, pp = by_month[c["period"]]
        rec = emissions_record(site, row, pp, c, m_train)
        rec["claim_scale"] = c["scale"]
        synth_claim_recs.append(rec)
    return month_recs, labels


def _demo_claims(site_id: str, metered_fy: float, metered_prev: float | None, ef_low: float) -> list[dict]:
    """Labelled synthetic company claims for the C12 demo, built from real metered numbers."""
    understated = round(metered_fy * 0.75)
    base = {"entry_mode": "synthetic", "source_page": None, "data_flags": "synthetic", "period": DEMO_FY}
    out = [
        {**base, "claim_type": "generation", "value": float(understated), "modality": "table", "raw_text": f"{understated:,}",
         "source_quote": f"Table: Net generation {DEMO_FY}: {understated:,} GWh (synthetic)"},
        {**base, "claim_type": "generation", "value": float(round(understated * 1.04)), "modality": "text",
         "raw_text": f"{round(understated * 1.04):,}", "source_quote": "Narrative: the plant delivered about the same energy as the table states (synthetic)"},
        {**base, "claim_type": "co2_total", "value": float(round(understated * 1000 * ef_low)), "modality": "table",
         "raw_text": "", "source_quote": "Table: Scope 1 emissions (synthetic)"},
        {**base, "claim_type": "trees_planted", "value": 50000.0, "modality": "text", "raw_text": "50,000",
         "source_quote": "Narrative: we planted 50,000 trees across Sindh (synthetic)"},
    ]
    if metered_prev:
        out.append({**base, "claim_type": "reduction_pct", "value": 25.0, "modality": "text", "raw_text": "25%",
                    "source_quote": f"Narrative: we reduced our carbon emissions by 25% compared to {PREV_FY} (synthetic)"})
    return out


def _trees(inputs, records, rows):
    plots, passes = inputs["plots"], inputs["plot_passes"].copy()
    have_features = set(c07.TREE_FEATURES) <= set(passes.columns)
    model = c07.train_tree_model(inputs["c07_samples"][inputs["c07_samples"]["split"] == "train"]) if have_features else None
    latest_imagery = str(passes.dropna(subset=["ndvi"])["date"].max())
    latest = {}
    for p in plots.to_dict("records"):
        dens = check_tree_density(p["trees_planted"], p["acres"])
        for row in passes[passes["plot_id"] == p["plot_id"]].sort_values("date").to_dict("records"):
            if str(row["date"]) < str(p["contract_since"]):
                continue
            flags = [f for f in str(row.get("data_flags") or "").split(";") if f and f != "nan"] + ["invented_farmer"]
            if dens:
                status, codes = "invalid", dens
            else:
                if model is not None and not pd.isna(row.get("ndvi_p10")):
                    prob = float(c07.classify(model, pd.DataFrame([row]))[0])
                    if inputs["sources"]["c07_samples"] != "real":
                        flags.append("classifier_trained_on_synthetic")
                elif not pd.isna(row.get("ndvi")):
                    prob, flags = (1.0 if row["ndvi"] >= 0.35 else 0.0), flags + ["threshold_fallback"]
                else:
                    prob = None
                status, codes = trees.verify_pass(row, latest_imagery, prob)
            pay = trees.payout(int(p["trees_planted"]), status)
            msg = {"verified": "Trees confirmed alive; payment released.", "failed": "No living trees seen; payment held.",
                   "cloudy": "Clouds hide the plot; payment waits for a clear image.",
                   "no_imagery": "No satellite image for this date yet; nothing paid or held.",
                   "invalid": "Impossible reading; no payment made on it."}[status]
            records.append(make_record("tree_pass", codes, msg, plot_id=p["plot_id"], period=str(row["date"]),
                                       pass_status=status, data_flags=sorted(set(flags)), **pay))
            rows.append({"plot_id": p["plot_id"], "farmer_name": p["farmer"], "date": row["date"], "ndvi": row.get("ndvi"),
                         "cloud": row.get("cloud"), "status": status, "reason_codes": ";".join(codes),
                         "trees": p["trees_planted"], "released": pay["released"], "farmer_pkr": pay["farmer"],
                         "financier_pkr": pay["financier"], "held": pay["held"], "data_flags": ";".join(sorted(set(flags)))})
            if status in ("verified", "failed", "invalid"):
                latest[p["plot_id"]] = status
    return trees.verified_trees(plots, latest)


def _write(out: Path, name: str, rows: list[dict]):
    df = pd.DataFrame(rows)
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (list, dict, tuple))).any():
            df[col] = df[col].map(lambda v: ";".join(map(str, v)) if isinstance(v, list) else json.dumps(v) if isinstance(v, (dict, tuple)) else v)
    df.to_csv(out / name, index=False)


def build(root: Path) -> dict:
    root = Path(root)
    inputs = load_inputs(root)
    assumptions = load_assumptions(inputs["assumptions_path"])
    out = root / "outputs"
    out.mkdir(exist_ok=True)
    records, monthly_rows, synth_recs, cross_rows, tree_rows = [], [], [], [], []
    pollution = {}
    verified = _trees(inputs, records, tree_rows)

    for site in inputs["sites"].to_dict("records"):
        month_recs, labels = _pollution(inputs, site, pollution, records, monthly_rows, synth_recs)
        lag1 = (pollution[site["site_id"]].get("annual") or {}).get("residual_lag1", 0.0)
        inflate = (1 + lag1) / (1 - lag1) if 0 < lag1 < 0.95 else 1.0
        fy = fiscal_rollup(month_recs, DEMO_FY, site, inflate=inflate)
        fy_prev = fiscal_rollup(month_recs, PREV_FY, site, inflate=inflate)
        records += [fy, fy_prev]
        metered_src = inputs["real_labels"] if inputs["real_labels"] is not None else labels
        metered, metered_prev = _fy_sum(metered_src, site["site_id"], DEMO_FY), _fy_sum(metered_src, site["site_id"], PREV_FY)
        if metered is None:
            continue
        cl = inputs["claims"]
        site_claims = (cl[cl["site_id"] == site["site_id"]].to_dict("records") if cl is not None
                       else _demo_claims(site["site_id"], metered, metered_prev, site["ef_low"]))
        sat = lambda r: {"low": r.get("interval_low"), "high": r.get("interval_high"), "status": r["status"]} if "interval_low" in r else None
        evidence = {"nepra_gwh": metered, "nepra_prev_gwh": metered_prev, "sat": sat(fy), "sat_prev": sat(fy_prev),
                    "ef": (site["ef_low"], site["ef_high"]), "verified_trees": verified if site["site_id"] == "sahiwal" else None}
        checks = claims_mod.cross_check(site["site_id"], DEMO_FY, site_claims, evidence)
        verdict = claims_mod.claim_verdict(checks)
        for c in checks:
            cross_rows.append({"site_id": site["site_id"], "period": DEMO_FY, **c})
        co2 = next((c["value"] for c in site_claims if c["claim_type"] == "co2_total"), None)
        exp = exposure(fy["co2_low_t"], fy["co2_high_t"], assumptions, declared_t=co2) if "co2_low_t" in fy else None
        msg = {"INCONSISTENT": "At least one company claim disagrees with independent evidence. Refer for review.",
               "CONSISTENT": "Company claims agree with the independent evidence available.",
               "CANNOT_VERIFY": "Not enough independent evidence to check these claims."}[verdict]
        flags = sorted({f for c in site_claims for f in str(c.get("data_flags") or "").split(";") if f})
        records.append(make_record("claim_check", [], msg, site_id=site["site_id"], period=DEMO_FY, verdict=verdict,
                                   n_checks=len(checks), n_contradictions=sum(c["result"] == "CONTRADICT" for c in checks),
                                   metered_gwh=metered, exposure=exp, data_flags=flags))

    guard_rows = []
    for case in GUARD_CASES:
        codes = case["run"]()
        rec = make_record("guard_test", codes, case["input"], case=case["name"], case_id=case["id"])
        ok = rec["status"] == case["expected_status"] and (case["expected_code"] in codes if case["expected_code"] else codes == [])
        guard_rows.append({**rec, "expected_status": case["expected_status"], "expected_code": case["expected_code"], "passed": ok})
        records.append(rec)

    records += synth_recs
    metrics = {
        "pollution": pollution,
        "trees": c07.benchmark(inputs["c07_samples"], inputs["c07_hand"]),
        "claims": claim_detection(synth_recs),
        "verified_trees": verified,
        "sources": inputs["sources"] | {"labels": next(iter({m["label_source"] for m in pollution.values()}), "synthetic")
                                         if len({m["label_source"] for m in pollution.values()}) == 1 else "mixed"},
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _write(out, "monthly.csv", monthly_rows)
    _write(out, "verdicts.csv", records)
    _write(out, "cross_checks.csv", cross_rows)
    _write(out, "tree_passes.csv", tree_rows)
    _write(out, "guard_results.csv", guard_rows)
    if inputs["climate_trace"] is not None:
        inputs["climate_trace"].to_csv(out / "climate_trace.csv", index=False)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    m = build(Path(ap.parse_args().root))
    for sid, p in m["pollution"].items():
        print(f"{sid}: RMSE {p['rmse']:.1f} GWh, r {p['r']}, coverage {p['coverage_80']:.2f}, "
              f"gain vs capacity {p['gain_vs_capacity_pct']}%, vs raw NO2 {p['gain_vs_raw_pct']}% (labels: {p['label_source']})")
    t = m["trees"]["test"]
    print(f"trees: RF F1 {t['rf_f1']:.3f} vs threshold {t['baseline_tuned_f1']:.3f} (gain {t['gain_vs_tuned_pct']}%)")
    print(f"claims (monthly): detection {m['claims']['detection_rate']}, false alarms {m['claims']['false_alarm_rate']}")
    for sid, p in m["pollution"].items():
        a = p.get("annual")
        if a:
            print(f"{sid} annual windows: n={a['n_windows']} half-width {a['half_width_gwh']:.0f} GWh, detection {a['detection_rate']:.2f} "
                  f"(by scale {a['by_scale']}), false alarms {a['false_alarm_rate']:.2f}, residual lag1 {a['residual_lag1']:.2f}")
    print("sources:", m["sources"])
