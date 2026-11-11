# Pitch Brief: Satellite Verification of Green Claims

New words are explained in [GLOSSARY.md](GLOSSARY.md).

BattleVerse 2026 · Battle of Intelligence · Pillar 5 (Greenwashing & Disclosure Verification) · Challenge C04
Draft, 11 Nov 2026. Items marked **(verify)** need checking before they go on a slide.

---

## Accuracy in one breath

- **About 77% accurate for one month.** Too uncertain to judge a single month, so the system refuses to.
- **About 93% accurate for a year** on average (85% in the strictest test).
- **62% less error than the rule of thumb** banks use today, and 30% less than raw satellite readings. C07 asks for 15%.
- All tested on months the model had never seen.

## 1. The project in one line

**We check both halves of a company's green claim, its pollution and its trees, from space, before any money moves.**

## 2. The project in simple words

A coal power company makes two green claims:

1. **"This is how much we pollute."**
2. **"We planted trees to make up for part of it."**

Today nobody checks either claim independently. Banks just read the company's own report.

We check both:

- **Pollution check.** A satellite measures the NO2 gas rising from the plant. Our model, trained on metered generation records (CPPA-G, matching NEPRA), estimates how hard the plant really ran. If the company's number doesn't fit, we flag it.
- **Tree check.** The company says it planted trees. Every quarter a satellite photo of each plot shows whether trees are actually there and alive. We compare trees claimed with trees seen. (The same check can release the company's payments to farmers only for living trees: one sentence in the pitch, not the main story.)
- **One answer for the bank.** For each claim: **Consistent**, **Inconsistent** or **Can't verify**.

When the data is impossible or too weak (a cloudy photo, a location that doesn't exist, a 200% reduction), the system refuses to answer instead of guessing. That is our C04 challenge.

## 3. Who is the user, who participates, who pays

**Rule:** the user is the person who opens the screen and makes a decision with what it shows.

| Role | Who | What they do | What they get |
|---|---|---|---|
| **User and payer** | **Environmental or credit risk officer at a Pakistani bank** (second user: ESG fund analyst) | Approves, reprices or questions a loan to a coal power company | Independent evidence for SBP climate-risk reporting, early warning on risky borrowers, protection for "green" loan labels |
| Participant | Coal power company (e.g. Sahiwal, Hub) | Makes the emissions and offset claims we check; pays farmers for its trees | A claim lenders and buyers can trust |
| Participant | Farmer | Plants and maintains the company's trees | Paid by the company, only for trees seen alive |
| Data sources | CPPA-G and NEPRA (metered generation), Sentinel satellites, ERA5, Climate TRACE | Supply evidence | None |

**Why the bank pays, not the company:** if the company paid for its own check, we would rebuild the problem we are solving, the company grading its own report card.

**How we earn (demo assumption, label it on the slide):** a yearly fee per company the bank checks.

**Decided 12 Nov: pitch as "verifying green claims".** Two kinds of claim (emissions and offsets), one kind of evidence (satellite plus meter). No investor or funder in the tree story: the factory owns its offsets and pays the farmer directly; we only verify. See `DISCUSSION_LOG.md` questions 8 and 12–14.

**Honest weakness:** Pakistani banks don't buy tools like this today. Demand is starting because of regulation (next section). Say this ourselves.

## 4. Why now

| Rule | What it says | Status |
|---|---|---|
| SECP order, 31 Dec 2024 | Listed companies must publish IFRS S1/S2 climate disclosures, in phases. SECP's press release says the first two phases start July 2026 and July 2027; the last phase covers periods from 1 Jul 2027 | **(verify)** phase dates against the order |
| SBP climate-risk framework | Banks submitted board-approved implementation plans by 30 Sep 2026; full compliance by 30 Jun 2029 | Confirmed in news coverage |
| SBP Green Taxonomy | Issued Dec 2025. Banks must reference it in green banking policies | No 2029 deadline; don't mix it up with the framework |

Companies are starting to disclose. Banks are now required to manage climate risk, and they have no way to check what they are told.

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

## 7. Pitch script (7 minutes, matches the deck)

Deck: `Satellite_Verification_Pitch_Deck.pptx` (IU template, 9 slides including Q&A). Satellite images used on slide 5: `docs/img/`.

| Time | Slide | What we say |
|---|---|---|
| 0:00–0:30 | 1. Title | "We check both halves of a company's green claim, its pollution and its trees, from space. The satellite measures NO2, not CO2." |
| 0:30–1:15 | 2. Problem | "A bank's risk officer is renewing a loan to a coal power company. The only evidence for its emissions and offsets is its own report. SECP disclosure starts 2026–27; SBP's climate-risk deadline is 2029." |
| 1:15–1:45 | 3. Approach | "Each claim gets independent evidence: NO2 for emissions, Sentinel-2 for trees, and seven cross-checks between the report, the meter and the satellite." |
| 1:45–2:30 | 4. Data | Walk the table: Sentinel-5P NO2 grid per daily pass, ERA5 wind, CPPA-G monthly Excel (matches NEPRA exactly), Sentinel-2 + WorldCover, the company report. "Downloaded once, saved as files; the demo doesn't need a live connection." |
| 2:30–4:15 | 5. Live demo | Point at the two images first: the real NO2 plume over Sahiwal and the Sentinel-2 photo of the plant. Then the app: verdict strip → range plot → 3D map (plume rose, then tree contracts) → claim rows → Reliability tab, run all 8 checks. Say the company claims are synthetic |
| 4:15–5:00 | 6. Evidence | "About 77% accurate for one month, so it refuses to judge a single month. About 93% for a year. Understated yearly claims caught 94–100% of the time, no honest claim flagged." |
| 5:00–6:10 | 7. Challenges | C04 refused inputs, C07 62% and 30% less error (tree model 11.6%, an honest gap), C12 Climate TRACE off about 5x at Hub. Adaptation: verdicts moved to the fiscal year |
| 6:10–7:00 | 8. Value, limits, next step | Exposure range, stated limits, pilot with one bank. Close: "Satellites can't see CO2, but they can tell a bank when a company's green numbers don't add up." |

**Words we never use:** fraud, breach, proves, zero carbon, net zero.

## 8. Likely jury questions and answers

**Business**

1. **Why would a bank pay for this?** SBP requires climate-risk management, with full compliance by 2029. Today a bank's only evidence is the borrower's own report. We are a cheap, independent second source.
2. **Why not let the company pay?** Then the company pays for its own report card, the same problem we are solving.
3. **Who else does this?** GHGSat, Kayrros and Floodlight sell satellite emission checks abroad. Nobody checks disclosures this way in Pakistan, and no other Pillar 5 team here uses satellites.
4. **How do you make money?** Yearly fee per company checked. Demo numbers, not tested with banks.
5. **Do banks actually want this?** Not yet at scale. Regulation is creating the need now. That is our "why now", and our next step is one pilot bank.

**Technical**

6. **Satellites can't see CO2.** Correct. We measure NO2, estimate activity trained on metered grid sales (CPPA-G, matching NEPRA), then calculate CO2 as a range labelled "estimated".
7. **Why NO2 and not SO2?** NO2 has a stronger, cleaner satellite signal at single plants. SO2 is noisier, and scrubbers at modern plants cut SO2 without changing coal burned.
8. **How accurate is it?** About 77% for a single month, so one month alone is too uncertain and the system refuses to judge it. About 93% for a whole year on average (worst year about 80%; our strictest test, learning only from the past, gave 85%). Every one of these figures was tested on months the model had never seen. An earlier 97.5% figure was withdrawn because the model had already seen those months.
9. **What if the model is wrong?** It says "can't verify" instead of guessing: too few clear days, inputs it hasn't seen, ranges too wide. C04 shows this live.
10. **What about monsoon clouds?** July–September often can't be verified. We say so on screen.
11. **What if the plant installs pollution controls?** Controls cut NO2 without cutting coal burned, so it would look like a drop in activity. We record each plant's equipment and dates, and treat a change as a break in the data.
12. **Two plants and ~90 months is tiny.** Yes, it is a proof of concept. That is why we use a simple model and test on held-out months, not a big model.
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

## 8b. The three challenges (one slide)

| Challenge | Our answer | Evidence |
|---|---|---|
| C04 out-of-bounds guard | 8 live cases: 5 rejected, 1 low confidence, 1 claim not in source, 1 noise control | All pass; real monthly data abstains by itself |
| C07 beat a baseline by 15% | Our model vs two simple methods: a rule of thumb (plants run at about 23% of capacity) and raw satellite readings | Our error is 62% and 30% smaller (misses by 170 GWh a month vs 442 and 244) |
| C12 multimodal cross-check | The company's table vs its own text vs the meter vs the satellite vs the tree plots (7 checks) | Caught 94–100% of yearly claims understated by 20% or more, with no false alarms (likely a little optimistic: see CHALLENGES.md) |

Full write-up: `docs/CHALLENGES.md`.

## 9. Limits we state ourselves

- The satellite measures NO2, not CO2. CO2 is estimated and shown as a range.
- Inconsistent is a reason to ask questions, not proof of a false statement.
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
