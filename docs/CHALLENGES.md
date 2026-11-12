# Our three challenges: what we changed, what we measured, what is still open

Numbers come from `outputs/metrics.json` (`python -m verify.build`, built 11 Nov 2026) and the test suite (`python -m pytest`, 80 tests). Each section follows the jury's four marks: coverage, changes, evidence, gaps.

## Summary slide

| Challenge | What it asks | Our answer | Evidence |
|---|---|---|---|
| **C04** Out-of-bounds guard | 5 impossible inputs → rejection or low confidence, never a confident wrong number | 8 live cases: 5 rejected out-of-bounds, 1 low-confidence, 1 claim not in source, 1 noise control that passes | `tests/test_guard.py`, 19 tests; app "Reliability" page; real monthly data abstains on its own |
| **C07** Beat a simple baseline by ≥15% | RMSE or F1 gain over a heuristic | Pollution model RMSE 169.5 vs 442.0 (capacity rule) and 243.5 (raw NO2) GWh | **61.7%** and **30.4%** gain on 9 held-out real months (Sahiwal) |
| **C12** Multimodal cross-check | Declared numbers vs text claims vs satellite | 10 checks of 7 kinds (X1–X7; X1 and X2 run on both the report table and the report text) between report table, report text, metered generation, satellite range, tree plots | Sahiwal: 10 of 10 disagree. Hub: 4 agree, 5 disagree, 1 cannot compare, so the checks don't flag everything. Climate TRACE about 5x off at Hub. Related model evidence: annual understatements of 20% or more caught in 94–100% of 16 rolling windows, 0 false alarms |

---

## C04: Out-of-bounds and hallucination guard

**Coverage and understanding.** Impossible inputs (no such place, negative wind, a 200% cut, more than 100% of capacity, a greenness above 1) must stop the pipeline. Thin evidence must lower confidence. Normal sensor noise must not be thrown away. These are three different behaviours, so we test all three.

**What we changed because of it.**
- Every request returns exactly one record with status OK / LOW_CONFIDENCE / REJECTED and reason codes. A REJECTED record cannot carry an estimate or a verdict (enforced in `verify/records.py`, tested).
- Three gates: physical bounds, plausibility, model confidence (`verify/gate.py`).
- Small negative NO2 (above −0.001 mol/m²) is kept, because it is normal retrieval noise.
- NASA POWER fill values (−999) are treated as missing, never as readings.
- A claim extracted from a report is rejected if its number is not on the cited page (`E_CLAIM_NOT_IN_SOURCE`). This guards against a misread or invented figure.

**Evidence.**

| # | Injected input | Result | Code |
|---|---|---|---|
| 1 | Latitude 124.5 | REJECTED | E_COORD_RANGE |
| 2 | Wind speed −8 m/s | REJECTED | E_WEATHER_RANGE |
| 3 | 200% emissions cut | REJECTED | E_REDUCTION_OVER_100 |
| 4 | 1,380 GWh in 30 days from a 1,320 MW plant (145% capacity factor) | REJECTED | E_CF_OVER_100 |
| 5 | NDVI 1.8 | REJECTED | E_NDVI_RANGE |
| 6 | August with 2 clear satellite passes | LOW_CONFIDENCE | W_FEW_OBS |
| 7 | Figure not on the cited page | REJECTED | E_CLAIM_NOT_IN_SOURCE |
| 8 | NO2 of −0.00002 mol/m² (noise) | OK | none |

All 8 pass in `tests/test_guard.py` and as buttons in the app. On real data, the guard also fired by itself: every single month's 80% interval was wider than half the plant's largest month, so every monthly verdict abstained (`W_WIDE_INTERVAL`) instead of guessing.

**Trade-offs and gaps.**
- Bounds marked "tune" in `verify/rules.py` (5 overpasses a month, 25 km site radius) are starting values, not fitted.
- The claim-in-source check only proves the number appears on the page, not that it means what we think.

## C07: Heuristic baseline showdown

**Coverage and understanding.** A model is only worth its complexity if it clearly beats the simple rule a person would otherwise use. We chose baselines a bank could actually use, and we held out the most recent months.

**What we changed because of it.**
- Two fair baselines that use no company-reported data:
  - *Capacity rule of thumb:* capacity × NEPRA's FY2024-25 imported-coal fleet utilisation (22.9%).
  - *Naive satellite:* a linear fit on raw NO2 over the plant, with no wind or background correction.
- The 3-month moving average of past metered generation is shown **for reference only**: it uses the reported numbers we are trying to check, so it is not a fair verification baseline.
- The main feature became enhancement × wind speed. Stronger wind dilutes the plume, so raw enhancement alone understates a windy month.
- Kept the model simple (ridge regression), because 27 labelled months cannot support anything bigger.

