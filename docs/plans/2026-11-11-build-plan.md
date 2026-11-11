> **Historical record.** This is the plan as written on 11 Nov and executed. Later changes (CPPA-G labels, yearly verdicts, no funder split, app redesign) are listed at the top of the design spec.

# Green Claims Verification: Build Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Python pipeline and Streamlit app that checks a coal plant's emissions and tree-offset claims against satellite and NEPRA evidence, with live demos for challenges C04, C07 and C12.

**Architecture:** Earth Engine scripts (run by the team) export per-overpass NO2 and per-plot Sentinel-2 readings to CSV. A Python package `verify/` gates every input, builds monthly plume features, fits a ridge model with conformal intervals, checks tree plots, extracts and cross-checks claims, and writes records to `outputs/`. A Streamlit app reads `outputs/` only.

**Tech Stack:** Python 3.11+, pandas, numpy, scikit-learn, pypdf, streamlit, plotly, pytest. Earth Engine Code Editor (JavaScript) for exports.

**Spec:** `docs/specs/2026-11-11-green-claims-verification-design.md`. Section numbers below (§) refer to it.

## Global Constraints

- Every request returns exactly one record with `status` in `OK`, `LOW_CONFIDENCE`, `REJECTED` (§8, §9). REJECTED records carry no `estimate_gwh`, `interval_*`, `co2_*` or `verdict` keys.
- Reason codes exactly as listed in §8. Codes starting `E_` → REJECTED; codes starting `W_` → LOW_CONFIDENCE.
- NO2 pixel/overpass values from −0.001 to 0.02 mol/m² are valid; −0.00002 passes (control case).
- Never call a network API from `verify/` or `app/`. Network access only in `scripts/fetch_*.py`.
- Banned words in any user-facing string: fraud, breach, proves, zero carbon, net zero. Never "1 km resolution".
- Every synthetic row has `synthetic` in `data_flags`; invented farmers have `invented_farmer`.
- All thresholds live in `verify/rules.py`; no magic numbers elsewhere.
- Commits: plain conventional messages, no co-author or "generated with" trailers, no mention of AI tools.
- Python 3.11+ on Windows; paths built with `pathlib`.

## Review Focus

1. **Missing or NaN values in CSVs** (a month with zero valid overpasses; a blank NEPRA cell). Expect LOW_CONFIDENCE (`W_FEW_OBS`) or a skipped row, never a crash or a NaN verdict. Tests in Task 3 and Task 5.
2. **Claims given as strings with commas or units** ("4,255 GWh", "25%"). Expect parsing to a float, and `E_CLAIM_NOT_IN_SOURCE` matching against the original string form. Test in Task 8.
3. **A month present in features but absent from NEPRA** (the month being verified). Expect a prediction and verdict, with no training on that month. Test in Task 4.
4. **Fiscal-year claims (FY2025 = Jul 2024–Jun 2025) vs monthly evidence.** Expect monthly estimates summed over the fiscal year, with any LOW_CONFIDENCE month widening the interval and making the status LOW_CONFIDENCE if more than 3 of 12 months are LOW_CONFIDENCE. Test in Task 5.
5. **Streamlit rerun with an empty `outputs/`** (fresh clone before build). Expect a message telling the user to run `python -m verify.build`, not a traceback. Check in Task 11.

---

## Team data track (people, in parallel with the code tasks)

These are not code tasks. They unblock real data. Owners per CLAUDE.md.

- [ ] **D1 (Baneen, first):** run `gee/overpass_export.js` (Task 2) for `sahiwal` and `hub`; download the CSVs from Drive into `data/raw/overpasses_sahiwal.csv`, `data/raw/overpasses_hub.csv`.
- [ ] **D2 (Baneen + Arham):** type NEPRA monthly net generation into `data/manual/nepra_monthly.csv` (`plant,month,net_generation_mwh,source_pdf,page`). Priority order from §12: last 24 months, Feb–May 2020, Dec 2025–Apr 2026, then the rest. For `hub`, type both CPHGC and Hub Power Company (RFO).
- [ ] **D3 (Ayesha):** download Hub Power's latest annual / integrated report and Sahiwal owner's report (if any) into `data/raw/reports/`; run `scripts/extract_report_text.py` (Task 8); confirm extracted claims into `data/manual/claims.csv`.
- [ ] **D4 (Baneen):** run `gee/c07_tree_samples.js` and `gee/plots_export.js` (Task 2); export hand labels from Shajar's `label.html` (browser localStorage key `shajar_c07_labels`) as `data/raw/c07_hand_labels.csv`.
- [ ] **D5 (Ayesha):** fill `evidence_pack.md` rows as each dataset lands.
- [ ] **Go/no-go 22:00:** count NEPRA months; pick monthly / quarterly / three-level per §14.

---

### Task 1: Scaffold, rules, records and the validation gate (C04)

