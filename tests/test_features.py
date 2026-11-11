import numpy as np
import pandas as pd
import pytest

from verify.features import clean_overpasses, monthly_features
from verify.rules import SITE_PLANTS
from verify.synthetic import make_nepra, make_overpasses

MONTHS = [str(p) for p in pd.period_range("2021-01", "2025-12", freq="M")]


def _row(**kw):
    base = dict(site_id="sahiwal", date="2024-01-05", no2_down=5e-5, no2_up=3e-5, no2_raw=4e-5,
                wind_u=2.0, wind_v=2.0, wind_speed=4.0, wind_dir=45.0, cloud_fraction=0.1, n_pixels=20)
    base.update(kw)
    return base


def test_clean_keeps_noise_rejects_bad_drops_calm():
    df = pd.DataFrame([_row(no2_up=-0.00002), _row(wind_speed=-8.0), _row(wind_speed=0.5)])
    kept, rejected = clean_overpasses(df)
    assert len(kept) == 1 and kept.iloc[0]["no2_up"] == -0.00002
    assert len(rejected) == 1 and "E_WEATHER_RANGE" in rejected.iloc[0]["reason_codes"]


def test_monthly_flux_proxy_is_enhancement_times_wind():
    df = pd.DataFrame([
        _row(date="2024-01-01", no2_down=4e-5, no2_up=3e-5, wind_speed=2.0),
        _row(date="2024-01-02", no2_down=5e-5, no2_up=3e-5, wind_speed=4.0),
        _row(date="2024-01-03", no2_down=6e-5, no2_up=3e-5, wind_speed=6.0),
    ])
    m = monthly_features(clean_overpasses(df)[0])
    row = m.iloc[0]
    assert row["month"] == "2024-01" and row["valid_overpasses"] == 3
    assert row["enh_mean"] == pytest.approx(2e-5)
    assert row["flux_proxy"] == pytest.approx((2e-5 + 8e-5 + 18e-5) / 3)
    assert row["month_sin"] == pytest.approx(np.sin(2 * np.pi * 1 / 12))


def test_synthetic_is_labelled_and_tracks_generation():
    ov = make_overpasses("sahiwal", MONTHS, seed=1)
    assert (ov["data_flags"] == "synthetic").all()
    m = monthly_features(clean_overpasses(ov)[0])
    assert m["synthetic"].all()
    nepra = make_nepra("sahiwal", MONTHS, 1320, seed=1)
    assert set(nepra["plant"]) == set(SITE_PLANTS["sahiwal"])
    gen = nepra.groupby("month")["net_generation_mwh"].sum()
    joined = m.set_index("month").join(gen, how="inner")
    assert joined["flux_proxy"].corr(joined["net_generation_mwh"]) > 0.6


def test_synthetic_monsoon_has_few_overpasses():
    m = monthly_features(clean_overpasses(make_overpasses("sahiwal", MONTHS, seed=2))[0])
    aug = m[m["month"].str.endswith("-08")]["valid_overpasses"]
    jan = m[m["month"].str.endswith("-01")]["valid_overpasses"]
    assert aug.max() < 5 <= jan.min()


def test_hub_nepra_has_both_plants():
    nepra = make_nepra("hub", MONTHS[:3], 2612, seed=0)
    assert set(nepra["plant"]) == set(SITE_PLANTS["hub"])
