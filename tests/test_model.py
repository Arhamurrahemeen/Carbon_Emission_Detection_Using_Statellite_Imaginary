import numpy as np
import pandas as pd
import pytest

from verify.features import clean_overpasses, monthly_features
from verify.model import (
    FEATURES,
    baseline_capacity,
    evaluate,
    fit,
    gain_pct,
    join_labels,
    loo_predictions,
    predict,
    window_detection,
)
from verify.rules import SITE_PLANTS
from verify.synthetic import make_nepra, make_overpasses

MONTHS = [str(p) for p in pd.period_range("2020-01", "2024-12", freq="M")]


@pytest.fixture(scope="module")
def data():
    feats = monthly_features(clean_overpasses(make_overpasses("sahiwal", MONTHS, seed=3))[0])
    nepra = make_nepra("sahiwal", MONTHS, 1320, seed=3)
    return join_labels(feats, nepra, SITE_PLANTS)


def test_join_labels_sums_plants_and_leaves_missing_as_nan():
    feats = pd.DataFrame({"site_id": ["hub", "hub"], "month": ["2025-01", "2025-02"]})
    nepra = pd.DataFrame({"plant": ["China Power Hub Generation", "The Hub Power Company"],
                          "month": ["2025-01", "2025-01"], "net_generation_mwh": [100000.0, 20000.0]})
    out = join_labels(feats, nepra, SITE_PLANTS)
    assert out.loc[out.month == "2025-01", "generation_gwh"].item() == pytest.approx(120.0)
    assert np.isnan(out.loc[out.month == "2025-02", "generation_gwh"].item())


def test_model_beats_capacity_rule_with_honest_intervals(data):
    m = evaluate(data, holdout=12, capacity_mw=1320, fleet_pf=0.229)
    assert m["n_test"] == 12
    assert 0.5 <= m["coverage_80"] <= 1.0
    assert m["rmse"] < m["baselines"]["capacity_heuristic"]["rmse"]
    assert set(m["baselines"]) == {"capacity_heuristic", "raw_no2_linear", "moving_avg_3_reference"}


def test_prediction_interval_is_ordered_and_non_negative(data):
    model = fit(data.dropna(subset=["generation_gwh"]))
    p = predict(model, data)
    assert (p["interval_low"] <= p["estimate_gwh"]).all() and (p["estimate_gwh"] <= p["interval_high"]).all()
    assert (p["interval_low"] >= 0).all()
    assert set(model) >= {"pipeline", "q80", "train_ranges", "max_monthly_gwh"}
    assert set(model["train_ranges"]) == set(FEATURES)


def test_unlabelled_month_is_predicted_but_never_trained_on(data):
    d = data.copy()
    d.loc[d.index[-1], "generation_gwh"] = np.nan
    m = evaluate(d, holdout=12, capacity_mw=1320, fleet_pf=0.229)
    assert m["n_train"] + m["n_test"] == d["generation_gwh"].notna().sum()
    model = fit(d.dropna(subset=["generation_gwh"]))
    assert not predict(model, d.tail(1)).isna().any().any()


def test_loo_predictions_never_see_their_own_month(data):
    lab = data.dropna(subset=["generation_gwh"]).reset_index(drop=True)
    loo, q80, lag1 = loo_predictions(lab)
    assert len(loo) == len(lab) and q80 > 0 and -1 <= lag1 <= 1
    poisoned = lab.copy()
    poisoned.loc[5, "generation_gwh"] = 1e6  # if month 5 leaked into its own fit, its prediction would explode
    assert loo_predictions(poisoned)[0][5] < 5000


def test_annual_window_detection(data):
    lab = data.dropna(subset=["generation_gwh"]).reset_index(drop=True)
    d = window_detection(lab, window=12)
    assert d["n_windows"] == len(lab) - 11
    assert d["by_scale"]["0.4"] >= 0.9
    assert d["false_alarm_rate"] <= 0.3
    assert set(d) >= {"detection_rate", "false_alarm_rate", "by_scale", "n_windows", "residual_lag1"}


def test_capacity_baseline_and_gain():
    rows = pd.DataFrame({"month": ["2025-04"]})
    assert baseline_capacity(rows, 1320, 0.5)[0] == pytest.approx(1320 * 720 * 0.5 / 1000)
    assert gain_pct(100, 80) == 20.0
