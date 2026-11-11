# Design: Satellite Verification of Green Claims

Status: built · Written 11 Nov 2026, updated 12 Nov · Owner: Arham

> **What changed after this spec was written (read first).** Where the sections below disagree, this list wins.
> 1. **Training labels:** monthly metered grid sales from CPPA-G Excel files (`data/raw/generation_monthly.csv`, Jul 2024 – Sep 2026, 27 months), not hand-typed NEPRA scans. FY2024-25 totals match NEPRA's annual report exactly.
> 2. **Verdicts are per fiscal year.** Single months are too noisy (±250 GWh) and abstain with `W_WIDE_INTERVAL`. Monthly errors are combined in quadrature, widened for autocorrelation.
> 3. **Shown estimates are out of sample:** months with known generation show leave-one-out estimates. An earlier 97.5% figure was withdrawn (leakage).
> 4. **Framing (decided 12 Nov): verifying green claims.** Two claims, emissions and offsets, checked against satellite and meter. The factory pays farmers directly for living trees; no funder, no farmer/funder split, no marketplace.
> 5. **Tree C07 result:** random forest F1 0.891 vs threshold 0.798 (11.6% gain), short of 15%; C07 is met by the emissions model (62% and 30% less error).
> 6. **App:** redesigned to `DESIGN.md`: verdict strip, range plot, 3D satellite map (plume rose, tree contracts), plain-language claim rows. Deployed on Streamlit Community Cloud.
> 7. **Hub** is two plants (CPHGC coal + Hub Power oil) sharing one plume; the oil plant barely ran.
> 8. Full record of decisions: `docs/DISCUSSION_LOG.md`.
Event: BattleVerse 2026, Battle of Intelligence, Pillar 5 · Challenges: C04, C07, C12
Plain-language companion: [PITCH_BRIEF.md](../PITCH_BRIEF.md)

