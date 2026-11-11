# Satellite Verification of Green Claims

A coal power company tells its bank two things: how much it emits, and how many trees it planted to offset part of it. This project checks both claims from space.

- **Emissions:** Sentinel-5P NO2 around the plant, corrected for wind, turned into an estimate of monthly generation by a model trained on NEPRA's metered records. CO2 is derived from that, always as a range.
- **Trees:** Sentinel-2 imagery of each offset plot, checked every quarter. Farmers are paid only when the trees are confirmed alive.
- **Answer:** for each claim, CONSISTENT, INCONSISTENT or CANNOT_VERIFY. Impossible or weak inputs are rejected or flagged, never answered with a confident number.

The satellite measures NO2, not CO2. An INCONSISTENT result is a reason to ask questions, not proof of a false statement.

BattleVerse 2026, Iqra University · Battle of Intelligence · Pillar 5: Greenwashing & Disclosure Verification

## Run

```bash
pip install -r requirements.txt
python -m verify.build
streamlit run app/streamlit_app.py
python -m pytest
```

## Docs

- [Design spec](docs/specs/2026-11-11-green-claims-verification-design.md)
- [Build plan](docs/plans/2026-11-11-build-plan.md)
- [Pitch brief and jury Q&A](docs/PITCH_BRIEF.md)

## Data

All data is fetched once and committed, so nothing calls the internet at demo time. Sources, licences and download dates are in `evidence_pack.md`. Synthetic and invented data is labelled in file names, data flags and the app.

## Team

Muhammad Arham · Baneen Raza · Ayesha Maryam

Tree-verification ideas and Earth Engine scripts adapted from [Shajar Ledger](https://github.com/Baneenraza/Shajar).
