"""Risk officer's view: does the satellite evidence support this company's green claims?
Reads outputs/ only (run `python -m verify.build` first). Run: streamlit run app/streamlit_app.py"""
import json
import math
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from verify.gate import GUARD_CASES  # noqa: E402
from verify.records import make_record  # noqa: E402

OUT = ROOT / "outputs"
STATUS_COLOUR = {"OK": "#1b7f3b", "LOW_CONFIDENCE": "#b26a00", "REJECTED": "#b3261e"}
VERDICT_COLOUR = {"CONSISTENT": "#1b7f3b", "INCONSISTENT": "#b3261e", "CANNOT_VERIFY": "#5f6368"}
SHUTDOWNS = {"sahiwal": ["2024-11", "2025-02", "2025-10"]}  # metered generation ~0 (CPPA-G)

st.set_page_config(page_title="Green Claims Check", layout="wide")

if not (OUT / "metrics.json").exists():
    st.info("No results yet. Run `python -m verify.build` in the project folder, then reload.")
    st.stop()


@st.cache_data
def load():
    return {
        "metrics": json.loads((OUT / "metrics.json").read_text()),
        "monthly": pd.read_csv(OUT / "monthly.csv"),
        "verdicts": pd.read_csv(OUT / "verdicts.csv"),
        "cross": pd.read_csv(OUT / "cross_checks.csv"),
        "trees": pd.read_csv(OUT / "tree_passes.csv"),
        "sites": pd.read_csv(ROOT / "data" / "manual" / "sites.csv"),
        "assumptions": pd.read_csv(ROOT / "data" / "manual" / "assumptions.csv"),
        "trace": pd.read_csv(OUT / "climate_trace.csv") if (OUT / "climate_trace.csv").exists() else None,
    }


D = load()
M = D["metrics"]


def badge(text, colour):
    return f"<span style='background:{colour};color:white;padding:2px 10px;border-radius:12px;font-weight:600'>{text}</span>"


synthetic_inputs = [k for k, v in M["sources"].items() if v in ("synthetic", "missing")]
if synthetic_inputs:
    st.warning("Some inputs are synthetic test data, labelled throughout: " + ", ".join(synthetic_inputs))

page = st.sidebar.radio("View", ["Company check", "Tree contracts", "Reliability (C04)", "Model vs baseline (C07)", "Log"])
st.sidebar.caption("The satellite measures NO2, not CO2. CO2 is derived from estimated generation and shown as a range. "
                   "INCONSISTENT means refer for review, not proof of a false statement.")

