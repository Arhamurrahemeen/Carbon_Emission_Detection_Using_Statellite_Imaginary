# Glossary: every term in plain words

Grouped by topic. Each entry says what the word means and, where it helps, how it shows up in our project.

---

## 1. Energy and emissions units

**kWh (kilowatt-hour):** the unit on a home electricity bill. Running a 1,000-watt heater for one hour uses 1 kWh.

**MWh (megawatt-hour):** 1,000 kWh.

**GWh (gigawatt-hour):** 1,000 MWh, or 1 million kWh. We measure plant output in GWh per month. Sahiwal makes about 500–750 GWh in a normal month, roughly what 300,000–500,000 Pakistani homes use in a month.

**TWh (terawatt-hour):** 1,000 GWh. Used for yearly totals of big plants.

**MW (megawatt):** power, the *speed* of making electricity, not the total. Sahiwal is a 1,320 MW plant: running flat out for one hour, it makes 1,320 MWh.

**Capacity:** the most a plant can produce, in MW.

**Capacity factor / utilisation:** how much a plant actually made compared with the most it could have made. 100% means it ran flat out all month; 0% means it was off. Pakistan's imported-coal plants averaged 22.9% in FY2024-25.

**CO2 (carbon dioxide):** the main gas causing climate change. Burning coal releases it.

**CO2e (CO2 equivalent):** all greenhouse gases converted into "the same warming as this much CO2". Climate TRACE reports in CO2e.

**t, Mt (tonne, megatonne):** 1 tonne = 1,000 kg. 1 Mt = 1 million tonnes. Sahiwal emits roughly 4–6 Mt of CO2 a year.

**Emission factor:** tonnes of CO2 released per MWh of electricity. For our coal plants it's about 0.80–0.95 t per MWh. We multiply generation by this to *estimate* CO2.

**Fiscal year (FY):** Pakistan's financial year, July to June. FY2026 = July 2025 to June 2026.

---

## 2. Accuracy and testing (the words people get confused by)

**Error:** how far the model's guess is from the true answer. If the plant made 600 GWh and the model said 480, the error is 120 GWh, or 20%.

**Accuracy (as we use it):** 100% minus the percentage error. A 23% average error means about 77% accurate. Statisticians often avoid this word for numbers like ours, but it's the clearest way to say it to a jury.

**Our numbers:**

| What | Error | Accuracy |
|---|---|---|
| One month | ~23% | ~77% |
| One year, average | ~7% | ~93% |
| One year, strictest test | ~15% | ~85% |

**Baseline:** a simple method you compare your model against. If your fancy model can't beat a simple rule, it isn't worth using. C07 makes us prove we beat one by at least 15%.

**Our two baselines:**
- **Rule of thumb:** "a coal plant runs at about 23% of its capacity." This is what a bank could assume today with no satellite at all. It misses by about 442 GWh a month.
- **Raw satellite reading:** using the NO2 over the plant directly, without correcting for wind or background pollution. It misses by about 244 GWh a month.
- **Our model** misses by about 170 GWh a month.

**"62% better" / "62% less error":** our miss (170) is 62% smaller than the rule of thumb's miss (442). It's *not* an accuracy score; it's a comparison. Same for "30% better" against raw readings (170 vs 244).

**Training data:** the examples the model learns from: here, months where we know both the satellite reading and the true generation.

**Test data / held-out / unseen months:** months hidden from the model during learning, used only to grade it. Grading on months it learned from is like giving students the exam answers in advance.

**Data leakage:** accidentally letting the model see the test answers. Our first "97.5%" figure had this problem, and we withdrew it.

**Leave-one-out:** hide one month, train on all the others, predict the hidden month; repeat for every month. Every month gets a fair guess from a model that never saw it. A small weakness: later months help predict earlier ones.

**Forward test (strictest):** train only on the past and predict the next month, the way the system would be used in real life. Our 15% yearly error comes from this test.

