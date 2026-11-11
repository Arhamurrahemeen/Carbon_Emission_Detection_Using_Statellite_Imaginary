# Evidence pack

Every dataset the results depend on: where it came from, when, under what licence, and what we changed. Synthetic and mocked parts are listed at the end. Rebuild every number with `python -m verify.build`.

## Datasets

| Dataset | Source | Downloaded | Licence | Changes we made | Status |
|---|---|---|---|---|---|
| Sentinel-5P NO2 (OFFL L3) | Copernicus via Earth Engine `COPERNICUS/S5P/OFFL/L3_NO2` | 2026-11-11 (`scripts/export_overpasses.py`) | Copernicus Sentinel data, free and open | Per overpass: mean NO2 in a 7 km circle 10 km downwind, 7 km circle 20 km upwind, 5 km circle on the plant. Only 05–10 UTC images (the Pakistan pass) | Real once `data/raw/overpasses_*.csv` exist |
| Wind (ERA5-Land hourly 10 m u/v) | ECMWF via Earth Engine `ECMWF/ERA5_LAND/HOURLY` | 2026-11-11 | Copernicus licence, attribution required | Hour nearest each overpass, mean within 15 km of the plant | Real, same files |
| Monthly plant generation (training labels) | CPPA-G "Energy Procurement Report (Provisional)", cppa.gov.pk → Downloads → XWDISCOs Energy Purchase Data, FY2024-25 to Q1 FY2026-27 (Excel) | 2026-11-11 | Public government data | kWh → MWh; three plants mapped to our sites (`verify/labels.py`). Cross-check: FY2024-25 sums equal NEPRA's PER Generation FY2024-25 (Huaneng 4,255 GWh, CPHGC 672 GWh) | Real, Jul 2024 – Sep 2026 (27 months) |
| Annual plant generation and fleet utilisation | NEPRA *Performance Evaluation Report, Generation FY2024-25* (nepra.org.pk) | 2026-11-11 | Public government document | Imported-coal fleet utilisation 22.9% used for the capacity baseline | Real |
| Climate TRACE benchmark | Climate TRACE API v6, assets 25455252, 25455585, 448261, years 2023–2025 | 2026-11-11 (`scripts/fetch_climate_trace.py`) | CC-BY 4.0 (Climate TRACE) | None. Display and comparison only, never a model input | Real |
| Plant locations | Climate TRACE asset centroids | 2026-11-11 | CC-BY 4.0 | None. To check on a map | Real |
| Emission factor range | 0.80–0.95 t CO2/MWh (Hub 0.70–0.95 for the oil plant share) | — | — | Climate TRACE's own factors (0.911 Sahiwal, 0.928 CPHGC) sit inside the range. Still to source from IPCC 2006 + NEPRA tariff heat rate | Assumption |
| Tree plot greenness | Sentinel-2 NDVI exported by the Shajar team (Earth Engine, 2026-11-11) | 2026-11-11 | Copernicus | None | Real readings, invented plots |
| C07 tree samples | ESA WorldCover v200 (2021) labels + Sentinel-2 features (`gee/c07_tree_samples.js`) | pending | CC-BY 4.0 (WorldCover) | Balanced sample, water and mangroves excluded | Synthetic until exported |
| Carbon prices, FX, fees | `data/manual/assumptions.csv` | — | — | — | Demo assumptions, each labelled |

## Synthetic and mocked parts

- **Company claims** for FY2026 (generation, CO2, trees, "25% reduction"): synthetic, built from real metered numbers (generation understated by 25%). No real company figure was found in a public report yet.
- **Detection test claims:** real held-out months with the claim scaled by 0.8 / 0.6 / 0.4 (misstated) and 1.0 (true).
- **Farmers, plots, prices:** invented (`invented_farmer` flag). Greenness readings are real Sentinel-2 values at those coordinates.
- **Tree pass decisions** use the NDVI 0.35 threshold (`threshold_fallback` flag) until the plot export with classifier features lands.
- **NO2 overpasses:** synthetic until the export finishes. When synthetic, the model also trains on synthetic labels (never synthetic NO2 against real labels) and every record is flagged.

## Corrections we found in our own sources

- No Sahiwal outage in Jan 2026: metered 628 GWh. The months near zero are Nov 2024 (3 GWh), Feb 2025 (0) and Oct 2025 (0).
- Climate TRACE vs metered, calendar 2025: CPHGC 3,816 vs ~702 GWh (about 5.4×); the Hub Power oil plant 3,158 vs ~0 GWh; Sahiwal 4,590 vs ~5,054 GWh. Climate TRACE rates its Hub capacity-factor confidence "low".
