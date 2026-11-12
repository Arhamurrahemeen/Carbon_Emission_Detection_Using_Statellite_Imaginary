# Pitch Brief: Satellite Verification of Green Claims

New words are explained in [GLOSSARY.md](GLOSSARY.md).

BattleVerse 2026 · Battle of Intelligence · Pillar 5 (Greenwashing & Disclosure Verification) · Challenges C04, C07, C12 · Team 13 (IU3048)
Updated 12 Nov 2026 for deck v2. Items marked **(verify)** need checking before they go on a slide. Scoring and the pre-pitch fix list: [JUDGING_CHECKLIST.md](JUDGING_CHECKLIST.md).

---

## Accuracy in one breath

- **About 77% accurate for one month.** Too uncertain to judge a single month, so the system refuses to.
- **About 93% accurate for a year**: the average over 16 overlapping 12-month windows (85% in the strictest forward test). We have 27 months of official records, not 16 years.
- **62% less error than the rule of thumb** banks use today, and 30% less than raw satellite readings. C07 asks for 15%.
- All tested on months the model had never seen.

## 1. The project in one line

**A factory measures its emissions from space, pays farmers only for trees the satellite sees alive, and publishes green claims that buyers and banks can check.**

> **Decided 12 Nov (latest): factory first.** The factory is the user. It uses the system to measure its own emissions, to check and pay the farmers who grow its offset trees, and to check its report before publishing. Banks and buyers are a **side feature**: they can read or re-run the check. The merged deck is `Team13_Merged_Pitch_v4.pptx`, combining Green Claims Check and Shajar Ledger. The earlier bank-first framing is history; see `DISCUSSION_LOG.md` question 37.

## 2. The project in simple words

A factory makes two green claims:

1. **"This is how much we pollute."**
2. **"We planted trees to make up for part of it."**

Buyers in Europe, the EU carbon border charge (CBAM, from 2026) and lenders increasingly ask for both. Today the emission figure is estimated by hand, and offset trees die or get counted twice, so the factory pays for offsets it cannot prove.

The factory's journey with our system:

1. **Measure emissions.** A satellite measures the NO2 gas rising from the plant. Our model, trained on official generation records (CPPA-G, matching NEPRA), estimates how hard the plant really ran. That gives a CO2 range, which sizes how many trees the factory needs.
2. **Pay farmers only for living trees (Shajar Ledger).** The factory pays the farmer upfront to plant. Then every quarter a satellite photo of each plot shows whether the trees are alive; the factory pays only while they are.
3. **Check the report before publishing.** Each claim gets **Consistent**, **Inconsistent** (fix or explain it) or **Can't verify**.
4. **Side feature:** share the checked report with the bank or buyers, who can re-run the same check from public data.

