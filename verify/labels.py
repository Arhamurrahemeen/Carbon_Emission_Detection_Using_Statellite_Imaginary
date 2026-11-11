"""Training labels: monthly energy each plant delivered, from CPPA-G's "Energy Procurement Report (Provisional)"
spreadsheets (cppa.gov.pk > Downloads > XWDISCOs Energy Purchase Data). These are the metered purchase figures
NEPRA's fuel-cost decisions are built on, published as Excel instead of scanned PDF.

Run:  python -m verify.labels data/raw/cppa/*.xlsx  ->  data/raw/generation_monthly.csv"""
import sys
from pathlib import Path

import pandas as pd

# CPPA-G row name -> our plant name (verify.rules.SITE_PLANTS)
CPPA_NAMES = {
    "Huaneng Shandong Ruyi Energy (Pvt) Ltd": "Huaneng Shandong Ruyi",
    "China Hub Power (Pvt.) Ltd": "China Power Hub Generation",
    "China Power Hub Generation company (Pvt.) Ltd": "China Power Hub Generation",
    "Hub Power": "The Hub Power Company",
}
# Two sheet layouts: up to Mar 2026 (name col 4, energy col 7); from Apr 2026 (name col 0, energy col 5).
OLD_LAYOUT, NEW_LAYOUT = (4, 7), (0, 5)


def _layout(df: pd.DataFrame) -> tuple[int, int]:
    head = [str(v) for v in df.iloc[:10].to_numpy().ravel()]
    return NEW_LAYOUT if any("Name of the Power Producers" in v for v in head) else OLD_LAYOUT


def _month(df: pd.DataFrame, sheet: str) -> str | None:
    for v in df.iloc[:6].to_numpy().ravel():
        if isinstance(v, str) and "for the month of" in v.lower():
            text = v[v.lower().index("for the month of") + len("for the month of"):].strip().title()
            return pd.to_datetime(text, format="%B %Y").strftime("%Y-%m")
    try:
        mon, yy = sheet.strip().split("-")  # "SEP-25", "April-26"
        return pd.to_datetime(f"{mon[:3].title()}-{yy[-2:]}", format="%b-%y").strftime("%Y-%m")
    except ValueError:
        return None  # summary sheet, not a month


def parse_sheet(df: pd.DataFrame, source_file: str, sheet: str) -> pd.DataFrame:
    month = _month(df, sheet)
    if month is None:
        return pd.DataFrame()
    name_col, energy_col = _layout(df)
    rows = []
    for _, r in df.iterrows():
        name = str(r[name_col]).strip() if pd.notna(r[name_col]) else ""
        if name in CPPA_NAMES:
            kwh = pd.to_numeric(r[energy_col], errors="coerce")
            rows.append({"plant": CPPA_NAMES[name], "month": month,
                         "net_generation_mwh": 0.0 if pd.isna(kwh) else round(float(kwh) / 1000, 3),
                         "source_pdf": source_file, "page": sheet, "data_flags": ""})
    return pd.DataFrame(rows)


def extract(files: list[Path]) -> pd.DataFrame:
    parts = []
    for f in files:
        book = pd.ExcelFile(f)
        for sheet in book.sheet_names:
            parts.append(parse_sheet(pd.read_excel(book, sheet_name=sheet, header=None), f.name, sheet))
    out = pd.concat(parts, ignore_index=True)
    return out.drop_duplicates(["plant", "month"], keep="last").sort_values(["month", "plant"]).reset_index(drop=True)


if __name__ == "__main__":
    files = [Path(p) for p in sys.argv[1:]]
    out = extract(files)
    dest = Path("data/raw/generation_monthly.csv")
    out.to_csv(dest, index=False)
    print(f"{len(out)} rows, {out['month'].min()}..{out['month'].max()} -> {dest}")
