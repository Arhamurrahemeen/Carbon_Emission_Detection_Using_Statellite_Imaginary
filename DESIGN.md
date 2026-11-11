# DESIGN.md: Green Claims Check

The design contract for the Streamlit app (`app/`). Every visual choice below has a reason. Change the reason before changing the choice.

## 1. Who it is for and the one decision

**User:** an environmental or credit risk officer at a Pakistani bank, reviewing a loan to a coal power company. Not a data scientist. Watches the demo on a projector, then judges it.

**The one decision on the main screen:** *refer this company's green claims for review, or not.* Everything on the landing view serves that decision, in this order:

1. The answer (verdict) and why, in one sentence.
2. The one picture that proves it: where the company's claim sits against the independent evidence.
3. Which claims disagree, in plain words.
4. The physical evidence: the plant, its plume and its tree plots on a 3D map, and the monthly record.

Anything that does not serve that decision moves to a secondary tab.

**Second audience:** the jury (banks, PSX, industry, technical judges), who also score the three challenges. Each challenge gets its own tab, reachable in one click.

## 2. Dials

| Dial | Setting | Meaning |
|---|---|---|
| Density | 3 of 5 | Report-like. Numbers are large and few; detail sits behind tabs and expanders |
| Rhythm | 3 of 5 | Sections vary: a full-width answer strip, a single chart, a two-column map and claims list, a wide timeline |
| Motion | 1 of 5 | Hover and the map's own camera only. No entrance animations, no loops |
| Liveliness | 2 of 5 | Calm and trustworthy. One accent colour, used for satellite evidence only |

## 3. Theme: light, warm neutral

**Why light, not dark:** the user reads a credit report, not a monitoring console, and the demo runs on a projector, where dark pages wash out. A warm off-white feels like paper and finance, not "tech". The map gets a light basemap so the 3D columns stand out by colour, not glow.

## 4. Colour tokens

Base palette: two neutrals plus one accent. Status colours are semantic and appear only where they mark a real state.

| Token | Hex | Use |
|---|---|---|
| `paper` | `#F6F4EF` | Page background |
| `card` | `#FFFFFF` | Raised surfaces (verdict strip, claim rows) |
| `rule` | `#E2DDD3` | Hairlines, borders, gridlines |
| `ink` | `#1D2A2F` | Body text, metered data (the trusted record is plain black ink) |
| `ink-soft` | `#5B676C` | Secondary text, captions, axis labels |
| **`sat`** (accent) | `#0F6B75` | **Satellite evidence only:** the estimate line, its 80% range, plume hexagons, satellite columns. Its single meaning is "what space saw" |
| `sat-bright` | `#3FC6CF` | The accent on satellite imagery only (map layers), where `sat` is too dark to see |
| `sat-tint` | `#0F6B7526` | The 80% range band (accent at 15% opacity) |
| `flag` | `#B3261E` | INCONSISTENT, CONTRADICT, REJECTED, the company's disputed claim marker |
| `warn` | `#A15C00` | LOW_CONFIDENCE, CANNOT_VERIFY |
| `ok` | `#2E6B3A` | CONSISTENT, AGREE, verified tree plots |
| `model` | `#8A8F98` | Climate TRACE and other modelled estimates (grey: an estimate, not evidence) |

Contrast: `ink` and `ink-soft` pass 4.5:1 on `paper` and `card`. Status colours are never the only signal; every status also has a word.

## 5. Typography

**IBM Plex Sans** for UI and text, **IBM Plex Sans** with tabular numerals for figures. *Reason:* Plex was drawn for corporate and technical documents, so it reads like a financial report, and its tabular figures keep columns of GWh aligned. Loaded from Google Fonts with a system sans fallback.

| Role | Size / weight |
|---|---|
| Verdict word | 30 px / 600 |
| Hero figure | 40 px / 600, tabular |
| Section heading | 20 px / 600 |
| Body | 16 px / 400 |
| Caption | 13 px / 400, `ink-soft` |

