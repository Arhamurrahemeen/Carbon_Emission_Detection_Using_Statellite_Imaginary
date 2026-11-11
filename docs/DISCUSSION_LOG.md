# Discussion log: questions we asked and the answers we settled on

A record of the decisions behind the project, BattleVerse 2026, 11–12 Nov. Read this before the pitch or Q&A if something is forgotten. Plain-language terms are explained in [GLOSSARY.md](GLOSSARY.md); jury answers in [PITCH_BRIEF.md](PITCH_BRIEF.md).

---

## A. The idea

### 1. What did Baneen's Shajar repo do, and how did it compare with our original idea?
Shajar was a working static web page: a factory's emissions become a contract to plant trees on a farmer's land, and payment is released only when Sentinel-2 imagery shows the trees alive. It took factory emissions from Climate TRACE and covered C04. Our original idea (in the Obsidian vault) checked a coal plant's *disclosed* emissions against satellite NO2. Nothing of it had been built.

### 2. Which was stronger for the hackathon?
On paper, the original: it matches Pillar 5 exactly (verify disclosures), AI is central, it matches the locked problem board, and no other Pillar 5 team uses satellites. Shajar was stronger on Green FinTech money flow and was already working, but its AI part was thin, and offsetting emissions with trees invites "isn't that greenwashing?" questions.

### 3. In the original idea, who is the customer? PEMRA?
Not PEMRA (that regulates TV and radio). NEPRA, the power regulator, is a **data source**, not the customer. The user is a **bank's environmental or credit risk officer** deciding on a loan to a coal power company.

### 4. Doesn't an environmental department already do this?
We found no Pakistani agency checking a company's *financial disclosure* against satellite data. EPAs use ground stations and self-reports; SUPARCO's satellite work is smog and air quality. Even if a regulator watches emissions, that information doesn't reach the bank's lending decision.

### 5. Is Shajar a platform for factories to "go zero carbon"?
It connects factories and farmers for tree offsets, but "zero carbon" can't be defended. Gul Ahmed Power emits about 294,000 t CO2 a year; offsetting all of it needs roughly 49,000–56,000 acres (25–28 million trees). Shajar's demo plots total about 87 acres. Claim verified *partial* offsets only.

### 6. Can we merge the two?
Yes. A company makes two green claims, "we emit X" and "we offset Y with trees", and we check both from space. The emissions check is the core (Pillar 5); the tree check is a second claim to verify.

### 7. The merged idea in one line?
"We check both halves of a company's green claim, its pollution and its trees, from space, before any money moves."

### 8. Should the pitch be framed as "verifying green claims"? (Decided: yes, 12 Nov)
Proposed: pitch as verifying two kinds of claims (emissions and offsets), with tree payments as one sentence, and drop the marketplace and the farmer/funder split from the main story. Reason: the Intelligence track rewards AI improving a decision, and the marketplace and payments are operations, not AI. **Decided by the team on 12 Nov.** The app now pays farmers directly from the factory (no funder split) and the Trees tab checks the tree claim.

---

## B. Users, payers and the money

### 9. Are we building two dashboards, one for farmers and factories and one for banks?
No. One main screen for the **bank**, the customer who pays. Farmers would use SMS or WhatsApp, not a dashboard. Factories only need to see contract status.

