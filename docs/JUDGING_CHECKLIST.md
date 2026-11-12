# Judging checklist: Team 13 (IU3048)

**Checked against:** the Participant Guide, Missions, Batch-wise Challenges, the Judge Pack (rubric and scoring form) and the 7-minute pitch template.

**Checked:**
- the pitch deck (`Satellite_Verification_Pitch_Deck.pptx`)
- the app (local and hosted)
- `outputs/`
- `evidence_pack.md`
- `docs/PITCH_BRIEF.md`

**Date:** 2026-11-12.

Legend: **[x]** done and shown, **[~]** done but weak or needs a fix, **[ ]** missing.

---

## 0. Fix before the pitch (ranked by marks at risk)

> **Update, 2026-11-12:** the deck has been rebuilt on the official **`Battle_of_Intelligence_7_Minute_Pitch_Template.pptx`** as **`Satellite_Verification_Pitch_Deck_v2.pptx`**, with a PDF next to it.
> - It follows the template's 7 slides plus a Q&A slide, one slide per rubric line.
> - Fixes 1–8 below are applied in v2, and its speaker notes match the on-slide timings: 20, 40, 60, 90, 90, 75 and 45 s.
> - **Fixes 9 and 10 are still open.**
> - Use v2 for the pitch. The old deck is kept for reference only.

| # | Problem | Where | Why it costs marks | Fix |
|---|---|---|---|---|
| 1 | **"About 7% average error over 16 years" is wrong.** We have 27 months of data, not 16 years. The 7% is the average over **16 overlapping 12-month windows** | Deck slide 6 | A judge who knows we have 27 months will doubt every other number (Value and evidence, 20) | Change to "about 7% average error across 16 overlapping 12-month windows; 15% in the strictest forward test" |
| 2 | **Speaker notes add up to 7:45; the on-slide timings add up to 7:00.** The notes still say 45 s, 2 min and 75 s. Anyone rehearsing from the notes will run over | Notes on slides 1–8 | 2 marks per started 30 s past 7:00, so up to 4 marks lost | Make the notes match the slide timings: 30, 45, 30, 45, 105, 45, 70 and 50 s |
| 3 | **The C12 evidence cell reports the wrong result.** "94–100% of understated claims caught" is the yearly *detection* test (closer to C07). C12 asks whether we *detect contradictions between sources* | Deck slide 7, C12 row | Challenge score, "evidence of results" (5) | Use: "Sahiwal: 10 of 10 checks disagree. Hub: 4 agree, 5 disagree, 1 cannot compare. Climate TRACE off about 5x at Hub" |
| 4 | **The demo only shows "disagree".** On Sahiwal, all 10 checks disagree, so a judge may think the system flags everything | Demo | Solution and demonstration (30) | Switch the company picker to **Hub** for 10 seconds: 4 checks agree. That shows the system can say "consistent" |
| 5 | **"7 cross-checks" on slide 3 vs "10 checks" in the app** | Deck slide 3 vs app | Looks inconsistent | Say "10 checks of 7 kinds" (X1 and X2 run on both the report table and the report text) |
| 6 | **The C04 cell says "(5 rejected)"; the run shows 6 rejected, 1 low confidence, 1 accepted** | Deck slide 7 | Small, but easy to catch | "8 of 8 correct: 6 rejected, 1 low confidence, 1 normal value accepted" |
| 7 | **Value is in USD only, and the range is very wide (USD 20M–519M)** | Deck slide 8 | Value (20): judges want transparent assumptions; the challenge set uses PKR | Add PKR (at 280: PKR 5.6bn–145bn) and say in one breath that the width comes from two carbon prices, USD 5 and USD 80 a tonne, not from the satellite |
| 8 | **No PDF of the deck** in the hackathon folder | Folder | Backup if the laptop or PowerPoint fails | Export the PDF after fixes 1–7 |
| 9 | **The hosted app may still show old numbers.** The local server had cached the old tree result | Hosted URL | A broken demo costs most of the 30 marks | Open the C07 tab on the hosted URL. It must say F1 0.89 vs 0.80. If not, reboot the app in the Streamlit Cloud dashboard |
| 10 | **Not yet checked:** carbon prices and the exchange rate in `data/manual/assumptions.csv` | Data | Value (20), Q&A | Check on pitch day and note the date in the file |