No all-caps labels with wide tracking. Sentence case everywhere.

## 6. Shape, depth, spacing

- **Radius:** 6 px on cards and inputs, 999 px only on status pills. Nothing else is rounded.
- **Shadow:** none, except the verdict strip (one soft shadow, because it is the single most important surface).
- **Borders:** 1 px `rule`. Cards are separated by borders, not shadows.
- **Spacing scale:** 4, 8, 16, 24, 40, 64 px. Sections separated by 40 px; related items by 8–16 px.

## 7. Components

**Verdict strip** (top of the landing view): status pill + verdict word + one sentence + three figures (satellite estimate with range, metered, company claim). Synthetic inputs are named inside the strip, not hidden in a footer.

**Range plot** (the proof): one horizontal bar per claim period. The teal band is the satellite 80% range; markers sit on it: company claim (red dot if outside the band, green if inside), metered figure (black tick), Climate TRACE (grey hollow dot). Title states the question: "Does the company's figure fall inside what the satellite supports?"

**Claim rows** (C12): one row per cross-check, in plain words. Left: what was compared ("Company's table vs the electricity meter"). Middle: the two values. Right: result word with its colour. No raw codes on this view.

**3D map** (pydeck, pitch 50°). **Basemap: real satellite imagery**, the EOX *Sentinel-2 cloudless* mosaic (the same satellite family as our tree check; free with attribution, CC BY-NC-SA 4.0, fine for this non-commercial demo), draped on AWS Terrain Tiles. A toggle switches to a plain light map (Carto) for projectors that wash out imagery. On imagery the accent is drawn as `sat-bright` `#3FC6CF` so it holds 3:1 against dark fields; on the light map it stays `sat`. *Trade-off:* map tiles need internet; every number, chart and verdict works offline.
- *Plant view:* a teal column for the satellite CO2 estimate and a grey column beside it for Climate TRACE, both scaled to the same tonnes. Teal hexagons, extruded by summed plume strength, at the downwind point of each real overpass over the last 24 months. Together they form a "plume rose" showing where the pollution really goes.
- *Contracts view:* camera pulls out to show the plant and its tree plots, with an arc from the plant to each plot. Plot columns are green (trees seen alive) or grey (no trees seen), with height set by trees contracted.
- Tooltips in plain words. A caption under the map says what height and colour mean.

**Monthly timeline:** metered generation as plain ink bars, the satellite estimate as a teal line with its band, low-confidence months marked with a light warn tint, shutdown months annotated in words.

**Status pill:** word + colour (OK, LOW_CONFIDENCE, REJECTED). The only pill shape in the app.

## 8. Navigation

Top tabs, no sidebar: **Verdict · Tree contracts · Reliability (C04) · Model test (C07) · Log**. A company picker sits above the tabs. Every tab works; nothing links to a page that does not exist.

## 9. Copy rules

- Plain words first, codes second. "Not enough clear satellite days" before `W_FEW_OBS`.
- Never: fraud, breach, proves, zero carbon, net zero, "1 km resolution", "AI-powered".
- The satellite measures NO2, not CO2; CO2 is always labelled "estimated".
- INCONSISTENT is explained as "refer for review", never as wrongdoing.
- Every synthetic or invented value says so where it appears.
- No emoji, no decorative arrows, no sparkle icons.

## 10. States

| State | What the user sees |
|---|---|
| No results built yet | "No results yet. Run `python -m verify.build` in the project folder, then reload." |
| Month or year too uncertain | Estimate shown in muted teal, verdict "Cannot verify", with the plain reason |
| Rejected input (C04) | Red pill, the reason in one sentence, no number at all |
| Synthetic inputs present | A single notice on the verdict strip listing which inputs are synthetic |

## 11. Accessibility

Text contrast at least 4.5:1; chart marks at least 3:1 against neighbours. Colour is never the only carrier of meaning: every coloured state has a word. All controls work by keyboard (Streamlit defaults).
