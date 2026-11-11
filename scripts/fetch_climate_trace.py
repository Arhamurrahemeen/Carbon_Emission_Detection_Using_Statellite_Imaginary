"""Climate TRACE benchmark for our sites, fetched once and saved (display only, never a model input).
Run:    python scripts/fetch_climate_trace.py
Writes: data/raw/climate_trace.csv
Source: Climate TRACE API v6, CC-BY 4.0."""
import csv
import json
import urllib.request
from datetime import date
from pathlib import Path

ASSETS = {25455252: "sahiwal", 25455585: "hub", 448261: "hub"}
URL = "https://api.climatetrace.org/v6/assets?countries=PAK&sectors=electricity-generation&limit=200&year={year}"
COLUMNS = ["site_id", "asset_id", "asset_name", "asset_type", "year", "emissions_t_co2e", "activity_mwh",
           "emissions_factor", "confidence_total", "confidence_capacity_factor", "fetched_at"]


def fetch(year: int) -> list[dict]:
    req = urllib.request.Request(URL.format(year=year), headers={"User-Agent": "research-client"})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    return data.get("assets", data) if isinstance(data, dict) else data


def _confidence(asset: dict, year: int, key: str) -> str:
    for block in asset.get("Confidence", []):
        if str(year) in block:
            return block[str(year)][0].get(key, "")
    return ""


def main():
    rows = []
    for year in (2023, 2024, 2025):
        for a in fetch(year):
            if a.get("Id") in ASSETS:
                s = a["EmissionsSummary"][0]
                rows.append({"site_id": ASSETS[a["Id"]], "asset_id": a["Id"], "asset_name": a["Name"],
                             "asset_type": a.get("AssetType"), "year": year,
                             "emissions_t_co2e": s.get("EmissionsQuantity"), "activity_mwh": s.get("Activity"),
                             "emissions_factor": s.get("EmissionsFactor"),
                             "confidence_total": _confidence(a, year, "total_co2e_100yrgwp"),
                             "confidence_capacity_factor": _confidence(a, year, "capacity_factor"),
                             "fetched_at": date.today().isoformat()})
    dest = Path("data/raw/climate_trace.csv")
    with dest.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {dest}")


if __name__ == "__main__":
    main()