Decisions marked **[team]** were made in conversation. Decisions marked **[builder's call]** were made while writing this spec and can be overridden.

---

## 1. Intent

A bank's environmental risk officer is reviewing a loan to a coal power company. The company makes two green claims: how much it emits, and how many trees it planted to offset part of that. Today the only evidence for either claim is the company's own report.

We build a system that checks both claims against independent evidence and returns one answer per claim: **CONSISTENT**, **INCONSISTENT** or **CANNOT_VERIFY**. When inputs are impossible or evidence is thin, it refuses rather than guesses.

- **Pollution evidence:** Sentinel-5P NO2 around the plant, corrected for wind, turned into an estimate of monthly generation by a model trained on metered grid sales (CPPA-G). Turned into CO2 with emission factors, always as a range.
- **Tree evidence:** Sentinel-2 imagery of each offset plot, classified tree / not tree, checked every quarter. Payments to the farmer are released only on a pass.

### Why now
SECP ordered IFRS S1/S2 climate disclosure on 31 Dec 2024, phased for listed companies from July 2026 (verify the phase dates against the order). SBP's climate-risk framework requires banks to comply by 30 Jun 2029; implementation plans were due 30 Sep 2026.

## 2. Users and roles [team]

| Role | Who | In the product |
|---|---|---|
| **User and payer** | Environmental / credit risk officer at a Pakistani bank. Secondary: ESG fund analyst | Opens the main screen, reads verdicts, decides on the loan |
| Participant | Coal power company (Sahiwal, CPHGC Hub) | Source of the claims being checked; buys tree contracts |
| Participant | Farmer | Plot owner; paid by the company only for trees seen alive |
| Data sources | NEPRA, Copernicus (Sentinel-5P, Sentinel-2), ECMWF ERA5, Climate TRACE, ESA WorldCover | Evidence only |

The company never pays for its own check; that would rebuild the self-reporting problem.

## 3. Goals

1. Show wind-corrected Sentinel-5P NO2 tracks monthly generation at Sahiwal on months the model never saw.
2. Turn the signal into a generation estimate with an 80% interval, and a derived CO2 range.
3. Compare company claims (numbers and text) with satellite and NEPRA evidence and return verdicts with reasons (**C12**).
4. Verify offset tree plots with a classifier that beats a single greenness threshold by ≥15% F1 (**C07**).
5. Reject impossible inputs and abstain on thin evidence, demonstrated live with at least 5 injected cases (**C04**).
6. A Streamlit app that walks one journey for the risk officer in under 2.5 minutes.

## 4. Non-goals

- Real-time monitoring, live API calls during the demo.
- Cement, steel, refineries, or any plant inside an industrial cluster (Korangi, Port Qasim). Plumes overlap.
- Measuring CO2 directly from space.
- Proving a legal breach.
- The Shajar marketplace (offers, ranking, funding requests). Mentioned on one slide, not built.
- User accounts, login, a database. Files only.
- Mobile app / SMS for farmers. One sentence in the pitch as a next step.

## 5. Anti-goals (failure even if it "works")

- A confident number for an impossible or unsupported input.
- Calling the satellite a CO2 sensor, or saying "fraud", "breach", "proves", "zero carbon", "net zero" anywhere in the UI.
- Synthetic or invented data shown without a visible label.
- A verdict the presenter cannot trace back to a file and a rule.
- A demo that fails with no internet.
- Claiming "1 km resolution".

## 6. Constraints

- **Time:** demo-ready by Day 3 morning (12 Nov). Two rehearsals under 7 minutes.
- **Earth Engine runs only from the team's own accounts** (project `shajar-514406` already works). The build writes Earth Engine scripts; a team member runs them and commits the CSV output. Nothing in the Python pipeline calls Earth Engine.
- **NEPRA monthly plant-wise figures are in scanned PDFs** (Fuel Charges Adjustment decisions). They must be typed by hand. The annual *Performance Evaluation Report, Generation* (FY2024-25) has readable plant-wise annual totals.
- **Shajar repo is read-only for us.** We may copy ideas and code with credit; we never commit to it.
- **Commits carry no AI attribution:** no co-author trailers, no "generated with" lines, authored by the team member.
- Python 3.11+ on Windows. Must run from a fresh clone with `pip install -r requirements.txt`.

## 7. How it works

```
 Earth Engine (team runs)          Hand-entered                 Downloaded once
 ─────────────────────────         ────────────                 ───────────────
 gee/overpass_export.js  ──►  data/raw/overpasses_<site>.csv
 gee/plots_export.js     ──►  data/raw/plot_passes.csv
 gee/c07_tree_benchmark.js ►  data/raw/c07_samples.csv
                               data/manual/nepra_monthly.csv
                               data/manual/claims.csv        data/raw/climate_trace.csv
                               data/manual/sites.csv         data/raw/reports/*.pdf (text extracted)
                                         │
                                         ▼
                     python -m verify.build   (one command rebuilds everything)
       ┌──────────────┬───────────────┬──────────────┬──────────────┬─────────────┐
       ▼              ▼               ▼              ▼              ▼             ▼
   gate.py       features.py      model.py      trees.py       claims.py     records.py
   (C04 bounds)  (monthly plume)  (ridge + PI)  (classifier,   (C12 extract  (one record
                                                 payouts)       + cross-check) per request)
                                         │
                                         ▼
                 outputs/*.csv, outputs/metrics.json  ──►  app/streamlit_app.py
```

### 7.1 Pollution pipeline
1. **Per overpass (Earth Engine).** For each Sentinel-5P OFFL L3 NO2 image over a site:
   - Wind: ERA5-Land hourly 10 m u/v at the hour nearest the overpass (~08:00–09:00 UTC), at the plant.
   - Drop the overpass if wind speed < 1 m/s (no plume direction) or the plant pixel is masked.
   - **Downwind mean:** NO2 inside a 7 km-radius circle centred 10 km downwind. **Upwind mean:** 7 km circle centred 20 km upwind. *(Starting values, tune.)*
   - **Raw mean:** NO2 in a 5 km circle on the plant, no wind used (feeds the C07 pollution baseline).
   - Export one row per overpass: `site_id, date, no2_down, no2_up, no2_raw, wind_u, wind_v, wind_speed, wind_dir, cloud_fraction, n_pixels`.
2. **Gate 1 per overpass** (physical bounds, §8). Pixels below −0.001 mol/m² were already dropped; overpasses with out-of-range values are rejected with a reason code and logged.
3. **Monthly features (Python).** Per site-month: `enh_mean` (downwind − upwind), `flux_proxy = mean(enhancement × wind_speed)`, `valid_overpasses`, `wind_mean`, `month_sin`, `month_cos`.
   **Correction to the earlier spec:** for a fixed emission, column enhancement falls as wind speed rises (the plume is diluted). Enhancement × wind speed is the quantity that scales with emissions, so `flux_proxy` is the primary feature. Raw enhancement is kept for comparison.
4. **Model.** Ridge regression, target = NEPRA monthly net generation (GWh). Features above. Standardised; alpha chosen by time-series cross-validation on training months.
   - **Validation A:** hold out the most recent 12 months with NEPRA data.
   - **Validation B (stretch):** train on Sahiwal, test on Hub, using plant factor (%) as the target.
   - **Interval:** split conformal. 80% band = estimate ± the 80th percentile of absolute residuals from out-of-fold predictions.
   - Gradient boosting only if it beats ridge on validation A **[builder's call: probably skip, too little data]**.
5. **Gate 3 per month** (model confidence, §8): too few overpasses, features outside the training range, or interval too wide → LOW_CONFIDENCE.
6. **CO2.** `co2 = generation_MWh × EF`, EF range per site in `sites.csv` (low/high). The final range spans the low end of the generation interval × EF_low to the high end × EF_high. Always labelled "derived, not measured".

### 7.2 Tree pipeline
1. **Plots.** `data/manual/plots.csv`: plot_id, farmer (invented, labelled), lat, lon, acres, trees_planted, contract_since, linked site_id.
2. **Quarterly passes (Earth Engine).** Adapt Shajar's `gee/export_data.js`: per plot and quarter date, the clearest Sentinel-2 image within ±15 days, masked with Cloud Score+ (≥0.6 clear), giving NDVI, cloud fraction, and the classifier features used in C07.
3. **Classifier.** Random forest trained on Sentinel-2 annual features (NDVI percentiles, std dev, band medians, NDMI), labels from ESA WorldCover tree class plus the team's hand labels (Shajar's `c07/label.html` approach). Baseline = single NDVI threshold tuned on training points (§10.2).
4. **Pass verdict.** Plot passes if the classifier says tree with probability ≥0.5 **and** cloud ≤30%. Statuses: `verified`, `failed`, `cloudy`, `no_imagery`, `invalid`.
5. **Payout.** Per pass: `trees × price_per_tree_year / passes_per_year`. Verified → released to the farmer by the company (no funder split; decided 12 Nov). Failed or invalid → held. Cloudy or no imagery → nothing paid or held, wait. Prices are labelled demo values.
6. **Tree claim.** The company's text claim ("planted 50,000 trees") is compared with trees on plots whose latest pass is verified. Feeds C12.

### 7.3 Claims and cross-check (C12)
**Claim sources, paired per site and period:**

| Source | Modality | Example |
|---|---|---|
| Company report table | Declared number | "Net generation FY2025: 4,100 GWh"; "Scope 1 emissions: 3.5 Mt CO2e" |
| Company report narrative | Unstructured text | "We reduced our emissions by 25% this year"; "We planted 50,000 trees" |
| NEPRA | Metered number | 4,255 GWh (FY2024-25) |
| Satellite | Estimate with interval | 3,900–4,600 GWh; CO2 3.1–4.4 Mt |
| Climate TRACE | Modelled number | Display and comparison only |
| Tree plots | Satellite-verified count | 30,500 trees on verified plots |

**Extraction [builder's call]:** rule-based. `pypdf` extracts page text; regular expressions find numbers next to keywords (generation, GWh, emissions, tCO2, reduction, %, trees, planted) and capture `value, unit, page, quote`. A person confirms each extracted claim before it enters `claims.csv` (`entry_mode = extracted | manual`). No LLM in the pipeline, so there's no hallucination risk, no API key, and every step is testable. Every extracted value must appear verbatim in its cited page text, or it is rejected with `E_CLAIM_NOT_IN_SOURCE`. An LLM extractor is a stretch goal only, and its output must pass the same check.

**Cross-checks (each pair returns AGREE / CONTRADICT / CANNOT_COMPARE plus a reason):**

| # | Pair | Rule |
|---|---|---|
| X1 | Declared generation vs NEPRA metered | Contradict if they differ by >5% |
| X2 | Declared generation vs satellite interval | Contradict if outside the 80% interval |
| X3 | Declared CO2 vs CO2 range from NEPRA generation × EF | Contradict if outside the range |
| X4 | Declared CO2 vs satellite CO2 range | Contradict if outside the range |
| X5 | Text reduction claim ("reduced by N%") vs year-on-year change in NEPRA generation, and separately in the satellite estimate | Contradict if the direction disagrees, or if the claimed % falls outside the evidence range |
| X6 | Text tree claim vs satellite-verified trees | Contradict if claimed trees exceed verified trees by >10% |
| X7 | Declared table number vs the same metric stated in the narrative | Contradict if they differ by >1% (internal inconsistency) |

A claim's overall verdict is INCONSISTENT if any cross-check involving independent evidence (X1–X6) contradicts with status OK; CONSISTENT if all available checks agree; otherwise CANNOT_VERIFY. The app shows the full matrix so the officer sees *which* sources disagree.

### 7.4 Sites

| site_id | Plant | Lat, lon (Climate TRACE centroid; check on a map) | Capacity | Climate TRACE asset | Notes |
|---|---|---|---|---|---|
| `sahiwal` | Huaneng Shandong Ruyi, Sahiwal (imported coal) | 30.7142, 73.2380 | 1,320 MW | 25455252 | Primary site. Isolated |
| `hub` | China Power Hub Generation Co (CPHGC, imported coal) | 24.9147, 66.6888 | 1,320 MW | 25455585 ("Hubco power station") | **Shares the site with the Hub Power Company oil plant (1,292 MW, asset 448261) about 1 km away.** The satellite sees both plumes as one, so the NEPRA label for `hub` is the sum of both plants' generation, and the CO2 factor is a generation-weighted mix. Secondary site / "mostly off" test (CPHGC 6.1% utilisation FY25) |

Correction to the earlier pitch note: the Climate TRACE asset that matches CPHGC is 25455585 (3.55 Mt CO2e, 3.82 TWh activity), not 448261 (the oil plant). Its reporting year is not stated in the API record, so the "~5× NEPRA" comparison stays unconfirmed until the year is checked.

## 8. Validation gates (C04)

Every request produces exactly one record with status **OK**, **LOW_CONFIDENCE** or **REJECTED**. REJECTED stops the request and shows no estimate. LOW_CONFIDENCE shows the estimate greyed, and the only verdict allowed is CANNOT_VERIFY.

### Gate 1: physical bounds → REJECTED

| Field | Valid | Code |
|---|---|---|
| lat / lon | −90..90 / −180..180 | E_COORD_RANGE |
| lat / lon | within 25 km of a registered site | E_SITE_UNKNOWN |
| month / period | 2018-07 to last complete month | E_DATE_RANGE |
| NO2 monthly mean | −0.001 to 0.02 mol/m² | E_NO2_RANGE |
| cloud_fraction | 0..1 | E_SAT_RANGE |
| wind_speed / wind_dir | 0..60 m/s / 0..360° | E_WEATHER_RANGE |
| solar_irradiance (if present) | 0..1361 W/m² | E_WEATHER_RANGE |
| NASA POWER fill value (−999) | treated as missing, never as a reading | none (dropped) |
| NDVI | −1..1 | E_NDVI_RANGE |
| trees per acre | >0 and ≤1000 | E_TREE_DENSITY |
| offset share | >0 and ≤100% | E_SHARE_RANGE |

### Gate 2: plausibility → REJECTED

| Check | Code |
|---|---|
| Generation above capacity × hours × 1.05 (capacity factor >100%) | E_CF_OVER_100 |
| Claimed reduction >100% | E_REDUCTION_OVER_100 |
| Negative generation or CO2 claim | E_CLAIM_RANGE |
| Unknown claim type | E_CLAIM_TYPE |
| Extracted value not in the cited page text | E_CLAIM_NOT_IN_SOURCE |

### Gate 3: confidence → LOW_CONFIDENCE

| Check | Code |
|---|---|
| valid_overpasses < 5 in the month (tune) | W_FEW_OBS |
| Any feature outside training min–max ± 10% | W_OUT_OF_DISTRIBUTION |
| 80% interval wider than half the plant's max monthly generation | W_WIDE_INTERVAL |
| Plot cloud fraction >30% | W_CLOUDY |
| No imagery for the pass date yet | W_NO_IMAGERY |

### C04 demo cases (shown as buttons in the app, also `tests/test_guard.py`)

| # | Injected input | Expected | Code |
|---|---|---|---|
| 1 | Latitude 124.5 | REJECTED | E_COORD_RANGE |
| 2 | Wind speed −8 m/s (or irradiance −50 W/m²) | REJECTED | E_WEATHER_RANGE |
| 3 | Claimed 200% emissions reduction | REJECTED | E_REDUCTION_OVER_100 |
| 4 | Generation implying 140% capacity factor | REJECTED | E_CF_OVER_100 |
| 5 | NDVI 1.8 on a tree plot | REJECTED | E_NDVI_RANGE |
| 6 | Valid monsoon month, 2 clear overpasses | LOW_CONFIDENCE | W_FEW_OBS |
| 7 | Extracted figure not on the cited page | REJECTED | E_CLAIM_NOT_IN_SOURCE |
| 8 (control) | NO2 column −0.00002 mol/m² (normal sensor noise) | OK | none |

Cases 1–5 are the five out-of-bounds cases the challenge asks for. Cases 6–8 show the system knows the difference between impossible, thin and noisy.

## 9. Output record

One record per request, written to `outputs/verdicts.csv` and shown in the app.

| Field | Notes |
|---|---|
| request_id, timestamp | Audit |
| kind | `emissions`, `tree_pass`, `claim_check`, `guard_test` |
| site_id / plot_id, period | Echo |
| status | OK / LOW_CONFIDENCE / REJECTED, always present |
| reason_codes | List; empty when OK with no warnings |
| message | One plain sentence a banker can read |
| estimate_gwh, interval_low, interval_high | Absent when REJECTED |
| co2_low_t, co2_high_t | Derived; labelled |
| valid_overpasses | Absent when REJECTED |
| claim_type, claim_value, claim_source_page, claim_quote | When a claim is present |
| verdict | CONSISTENT / INCONSISTENT / CANNOT_VERIFY; absent when REJECTED |
| gap_pct | Distance from the nearest interval edge, signed; only when INCONSISTENT |
| cross_checks | For claim_check: list of {pair, result, reason} |
| benchmark_climate_trace_t | Display only |
| data_flags | e.g. `synthetic`, `manual_entry`, `invented_farmer` |

Verdict rules: CONSISTENT = claim inside the interval. INCONSISTENT = outside, with direction and gap. CANNOT_VERIFY = status LOW_CONFIDENCE, or no claim.

## 10. Model justification (C07): ≥15% gain over a simple baseline

### 10.1 Pollution model (RMSE on held-out months)
| Model | Inputs | Role |
|---|---|---|
| **Primary** | Ridge on flux_proxy, enhancement, valid_overpasses, wind, season | Our model |
| Baseline H1 | Capacity × fleet-average coal plant factor for that fiscal year (NEPRA annual report) | The "rule of thumb" a bank uses today |
| Baseline L1 | Simple linear fit on raw plant NO2 (no wind, no background) | The "naive satellite" approach |
| Reference only | 3-month moving average of past NEPRA generation | Shown for honesty, **not** a fair baseline: it uses the company-reported data we are trying to check |

Gain = (RMSE_baseline − RMSE_primary) / RMSE_baseline, reported against H1 and L1.

**Honest note:** primary and L1 are both linear, so here the gain comes from better features (wind and background correction), not from a more complex model. Say so if asked. The 15% is a test result we report, not a promise; if it isn't reached, we report the number anyway.

### 10.2 Tree classifier (F1 on held-out points), the primary C07 submission [builder's call]
| Model | Role |
|---|---|
| **Primary** | Random forest on a year of Sentinel-2 features |
| Baseline | Single NDVI threshold from one quarterly image, threshold tuned on training points (fair) and fixed at 0.35 (what Shajar uses) |

Scored on (a) the WorldCover held-out split and (b) the team's hand-labelled points. **Why both:** WorldCover is itself a model built from Sentinel-2, so beating it on its own labels is partly circular. Hand labels are the honest test.

This is the cleaner C07 story: a genuinely more complex model against a one-line rule, on a classification task where the baseline is known to struggle (green crops look like trees in a single image). It is also the model the tree pipeline uses, so the complexity is earned in the product. It builds on Baneen's existing C07 scripts.

## 11. Evidence to show

| Evidence | Measure |
|---|---|
| Satellite tracks activity | Correlation, RMSE and MAPE vs NEPRA on held-out months |
| Intervals are honest | Share of held-out months inside the 80% interval (target ~80%) |
| Real events visible | Mar–Apr 2020 lockdown dip; Sahiwal forced outage Jan 2026 / reduced capacity ~3 months |
| Verdicts work | Detection rate on synthetic misstated claims (scaled −20/−40/−60%, labelled synthetic) and false-alarm rate on true claims |
| C04 | `pytest tests/test_guard.py` passing, plus live buttons |
| C07 | Gain table from `outputs/metrics.json` |
| C12 | One real or labelled-synthetic report where text and number disagree, caught and explained |

## 12. Data sources and files

| File | Source | Who fills it |
|---|---|---|
| `data/manual/sites.csv` | Global Energy Monitor (coords), NEPRA (capacity), IPCC 2006 + NEPRA tariff heat rate (EF low/high), NOx control dates | Team, by hand |
| `data/raw/overpasses_<site>.csv` | Earth Engine `COPERNICUS/S5P/OFFL/L3_NO2`, `ECMWF/ERA5_LAND/HOURLY` | Team runs `gee/overpass_export.js` |
| `data/manual/nepra_monthly.csv` | NEPRA FCA decisions (scanned), with `source_pdf, page` per row | Team, by hand |
| `data/manual/nepra_annual.csv` | NEPRA PER Generation FY2024-25 (and earlier years if available) | Team, from readable PDF text |
| `data/raw/climate_trace.csv` | Climate TRACE API v6 | Script `scripts/fetch_climate_trace.py` (run once, saved) |
| `data/raw/reports/*.txt` | Company annual reports, text extracted from PDF | Team downloads; script extracts |
| `data/manual/claims.csv` | Extracted and confirmed claims | Team confirms |
| `data/synthetic/*.csv` | Generated misstated claims, invented farmers | Script; every row flagged |
| `data/manual/plots.csv`, `data/raw/plot_passes.csv` | Invented plots (labelled), real Sentinel-2 readings | Team + Earth Engine |
| `data/raw/c07_*.csv` | Earth Engine C07 export, hand labels | Team |
| `evidence_pack.md` | Per dataset: URL, download date, licence, changes | Team |

**Data window [builder's call]:** Sahiwal from 2018-07 (Sentinel-5P OFFL start) to the latest NEPRA month entered. Minimum to train: 30 months. Typing priority: (1) the most recent 24 months, (2) Feb–May 2020 for the lockdown, (3) Dec 2025–Apr 2026 for the outage, (4) everything else.

## 13. App (Streamlit, one main view for the risk officer)

1. **Company check** (landing page): pick a site → map with plant, downwind/upwind circles → monthly chart (satellite estimate + 80% band, NEPRA, Climate TRACE; LOW_CONFIDENCE months shaded) → claims table with verdict cards → C12 cross-check matrix.
2. **Tree contracts:** plots linked to the company; latest pass per plot; payouts released / held; tree claim vs verified trees.
3. **Reliability (C04):** one button per guard case; shows the returned record.
4. **Model vs baseline (C07):** gain tables and one chart each for trees and pollution.
5. **Log:** every record, filter by status, CSV download.

Every synthetic or invented value carries a visible "synthetic" or "demo" tag.

## 14. Fallbacks (go/no-go at Day 2, 22:00)

| Problem | Fallback |
|---|---|
| Fewer than 30 NEPRA months typed | Train on what exists; report results on quarters; use annual PER totals for validation |
| Monthly correlation weak | Quarterly aggregation → if still weak, three activity levels (high / low / off) with the same verdict logic |
| Hub has too little generation to train | Hub becomes the "mostly off" test case only |
| No real company figure found | Labelled synthetic claims built from real NEPRA numbers |
| Earth Engine export not ready | Pipeline runs on labelled synthetic overpasses so the app and tests work; swap the CSV when real data lands |
| C07 tree RF gain <15% | Report the real number; show pollution C07 too |

## 15. Judging rubric and what each mark needs

Source: *Battle of Intelligence Judge Pack*, 100 marks. A missing piece of evidence scores 0 for that criterion. Overrunning 7:00 costs 2 points per started 30 seconds, capped at 10.

| Criterion | Marks | "Strong" band asks for | What we build or show |
|---|---|---|---|
| Problem, mission, AI relevance | 15 | Precise, feasible task; convincing Green FinTech need; justified AI role | Problem statement naming the risk officer; why a model is needed (NO2 → activity is not a fixed formula; per-plant learning absorbs physics bias) |
| AI solution and demonstration | 30 | Convincing **end-to-end** demo; sound choices; limits explained | One journey in the app, from raw overpasses to verdict, on real data. End-to-end first, breadth second |
| Three challenges | 20 | 5 each: coverage, **appropriate changes**, evidence, **learning / trade-offs / gaps** | `docs/CHALLENGES.md`: for each of C04, C07, C12, what we changed in the design because of it, the test evidence, and what is still unresolved. One slide summarising all three |
| Value and AI evidence | 20 | **Transparent financial assumptions**, environmental rationale, convincing evaluation, data provenance | Financial value model (§15.1), metrics from `outputs/metrics.json`, `evidence_pack.md` |
| Feasibility | 5 | Implementation route, resources, integration | Next-steps slide: pilot bank, cost to run, data licences (§15.2) |
| Pitch clarity | 5 | Clear demo | Two timed rehearsals, recorded backup |
| Q&A | 5 | Accurate answers, team understands its work | PITCH_BRIEF.md question bank; every teammate can explain the 7 NO2 steps |

### 15.1 Financial value model (new, required for the 20-mark criterion)

`verify/value.py` computes, for the selected site and period, with every assumption in `data/manual/assumptions.csv` (value, unit, source, "demo assumption" flag):

1. **Carbon cost exposure:** CO2 range (t) × carbon price scenarios. Use a low and a high illustrative price, e.g. the EU CBAM-linked EU ETS price and a lower voluntary-market price. Label both as scenarios; Pakistan has no domestic carbon price.
2. **Exposure from a misstatement:** (satellite CO2 range − declared CO2) × the same prices = the cost the bank would not see if it trusted the disclosure.
3. **Cost of checking:** our per-company fee (demo assumption) vs a manual site audit (sourced estimate or a labelled assumption).
4. **Tree side:** verified payments released vs held; held money is what the company avoided paying for trees that are not there.

The app shows these as ranges on the verdict card, with an "assumptions" expander. No single-point PKR or USD figure without a range.

### 15.2 Feasibility facts to state

- **Earth Engine licence:** free for research and non-commercial use. Commercial use needs a paid Google Cloud Earth Engine licence. Name this as a cost in the next-steps slide.
- Sentinel data: free and open (Copernicus licence). ERA5: free with attribution (Copernicus licence). Climate TRACE: CC-BY 4.0. NEPRA: public documents.
- Scaling: one Earth Engine script per new isolated plant; NEPRA monthly data entry is the bottleneck. A pilot bank could supply borrower lists and its own disclosure documents.

## 16. Left to the builder

Exact Earth Engine geometry code, regex patterns, chart styling, Streamlit layout details, test file organisation beyond the named files, and conformal implementation details.

## 17. Open questions for the team

1. What Earth Engine output and NEPRA months does Baneen already have?
2. Has anyone found a real generation or CO2 figure in Hub Power's or Sahiwal's owner's reports?
3. Who types the NEPRA months tonight, and how many can realistically be done by 22:00?
4. Are the C07 hand labels done in Shajar's `label.html`, and can they be exported?