**Evidence (real data, Sahiwal, 18 training months, 9 held-out months Jan–Sep 2026).**

| Model | RMSE (GWh/month) | Gain |
|---|---|---|
| **Ridge on wind-corrected plume** | **169.5** | — |
| Capacity × fleet average | 442.0 | **61.7%** |
| Linear on raw plant NO2 | 243.5 | **30.4%** |
| 3-month moving average of reported data (reference only) | 139.8 | (model is 21% worse) |

Correlation on held-out months r = 0.45; across all 27 labelled months, the monthly plume correlates with metered generation at r = 0.62 (raw NO2: 0.53). 78% of held-out months fall inside the 80% interval.

**Tree classifier (second C07 entry), real data:** random forest on a year of Sentinel-2 vs a single NDVI threshold, 1,385 training and 575 test points in lower Sindh, labels from ESA WorldCover 2021. F1 on the test points: random forest **0.891**, best single threshold 0.798, the fixed 0.35 threshold 0.781. Gain **11.6%** over the tuned threshold and **14.1%** over the fixed one: **short of the 15% bar.** Adding the four seasonal greenness values improved training-set cross-validation only from 0.881 to 0.887, so we did not keep tuning towards the bar. Honest reading: for spotting trees, a well-chosen threshold gets most of the way; the forest's edge is real but modest. C07 is met by the emissions model, not by this one. WorldCover is itself a Sentinel-2 model, and the team's own hand labels were not collected, so this is scored against another model's labels.

**Trade-offs and gaps.**
- At Hub the model barely beats raw NO2 (−1.9%): CPHGC was mostly off and the site is coastal, where sea breezes move the plume. Stated as a limit.
- The moving average of reported data does better month to month. That is expected: generation this month is close to last month's. It needs the very figures under question, so it cannot verify anything.
- Nine test months is a small test set.

## C12: Multimodal consistency cross-check

**Coverage and understanding.** A company's report states numbers in tables and claims in prose. We check each against independent sources and against each other, and show the officer *which* sources disagree.

**What we changed because of it.**
- Rule-based extraction (no language model) keeps the page, the sentence and the number as printed. Every extracted value must appear verbatim on its page (C04 case 7).
- Seven cross-checks: X1 table vs metered, X2 table vs satellite range, X3 CO2 vs metered × emission factor, X4 CO2 vs satellite CO2, X5 "we cut emissions N%" vs actual change, X6 tree claim vs satellite-verified trees, X7 table vs narrative (internal consistency).
- **Verdicts moved from months to fiscal years.** Single months are too noisy (±250 GWh). Companies disclose annually, and independent monthly errors add in quadrature, so a year is much tighter: about ±940 GWh on a ~6,000 GWh year. The interval is widened for the residuals' measured autocorrelation (lag-1 = 0.10).

**Evidence.**
- *Detection test:* 16 rolling 12-month windows of leave-one-out estimates (each month predicted by a model that never saw it), with true and understated claims built from metered numbers. Understated by 20%: caught in 94% of windows. By 40% or 60%: 100%. False alarms on true claims: 0%. The windows overlap, so they are not 16 independent tests.
- *FY2026 Sahiwal:* satellite estimate 5,896 GWh (80% range 4,967–6,833), each month predicted by a model that never saw it; metered 6,138 GWh, so 3.9% low. Across 16 rolling years the annual error averages 7.3% (worst 20.2%); a strict forward-only test over the last 15 months is 15.4% low. An earlier draft quoted 5,982 GWh from a model that had seen those months; that figure was withdrawn.
- *Demo company claim (synthetic, labelled):* table says 4,603 GWh (25% under the meter). X1 metered and X2 satellite both disagree; the satellite catches it with no access to the meter. The narrative "we cut emissions by 25%" contradicts a metered rise of 44%. "50,000 trees planted" contradicts 2,200 trees on plots the satellite confirms alive.
- *Climate TRACE vs metered, calendar 2025:* CPHGC 3,816 vs ~702 GWh (5.4×); Hub Power oil plant 3,158 vs ~0 GWh. A modelled inventory is no substitute for a check against real data.

**Trade-offs and gaps.**
- No real company figure was found in a public report, so the demo claims are synthetic, built from real metered numbers.
- At Hub, the satellite range is too wide to catch a 25% understatement (detection 33%). The metered check (X1) still catches it.
- CO2 is derived (generation × 0.80–0.95 t/MWh) and is a range, never a measurement.