---

## 1. Which documents apply to us

| Document | Applies? | Note |
|---|---|---|
| Participant Guide | Yes | Sections 01 (AI track), 05 (problem), 07 (worksheet), 08 (solution format), 11 (dependable demo), 12 (pitch and evidence pack) |
| Missions | Yes, the Battle of Intelligence half only | **Pillar 5: Green Fraud, Greenwashing & Disclosure Verification.** The Battle of Byte pillars are another track |
| Batch-wise Challenges | Yes, our three cards only | **C04, C07, C12** of Battle of Intelligence |
| Judge Pack (Intelligence) | Yes. **This is what we are scored on** | 100 marks, five criteria (section 4 below) |
| `Battle_of_Intelligence_7_Minute_Pitch_Template.pptx` | **Yes. This is our official template** | 7 slides plus Q&A, each tied to a rubric line: problem 15, solution 30 (slides 3 and 4), challenges 20, value 20, feasibility 15. Deck v2 is built on it |
| `Battle_of_Stocks_7_Minute_Pitch_Template.pptx` | **No** | It is the **Battle of Stocks** template: portfolio value, trades, "20 transactions a day". None of that content applies. We kept its 7-minute timing strip and table layout, and our deck is correctly titled "Battle of Intelligence". Do not add a portfolio or compliance slide because the template has one |

---

## 2. Participant Guide checklist

### 2.1 The core task and the AI fit check (section 01)

- [x] **A real difficulty where finance and environment meet:** a bank prices loans and green labels on a coal company's own emissions and tree claims, with no independent check.
- [x] **AI fit check:** the guide asks us to name the input, the output, the person who acts on it, and why learning from data helps.
  - **Input:** Sentinel-5P NO2, ERA5 wind, Sentinel-2 images, the company's report.
  - **Output:** a yearly range for plant output and CO2, a verdict on each claim (Consistent, Inconsistent or Cannot verify), and trees seen alive per plot.
  - **Who acts:** the bank's environmental or credit risk officer refers the company for review, or not.
  - **Why learn from data:** the link between "NO2 seen from space" and "electricity generated" depends on wind, season and the plant. No fixed formula gives it, so the model learns it from 27 months of metered grid sales.
- [x] **The "Understanding environmental claims" questions:**
  - *Who must judge a claim?* The bank's risk officer, before lending or before accepting a "green" label.
  - *What makes a claim verifiable rather than persuasive?* An independent measurement the company does not control (satellite), checked against an official record (CPPA-G purchases), with a stated error range and a refusal when the evidence is too thin.

### 2.2 Problem statement (section 05 template)

- [~] Not yet written in the guide's exact template. Use this wording:

> **A bank's environmental risk officer** struggles to **check a coal power company's emissions and tree-offset claims** in **green and transition lending** because **the only evidence is the company's own report**. This leads to **loans and green labels priced on unchecked numbers, and carbon-cost exposure the bank cannot see** and affects **real emission cuts and real tree cover, which nobody verifies**. We will investigate whether **a model that turns satellite NO2 and wind into a yearly output estimate, plus satellite tree checks,** improves **how often an understated claim is caught (yearly error against metered sales, catch rate, false alarms)**.

### 2.3 Team worksheet (section 07)