**Files:**
- Create: `requirements.txt`, `verify/__init__.py`, `verify/rules.py`, `verify/records.py`, `verify/gate.py`
- Test: `tests/test_guard.py`, `tests/conftest.py`

**Interfaces:**
- Produces:
  - `verify.rules.RULES: dict` with keys: `lat_range=(-90,90)`, `lon_range=(-180,180)`, `site_radius_km=25`, `date_min="2018-07"`, `no2_range=(-0.001,0.02)`, `cloud_range=(0,1)`, `wind_speed_range=(0,60)`, `wind_dir_range=(0,360)`, `calm_wind=1.0`, `irradiance_range=(0,1361)`, `temperature_range=(-40,60)`, `fill_values=(-999,-999.0,-9999)`, `cf_tolerance=1.05`, `ndvi_range=(-1,1)`, `max_trees_per_acre=1000`, `min_overpasses=5`, `ood_margin=0.10`, `max_interval_frac=0.5`, `max_plot_cloud=0.30`, `tree_prob=0.5`, `interval_level=0.80`, `nepra_match_tol=0.05`, `tree_claim_tol=0.10`, `internal_match_tol=0.01`, `fy_low_conf_max=3`, `price_per_tree_year=400`, `passes_per_year=4`, `farmer_share=0.6`, `claim_types=("generation","co2_total","co2_intensity","reduction_pct","trees_planted")`.
  - `verify.records.status_for(codes: list[str]) -> str`: any `E_` → `"REJECTED"`; else any `W_` → `"LOW_CONFIDENCE"`; else `"OK"`.
  - `verify.records.make_record(kind: str, codes: list[str], message: str, **fields) -> dict`: adds `request_id` (`r-0001` counter), `timestamp` (ISO UTC), `kind`, `status`, `reason_codes`, `message`; if REJECTED, drops `estimate_gwh, interval_low, interval_high, co2_low_t, co2_high_t, verdict, gap_pct, valid_overpasses`.
  - `verify.gate` functions, each returning `list[str]` of reason codes (empty = pass):
    - `check_location(lat, lon, sites: pd.DataFrame) -> list[str]` (E_COORD_RANGE, else E_SITE_UNKNOWN if > 25 km from every site; haversine)
    - `check_period(period: str, last_month: str) -> list[str]` (accepts `YYYY-MM` or `FY2025`; E_DATE_RANGE)
    - `check_weather(wind_speed=None, wind_dir=None, solar_irradiance=None, temperature=None) -> list[str]` (fill values → treated as missing, no code)
    - `check_no2(value: float) -> list[str]`, `check_cloud(value: float) -> list[str]`
    - `check_generation(generation_gwh: float, capacity_mw: float, days: int) -> list[str]` (E_CF_OVER_100 above capacity × 24 × days / 1000 × 1.05; E_CLAIM_RANGE if negative)
    - `check_claim(claim: dict, page_text: str | None) -> list[str]` (E_CLAIM_TYPE, E_CLAIM_RANGE, E_REDUCTION_OVER_100, E_CLAIM_NOT_IN_SOURCE when `entry_mode == "extracted"` and `claim["raw_text"]` not in `page_text`)
    - `check_ndvi(value) -> list[str]`, `check_tree_density(trees, acres) -> list[str]` (E_TREE_DENSITY), `check_share(share) -> list[str]` (E_SHARE_RANGE, share in (0,1])
    - `check_confidence(valid_overpasses: int, features: dict, train_ranges: dict, interval_width: float, max_monthly_gwh: float) -> list[str]` (W_FEW_OBS, W_OUT_OF_DISTRIBUTION, W_WIDE_INTERVAL)
  - `verify.gate.GUARD_CASES: list[dict]`, each `{"id": int, "name": str, "input": str, "expected_status": str, "expected_code": str | None, "run": Callable[[], list[str]]}`, the eight cases in §8 in that order.
  - `tests/conftest.py` fixture `sites` → DataFrame with the two rows of §7.4.

- [ ] **Step 1: Write failing tests** in `tests/test_guard.py`:

```python
import pytest
from verify.gate import GUARD_CASES
from verify.records import status_for, make_record

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
    assert r["status"] == "REJECTED" and "estimate_gwh" not in r and "verdict" not in r
```

plus direct tests: `check_location(124.5, 67.1, sites) == ["E_COORD_RANGE"]`; `check_location(30.72, 73.24, sites) == []`; `check_location(25.0, 70.0, sites) == ["E_SITE_UNKNOWN"]`; `check_weather(wind_speed=-8) == ["E_WEATHER_RANGE"]`; `check_weather(solar_irradiance=-999) == []`; `check_no2(-0.00002) == []`; `check_no2(-0.002) == ["E_NO2_RANGE"]`; `check_generation(1300, 1320, 30)` contains `E_CF_OVER_100` (1300 GWh vs 950 max); `check_generation(900, 1320, 30) == []`; `check_claim({"claim_type":"reduction_pct","value":200,"entry_mode":"manual"}, None) == ["E_REDUCTION_OVER_100"]`; `check_claim({"claim_type":"generation","value":4100,"raw_text":"4,100","entry_mode":"extracted"}, "net generation of 4,255 GWh") == ["E_CLAIM_NOT_IN_SOURCE"]`; `check_ndvi(1.8) == ["E_NDVI_RANGE"]`; `check_share(2.0) == ["E_SHARE_RANGE"]`; `check_tree_density(5000, 2) == ["E_TREE_DENSITY"]`; `check_confidence(2, {}, {}, 10, 1000) == ["W_FEW_OBS"]`.