When the data is impossible or too weak (a cloudy photo, a location that doesn't exist, a 200% reduction), the system refuses to answer instead of guessing. That is our C04 challenge.

## 3. Who is the user, who participates, who pays

**Rule:** the user is the person who opens the screen and makes a decision with what it shows.

| Role | Who | What they do | What they get |
|---|---|---|---|
| **User and payer** | **The factory's sustainability or finance manager** (coal power plant, textile mill, cement or steel plant) | Measures emissions, accepts farmers' offers, releases or holds tree payments, checks the report before publishing | No money for dead trees; an emission figure and offset claim that hold up when buyers, CBAM or lenders ask |
| Participant | Farmer | Offers land, plants and keeps the factory's trees | Planting money upfront, then quarterly payments while the trees are seen alive; the reason on their phone, in Urdu, when a payment is held |
| Side feature | The factory's bank or buyers | Read the checked report, or re-run the check | Evidence for green-loan terms, SBP climate-risk work or CBAM reporting |
| Data sources | Sentinel satellites, ERA5, CPPA-G and NEPRA (official generation), ESA WorldCover, Climate TRACE (comparison only) | Supply evidence | None |

**"Isn't the factory checking itself?"** It would be, if the factory produced the numbers. It doesn't: the satellite figure comes from public data the factory cannot edit, so a buyer or bank can re-run the same check and get the same answer. That is what makes the claim checkable rather than self-certified.

**How we earn (demo assumption, label it on the slide):** a yearly subscription per factory. Demo numbers, not tested with factories.

**Honest weakness:** Pakistan has no legal cap on factory CO2 today (NEQS limits SO2, NOx and dust). Demand comes from export buyers, CBAM and lenders, not from a local law. Say this ourselves.

## 4. Why now

| Rule | What it says | Status |
|---|---|---|
| EU CBAM | Carbon charge on imports of steel, cement, aluminium, fertiliser and more; definitive period from 1 Jan 2026. Exporters must report embedded emissions | Main driver for exporting factories |
| Pakistan carbon-market guidelines | Policy Guidelines for Trading in Carbon Markets, cabinet-approved Dec 2024 | Offsets need credible evidence |
| NEQS (Pakistan EPA) | Limit SO2, NOx and dust; **no CO2 cap** | Say this ourselves: demand is from buyers and lenders, not a local CO2 law |
| SECP order, 31 Dec 2024 | Listed companies must publish IFRS S1/S2 climate disclosures, in phases. SECP's press release says the first two phases start July 2026 and July 2027; the last phase covers periods from 1 Jul 2027 | **(verify)** phase dates against the order |
| SBP climate-risk framework | Banks submitted board-approved implementation plans by 30 Sep 2026; full compliance by 30 Jun 2029 | Confirmed in news coverage |
| SBP Green Taxonomy | Issued Dec 2025. Banks must reference it in green banking policies | No 2029 deadline; don't mix it up with the framework |

Export buyers and CBAM want emission figures now, listed companies are starting to disclose, and banks (our side feature) must manage climate risk. A factory needs numbers that hold up when any of them checks.

## 5. Where the data comes from

| What | Source | How | Notes |
|---|---|---|---|
| NO2 over the plant | Sentinel-5P TROPOMI, Earth Engine `COPERNICUS/S5P/OFFL/L3_NO2` | Earth Engine script → CSV | Free, open Copernicus licence. Data from mid-2018 |
| Wind at overpass time (~13:30 local) | ERA5-Land hourly, Earth Engine `ECMWF/ERA5_LAND/HOURLY` (10 m u/v) | Earth Engine → CSV | Tells us which way the plume blew |
| How much the plant really ran (training answers) | CPPA-G *Energy Procurement Report* spreadsheets (cppa.gov.pk), Jul 2024 – Sep 2026, checked against NEPRA's annual *Performance Evaluation Report, Generation* FY2024-25 | Machine-extracted (`verify/labels.py`). FY2024-25 totals match NEPRA exactly | Done: 27 real months |
| The company's own claim | Company annual / integrated reports (Hub Power, Sahiwal's owner) | Entered by hand with page number and quote | Not found yet; Hub's CO2 figure may not be disclosed at plant level |
| Tree health | Sentinel-2 surface reflectance + Cloud Score+, ESA WorldCover | Earth Engine (reused from the Shajar demo) | Already working |
| Benchmark line on the chart | Climate TRACE API v6 | One call → CSV | Display only, never a model input. CC-BY 4.0 |
| Plant locations, capacity | Global Energy Monitor wiki, NEPRA | Copied by hand | Easy |
| CO2 per MWh | IPCC 2006 default coal factors + plant heat rate from NEPRA tariff documents | Fixed values in config | **(verify)** heat rate per plant |
| Tree CO2 uptake | IPCC 2019 Refinement, Vol 4 Ch 4 (6.03 t CO2 per acre per year) | Fixed value | A default, not measured on the plot |

Everything is downloaded once and saved to files. **The demo never needs the internet.**

NEPRA FY2024-25, coal plants (from the annual report; check the table once before using on a slide):