| Prompt | Our answer |
|---|---|
| Registered battle and focus area | Battle of Intelligence. Pillar 5, Greenwashing & Disclosure Verification. Focus area: understanding environmental claims |
| User and difficult task | A bank's environmental or credit risk officer, who has to decide whether to refer a coal company's green claims for review before renewing a loan |
| Finance and environment connection | **Finance:** loan pricing, green labels, and carbon-cost exposure for Sahiwal of USD 20M–519M a year under two carbon-price scenarios. **Environment:** emissions and offsets that are actually real. **The link:** if claims are checked, money follows real cuts |
| Evidence and assumptions | **Verified:** satellite data (public), CPPA-G metered purchases (public; they match NEPRA's annual totals), out-of-sample test results. **Assumed or synthetic:** the company's report figures (no public figure found, so they are built from real metered numbers and labelled), farmer names, carbon prices, our fee |
| Smallest useful demonstration | One plant (Sahiwal) and one decision: refer or not. We judge success by yearly error against the official record, the catch rate for understated claims, and false alarms |

### 2.4 Solution format (section 08)

- [x] **A working MVP:** a Streamlit app, hosted on Streamlit Community Cloud and also runnable locally.
- [x] One complete user journey: pick the company, see the verdict, see why, open the evidence.
- [x] Simulated parts named on screen: "Synthetic inputs, labelled: claims", "Farmer (invented)".
- [x] It is more than a title or a slide: the guard cases run live and the model test uses held-out months.

### 2.5 Credible data (section 09)

- [x] Every dataset has a source, download date, licence and the changes we made: see `evidence_pack.md`.
- [x] Checked that the data really exists: CPPA-G totals match NEPRA's published FY2024-25 figures.
- [~] We did not use the guide's example datasets (NASA POWER, World Bank and others). That's fine: the guide says to pick data because it fits the problem. If asked: we don't use NASA POWER data. The guard's limits cover its kind of fields (solar irradiance up to 1,361 W/m², its −999 missing-data markers), so the same guard would work if a bank fed that data in.

### 2.6 A dependable demo (section 11)

- [x] Hosted link: https://carbonemissiondetectionusingstatelliteimaginary-lvdbcjesxlusrz.streamlit.app
- [x] Local copy runs: `streamlit run app/streamlit_app.py`
- [x] Recorded walkthrough: `Demo_Backup.mp4` (2 min 26 s, captioned). **If we use it, say so:** "This is a recording of the same app running locally on our committed data."
- [ ] Screenshots of key results as a third backup. Deck slides 5–7 partly cover this.
- [x] No credentials in the public repo. Checked: no keys or tokens are tracked. The Earth Engine login lives on the laptop, not in the repo.
- [ ] Open the hosted link on the venue network before our slot (see fix 9).

### 2.7 Pitch running order (section 12) against our deck

| Guide slot | Our slides | Times on the slides | OK? |
|---|---|---|---|
| 0:00–1:00 Problem and user | 1, 2 | 0:00–1:15 | [x] |
| 1:00–2:00 Solution approach | 3, 4 | 1:15–2:30 | [x] |
| 2:00–4:30 Demonstration | 5 | 2:30–4:15 (1 min 45 s) | [~] Short. Rehearse the click path so it fits: verdict, range plot, map, Hub picker, Reliability tab |
| 4:30–5:45 Evidence | 6, 7 | 4:15–6:10 | [x] |
| 5:45–7:00 Value and limits | 8 | 6:10–7:00 | [x] |
| 7:00–10:00 Q&A | 9 | | [x] Answers are in `docs/PITCH_BRIEF.md` and `docs/DISCUSSION_LOG.md` |

### 2.8 Evidence pack (section 12)

- [x] Demo link and local artifact
- [x] Source code in the public repo
- [x] Sample inputs and outputs (`data/`, `outputs/`)
- [x] Test notes (78 automated tests)
- [x] Dataset sources, dates, licences and changes (`evidence_pack.md`)
- [x] Synthetic data labelled
- [ ] Printed or offline copy of `evidence_pack.md` and the key numbers, for quick look-ups during Q&A

---

## 3. Mission fit (Missions.docx)

**Pillar 5 guiding intent:** *"How can language models and analytical pipelines cross-verify corporate disclosures against operational evidence to eliminate greenwashing?"*

| Part of the intent | What we do | Strength |
|---|---|---|
| Cross-verify corporate disclosures | 10 checks of 7 kinds between the report table, report text, CPPA-G purchases, the satellite estimate and tree plots | Strong |
| Against operational evidence | Plant output seen from space (NO2 and wind) and tree cover seen from space | Strong, and unusual: most teams will only read documents |
| Anomaly detection | A yearly claim outside the satellite's 80% range is flagged | Good |
| NLP, document intelligence, language models | Figures are pulled from report text and tables, with page and quote. A figure not found on the cited page is rejected (`E_CLAIM_NOT_IN_SOURCE`) | **Weakest part.** The extraction is rule-based, and the report figures are synthetic because no public Huaneng figure was found |

**Prepared answer for "Where is the language model?":** "Our contribution is the *operational evidence* half of the mission: what the plant actually did, seen from space. Pulling claims out of a report is the solved half: we read figures from text and tables with their page and quote, and refuse any figure that isn't on the page. A language model could do that extraction step, but it is not where the risk is. The risk is having nothing independent to compare the claim against."

---

## 4. Judge rubric (100 marks): what earns marks and where we stand

| Criterion | Marks | What "Strong" needs | Our evidence | Risk | Our honest band |
|---|---|---|---|---|---|
| Problem, mission and AI relevance | 15 | Precise, feasible task; convincing Green FinTech need; a justified role for AI | Named user and decision; Pillar 5; the model learns NO2 → output because no formula can | Weak NLP angle (section 3) | Strong, 11–15 |
| AI solution and demonstration | 30 | Convincing end-to-end demo; sound choices; limits explained | Live app with real data from satellite to verdict; held-out tests; guard runs live | Demo only 1 min 45 s; all Sahiwal checks disagree (fix 4); hosted app may be stale (fix 9) | Strong, 21–30, if the demo runs cleanly |
| Response to all three challenges | 20 | All three covered; justified adaptations; traceable evidence; honest gaps | C04, C07 and C12 each on slide 7 with evidence; the tree gap stated openly | C12 evidence cell is wrong (fix 3) | Strong, 15–20, after fix 3 |
| Value and AI evidence | 20 | Transparent financial assumptions, credible environmental reasoning, convincing evaluation with honest limits | Out-of-sample numbers; the withdrawn 97.5% figure; evidence pack; assumptions file | "16 years" error (fix 1); wide USD range (fix 7); company figures synthetic | Competent to Strong, 12–17 |
| Feasibility, pitch and Q&A | 15 (5 each) | Realistic next steps; clear pitch; accurate answers | Pilot with one bank; costs include the Earth Engine commercial licence; 35 answered questions in the discussion log | Overrun if rehearsed from the notes (fix 2) | 10–14 |

**Judge form fields** (the team fills none of these, but say them clearly at the start so the judges can):
- **Team name:** Team 13
- **Team no.:** IU3048
- **Selected mission:** Battle of Intelligence, Pillar 5, Greenwashing & Disclosure Verification
- **Problem title:** Satellite Verification of Green Claims

---

## 5. Our three challenges: requirement, response, evidence, gap

The judges score all three together out of 20, in four parts of 5 marks each:
- coverage and understanding
- appropriate changes
- evidence of results
- learning, trade-offs and gaps

### C04: Out-of-bounds and hallucination guard

- **The card asks:** inject 5 out-of-bounds edge cases; show that the pipeline returns low-confidence flags or rejections, not confident wrong predictions.
- **What we built:** every request returns exactly one status, `OK`, `LOW_CONFIDENCE` or `REJECTED`, after three gates:
  1. physical limits
  2. plausibility, such as output above what the plant can produce
  3. confidence, such as too few clear days
- **Evidence:** `outputs/guard_results.csv`, Reliability tab, `tests/test_guard.py`. All 8 cases behave as expected:

| # | Injected case | Result | Reason code |
|---|---|---|---|
| 1 | Latitude 124.5 | Rejected | `E_COORD_RANGE` |
| 2 | Wind speed −8 m/s | Rejected | `E_WEATHER_RANGE` |
| 3 | "We cut emissions by 200%" | Rejected | `E_REDUCTION_OVER_100` |
| 4 | Sahiwal reports 145% of capacity | Rejected | `E_CF_OVER_100` |
| 5 | Greenness (NDVI) 1.8, maximum possible is 1 | Rejected | `E_NDVI_RANGE` |
| 6 | August with only 2 clear passes | Low confidence | `W_FEW_OBS` |
| 7 | Extracted figure not on the cited page | Rejected | `E_CLAIM_NOT_IN_SOURCE` |
| 8 | Control: tiny negative NO2 (normal noise) | OK, accepted | none |

- **Adaptation:** case 8 shows the guard is not over-strict. Small negative NO2 readings are normal sensor noise, so we let them through rather than throw away good data.
- **Gap or trade-off:** the limits are set by hand in `verify/rules.py`, not learned. A value that is wrong but still physically possible, like a plausible but false figure, passes the guard. C12 is what catches those.

### C07: Beat a heuristic baseline by at least 15% (F1 or RMSE)

- **The card asks:** benchmark against a simple rule, moving average or linear baseline, and show at least a 15% gain.
- **Emissions model (RMSE on 9 months the model never saw):**

| Method | Typical monthly miss | Our gain |
|---|---|---|
| Rule of thumb: capacity × 22.9% fleet utilisation | 442 GWh | **61.7% less error** |
| Raw NO2, no wind correction | 244 GWh | **30.4% less error** |
| Our wind-corrected plume model | 169.5 GWh | |

  - **Passes, twice over.** The 3-month moving average is shown for reference only: it uses the company's own figures, the very numbers we are checking.
- **Tree classifier (F1, on 575 held-out points):**

| Method | F1 |
|---|---|
| Random forest | 0.891 |
| Best tuned greenness threshold | 0.798 (**11.6% gain, short of 15%**) |
| Standard fixed threshold | 0.781 (14.1% gain) |

  - **Honest gap,** said on the slide.
- **Adaptation:** single months were too noisy (about 23% error), so verdicts moved to the fiscal year:
  - about 7% average error across 16 overlapping 12-month windows
  - 15% in the strictest forward test
  - FY2026: 5,896 vs 6,138 GWh, 3.9% low
- **Learning:** we withdrew an early 97.5% figure. The model had already seen those months.

### C12: Multimodal consistency cross-check

- **The card asks:** take in paired data from several sources; show the system detects contradictions between declared figures and secondary sources, such as satellite reference points.
- **What we built:** 10 checks of 7 kinds, each in plain words in the app's "Each claim, checked" panel:
  - report table vs metered grid sales
  - report table vs the satellite
  - report text vs the meter and the satellite
  - declared CO2 vs meter × emission factor
  - declared CO2 vs satellite-based CO2
  - trees claimed vs trees seen alive
  - "we cut emissions" vs what happened
  - report table vs report text
- **Evidence** (`outputs/cross_checks.csv`):
  - **Sahiwal:** 10 of 10 disagree.
  - **Hub:** 4 agree, 5 disagree, 1 cannot compare. **This shows the check can say "consistent" too.**
  - **External model vs the official record:** Climate TRACE puts the Hub coal plant at about 3,816 GWh for 2025; CPPA-G shows about 702 GWh, roughly 5x lower.
- **Gap:** the company figures are synthetic, built from real metered numbers, because no public plant-level report figure was found. The checks and the satellite side are real.

---

## 6. Pitch template (layout) checklist

- [x] Seven pitch slides plus a Q&A slide; the on-slide timings add up to exactly 7:00
- [x] Slide 1 has team number, members and roles, the goal in one sentence and the result in one sentence
- [x] A challenges slide with "response" and "evidence and gaps" columns, plus a "most important adaptation" line (slide 7)
- [x] A closing message (slide 8)
- [~] Speaker notes timings disagree with the slides (fix 2)
- [x] No passwords or credentials on the slides

---

## 7. Rehearsal checklist (pitch day)

- [ ] Fixes 1–7 made in the deck, then PDF exported (fix 8)
- [ ] Hosted app checked on the venue Wi-Fi (C07 tab shows F1 0.89)
- [ ] App opened once before the slot, so the satellite map tiles are cached
- [ ] Full timed run at 6:45 or less, with a 15-second buffer. The judges warn at 6:00
- [ ] Demo click path practised: verdict, range plot, map (plume, then contracts), Hub picker, Reliability tab
- [ ] One person owns the clicker, one owns the demo, one takes Q&A, so hand-overs don't eat time
- [ ] `Demo_Backup.mp4` on the laptop desktop and a USB drive. If it is used, say it is a recording
- [ ] Carbon prices and the USD/PKR rate checked and dated in `assumptions.csv`
- [ ] Every team member can explain:
  - NO2 vs CO2
  - what CPPA-G is: the official record of what the government bought from each plant, **not** a factory's electricity bill
  - why 97.5% was withdrawn
  - why the tree result is short of 15%