- [ ] **Step 2:** `python -m pytest tests/test_guard.py -v`. Expected: FAIL (module not found).
- [ ] **Step 3:** Write `requirements.txt` (`pandas>=2.1`, `numpy>=1.26`, `scikit-learn>=1.4`, `pypdf>=4`, `streamlit>=1.35`, `plotly>=5.20`, `pytest>=8`), then implement `rules.py`, `records.py`, `gate.py` per Interfaces.
- [ ] **Step 4:** `python -m pytest tests/test_guard.py -v`. Expected: all PASS.
- [ ] **Step 5:** Commit: `git add requirements.txt verify tests && git commit -m "feat: validation gate and C04 guard cases"`

---

### Task 2: Earth Engine export scripts

No automated tests (they run in the Code Editor). Deliverable: scripts that a teammate can paste and run, and a header comment listing the output columns.

**Files:**
- Create: `gee/overpass_export.js`, `gee/plots_export.js`, `gee/c07_tree_samples.js`, `gee/README.md`

**Interfaces:**
- Produces CSVs consumed by Tasks 3, 6, 7:
  - `overpasses_<site>.csv`: `site_id,date,no2_down,no2_up,no2_raw,wind_u,wind_v,wind_speed,wind_dir,cloud_fraction,n_pixels` (one row per Sentinel-5P image; `date` = `YYYY-MM-DD`)
  - `plot_passes.csv`: `plot_id,date,ndvi,cloud,ndvi_p10,ndvi_p25,ndvi_p50,ndvi_p75,ndvi_p90,ndvi_stdDev,mean,B2,B3,B4,B8,B11,B12,ndmi` (annual features over the 12 months ending at `date`, computed as in Shajar's `c07_benchmark.js`)
  - `c07_samples.csv`: `label,split,ndvi_p10,…,ndmi,q1,q2,q3,q4,lon,lat` (same feature names; `split` = train/test; balanced 1,200 per class, seed 7)

- [ ] **Step 1:** `overpass_export.js`: sites list from §7.4. Window 2018-07-01 to today. Map over `COPERNICUS/S5P/OFFL/L3_NO2` filtered to a 60 km box around the site. For each image: ERA5-Land hourly `u_component_of_wind_10m`, `v_component_of_wind_10m` at the image hour rounded to the nearest hour, sampled at the plant. Wind direction *towards* = `atan2(u, v)` in degrees (0 = north). Downwind centre = plant + 10 km along that bearing; upwind centre = plant − 20 km; circles radius 7 km; raw = 5 km circle on the plant; scale 1113 m. Use `cloud_fraction` band mean in the 5 km circle. Skip images where `no2_raw` is null. `Export.table.toDrive` one CSV per site, `selectors` in the column order above. Header comment: "km → degrees: dlat = km/111.32, dlon = km/(111.32·cos(lat))".
- [ ] **Step 2:** `plots_export.js`: copy and adapt Shajar `gee/export_data.js` plot logic (credit Shajar in the header). Read plot coordinates and acres from a pasted list matching `data/manual/plots.csv`; pass dates every quarter from 2025-02-10 to the latest imagery; add the annual feature bands from Shajar `c07_benchmark.js`. Export to Drive.
- [ ] **Step 3:** `c07_tree_samples.js`: adapt Shajar `gee/c07_benchmark.js`, but export the sampled feature table (train and test, with `split`) to Drive instead of training the random forest in Earth Engine. Training happens in Python (Task 7) so it is reproducible and tested.
- [ ] **Step 4:** `gee/README.md`: three numbered run instructions plus where each output goes in `data/raw/`.
- [ ] **Step 5:** Commit: `git add gee && git commit -m "feat: Earth Engine export scripts for overpasses, plots and C07 samples"`

---

### Task 3: Synthetic fixtures and monthly features

**Files:**
- Create: `verify/synthetic.py`, `verify/features.py`, `data/manual/sites.csv`
- Test: `tests/test_features.py`

**Interfaces:**
- Consumes: `verify.gate.check_no2, check_cloud, check_weather`; `verify.rules.RULES`.
- Produces:
  - `data/manual/sites.csv` columns: `site_id,name,owner,listed_parent,lat,lon,capacity_mw,ef_low,ef_high,climate_trace_id,nox_control,nox_control_date,notes` with the two rows of §7.4. `ef_low=0.80`, `ef_high=0.95` for both, with note "to verify: IPCC 2006 + NEPRA tariff heat rate".
  - `verify.synthetic.make_overpasses(site_id: str, months: list[str], seed: int = 0) -> pd.DataFrame` in the `overpasses_<site>.csv` schema, plus `data_flags="synthetic"`. Generation pattern is driven by `make_nepra(...)` so features correlate with labels. Monsoon months (Jul–Sep) get 2–4 overpasses, the rest 12–20.
  - `verify.synthetic.make_nepra(site_id, months, capacity_mw, seed=0) -> pd.DataFrame` with columns `plant,month,net_generation_mwh,source_pdf,page,data_flags`.
  - `verify.features.clean_overpasses(df) -> tuple[pd.DataFrame, pd.DataFrame]` → (kept, rejected-with-`reason_codes`). Calm (< 1 m/s) rows are dropped from kept but not counted as rejected.
  - `verify.features.monthly_features(df) -> pd.DataFrame` with one row per `site_id, month` and columns `enh_mean, flux_proxy, raw_mean, valid_overpasses, wind_mean, month_sin, month_cos, synthetic: bool`.

- [ ] **Step 1: Failing tests:** `clean_overpasses` keeps a row with `no2_down=-0.00002`, rejects `wind_speed=-8` with `E_WEATHER_RANGE`, drops `wind_speed=0.5` silently; `monthly_features` on three overpasses with enhancements 1e-5, 2e-5, 3e-5 and wind 2, 4, 6 gives `enh_mean == 2e-5` and `flux_proxy == pytest.approx((2e-5 + 8e-5 + 18e-5) / 3)`; a month with no kept rows does not appear (handled in Task 5); synthetic overpasses give `monthly_features(...)["synthetic"].all()`; Pearson r between synthetic `flux_proxy` and synthetic generation > 0.6.
- [ ] **Step 2:** run `python -m pytest tests/test_features.py -v`. Expected: FAIL.
- [ ] **Step 3:** implement. `enhancement = no2_down − no2_up`; `month = date[:7]`; `month_sin/cos = sin/cos(2π·m/12)`.
- [ ] **Step 4:** run the tests. Expected: PASS.
- [ ] **Step 5:** commit `"feat: monthly plume features and labelled synthetic fixtures"`

---

### Task 4: Activity model, intervals and C07 pollution baselines

**Files:**
- Create: `verify/model.py`
- Test: `tests/test_model.py`

**Interfaces:**
- Consumes: `monthly_features` output; NEPRA DataFrame (`plant, month, net_generation_mwh`).
- Produces:
  - `FEATURES = ["flux_proxy", "enh_mean", "valid_overpasses", "wind_mean", "month_sin", "month_cos"]`
  - `join_labels(features: pd.DataFrame, nepra: pd.DataFrame, site_map: dict[str, list[str]]) -> pd.DataFrame` adds `generation_gwh` (sum of mapped plants; NaN when missing). `site_map = {"sahiwal": ["Huaneng Shandong Ruyi"], "hub": ["China Power Hub Generation", "The Hub Power Company"]}`.
  - `fit(train: pd.DataFrame) -> dict` → `{"pipeline": sklearn Pipeline(StandardScaler, RidgeCV(alphas=logspace(-3,3,13))), "q80": float, "train_ranges": {feature: (min, max)}, "max_monthly_gwh": float}`. `q80` = 80th percentile of absolute out-of-fold residuals from `TimeSeriesSplit(n_splits=min(5, len(train)//6))`.
  - `predict(model: dict, rows: pd.DataFrame) -> pd.DataFrame` with `estimate_gwh, interval_low (clipped at 0), interval_high`.
  - `evaluate(data: pd.DataFrame, holdout: int = 12) -> dict` → `{"n_train", "n_test", "rmse", "mae", "mape", "r", "coverage_80", "baselines": {"capacity_heuristic": {"rmse"}, "raw_no2_linear": {"rmse"}, "moving_avg_3_reference": {"rmse"}}, "gain_vs_capacity_pct", "gain_vs_raw_pct"}`. Holdout = last `holdout` months that have labels.
  - `baseline_capacity(rows, capacity_mw: float, fleet_pf: float) -> np.ndarray` = capacity × hours in month × fleet_pf / 1000.
  - `baseline_raw_linear(train, test) -> np.ndarray` = `LinearRegression` on `raw_mean` only.
  - `gain_pct(baseline_rmse, primary_rmse) -> float` = (b − p) / b × 100.

- [ ] **Step 1: Failing tests:** on 60 synthetic months, `evaluate(...)["coverage_80"]` between 0.5 and 1.0; `evaluate(...)["rmse"] < baselines["capacity_heuristic"]["rmse"]`; `predict` interval_low ≤ estimate ≤ interval_high and interval_low ≥ 0; a features row whose month has no NEPRA label still gets a prediction and is never in training (assert `fit` called on labelled rows only, via `n_train` count); `gain_pct(100, 80) == 20.0`.
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement per Interfaces. `fleet_pf` comes from `data/manual/nepra_annual.csv` (imported-coal fleet utilisation for the fiscal year); in tests pass 0.229 (FY25 imported-coal total from the NEPRA report).
- [ ] **Step 4:** run, expect PASS.
- [ ] **Step 5:** commit `"feat: ridge activity model, conformal interval, pollution baselines"`

---

### Task 5: Verdicts, CO2 range, fiscal-year roll-up and value model

**Files:**
- Create: `verify/verdict.py`, `verify/value.py`, `data/manual/assumptions.csv`
- Test: `tests/test_verdict.py`

**Interfaces:**
- Consumes: `gate.check_confidence`, `records.make_record`, `model.predict` output.
- Produces:
  - `compare(value: float, low: float, high: float) -> tuple[str, float | None]` → `("CONSISTENT", None)` inside; else `("INCONSISTENT", gap_pct)` where gap_pct = (value − nearest edge) / nearest edge × 100 (signed, 1 decimal).
  - `co2_range(gen_low_gwh, gen_high_gwh, ef_low, ef_high) -> tuple[float, float]` in tonnes (GWh × 1000 × EF).
  - `emissions_record(site: dict, month_row: dict, pred: dict | None, claim: dict | None, model: dict) -> dict`: runs `check_confidence`; month with `valid_overpasses == 0` or missing → `W_FEW_OBS`; builds the record; verdict = `CANNOT_VERIFY` if LOW_CONFIDENCE or no claim. Message templates:
    - INCONSISTENT low: `"Disclosed {metric} is {abs(gap)}% below the lowest value the satellite evidence supports. Refer for review."`
    - INCONSISTENT high: `"... {gap}% above the highest value ..."`
    - CONSISTENT: `"Disclosed {metric} is within the range the satellite evidence supports."`
    - CANNOT_VERIFY: `"Not enough clear satellite evidence this month to check the claim."`
  - `fiscal_rollup(records: list[dict], fy: str) -> dict`: sums estimate and interval over Jul–Jun; LOW_CONFIDENCE months are included but widen the band by their own interval; status LOW_CONFIDENCE if > `fy_low_conf_max` months are LOW_CONFIDENCE or any month is missing.
  - `data/manual/assumptions.csv`: `key,value,unit,source,demo_assumption` with rows `carbon_price_low` (voluntary-market illustrative, USD/t), `carbon_price_high` (EU ETS recent level, USD/t; fill with source and date), `usd_pkr`, `fee_per_company_pkr` (demo), `manual_audit_cost_pkr` (demo unless sourced).
  - `verify.value.exposure(co2_low_t, co2_high_t, assumptions: dict) -> dict` → `{"carbon_cost_usd": (lo, hi), "misstatement_usd": (lo, hi) | None}` where lo uses co2_low × price_low and hi uses co2_high × price_high; misstatement uses `max(0, co2_low − declared)` and `max(0, co2_high − declared)`.

- [ ] **Step 1: Failing tests:** `compare(300, 430, 590) == ("INCONSISTENT", -30.2)`; `compare(500, 430, 590) == ("CONSISTENT", None)`; `co2_range(400, 500, 0.8, 0.95) == (320000.0, 475000.0)`; a LOW_CONFIDENCE month with a claim gives `verdict == "CANNOT_VERIFY"` and `estimate_gwh` present; a month with 0 overpasses gives status LOW_CONFIDENCE and code `W_FEW_OBS`, with no exception; `fiscal_rollup` with 4 LOW_CONFIDENCE months → status LOW_CONFIDENCE; a user-facing message contains none of the banned words (loop over all templates); `exposure(...)` returns ranges with lo ≤ hi.
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** run, expect PASS.
- [ ] **Step 5:** commit `"feat: verdict engine, CO2 range, fiscal roll-up, exposure model"`

---

### Task 6: Tree plots, passes and payouts

**Files:**
- Create: `verify/trees.py`, `data/manual/plots.csv`
- Test: `tests/test_trees.py`

**Interfaces:**
- Consumes: `gate.check_ndvi, check_cloud, check_tree_density`; a fitted tree classifier from Task 7 (`classify(model, rows) -> np.ndarray` of probabilities). Until Task 7 lands, tests pass a stub returning fixed probabilities.
- Produces:
  - `data/manual/plots.csv`: Shajar's six plots (credit in a comment row), columns `plot_id,farmer,village,lat,lon,acres,trees_planted,contract_since,financier,site_id,data_flags` with `data_flags="invented_farmer"`; `site_id` = `sahiwal` for all.
  - `verify_pass(row: dict, latest_imagery: str, tree_prob: float | None) -> tuple[str, list[str]]` → status in `verified|failed|cloudy|no_imagery|invalid` and codes (`E_NDVI_RANGE`, `E_SAT_RANGE`, `W_CLOUDY`, `W_NO_IMAGERY`). `verified` iff prob ≥ 0.5 and cloud ≤ 0.30.
  - `payout(trees: int, status: str) -> dict` → `{"released", "farmer", "financier", "held"}` (verified: released = trees × 400 / 4, split 60/40; failed or invalid: held = same amount; cloudy or no_imagery: all zero).
  - `verified_trees(plots: pd.DataFrame, latest_status: dict[str, str]) -> int`: sum of `trees_planted` for plots whose latest status is `verified`.

- [ ] **Step 1: Failing tests:** NDVI 1.8 → `("invalid", ["E_NDVI_RANGE"])`; cloud 0.9 → `("cloudy", ["W_CLOUDY"])`; date after latest imagery → `("no_imagery", ["W_NO_IMAGERY"])`; prob 0.8 and cloud 0.1 → `verified`; prob 0.2 → `failed`; `payout(1200, "verified") == {"released": 120000, "farmer": 72000, "financier": 48000, "held": 0}`; `payout(1200, "cloudy")["held"] == 0`; `verified_trees` sums verified plots only.
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** run, expect PASS.
- [ ] **Step 5:** commit `"feat: tree pass verification and payouts"`

---

### Task 7: C07 tree benchmark (random forest vs NDVI threshold)

**Files:**
- Create: `verify/c07.py`
- Test: `tests/test_c07.py`

**Interfaces:**
- Consumes: `c07_samples.csv` schema (Task 2); optional `c07_hand_labels.csv` (`lon,lat,label`).
- Produces:
  - `TREE_FEATURES = ["ndvi_p10","ndvi_p25","ndvi_p50","ndvi_p75","ndvi_p90","ndvi_stdDev","mean","B2","B3","B4","B8","B11","B12","ndmi"]`
  - `f1(y_true, y_pred) -> float` (sklearn `f1_score`, zero_division=0)
  - `train_tree_model(train: pd.DataFrame) -> RandomForestClassifier` (`n_estimators=200, random_state=7, class_weight="balanced"`)
  - `classify(model, rows: pd.DataFrame) -> np.ndarray` (probability of class 1)
  - `threshold_baseline(train, test, quarter_cols=("q1","q2","q3","q4")) -> dict` → `{"tuned": {"threshold", "f1"}, "fixed_035": {"f1"}}`: a single quarter's NDVI ≥ threshold, threshold swept 0.10–0.80 step 0.01 on train, scored on test, averaged over the four quarters (fair: the baseline gets its best threshold).
  - `benchmark(samples: pd.DataFrame, hand: pd.DataFrame | None) -> dict` → `{"test": {"rf_f1", "baseline_tuned_f1", "baseline_fixed_f1", "gain_vs_tuned_pct", "gain_vs_fixed_pct"}, "hand": {...same, or None}, "n_train", "n_test", "answer_key": "ESA WorldCover v200 tree class + team hand labels"}`

- [ ] **Step 1: Failing tests:** on a synthetic sample set where class 1 has a high NDVI p10 and class 0 has a high NDVI in only one quarter (crops), `benchmark(...)["test"]["rf_f1"] > ["baseline_tuned_f1"]`; `gain` uses (rf − base) / base × 100; `f1` of perfect predictions == 1.0; with `hand=None` the result has `"hand": None`.
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement. The synthetic generator for this test lives in the test file, not `verify/synthetic.py`.
- [ ] **Step 4:** run, expect PASS.
- [ ] **Step 5:** commit `"feat: C07 tree classifier benchmark against NDVI threshold"`

---

### Task 8: Claim extraction and cross-check (C12)

**Files:**
- Create: `verify/claims.py`, `scripts/extract_report_text.py`, `data/synthetic/claims_synthetic.csv` (generated)
- Test: `tests/test_claims.py`

**Interfaces:**
- Consumes: `gate.check_claim`; `verdict.compare`, `verdict.co2_range`; `trees.verified_trees`.
- Produces:
  - `scripts/extract_report_text.py <pdf>` → writes `data/raw/reports/<name>.pages.json` (`[{"page": n, "text": str}]`) using pypdf.
  - `parse_number(s: str) -> float`: `"4,255"` → 4255.0; `"25%"` → 25.0; `"3.5 million"` → 3_500_000.0.
  - `extract_claims(pages: list[dict], source: str) -> list[dict]`: each `{"claim_type", "value", "unit", "period" | None, "source_page", "source_quote" (the sentence), "raw_text" (the matched number string as printed), "modality": "table" | "text", "entry_mode": "extracted", "source"}`. Patterns:
    - generation: number + `GWh` / `MWh` / `million units` near `generat|dispatch`
    - co2_total: number + `tCO2` / `tonnes of CO2` / `tCO2e` / `million tonnes`
    - reduction_pct: `(reduc|cut|lower)\w*[^.]{0,60}?(\d+(\.\d+)?)\s?%`
    - trees_planted: number near `trees?` and `plant`
    - modality = `table` if the matching line has ≥ 3 numbers, else `text`.
  - `cross_check(site_id: str, period: str, claims: list[dict], evidence: dict) -> list[dict]` with `evidence = {"nepra_gwh": float | None, "sat": {"low", "high", "status"} | None, "nepra_prev_gwh": float | None, "sat_prev": {...} | None, "ef": (low, high), "verified_trees": int | None}`. Returns one dict per applicable pair X1–X7 from §7.3: `{"pair": "X1", "left": str, "right": str, "result": "AGREE"|"CONTRADICT"|"CANNOT_COMPARE", "reason": str}`. X2/X4 give `CANNOT_COMPARE` when `sat.status != "OK"`.
  - `claim_verdict(checks: list[dict]) -> str` per §7.3.
  - `make_synthetic_claims(nepra: pd.DataFrame, scales=(0.8, 0.6, 0.4, 1.0)) -> pd.DataFrame` → misstated + true claims with `data_flags="synthetic"`, plus one paired text claim per period ("reduced emissions by 25%") whose direction contradicts the NEPRA year-on-year change, to demo C12.

- [ ] **Step 1: Failing tests:**
  - `parse_number("4,255") == 4255.0`, `parse_number("3.5 million") == 3_500_000.0`
  - `extract_claims([{"page": 12, "text": "In FY2025 the plant dispatched 4,100 GWh to the national grid."}], "hub_ar_2025")[0]` has `claim_type == "generation"`, `value == 4100.0`, `source_page == 12`, `raw_text == "4,100"`
  - `extract_claims` finds `reduction_pct == 25.0` in "We reduced our carbon emissions by 25% compared to last year."
  - cross-check: declared 4,100 vs NEPRA 4,255 → X1 `AGREE` (3.6% < 5%); declared 3,000 vs NEPRA 4,255 → X1 `CONTRADICT`
  - text "reduced emissions by 25%" with `nepra_gwh=4255`, `nepra_prev_gwh=3800` → X5 `CONTRADICT` (generation rose 12%)
  - claimed 50,000 trees vs `verified_trees=30500` → X6 `CONTRADICT`
  - table value 4,100 vs text value 4,300 for the same metric → X7 `CONTRADICT`
  - `sat.status == "LOW_CONFIDENCE"` → X2 `CANNOT_COMPARE`
  - `claim_verdict` with one X1 CONTRADICT → `INCONSISTENT`; all AGREE → `CONSISTENT`; only CANNOT_COMPARE → `CANNOT_VERIFY`
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement.
- [ ] **Step 4:** run, expect PASS.
- [ ] **Step 5:** commit `"feat: claim extraction and multi-source cross-check (C12)"`

---

### Task 9: Climate TRACE fetch

**Files:**
- Create: `scripts/fetch_climate_trace.py`, `data/raw/climate_trace.csv` (output, committed)

**Interfaces:**
- Produces `climate_trace.csv`: `site_id,asset_id,asset_name,emissions_t_co2e,activity_mwh,confidence,year_note,fetched_at`, for assets 25455252 (sahiwal), 25455585 and 448261 (both `hub`).

- [ ] **Step 1:** script using `urllib.request` against `https://api.climatetrace.org/v6/assets?countries=PAK&sectors=electricity-generation&limit=100`; filter by the three IDs; write CSV. If the record holds per-year values, write one row per year; else `year_note = "not stated in API record"`.
- [ ] **Step 2:** run `python scripts/fetch_climate_trace.py`. Expected: a CSV with ≥ 3 rows.
- [ ] **Step 3:** commit `"data: Climate TRACE benchmark for Sahiwal and Hub"`

---

### Task 10: Build orchestrator

**Files:**
- Create: `verify/build.py`, `verify/io.py`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes everything above.
- Produces:
  - `verify.io.load_inputs(root: Path) -> dict` reads every input CSV; for any missing real file, falls back to `verify.synthetic` and records `"synthetic"` in a `sources` dict (`{"overpasses_sahiwal": "real" | "synthetic", ...}`).
  - `python -m verify.build [--root .]` writes: `outputs/monthly.csv` (features + labels + predictions + status), `outputs/verdicts.csv` (all records, JSON-encoded list fields), `outputs/cross_checks.csv`, `outputs/tree_passes.csv`, `outputs/guard_results.csv` (the eight `GUARD_CASES` run through `make_record`), `outputs/metrics.json` (`{"pollution": evaluate(...), "trees": benchmark(...), "claims": {"detection_rate", "false_alarm_rate", "by_scale": {"0.8", "0.6", "0.4"}}, "sources": {...}, "built_at"}`).
  - `claim_detection(records: list[dict]) -> dict`: over synthetic generation claims on held-out OK months, detection rate = share of misstated claims (scale < 1) marked INCONSISTENT; false-alarm rate = share of true claims (scale 1.0) marked INCONSISTENT.

- [ ] **Step 1: Failing test:** `build(tmp_path)` on an empty `data/` (all synthetic) creates all six output files; `metrics.json["sources"]` values are all `"synthetic"`; every row in `verdicts.csv` has a status; every record built from synthetic data has `synthetic` in `data_flags`; `claim_detection` on two misstated INCONSISTENT records and one true CONSISTENT record gives `{"detection_rate": 1.0, "false_alarm_rate": 0.0, ...}`.
- [ ] **Step 2:** run, expect FAIL.
- [ ] **Step 3:** implement. `build(root: Path) -> dict` returns the metrics dict; `__main__` calls it.
- [ ] **Step 4:** run `python -m pytest -v` (whole suite). Expected: PASS.
- [ ] **Step 5:** commit `"feat: one-command build of all outputs"`

---

### Task 11: Streamlit app

**Files:**
- Create: `app/streamlit_app.py`, `app/components.py`

**Interfaces:**
- Consumes `outputs/*` only (no imports from `verify/` except `verify.gate.GUARD_CASES` and `verify.records.make_record` for the live C04 buttons).

- [ ] **Step 1:** Five pages via `st.sidebar.radio`, in the order of spec §13. Company check is the landing page.
  - Map: `pydeck` or `plotly.scatter_mapbox` with the open-street-map style (no token). Plant marker plus downwind/upwind circles for the selected month's mean wind.
  - Chart: plotly line chart with the satellite estimate and an 80% band (filled), NEPRA, and Climate TRACE as a horizontal annual reference; LOW_CONFIDENCE months shaded grey; labelled vertical bands for the strict lockdown (2020-03-23 to 2020-04-15) and the Sahiwal forced outage / reduced capacity (2026-01 to 2026-03).
  - Verdict card: status badge colour (OK green, LOW_CONFIDENCE amber, REJECTED red), verdict, message, gap, source page and quote, CO2 range labelled "derived, not measured", and an exposure range with an "Assumptions" expander.
  - Cross-check matrix (C12): table of X1–X7 with AGREE / CONTRADICT / CANNOT_COMPARE.
  - Trees: table of plots, latest status, released/held PKR; tree claim vs verified trees.
  - Reliability: one `st.button` per guard case; shows the JSON record.
  - Model vs baseline: two small tables from `metrics.json` (trees F1, pollution RMSE) with gain %, and a note when the gain is under 15%.
  - Log: `verdicts.csv` with a status filter and `st.download_button`.
  - A visible banner when `metrics.json["sources"]` has any `"synthetic"`: "Some inputs are synthetic test data: <list>".
- [ ] **Step 2:** empty-outputs check: with `outputs/` absent, the app shows "Run `python -m verify.build` first" and stops.
- [ ] **Step 3:** run `streamlit run app/streamlit_app.py`; click through all five pages and all eight guard buttons. Expected: no exceptions; the synthetic banner is visible.
- [ ] **Step 4:** commit `"feat: Streamlit app for the risk officer journey"`

---

### Task 12: Evidence pack, challenge write-up, pitch update

**Files:**
- Create: `evidence_pack.md`, `docs/CHALLENGES.md`
- Modify: `docs/PITCH_BRIEF.md`

- [ ] **Step 1:** `evidence_pack.md`: one row per dataset (§12): URL, download date, licence, changes made, real / synthetic. List every mocked part.
- [ ] **Step 2:** `docs/CHALLENGES.md`: for each of C04, C07, C12, four headings that mirror the rubric (§15): *Coverage and understanding*, *What we changed because of it*, *Evidence* (exact numbers from `outputs/metrics.json` and test names), *Trade-offs and unresolved gaps*. Fill the numbers only from outputs, never by hand.
- [ ] **Step 3:** `docs/PITCH_BRIEF.md`: add C07 and C12 to sections 2, 7 and 8; fill accuracy question 8 from `metrics.json`; add a one-slide challenge summary table.
- [ ] **Step 4:** commit `"docs: evidence pack and challenge write-up"`

---

## Order and timing (Day 2 evening → Day 3 morning)

| Block | Tasks | Done means |
|---|---|---|
| 16:30–18:00 | 1, 2 | Gate tests green; Earth Engine scripts in teammates' hands |
| 18:00–20:30 | 3, 4, 5 | Model and verdicts work end to end on synthetic data |
| 20:30–22:00 | 6, 7, 8, 9 | Trees, C07 and C12 in |
| 22:00 | go/no-go | Swap in real overpasses and NEPRA months; rerun build |
| 22:00–01:00 | 10, 11 | App runs on real data where available |
| Day 3 morning | 12 + rehearsals | Evidence pack, challenge write-up, two timed run-throughs, recorded backup |