# ---------------------------------------------------------------- Company check
if page == "Company check":
    sites = D["sites"].set_index("site_id")
    sid = st.selectbox("Company / plant", sites.index, format_func=lambda s: sites.loc[s, "name"])
    site = sites.loc[sid]
    st.title(site["name"])
    st.caption(f"Owner: {site['owner']} · Capacity {site['capacity_mw']:,} MW · {site['notes']}")

    v = D["verdicts"]
    claim = v[(v.kind == "claim_check") & (v.site_id == sid)]
    fy = v[(v.kind == "emissions") & (v.site_id == sid) & (v.period == "FY2026")]
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Verdict on the company's FY2026 claims")
        if len(claim):
            r = claim.iloc[0]
            st.markdown(badge(r["verdict"], VERDICT_COLOUR[r["verdict"]]), unsafe_allow_html=True)
            st.write(r["message"])
            st.caption(f"{int(r['n_contradictions'])} of {int(r['n_checks'])} checks disagree · flags: {r['data_flags']}")
        if len(fy):
            r = fy.iloc[0]
            st.markdown(f"**Satellite estimate FY2026:** {r['estimate_gwh']:,.0f} GWh "
                        f"(80% range {r['interval_low']:,.0f}–{r['interval_high']:,.0f}) · "
                        f"status {badge(r['status'], STATUS_COLOUR[r['status']])}", unsafe_allow_html=True)
            if not pd.isna(r.get("co2_low_t")):
                st.markdown(f"**CO2, derived, not measured:** {r['co2_low_t'] / 1e6:,.2f}–{r['co2_high_t'] / 1e6:,.2f} Mt")
        if len(claim) and isinstance(claim.iloc[0].get("exposure"), str):
            exp = json.loads(claim.iloc[0]["exposure"])
            lo, hi = exp["carbon_cost_usd"]
            st.markdown(f"**Carbon cost exposure (scenario):** USD {lo / 1e6:,.1f}M – {hi / 1e6:,.1f}M a year")
            if exp.get("misstatement_usd"):
                a, b = exp["misstatement_usd"]
                st.markdown(f"**Hidden by the disclosed CO2 figure:** USD {a / 1e6:,.1f}M – {b / 1e6:,.1f}M")
            with st.expander("Assumptions behind these numbers"):
                st.dataframe(D["assumptions"], hide_index=True)
    with c2:
        st.subheader("Where the satellite looks")
        mon = D["monthly"][D["monthly"].site_id == sid]
        wd = 0.0
        lat, lon = float(site["lat"]), float(site["lon"])

        def circle(clat, clon, r_km, n=40):
            pts = [(clat + r_km / 111.32 * math.cos(2 * math.pi * k / n),
                    clon + r_km / (111.32 * math.cos(math.radians(clat))) * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
            return [p[0] for p in pts], [p[1] for p in pts]

        def offset(km, bearing):
            b = math.radians(bearing)
            return lat + km * math.cos(b) / 111.32, lon + km * math.sin(b) / (111.32 * math.cos(math.radians(lat)))

        fig = go.Figure()
        for name, (clat, clon), colour in [("Downwind (10 km)", offset(10, 45), "#b3261e"), ("Upwind background (20 km)", offset(20, 225), "#1a73e8")]:
            la, lo_ = circle(clat, clon, 7)
            fig.add_trace(go.Scattermap(lat=la, lon=lo_, mode="lines", fill="toself", name=name, line={"color": colour}, opacity=0.35))
        fig.add_trace(go.Scattermap(lat=[lat], lon=[lon], mode="markers", marker={"size": 14, "color": "black"}, name="Plant"))
        fig.update_layout(map={"style": "open-street-map", "center": {"lat": lat, "lon": lon}, "zoom": 8.3},
                          margin={"l": 0, "r": 0, "t": 0, "b": 0}, height=330, legend={"orientation": "h", "y": -0.05})
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Boxes rotate with each day's wind. Shown for a north-east wind. Plume = downwind minus upwind NO2.")

    st.subheader("Monthly evidence")
    mon = D["monthly"][D["monthly"].site_id == sid].sort_values("month")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=mon.month, y=mon.interval_high, line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=mon.month, y=mon.interval_low, fill="tonexty", line={"width": 0}, name="Satellite 80% range",
                             fillcolor="rgba(26,115,232,0.18)"))
    fig.add_trace(go.Scatter(x=mon.month, y=mon.estimate_gwh, name="Satellite estimate", line={"color": "#1a73e8"}))
    if "metered_gwh" in mon:
        fig.add_trace(go.Scatter(x=mon.month, y=mon.metered_gwh, name="Metered (CPPA-G)", mode="lines+markers", line={"color": "black"}))
    if D["trace"] is not None:
        t = D["trace"][D["trace"].site_id == sid].groupby("year")["activity_mwh"].sum() / 12000
        for yr, val in t.items():
            fig.add_trace(go.Scatter(x=[f"{yr}-01", f"{yr}-12"], y=[val, val], mode="lines", line={"dash": "dash", "color": "#9334e6"},
                                     name="Climate TRACE (model, monthly avg)", showlegend=bool(yr == t.index[0])))
    for m in mon.loc[mon.status == "LOW_CONFIDENCE", "month"]:
        fig.add_vrect(x0=m, x1=m, line_width=6, line_color="rgba(120,120,120,0.25)")
    for m in SHUTDOWNS.get(sid, []):
        fig.add_vline(x=m, line_dash="dot", line_color="#b3261e")
    fig.add_vrect(x0="2020-03", x1="2020-04", fillcolor="rgba(179,38,30,0.08)", line_width=0, annotation_text="2020 lockdown")
    fig.update_layout(height=380, yaxis_title="GWh per month", margin={"t": 10}, legend={"orientation": "h", "y": -0.2})
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Grey marks: low-confidence months (few clear satellite passes). Red dotted lines: months the plant was metered near zero.")

    st.subheader("Cross-check: claims against independent sources (C12)")
    cx = D["cross"][D["cross"].site_id == sid][["pair", "left", "right", "result", "reason"]]
    st.dataframe(cx.style.map(lambda x: f"color:{ {'CONTRADICT': '#b3261e', 'AGREE': '#1b7f3b'}.get(x, '#5f6368')}", subset=["result"]),
                 hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- Trees
elif page == "Tree contracts":
    st.title("Tree-offset contracts")
    t = D["trees"]
    latest = t.sort_values("date").groupby("plot_id").tail(1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Released to farmers and funders (PKR)", f"{t['released'].sum():,.0f}")
    c2.metric("Held: trees not seen (PKR)", f"{t['held'].sum():,.0f}")
    c3.metric("Trees on satellite-verified plots", f"{M['verified_trees']:,}")
    st.caption("Farmers are invented for the demo. Greenness readings are real Sentinel-2 values. Prices are demo values.")
    st.dataframe(t[["plot_id", "farmer", "date", "ndvi", "cloud", "status", "trees", "released", "farmer", "held", "data_flags"]]
                 .loc[:, ~t[["plot_id", "farmer", "date", "ndvi", "cloud", "status", "trees", "released", "farmer", "held", "data_flags"]].columns.duplicated()],
                 hide_index=True, use_container_width=True)

# ---------------------------------------------------------------- C04
elif page == "Reliability (C04)":
    st.title("Impossible or weak inputs are refused, never answered")
    st.write("Each button sends one input through the same checks the pipeline uses.")
    for case in GUARD_CASES:
        c1, c2 = st.columns([2, 3])
        if c1.button(f"{case['id']}. {case['name']}", key=f"g{case['id']}", use_container_width=True):
            codes = case["run"]()
            rec = make_record("guard_test", codes, case["input"], case=case["name"])
            c2.markdown(badge(rec["status"], STATUS_COLOUR[rec["status"]]) + f" &nbsp; `{', '.join(codes) or 'no issues'}`",
                        unsafe_allow_html=True)
            c2.caption(case["input"])
            c2.json(rec, expanded=False)
        else:
            c2.caption(case["input"])

# ---------------------------------------------------------------- C07
elif page == "Model vs baseline (C07)":
    st.title("Is the model worth its complexity?")
    tr = M["trees"]["test"]
    st.subheader("Tree check: random forest vs one greenness threshold (F1, higher is better)")
    st.dataframe(pd.DataFrame([
        {"model": "Random forest, a year of Sentinel-2", "F1": round(tr["rf_f1"], 3)},
        {"model": f"Single NDVI threshold, tuned ({tr['baseline_threshold']})", "F1": round(tr["baseline_tuned_f1"], 3)},
        {"model": "Single NDVI threshold, fixed 0.35", "F1": round(tr["baseline_fixed_f1"], 3)},
    ]), hide_index=True)
    st.markdown(f"**Gain vs tuned threshold: {tr['gain_vs_tuned_pct']}%** (target ≥ 15%) · samples: {M['sources']['c07_samples']}")
    if M["trees"].get("hand"):
        h = M["trees"]["hand"]
        st.markdown(f"On the team's hand labels (n={h['n']}): RF {h['rf_f1']:.3f} vs threshold {h['baseline_tuned_f1']:.3f}")
    st.subheader("Pollution model: RMSE in GWh per month on held-out months (lower is better)")
    for sid, p in M["pollution"].items():
        st.markdown(f"**{sid}** ({p['n_test']} test months, {p['test_months'][0]} to {p['test_months'][1]}, labels: {p['label_source']})")
        st.dataframe(pd.DataFrame([
            {"model": "Ridge on wind-corrected plume", "RMSE": round(p["rmse"], 1), "gain %": ""},
            {"model": "Capacity x fleet average (rule of thumb)", "RMSE": round(p["baselines"]["capacity_heuristic"]["rmse"], 1), "gain %": p["gain_vs_capacity_pct"]},
            {"model": "Linear on raw plant NO2 (no wind)", "RMSE": round(p["baselines"]["raw_no2_linear"]["rmse"], 1), "gain %": p["gain_vs_raw_pct"]},
            {"model": "3-month moving average of reported data (reference only)", "RMSE": round(p["baselines"]["moving_avg_3_reference"]["rmse"], 1), "gain %": ""},
        ]), hide_index=True)
        st.caption(f"Correlation {p['r']:.2f} · {p['coverage_80'] * 100:.0f}% of test months inside the 80% range")
    st.caption("The moving average uses the company-reported numbers we are trying to check, so it is shown for honesty, not as a baseline.")

# ---------------------------------------------------------------- Log
else:
    st.title("Validation log")
    v = D["verdicts"]
    pick = st.multiselect("Status", ["OK", "LOW_CONFIDENCE", "REJECTED"], default=["OK", "LOW_CONFIDENCE", "REJECTED"])
    kinds = st.multiselect("Kind", sorted(v.kind.unique()), default=sorted(v.kind.unique()))
    view = v[v.status.isin(pick) & v.kind.isin(kinds)]
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.download_button("Download CSV", view.to_csv(index=False), "verdicts.csv", "text/csv")