### 10. Why would a bank or investor use this? What do they gain?
They never look at smoke or plants; they read one line: "Can I trust this company's green numbers?"
- They avoid mispriced loans (carbon costs, regulator action and lost buyers can hit a polluter's profits).
- SBP requires banks to manage climate risk (plans due Sep 2026, compliance by June 2029), and this gives them independent evidence.
- It protects the "green" label on loans.
- It's monthly, while company reports are yearly.

Honest weakness: Pakistani banks don't buy tools like this yet; regulation is creating the need now.

### 11. Who is the user, who are the participants, and who pays?
Rule: **the user is the person who opens the screen and makes a decision with it.**
- **User and payer:** the bank's risk officer (second: an ESG fund analyst).
- **Participants:** the coal company (makes the claims), farmers (plant trees). NEPRA, CPPA-G, the satellites and Climate TRACE are data sources.
- **The company never pays for its own check;** that would rebuild the self-reporting problem.

### 12. Why would an investor pay for trees?
They don't. **The factory pays for the trees.** In the original design an investor or bank only *lent* the planting money upfront and was repaid from verified payments (demo example: lend PKR 250,000, earn PKR 160,000 a year, repaid in about 1.6 years). The satellite check makes that loan safe, because nobody gets paid for trees that aren't there.

### 13. Why involve a third party at all? Why doesn't the factory just pay?
It can, and that's simpler. A financier only helps when someone must pay *before* the trees exist: the factory doesn't want to pay for trees that may die, and small farmers lack the cash. The financier is optional; for the pitch the simple version (factory pays the farmer, only for living trees) is better.

### 14. Planting trees means the factory takes responsibility for its emissions. Why would it take a loan for that?
In the design the factory never borrows; at most the farmer does, for saplings. The factory still pays the full cost of every tree, only once the satellite confirms it. Borrowing changes *when* you pay, not *who* is responsible. The deeper point is right, though: real accountability means cutting emissions, and tree offsets are a voluntary claim in Pakistan (no carbon tax or cap). So we show emissions and trees **separately** and never let trees cancel emissions.

---

## C. Data

### 15. Where does the data come from?
| What | Source | Form |
|---|---|---|
| NO2 over the plant | Sentinel-5P (ESA) via Google Earth Engine | NO2 grid for every daily pass, 2018–2026 (5,570 passes over our two plants) |
| Wind | ERA5 (ECMWF) | Hourly wind components |
| How much the plant really ran (the model's answers) | CPPA-G Energy Procurement Report | Monthly Excel, kWh bought per plant, Jul 2024 – Sep 2026 (27 months) |
| Check on those answers | NEPRA Performance Evaluation Report FY2024-25 | Annual plant totals (CPPA-G matches exactly) |
| Tree plots | Sentinel-2 + ESA WorldCover | 10 m photos; land-cover labels |
| Benchmark | Climate TRACE API | Modelled yearly emissions (display only) |
| Company claims | Company annual reports | PDF text and tables (none found yet, so synthetic) |

### 16. Why CPPA-G instead of typing NEPRA's monthly decisions?
NEPRA's monthly fuel-cost decisions are scanned images, so they'd have to be typed by hand. CPPA-G publishes the same metered figures as Excel files, which a script reads. The FY2024-25 totals match NEPRA's annual report exactly (Sahiwal 4,255 GWh, CPHGC 672 GWh).

### 17. How do we read NO2 from the satellite and turn it into CO2?
1. Sentinel-5P measures NO2 in the air above each patch of ground once a day (~1:30 pm).
2. Drop cloudy and windless days.
3. Subtract NO2 upwind (background) from NO2 downwind (the plume).
4. Multiply by wind speed (strong wind spreads the plume thinner) and average by month.
5. A ridge model learns the link between plume strength and the plant's metered generation.
6. CO2 = generation × an emission factor (0.80–0.95 t per MWh), always shown as a range and labelled estimated.

**Why not convert NO2 straight to CO2?** The ratio changes with coal type, burners and pollution controls; physics-only conversions run 40–50% low. Learning each plant's link from metered data absorbs that.

### 18. Why is Hub treated differently?
Hub has two plants about 1 km apart (CPHGC coal and the Hub Power oil plant), and the satellite sees one combined plume, so we add both plants' generation together. The oil plant barely ran. Hub is mostly idle and coastal, so its signal is weak, and we state that as a limit.

### 19. Facts we got wrong at first and corrected
- **No Sahiwal outage in Jan 2026** (628 GWh metered). The near-zero months were Nov 2024, Feb 2025 and Oct 2025.
- **The right Climate TRACE asset for CPHGC is 25455585, not 448261** (the oil plant). For calendar 2025, Climate TRACE says 3,816 GWh vs about 702 metered (about 5.4×).
- **SECP's first IFRS S1/S2 phases start July 2026 and 2027;** 1 Jul 2027 is only the last phase.
- **The 2029 deadline belongs to SBP's climate-risk framework,** not the Green Taxonomy.

### 20. Will more Earth Engine data make the model more reliable?
Not the satellite side; all 5,570 passes are already used. What would help is **more months of metered generation** to learn from. We have only 27 because CPPA-G's Excel files start in July 2024.

---

## D. Accuracy and the model

### 21. Is the model really 97.5% accurate?
**No; that figure was withdrawn.** It came from a model trained on the same months it was graded on (data leakage). The honest figures come from months the model never saw.

### 22. What are the accuracy and baseline numbers, in plain words?
| Test | Error | Accuracy |
|---|---|---|
| One month | ~23% | ~77%: too uncertain alone, so the system refuses to judge a single month |
| One year (FY2026) | 3.9% low (5,896 vs 6,138 GWh) | |
| A year, average over 16 periods | ~7% (worst 20%) | ~93% |
| A year, strictest forward test | ~15% | ~85% |

**A baseline** is the simple method you'd use without our model. Typical monthly miss:
- Rule of thumb "plants run at 23% of capacity": 442 GWh
- Raw satellite NO2 without wind correction: 244 GWh
- **Our model: 170 GWh**

"62% better" means our error is 62% smaller than the rule of thumb's; it's a comparison, not an accuracy score. C07 needs at least 15%.

### 23. Did we actually train the model?
Yes, on real satellite data and real metered generation. The download that was still running at one point was only the tree classifier's samples, which have since finished too.

### 24. How did the tree classifier do on C07?
On 575 real test points it scored F1 0.891 against 0.798 for one greenness threshold: an **11.6% gain, short of 15%** (14.1% against Shajar's fixed 0.35). Adding seasonal features barely helped, so we didn't keep tuning toward the target. Present it as an honest gap; C07 is met by the emissions model.

### 25. How well does it catch false claims?
Yearly claims understated by 20%: caught 94% of the time; by 40% or 60%: 100%; honest claims wrongly flagged: 0%. The test windows overlap, so treat these as slightly optimistic.

---

## E. The hackathon brief

### 26. Which mission are we in?
**Pillar 5: Green Fraud, Greenwashing & Disclosure Verification.** Its guiding intent, "cross-verify corporate disclosures against operational evidence", describes our product. Weaker spot: Pillar 5 names NLP and language models, and our document part is small and rule-based. Answer: "Most Pillar 5 teams read the documents; we check them against physical evidence."

### 27. Does our project meet the brief (difficulty, user, why it matters, prototype, AI fit)?
- **Difficulty:** banks must trust a coal company's own green numbers.
- **User:** a bank risk officer.
- **Why now:** SECP disclosure from 2026–27; SBP compliance by 2029.
- **Prototype improves:** "trust the report" becomes a checked verdict.
- **AI fit:** input = satellite NO2, wind, disclosed figures; output = estimated output with a range and a verdict; person who acts = the risk officer; learning helps because there's no fixed NO2-to-output formula.
- **Focus area:** "understanding environmental claims" (main), "sustainable investment decisions" (secondary).

### 28. Which guide vocabulary applies to us?
- **Finance:** disclosure and greenwashing, capital allocation, creditworthiness and underwriting, the environmental part of ESG; partly carbon credits, double-counting (one contract per plot) and disbursement.
- **Technology:** geospatial analytics and satellite observation, predictive machine learning, anomaly detection, data integrity and audit trail, adversarial inputs (C04); partly document intelligence.

### 29. Which solution format are we?
Two of the four: a **working MVP** (the deployed app) and an **analytical model** (a trained model with held-out test results). Gap: the guide asks to "provide a sample input"; adding a box to type a claim and get a verdict live would match it exactly.

---

## F. App, demo and deck

### 30. Why not use Google imagery like the Aleph repo?
Aleph downloads Google imagery without a key, which is a terms-of-service grey area. We use EOX Sentinel-2 cloudless imagery: free with attribution, from the same satellite family as our tree check.

### 31. Why a light theme?
The user reads a bank report, not a monitoring console, and projectors wash out dark pages. Full design rules are in `DESIGN.md`.

### 32. What did the 3D map show us?
About 29% of Sahiwal's NO2 blows north-east, which matches Punjab's prevailing south-westerly winds. The raw Sentinel-5P image shows the same plume shape.

### 33. Where is the app hosted?
https://carbonemissiondetectionusingstatelliteimaginary-lvdbcjesxlusrz.streamlit.app (Streamlit Community Cloud, updates on every push to `main`). The satellite map needs internet; open the link once before the pitch so it's awake and the imagery is cached.

### 34. Which pitch template did we use?
IU shared the **Battle of Stocks** template. We kept its look and timed structure, retitled it Battle of Intelligence and filled it to our rubric: 9 slides, 7:00 plus Q&A, including a data-pipeline slide and real satellite images (Baneen's request, because every jury asks how the data is collected and made usable).

---

### 35. The app shows an "Electricity meter" number. Where does it come from, and why?
It's CPPA-G's monthly record of electricity each plant sold to the grid, measured by meters and published as Excel (it matches NEPRA's annual report). It's the model's answer key for training and testing, our proof the satellite tracks reality (5,896 vs 6,138 GWh), and cross-check X1. Renamed in the app to "Metered sales to the grid (CPPA-G)".
**"If you have the meter, why the satellite?"** The meter only exists for plants selling to the grid and only shows electricity; factories, cement, steel and captive plants have none. The satellite is independent, works anywhere and goes back to 2018 (monthly meter files only to July 2024). We train and prove it where both exist, then it can check where no meter is published.

## Still open
- A real company figure from Hub Power's annual report.
- Re-export the deck PDF (team number Team 13, IU3048, is now on slide 1).
- Optional: the "check a claim" input box (question 29).