**RMSE (root mean squared error):** an average error that punishes big misses more than small ones. Our 170 / 442 / 244 GWh figures are RMSE.

**MAE (mean absolute error):** the plain average miss, ignoring direction. Ours is about 131 GWh per month.

**Correlation (r):** how closely two things rise and fall together, from 0 (no link) to 1 (perfect). The satellite plume and real generation have r = 0.62 across 27 months: a clear but imperfect link.

**80% range / interval:** instead of one number, the model gives a range it expects the true value to fall in 8 times out of 10. Example: FY2026 is 4,967–6,833 GWh.

**Confidence / LOW_CONFIDENCE:** a flag meaning "the evidence is too weak to judge". Single months often get it because the range is too wide.

**Abstain:** refuse to give a verdict. The system does this rather than guess.

**Detection rate:** of the false claims we tested, the share the system caught. 94–100% for yearly claims understated by 20% or more.

**False alarm:** flagging an honest claim as suspicious. We had 0% in our tests.

**Synthetic data:** made-up data in a realistic shape, used for testing when real data doesn't exist. Always labelled in our app. Our company claims are synthetic because no public report figure was found.

**Autocorrelation:** when one month's error tends to resemble the next month's. If errors cluster, a year is less certain than it looks, so we widen the yearly range to account for it.

**Quadrature (adding errors):** when independent errors are combined, they partly cancel out. Twelve monthly misses of ±250 GWh don't add up to ±3,000 for the year; they add to about ±870 (250 × √12). This is why a year is far more accurate than a month.

---

## 3. The models

**Model:** a formula learned from data that turns inputs (satellite readings) into an output (estimated generation).

**Ridge regression:** a simple straight-line model with a safety brake that stops it over-reacting to small datasets. Our emissions model. We chose simple on purpose: 27 months is too little data for anything fancy.

**Random forest:** many small decision trees voting together. Our tree classifier uses it to tell trees from crops across a year of images.

**Threshold:** a single cut-off rule, for example "greenness above 0.35 means trees". The simple baseline for the tree classifier.

**F1 score:** a 0-to-1 score for yes/no classifiers that balances catching every tree against not mistaking crops for trees. Used for the tree C07 test.

**Conformal interval:** a way of building the 80% range from the model's own past mistakes, so the range is honest about how wrong it tends to be.

**Feature:** one input the model uses, for example plume strength or wind speed.

---

## 4. Satellites and the measurement method

**Sentinel-5P / TROPOMI:** a European satellite (Sentinel-5P) carrying an instrument (TROPOMI) that measures gases in the air, including NO2. It passes over Pakistan once a day around 1:30 pm.

**NO2 (nitrogen dioxide):** a gas released when coal is burned. The satellite can see it; it can't see CO2. More coal burned means more NO2, so NO2 tells us how hard the plant ran.

**Overpass:** one pass of the satellite over the plant. Sahiwal has about 2,700 usable overpasses since 2018.

**Plume:** the cloud of pollution blowing away from the chimney.

**Upwind / downwind:** upwind is where the air comes from (clean background); downwind is where the plume goes. We subtract upwind NO2 from downwind NO2 to isolate the plant's own pollution from city smog and crop burning.

**Enhancement:** that difference, downwind minus upwind. The plant's own signal.

**Wind correction / flux proxy:** strong wind spreads the plume thin, so the same plant looks weaker on a windy day. Multiplying the enhancement by wind speed corrects for this. That's our main input.