| Plant | Capacity | Net generation | Utilisation |
|---|---|---|---|
| Huaneng Shandong Ruyi (**Sahiwal**) | 1,320 MW | 4,255,189 MWh | 39.1% |
| China Power Hub (**CPHGC**) | 1,320 MW | 671,654 MWh | 6.1% |
| Port Qasim | 1,320 MW | 2,751,197 MWh | 25.3% |

Sahiwal is the main site. Hub barely ran in FY25, so it serves as the "plant mostly off" test.

## 6. How we read NO2 from the satellite and turn it into CO2

**Short version for the pitch:** *The satellite can't see CO2. It sees NO2, which burning coal produces. We use NO2 to work out how hard the plant ran, then turn that into CO2 with standard factors, shown as a range.*

### Step by step

1. **The satellite measures NO2.** Sentinel-5P passes over Pakistan once a day around 13:30. NO2 absorbs specific colours of sunlight, so the instrument measures how much NO2 sits in the air column above each patch of ground. Each pixel is a few km wide. (Earth Engine's grid is ~1.1 km, but the real footprint is larger, so never claim "1 km resolution".)
2. **Remove bad days.** Earth Engine already drops low-quality pixels. Cloudy days have no reading. Days with almost no wind are dropped because the plume has no direction.
3. **Separate the plant from the background.** Using that day's wind, we take NO2 in a box **downwind** of the plant and subtract NO2 in a box **upwind**. The difference is the plant's own plume. This removes city pollution and seasonal crop burning (Sahiwal, Oct–Nov).
4. **Average by month.** Monthly mean plume strength, plus a count of how many good days we had.
5. **Estimate how hard the plant ran.** A simple model (ridge regression) learns the link between plume strength and the plant's real monthly generation from NEPRA. Inputs: plume strength, number of good days, wind speed, month. Output: **generation in GWh with an 80% range**. We test it on months the model never saw.
6. **Turn generation into CO2.**
   CO2 (tonnes) = generation (MWh) × emission factor (t CO2 per MWh)
   The emission factor comes from IPCC default coal factors and the plant's heat rate. For large imported-coal plants it is roughly 0.8–0.95 t CO2/MWh **(verify per plant)**. Overall uncertainty is about ±30%, so CO2 is always shown as a range and labelled "estimated".
7. **Compare with the claim.** Claim inside the range → **Consistent**. Outside → **Inconsistent**, with how far and in which direction. Too few good days, or inputs outside what the model has seen → **Can't verify**.

### Why we don't convert NO2 straight to CO2

The NO2-to-CO2 ratio changes with coal type, burner settings and pollution controls. Published studies show ~23% spread in the ratio and ~33% in CO2 estimates even at well-studied plants, and simple physics conversions run 40–50% low. Training on NEPRA's metered generation for each plant absorbs those errors. This is our strongest methodological defence.

### Trees, in one paragraph

Sentinel-2 photographs each plot every few days. We compute a greenness score (NDVI) from red and near-infrared light. Living trees score high, and bare soil scores low. Each quarter, a plot with greenness of at least 0.35 and less than 30% cloud passes, and the payment is released. Below 0.35, the payment is held. Too cloudy: wait for the next clear photo. CO2 absorbed is estimated from the number of trees and the IPCC default, not measured.

## 7. Pitch script (7 minutes, matches the merged deck v4)

**Deck:** `Team13_Merged_Pitch_v4.pptx`, with a PDF beside it, in the hackathon folder. It is built on the official Battle of Intelligence template and **merges Green Claims Check (this repo) with Shajar Ledger (Baneen's app), factory first**. It has 8 pitch slides, including Shajar's "From satellite photo to payment" as 3b, then a Q&A slide and one backup slide ("Built on proven ideas"). Earlier decks (v2 bank-first, v3 merged bank-first, the 9-slide original, Shajar v5) are reference only; do not present them.

**Before the slot:**
- Open the hosted app once, so map imagery is cached, and check that the Model test tab shows tree F1 0.89.
- Start Shajar Ledger locally: `node server/server.js` in the Shajar repo, then open http://localhost:8765.
- Keep `Demo_90s.mp4` ready (Green Claims Check part). If it is used, say: "This is a recording of the same app running locally."

| Time | Slide (marks) | What we say and do |
|---|---|---|
| 0:00–0:20 | 1. Title | "Team 13, IU3048. Battle of Intelligence, Pillar 5. A factory measures its emissions from space, pays farmers only for trees the satellite sees alive, and publishes green claims that buyers and banks can check." |
| 0:20–1:00 | 2. Problem and role of AI (15) | "Our user is the factory's sustainability manager. Buyers, the EU carbon border charge from 2026 and lenders now ask for its emissions and offsets. Today the emission figure is estimated by hand, and offset trees die or are counted twice, so the factory pays for offsets it can't prove. Why AI: the NO2 a satellite sees depends on wind, season and plant, so no formula turns it into plant output. A model learns that link from 27 months of official records." |
| 1:00–1:50 | 3. AI solution and workflow (30, with slide 4) | Read the output column as the factory's journey: 1 emissions as a range, which sizes the tree offset; 2 Shajar Ledger pays farmers only while trees are seen alive; 3 the report is checked before publishing. Then the quality row: guards, trained on 18 months and tested on 9 unseen, "fix or explain", never an accusation. |
| 1:50–2:10 | 3b. From satellite photo to payment (Baneen) | Hakim's plot: green in February, paid PKR 800,000; brown from May, held back. "0.35 or more means alive." |
| 2:10–3:40 | 4. Demonstration (30, with slide 3) | **Shajar Ledger (about 35 s):** factory dashboard, accept a farmer's offer (planting paid upfront), Hakim's plot held back, his phone in Urdu. **Green Claims Check (about 55 s):** Sahiwal emissions estimate and range plot ("the draft report's 4,603 sits outside the satellite range: flagged before publishing"), plume map, **switch to Hub** ("4 checks agree: it doesn't flag everything"), Reliability tab ("we cut emissions by 200%" is rejected, no number shown). Say: "Report figures are synthetic, built from real official numbers." |
| 3:40–5:10 | 5. Three challenges (20) | About 25 seconds each. **C04:** both apps, 13 cases, all as expected. Gap: limits are hand-set. **C07:** 62% and 30% less error than the rule of thumb and raw NO2. Gap: the tree model is only 11.6% better, so the simple rule still decides payments. **C12:** farmer claims vs satellite, and the factory's report: Sahiwal 10 of 10 disagree, Hub 4 agree. **Learning:** fiscal years, not months; AI earns a say in payments only once it beats the simple rule by 15%. |
| 5:10–6:20 | 6. Value and AI evidence (20) | "For the factory: PKR 2.4 million held from one plot while its trees were missing. Carbon-cost exposure for Sahiwal: USD 20 to 519 million a year; the width is two carbon prices, not the satellite." "Paying farmers to keep trees halved tree loss in a Uganda trial." Then the measured results: FY2026 3.9% from the official record, about 7% across 16 overlapping 12-month windows. "We withdrew an early 97.5% because the model had seen those months." |
| 6:20–7:00 | 7. Feasibility and closing (15) | Works today: two apps, real satellite data, 78 + 26 tests. Deploy: paid Earth Engine licence, mobile-wallet payouts. Next: a pilot with one factory and 5 farmers for 2 quarters, sharing the checked report with its bank as a side feature. Close: "A factory pays only for trees that live, and publishes green numbers a satellite backs up." |
| 7:00–10:00 | 8. Q&A | Answers in section 8 below, `DISCUSSION_LOG.md` and `JUDGING_CHECKLIST.md`. Backup slide: "Built on proven ideas" |

**Who speaks** (fill in before rehearsal; one hand-over per slide at most): slides 1–3 ______ · 3b and the Shajar part of the demo: Baneen · Green Claims Check demo ______ · slides 5–7 ______ · Q&A: everyone, with technical questions to Arham.

**Words we never use:** fraud, breach, proves, zero carbon, net zero.

## 8. Likely jury questions and answers

**Business** (factory first, decided 12 Nov)

1. **Why would a factory pay for this?** Three reasons: it stops paying for dead trees (in the demo, PKR 2.4M held from one plot over 3 quarters); export buyers and the EU carbon border charge (from 2026) ask for emission figures; and a claim backed by satellites holds up when anyone checks it, instead of being called greenwashing.
2. **Isn't the factory checking itself?** The factory runs the check, but it doesn't produce the numbers. They come from public satellite data it cannot edit, so a buyer or bank can re-run the same check and get the same answer. That makes the claim checkable, not self-certified.
3. **Where do banks come in?** As a side feature. The factory can share the checked report with its lender: some loans tie the interest rate to emission targets (sustainability-linked loans), and SBP's climate-risk rules make banks account for borrowers' climate risk. The bank doesn't refuse a plant for emitting a lot; it wants true numbers.
4. **Is anyone lending money for the trees?** No. The factory pays the farmers directly: planting money upfront, then quarterly payments while the trees are seen alive.
5. **Who else does this?** GHGSat and Kayrros sell satellite emission checks abroad; Pachama and Farmers for Forests verify tree cover; a Uganda trial paid farmers to keep trees. Nobody joins emissions and tree payments for Pakistani factories. Backup slide B1 has the sources.
6. **How do you make money?** A yearly subscription per factory. Demo numbers, not tested with factories.
7. **There's no CO2 law in Pakistan. Who needs this?** Correct: NEQS limits SO2, NOx and dust, not CO2. Demand comes from export buyers, CBAM and lenders. That's our "why now", and the pilot is one factory.

**Technical**

6. **Satellites can't see CO2.** Correct. We measure NO2, estimate activity trained on metered grid sales (CPPA-G, matching NEPRA), then calculate CO2 as a range labelled "estimated".
7. **Why NO2 and not SO2?** NO2 has a stronger, cleaner satellite signal at single plants. SO2 is noisier, and scrubbers at modern plants cut SO2 without changing coal burned.
8. **How accurate is it?** About 77% for a single month, so one month alone is too uncertain and the system refuses to judge it. About 93% for a whole year, averaged over 16 overlapping 12-month windows (worst window about 80%; our strictest test, learning only from the past, gave 85%). Every one of these figures was tested on months the model had never seen. An earlier 97.5% figure was withdrawn because the model had already seen those months.
9. **What if the model is wrong?** It says "can't verify" instead of guessing: too few clear days, inputs it hasn't seen, ranges too wide. C04 shows this live.
10. **What about monsoon clouds?** July–September often can't be verified. We say so on screen.
11. **What if the plant installs pollution controls?** Controls cut NO2 without cutting coal burned, so it would look like a drop in activity. We record each plant's equipment and dates, and treat a change as a break in the data.
12. **Two plants and 27 months of official records is tiny.** (The satellite record goes back to 2018, about 90 months, but only 27 months have official generation figures to learn from.) Yes, it is a proof of concept. That is why we use a simple model and test on held-out months, not a big model.
13. **Why not just use Climate TRACE?** It is a model, not a measurement. For calendar 2025 it puts CPHGC Hub at 3,816 GWh; CPPA-G's metered figure is about 702 GWh, roughly 5.4× lower. It puts the Hub Power oil plant at 3,158 GWh when the meter shows almost zero. Climate TRACE itself rates its Hub capacity-factor confidence "low". For Sahiwal it is within about 9%.
14. **Hub has two plants side by side. How do you separate them?** We don't. The satellite sees one combined plume, so we treat Hub as one site and compare it with both plants' NEPRA generation added together.
15. **What about cities or other factories nearby?** We only use isolated plants. Clusters like Port Qasim and Korangi are excluded because plumes overlap.

**Trees and greenwashing**

16. **Isn't tree offsetting greenwashing itself?** That's why we check it. We never say net zero. Emissions and trees are shown separately, and trees only count while the satellite shows them alive.
17. **How do you know it's *your* trees and not existing forest?** Each plot gets a baseline before the contract. Plots already covered in trees score low on our plot ranking, because new trees must add something.
18. **What about permanence? Trees can be cut later.** Payment is spread over years and stops the moment the trees disappear. We never sell a one-time permanent credit.
19. **Can a farmer fake it with crops?** A single photo can be fooled by a green crop, so the tree check looks at a whole year of Sentinel-2 images. On 575 real test points it scores F1 0.89 against 0.80 for one greenness threshold. That's an 11.6% gain, short of the 15% C07 asks for, and we say so: a good threshold gets most of the way, and the forest adds a modest but real edge.

**Legal and ethics**

20. **Does "Inconsistent" mean the company lied?** No. It means "ask questions", like an auditor flagging an item for review.
21. **Can you use this data commercially?** Sentinel data is free and open under the Copernicus licence. Climate TRACE is CC-BY 4.0 with credit. NEPRA reports are public.

## 8b. The three challenges (merged deck v4, slide 5)

| Challenge | Our answer | Evidence and gap |
|---|---|---|
| C04 out-of-bounds guard | Both apps refuse bad input: 8 cases in Green Claims Check (3 gates; OK, Low confidence or Rejected) and 5 in Shajar Ledger | All 13 as expected. Green Claims Check: 6 rejected (including a claim not in the source), 1 low confidence, 1 noise control accepted. Gap: limits are hand-set, so a plausible false figure passes (C12 catches it) |
| C07 beat a baseline by 15% | Our model vs two simple methods: a rule of thumb (plants run at about 23% of capacity) and raw satellite readings | Our error is 62% and 30% smaller (misses by 170 GWh a month vs 442 and 244). Gap: the tree model is only 11.6% better than a tuned threshold |
| C12 multimodal cross-check | Farmer plot claims vs Sentinel-2, WorldCover and the per-acre limit (Shajar Ledger); the factory's report: 10 checks of 7 kinds, table and text vs the official record, the satellite and the tree plots | Sahiwal: 10 of 10 disagree. Hub: 4 agree, 5 disagree, 1 cannot compare, so it doesn't flag everything. Climate TRACE about 5x off at Hub. Gap: company figures synthetic |

The yearly catch rate (94–100% of claims understated by 20% or more, no false alarms) is model evidence and belongs on slide 6, not here.

Full write-up: `docs/CHALLENGES.md`.

## 9. Limits we state ourselves

- The satellite measures NO2, not CO2. CO2 is estimated and shown as a range.
- Inconsistent means fix or explain before publishing, not proof of a false statement.
- Karachi industrial clusters (Korangi, Port Qasim) can't be separated by NO2; the emissions check needs an isolated plant. Shajar Ledger's factory figures come from Climate TRACE, a model, used for comparison only.
- Large isolated plants only. Not cement process emissions, not industrial clusters.
- Monsoon months often can't be verified.
- Two plants is a proof of concept, not a national system.
- Tree CO2 uptake is an IPCC default, not measured per plot.
- Farmers, plots and prices in the demo are invented. Satellite readings are real.

## 10. Open items before Day 3

- [ ] Confirm SECP phase dates from the order
- [ ] Confirm the Climate TRACE Hub asset and year before using the "~5×" line
- [ ] Find the claimed figures in Hub's and Sahiwal owner's annual reports
- [ ] Heat rate per plant for the CO2 factor
- [ ] NOx control equipment and dates at Sahiwal and Hub
- [x] Fill in accuracy numbers in question 8 after the first test
- [x] Climate TRACE reporting year confirmed (2025, asset 25455585)
- [x] C07 tree benchmark on real WorldCover samples: 11.6% gain, short of 15%. Say it as an honest gap; C07 is met by the emissions model
- Correction: there was no Sahiwal outage in Jan 2026 (metered 628 GWh). Near-zero months were Nov 2024, Feb 2025 and Oct 2025.
