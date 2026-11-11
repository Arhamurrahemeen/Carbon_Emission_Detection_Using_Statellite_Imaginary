"""Green Claims Check: does the satellite evidence support this company's green claims?
Reads outputs/ only (run `python -m verify.build` first). Run: streamlit run app/streamlit_app.py
Design contract: DESIGN.md."""
import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
import charts  # noqa: E402
from verify.gate import GUARD_CASES  # noqa: E402
from verify.records import make_record  # noqa: E402

OUT = ROOT / "outputs"
SHUTDOWNS = {"sahiwal": ["2024-11", "2025-02", "2025-10"]}  # months the meter shows the plant near zero
PAIR_TITLE = {
    "X1": "Company's table vs the electricity meter",
    "X2": "Company's table vs the satellite",
    "X3": "Declared CO2 vs meter × emission factor",
    "X4": "Declared CO2 vs satellite-based CO2",
    "X5": "\"We cut emissions\" vs what actually happened",
    "X6": "Trees claimed vs trees the satellite sees",
    "X7": "Report's table vs report's own text",
}
RESULT = {"CONTRADICT": ("Disagrees", charts.FLAG), "AGREE": ("Agrees", charts.OK), "CANNOT_COMPARE": ("Not enough evidence", charts.WARN)}
VERDICT = {"INCONSISTENT": ("Refer for review", charts.FLAG), "CONSISTENT": ("Consistent", charts.OK),
           "CANNOT_VERIFY": ("Cannot verify", charts.WARN)}
STATUS = {"OK": charts.OK, "LOW_CONFIDENCE": charts.WARN, "REJECTED": charts.FLAG}