**ERA5:** a global weather dataset (from Europe's weather centre, ECMWF) giving wind for every hour. We take the wind at the satellite's pass time.

**Sentinel-2:** a different European satellite taking sharp colour and infrared photos every few days. Used for the tree plots.

**NDVI (greenness score):** a number from −1 to 1 computed from red and infrared light. Healthy plants score high (0.4+), bare soil low (around 0.1). Anything above 1 is impossible, which is one of our C04 tests.

**Cloud Score+:** a Google dataset marking which pixels in a Sentinel-2 photo are cloudy, so we don't judge trees through clouds.

**ESA WorldCover:** a global map of land cover (trees, crops, water...) used as the answer key for training the tree classifier.

**Google Earth Engine:** Google's free (for non-commercial use) platform holding these satellite archives, where we run the calculations.

**Resolution / footprint:** how big an area one satellite measurement covers. Sentinel-5P sees patches several km wide, so we never claim "1 km resolution".

---

## 5. Organisations and regulation

**NEPRA:** National Electric Power Regulatory Authority, Pakistan's electricity regulator. Publishes yearly plant performance reports.

**CPPA-G:** Central Power Purchasing Agency, the government buyer of electricity from power plants. Publishes monthly metered energy bought from each plant. These are our "true answers" for training.

**Metered generation:** electricity measured by the meter and paid for. The most trustworthy number we have.

**SECP:** Securities and Exchange Commission of Pakistan. Ordered listed companies to publish climate disclosures (IFRS S1/S2), phased in from 2026–27.

**IFRS S1 / S2:** international standards for how companies report sustainability and climate information.

**SBP:** State Bank of Pakistan. Requires banks to manage climate risk, with full compliance by June 2029.

**Green Taxonomy:** SBP's list of what counts as a "green" activity for banks.

**PSX:** Pakistan Stock Exchange. Hub Power (HUBC) is listed there.

**Climate TRACE:** a global group that *estimates* emissions from satellites and models. Useful, but an estimate, not a measurement. For the Hub coal plant it overestimated 2025 output by about 5×.

**Copernicus:** the EU's Earth observation programme that runs the Sentinel satellites. Its data is free and open.

**CC-BY 4.0:** a licence meaning "free to use, just give credit".

---

## 6. Finance and green claims

**Green FinTech:** technology for financial activities tied to environmental goals.

**ESG:** Environmental, Social and Governance, the non-financial factors investors check.

**Disclosure:** what a company publicly reports about itself, for example its emissions.

**Greenwashing:** making a company look greener than it is.

**Carbon offset:** paying for something (like planting trees) that removes CO2, to balance out emissions.

**Permanence:** whether the offset lasts. Trees can be cut down, so we pay only while they're alive.

**Additionality:** whether the offset would have happened anyway. Planting on land that was already forest adds nothing.

**Carbon price:** the cost of emitting one tonne of CO2 in a carbon market. Our USD 5 and USD 80 per tonne are scenario values, labelled as such.

**Exposure:** how much money is at risk, for example the carbon cost a company might face.

**EU CBAM:** the EU's border tax on the carbon content of imports. Linked to the EU carbon price.

**Escrow / held payment:** money set aside and released only when a condition is met. Here: when the satellite confirms the trees are alive.

---

## 7. Our system's own words

**C04, C07, C12:** the three challenges the organisers gave us. C04 = refuse impossible inputs. C07 = beat a simple baseline by 15%. C12 = catch contradictions between numbers, text and satellite evidence.

**Status: OK / LOW_CONFIDENCE / REJECTED:** every answer carries one. OK = trust it; LOW_CONFIDENCE = evidence too thin, no verdict; REJECTED = impossible input, no estimate at all.

**Verdict: CONSISTENT / INCONSISTENT / CANNOT_VERIFY:** CONSISTENT = the claim fits the evidence; INCONSISTENT = it doesn't, so refer for review (not proof of lying); CANNOT_VERIFY = not enough evidence.

**Reason code:** a short tag explaining a status, for example `E_COORD_RANGE` (impossible location) or `W_FEW_OBS` (too few clear satellite passes). E_ means rejected; W_ means low confidence.

**Cross-check (X1–X7):** one comparison between two sources, for example the company's table vs the meter (X1).

**Pipeline:** the chain of steps from raw data to verdict.

**Streamlit:** the Python tool we use to build the web app.
