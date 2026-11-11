import pandas as pd

from verify.labels import parse_sheet


def _sheet(month_title, rows):
    head = [[None] * 8 for _ in range(4)]
    head[3][2] = f"For the Month of {month_title}"
    body = [[None, None, None, sno, name, fuel, cap, kwh] for sno, name, fuel, cap, kwh in rows]
    return pd.DataFrame(head + body)


def test_parse_sheet_maps_plants_and_converts_to_mwh():
    df = _sheet("April 2025", [
        (2, "Hub Power", "RFO", 1208, 1500000),
        (22, "China Hub Power (Pvt.) Ltd", "Coal- Imported", 1220, 62361700),
        (27, "Huaneng Shandong Ruyi Energy (Pvt) Ltd", "Coal- Imported", 1320, 465127200),
        (28, "Gul Power Gen", "RFO", 100, 99),
    ])
    out = parse_sheet(df, source_file="x.xlsx", sheet="Apr-25")
    assert list(out["month"].unique()) == ["2025-04"]
    got = dict(zip(out["plant"], out["net_generation_mwh"]))
    assert got == {"The Hub Power Company": 1500.0, "China Power Hub Generation": 62361.7, "Huaneng Shandong Ruyi": 465127.2}
    assert (out["source_pdf"] == "x.xlsx").all() and (out["page"] == "Apr-25").all()


def test_month_falls_back_to_sheet_name_when_title_missing():
    df = _sheet("April 2025", [(27, "Huaneng Shandong Ruyi Energy (Pvt) Ltd", "Coal- Imported", 1320, 1000)])
    df.iloc[3, 2] = "Energy Procurement Report"
    out = parse_sheet(df, source_file="x.xlsx", sheet="SEP-25")
    assert out.iloc[0]["month"] == "2025-09"


def test_new_2026_layout_name_col0_energy_col5():
    head = [[None] * 9 for _ in range(6)]
    head[2][0] = "FOR THE MONTH OF APRIL 2026"
    head[5][0] = "Name of the Power Producers"
    head[5][5] = "Energy Units (kWh)"
    body = [
        ["China Power Hub Generation company (Pvt.) Ltd", "Hub Balochistan", "Coal-Imported", 1249, "x", 333479000, 0, 0, 0],
        ["Huaneng Shandong Ruyi Energy (Pvt) Ltd", "Sahiwal, Punjab", "Coal-Imported", 1244, "x", 646752100, 0, 0, 0],
    ]
    out = parse_sheet(pd.DataFrame(head + body), source_file="q4.xlsx", sheet="APRIL-26")
    got = dict(zip(out["plant"], out["net_generation_mwh"]))
    assert got == {"China Power Hub Generation": 333479.0, "Huaneng Shandong Ruyi": 646752.1}
    assert (out["month"] == "2026-04").all()


def test_non_month_summary_sheet_is_skipped():
    df = _sheet("April 2025", [(27, "Huaneng Shandong Ruyi Energy (Pvt) Ltd", "Coal- Imported", 1320, 1000)])
    df.iloc[3, 2] = "Summary"
    assert parse_sheet(df, source_file="x.xlsx", sheet="FCA-26").empty


def test_parse_sheet_treats_blank_energy_as_zero_not_missing_plant():
    df = _sheet("July 2024", [(2, "Hub Power", "RFO", 1208, None)])
    out = parse_sheet(df, source_file="x.xlsx", sheet="Jul-24")
    assert out.iloc[0]["net_generation_mwh"] == 0.0