st.set_page_config(page_title="Green Claims Check", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"], .stMarkdown, button, input { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
.block-container { padding-top: 1.6rem; max-width: 1280px; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none; }
.num { font-variant-numeric: tabular-nums; }
.strip { background:#fff; border:1px solid #E2DDD3; border-radius:6px; padding:20px 24px; box-shadow:0 2px 10px rgba(29,42,47,.07); }
.pill { display:inline-block; padding:2px 12px; border-radius:999px; color:#fff; font-weight:600; font-size:14px; }
.verdict { font-size:30px; font-weight:600; margin:6px 0 2px; }
.why { font-size:16px; color:#1D2A2F; margin-bottom:14px; }
.fig-label { font-size:13px; color:#5B676C; }
.fig { font-size:30px; font-weight:600; line-height:1.15; }
.note { font-size:13px; color:#5B676C; margin-top:10px; }
.row { display:grid; grid-template-columns: 2.1fr 2.4fr 1.1fr; gap:12px; padding:10px 0; border-bottom:1px solid #E2DDD3; align-items:center; }
.row .what { font-weight:600; } .row .vals { color:#5B676C; font-size:14px; } .row .res { font-weight:600; text-align:right; }
.card { background:#fff; border:1px solid #E2DDD3; border-radius:6px; padding:14px 16px; }
</style>""", unsafe_allow_html=True)

if not (OUT / "metrics.json").exists():
    st.info("No results yet. Run `python -m verify.build` in the project folder, then reload.")
    st.stop()


@st.cache_data
def load():
    read = lambda n: pd.read_csv(OUT / n) if (OUT / n).exists() else pd.DataFrame()
    return {"metrics": json.loads((OUT / "metrics.json").read_text()), "monthly": read("monthly.csv"),
            "verdicts": read("verdicts.csv"), "cross": read("cross_checks.csv"), "trees": read("tree_passes.csv"),
            "claims": read("claims_used.csv"), "plume": read("plume_points.csv"), "trace": read("climate_trace.csv"),
            "sites": pd.read_csv(ROOT / "data" / "manual" / "sites.csv"),
            "plots": pd.read_csv(ROOT / "data" / "manual" / "plots.csv"),
            "assumptions": pd.read_csv(ROOT / "data" / "manual" / "assumptions.csv")}


D = load()
M = D["metrics"]
pill = lambda text, colour: f"<span class='pill' style='background:{colour}'>{text}</span>"


def latest_plot_status() -> pd.DataFrame:
    t = D["trees"]
    decided = t[t["status"].isin(["verified", "failed", "invalid"])].sort_values("date").groupby("plot_id").tail(1)
    p = D["plots"].merge(decided[["plot_id", "status"]], on="plot_id", how="left")
    p["alive"] = p["status"].eq("verified")
    return p


st.markdown("<div style='font-size:13px;color:#5B676C'>Green Claims Check · satellite evidence for a bank's risk officer</div>", unsafe_allow_html=True)
sites = D["sites"].set_index("site_id")
sid = st.selectbox("Company and plant under review", sites.index, format_func=lambda s: sites.loc[s, "name"], label_visibility="collapsed")
site = {"site_id": sid, **sites.loc[sid].to_dict()}

tab_v, tab_t, tab_r, tab_m, tab_l = st.tabs(["Verdict", "Tree contracts", "Reliability (C04)", "Model test (C07)", "Log"])

# ------------------------------------------------------------------ Verdict
with tab_v:
    v = D["verdicts"]
    claim_rec = v[(v.kind == "claim_check") & (v.site_id == sid)]
    fy = v[(v.kind == "emissions") & (v.site_id == sid) & (v.period == "FY2026")]
    cl = D["claims"][D["claims"].site_id == sid] if len(D["claims"]) else pd.DataFrame()
    table_claim = cl[(cl.claim_type == "generation") & (cl.modality == "table")]["value"].astype(float)
    claim_val = float(table_claim.iloc[0]) if len(table_claim) else None
    metered = float(claim_rec.iloc[0]["metered_gwh"]) if len(claim_rec) and pd.notna(claim_rec.iloc[0]["metered_gwh"]) else None
    tr = D["trace"]
    trace_year = tr[(tr.site_id == sid) & (tr.year == 2025)] if len(tr) else pd.DataFrame()
    trace_gwh = float(trace_year["activity_mwh"].sum() / 1000) if len(trace_year) else None
    trace_t = float(trace_year["emissions_t_co2e"].sum()) if len(trace_year) else None

    if len(claim_rec) and len(fy):
        r, e = claim_rec.iloc[0], fy.iloc[0]
        word, colour = VERDICT[r["verdict"]]
        synthetic = [k for k, s in M["sources"].items() if s in ("synthetic", "missing")]
        st.markdown(f"""<div class='strip'>
          {pill(word, colour)}
          <div class='verdict'>{int(r['n_contradictions'])} of {int(r['n_checks'])} checks disagree with independent evidence</div>
          <div class='why'>{r['message']}</div>
          <div style='display:grid;grid-template-columns:repeat(3,1fr);gap:24px'>
            <div><div class='fig-label'>Satellite estimate, FY2026</div><div class='fig num' style='color:{charts.SAT}'>{e['estimate_gwh']:,.0f} GWh</div>
                 <div class='fig-label num'>80% range {e['interval_low']:,.0f}–{e['interval_high']:,.0f}</div></div>
            <div><div class='fig-label'>Metered sales to the grid, FY2026</div><div class='fig num'>{metered:,.0f} GWh</div>
                 <div class='fig-label'>CPPA-G metered purchases</div></div>
            <div><div class='fig-label'>Company says</div><div class='fig num' style='color:{charts.FLAG}'>{claim_val:,.0f} GWh</div>
                 <div class='fig-label'>{(claim_val / metered - 1) * 100:+.0f}% vs the meter</div></div>
          </div>
          <div class='note'>Synthetic inputs, labelled: {', '.join(synthetic) or 'none'}. The company figures are synthetic, built from real metered numbers; no public report figure was found.</div>
        </div>""", unsafe_allow_html=True)
        st.plotly_chart(charts.range_plot(e.to_dict(), claim_val, metered, None, "FY2026"), use_container_width=True)

    left, right = st.columns([1.25, 1], gap="large")
    with left:
        st.markdown("#### The plant from space")
        c1, c2 = st.columns(2)
        mode = c1.radio("View", ["Plant and plume", "Plant and tree contracts"], horizontal=True, label_visibility="collapsed")
        sat = c2.toggle("Satellite imagery", value=True)
        co2_mid = (e["co2_low_t"] + e["co2_high_t"]) / 2 if len(fy) else None
        deck = charts.map_deck(site, D["plume"][D["plume"].site_id == sid], co2_mid, trace_t,
                               latest_plot_status() if sid == "sahiwal" else None,
                               "plant" if mode.startswith("Plant and plume") else "contracts", sat)
        st.pydeck_chart(deck, use_container_width=True, height=470)
        if mode.startswith("Plant and plume"):
            st.caption("Dark teal column: CO2 estimated from the satellite (FY2026). Grey column: Climate TRACE's model for 2025, same scale. "
                       "Ring of light teal columns: which way the plume blew over 24 months of satellite passes; taller means more of the plant's own NO2 went that way. "
                       + (charts.ATTRIBUTION if sat else ""))
        else:
            st.caption("Arcs run from the plant to the farms it pays to plant trees. Green: the satellite sees trees alive. Grey: no trees seen, payment held. "
                       "Height: trees contracted. Farmers are invented for the demo. " + (charts.ATTRIBUTION if sat else ""))
    with right:
        st.markdown("#### Each claim, checked")
        cx = D["cross"][D["cross"].site_id == sid]
        html = ""
        for c in cx.itertuples():
            word, colour = RESULT[c.result]
            html += (f"<div class='row'><div class='what'>{PAIR_TITLE.get(c.pair, c.pair)}</div>"
                     f"<div class='vals num'>{c.left}<br/>vs {c.right}</div>"
                     f"<div class='res' style='color:{colour}'>{word}</div></div>")
        st.markdown(html or "<div class='note'>No company claims for this plant.</div>", unsafe_allow_html=True)
        if len(claim_rec) and isinstance(claim_rec.iloc[0].get("exposure"), str):
            exp = json.loads(claim_rec.iloc[0]["exposure"])
            lo, hi = exp["carbon_cost_usd"]
            st.markdown(f"<div class='card' style='margin-top:16px'><div class='fig-label'>What it could cost the company (carbon price scenarios)</div>"
                        f"<div class='fig num' style='font-size:22px'>USD {lo / 1e6:,.0f}M – {hi / 1e6:,.0f}M a year</div>"
                        + (f"<div class='fig-label num'>Hidden by the disclosed CO2 figure: USD {exp['misstatement_usd'][0] / 1e6:,.1f}M – {exp['misstatement_usd'][1] / 1e6:,.0f}M</div>"
                           if exp.get("misstatement_usd") else "") + "</div>", unsafe_allow_html=True)
            with st.expander("Assumptions behind these numbers"):
                st.dataframe(D["assumptions"], hide_index=True, use_container_width=True)

    mon = D["monthly"][D["monthly"].site_id == sid].sort_values("month")
    st.plotly_chart(charts.timeline(mon, SHUTDOWNS.get(sid, [])), use_container_width=True)
    st.caption("A single month is too uncertain to judge on its own (about 23% typical error), so verdicts use the whole year, "
               "where errors partly cancel (about 7% typical error). Words used here are explained in docs/GLOSSARY.md.")

# ------------------------------------------------------------------ Trees
with tab_t:
    t = D["trees"]
    st.markdown("#### The company's tree claim, checked plot by plot")
    a, b, c = st.columns(3)
    a.metric("Paid to farmers for living trees", f"PKR {t['released'].sum():,.0f}")
    b.metric("Held back: no trees seen", f"PKR {t['held'].sum():,.0f}")
    c.metric("Trees on plots seen alive", f"{M['verified_trees']:,}")
    plots = latest_plot_status()
    st.pydeck_chart(charts.map_deck({"site_id": "sahiwal", **sites.loc["sahiwal"].to_dict()}, pd.DataFrame(), None, None, plots, "contracts", False),
                    use_container_width=True, height=420)
    view = t.rename(columns={"plot_id": "Plot", "farmer_name": "Farmer (invented)", "date": "Satellite check", "ndvi": "Greenness",
                             "status": "Result", "released": "Paid (PKR)", "held": "Held (PKR)"})
    st.dataframe(view[["Plot", "Farmer (invented)", "Satellite check", "Greenness", "Result", "Paid (PKR)", "Held (PKR)"]],
                 hide_index=True, use_container_width=True)
    st.caption("Greenness (NDVI) readings are real Sentinel-2 values at these coordinates; farmers, plots and prices are invented. "
               "A plot that was green only once (a crop, not trees) does not pass.")

# ------------------------------------------------------------------ C04
with tab_r:
    st.markdown("#### Impossible or weak inputs are refused, never answered with a confident number")
    st.caption("Each check sends one input through the same gates the pipeline uses.")
    if "guard" not in st.session_state:
        st.session_state.guard = {}
    if st.button("Run all 8 checks", type="primary"):
        st.session_state.guard = {c["id"]: c["run"]() for c in GUARD_CASES}
    for case in GUARD_CASES:
        c1, c2, c3 = st.columns([0.5, 3, 1.6])
        if c1.button("Run", key=f"g{case['id']}"):
            st.session_state.guard[case["id"]] = case["run"]()
        c2.markdown(f"**{case['id']}. {case['name']}**  \n<span class='fig-label'>{case['input']}</span>", unsafe_allow_html=True)
        if case["id"] in st.session_state.guard:
            codes = st.session_state.guard[case["id"]]
            rec = make_record("guard_test", codes, case["input"])
            c3.markdown(pill(rec["status"].replace("_", " ").title(), STATUS[rec["status"]]) +
                        f"<div class='fig-label'>{', '.join(codes) or 'no issues: normal noise is kept'}</div>", unsafe_allow_html=True)

# ------------------------------------------------------------------ C07
with tab_m:
    p = M["pollution"].get(sid)
    if p:
        g1, g2 = p["gain_vs_capacity_pct"], p["gain_vs_raw_pct"]
        st.markdown(f"#### Our model's error is {g1:.0f}% smaller than the rule of thumb and {g2:.0f}% smaller than raw satellite readings"
                    if g2 > 0 else f"#### Our model's error is {g1:.0f}% smaller than the rule of thumb")
        st.caption(f"Challenge C07 asks for at least 15%. Tested on {p['n_test']} months the model never saw "
                   f"({p['test_months'][0]} to {p['test_months'][1]}), with real metered generation as the answer.")
        st.plotly_chart(charts.error_bars(p), use_container_width=True)
        a = p.get("annual")
        if a:
            st.markdown(f"**Yearly claims:** across {a['n_windows']} different 12-month periods, understated claims were caught "
                        + ", ".join(f"{int(round((1 - float(s)) * 100))}% low → {v * 100:.0f}% of the time" for s, v in a["by_scale"].items())
                        + f"; honest claims were wrongly flagged {a['false_alarm_rate'] * 100:.0f}% of the time.")
            st.caption("These periods overlap and later months help predict earlier ones, so treat the catch rates as slightly optimistic. "
                       "A 3-month average of the company's own reported numbers misses less month to month, but it relies on the very figures we are checking.")
    tr = M["trees"]["test"]
    st.markdown("#### Tree check: random forest vs one greenness threshold")
    if M["sources"]["c07_samples"] != "real":
        st.warning("Scored on synthetic samples until the WorldCover export finishes. Not a result yet.")
    st.markdown(f"F1 score (higher is better): random forest **{tr['rf_f1']:.2f}**, single threshold **{tr['baseline_tuned_f1']:.2f}**, "
                f"gain **{tr['gain_vs_tuned_pct']}%**.")

# ------------------------------------------------------------------ Log
with tab_l:
    v = D["verdicts"]
    pick = st.multiselect("Status", ["OK", "LOW_CONFIDENCE", "REJECTED"], default=["OK", "LOW_CONFIDENCE", "REJECTED"])
    kinds = st.multiselect("Kind", sorted(v.kind.unique()), default=sorted(v.kind.unique()))
    view = v[v.status.isin(pick) & v.kind.isin(kinds)]
    st.dataframe(view, hide_index=True, use_container_width=True)
    st.download_button("Download CSV", view.to_csv(index=False), "verdicts.csv", "text/csv")
