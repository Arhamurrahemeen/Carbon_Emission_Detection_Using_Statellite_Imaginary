"""Activity model: monthly plume features -> monthly generation (GWh) with an 80% interval.
Ridge regression fitted to each plant's metered generation (CPPA-G / NEPRA). The interval is split-conformal:
estimate +- the 80th percentile of absolute out-of-fold residuals.

C07 pollution baselines: a capacity rule of thumb (what a bank uses today) and a naive linear fit on raw plant NO2.
A 3-month moving average of past metered generation is reported for reference only: it uses the reported data we
are trying to check, so it is not a fair baseline for verification."""
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from verify.rules import RULES

FEATURES = ["flux_proxy", "enh_mean", "valid_overpasses", "wind_mean", "month_sin", "month_cos"]


def join_labels(features: pd.DataFrame, labels: pd.DataFrame, site_map: dict[str, list[str]]) -> pd.DataFrame:
    plant_to_site = {p: s for s, plants in site_map.items() for p in plants}
    lab = labels.assign(site_id=labels["plant"].map(plant_to_site)).dropna(subset=["site_id"])
    gwh = (lab.groupby(["site_id", "month"])["net_generation_mwh"].sum(min_count=1) / 1000).rename("generation_gwh")
    return features.merge(gwh.reset_index(), on=["site_id", "month"], how="left")


def _pipeline():
    return make_pipeline(StandardScaler(), RidgeCV(alphas=np.logspace(-3, 3, 13)))


def _oof_residuals(train: pd.DataFrame) -> np.ndarray:
    n_splits = max(2, min(5, len(train) // 6))
    res = []
    for tr, te in TimeSeriesSplit(n_splits=n_splits).split(train):
        p = _pipeline().fit(train.iloc[tr][FEATURES], train.iloc[tr]["generation_gwh"])
        res.extend(np.abs(train.iloc[te]["generation_gwh"] - p.predict(train.iloc[te][FEATURES])))
    return np.asarray(res)


def fit(train: pd.DataFrame) -> dict:
    train = train.sort_values("month").dropna(subset=FEATURES + ["generation_gwh"])
    return {
        "pipeline": _pipeline().fit(train[FEATURES], train["generation_gwh"]),
        "q80": float(np.quantile(_oof_residuals(train), RULES["interval_level"])),
        "train_ranges": {f: (float(train[f].min()), float(train[f].max())) for f in FEATURES},
        "max_monthly_gwh": float(train["generation_gwh"].max()),
        "n_train": int(len(train)),
    }


def predict(model: dict, rows: pd.DataFrame) -> pd.DataFrame:
    est = np.clip(model["pipeline"].predict(rows[FEATURES]), 0, None)
    return pd.DataFrame({
        "estimate_gwh": est,
        "interval_low": np.clip(est - model["q80"], 0, None),
        "interval_high": est + model["q80"],
    }, index=rows.index)


def _hours(months: pd.Series) -> np.ndarray:
    return np.array([pd.Period(m, freq="M").days_in_month * 24 for m in months])


def baseline_capacity(rows: pd.DataFrame, capacity_mw: float, fleet_pf: float) -> np.ndarray:
    return capacity_mw * _hours(rows["month"]) * fleet_pf / 1000


def baseline_raw_linear(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    lr = LinearRegression().fit(train[["raw_mean"]], train["generation_gwh"])
    return np.clip(lr.predict(test[["raw_mean"]]), 0, None)


def gain_pct(baseline_rmse: float, primary_rmse: float) -> float:
    return round((baseline_rmse - primary_rmse) / baseline_rmse * 100, 1)


def _rmse(y, p) -> float:
    return float(np.sqrt(np.mean((np.asarray(y) - np.asarray(p)) ** 2)))


def evaluate(data: pd.DataFrame, holdout: int, capacity_mw: float, fleet_pf: float) -> dict:
    lab = data.dropna(subset=FEATURES + ["generation_gwh"]).sort_values("month").reset_index(drop=True)
    train, test = lab.iloc[:-holdout], lab.iloc[-holdout:]
    model = fit(train)
    pred = predict(model, test)
    y = test["generation_gwh"].to_numpy()
    rmse = _rmse(y, pred["estimate_gwh"])
    nonzero = y > 1
    cap = _rmse(y, baseline_capacity(test, capacity_mw, fleet_pf))
    raw = _rmse(y, baseline_raw_linear(train, test))
    ma = lab["generation_gwh"].rolling(3).mean().shift(1).iloc[-holdout:]
    return {
        "n_train": int(len(train)), "n_test": int(len(test)),
        "test_months": [test["month"].iloc[0], test["month"].iloc[-1]],
        "rmse": rmse,
        "mae": float(np.mean(np.abs(y - pred["estimate_gwh"]))),
        "mape_nonzero": float(np.mean(np.abs(y[nonzero] - pred["estimate_gwh"].to_numpy()[nonzero]) / y[nonzero]) * 100)
        if nonzero.any() else None,
        "r": float(np.corrcoef(y, pred["estimate_gwh"])[0, 1]) if len(y) > 2 else None,
        "coverage_80": float(np.mean((y >= pred["interval_low"]) & (y <= pred["interval_high"]))),
        "q80_gwh": model["q80"],
        "baselines": {
            "capacity_heuristic": {"rmse": cap},
            "raw_no2_linear": {"rmse": raw},
            "moving_avg_3_reference": {"rmse": _rmse(y[ma.notna().to_numpy()], ma.dropna())},
        },
        "gain_vs_capacity_pct": gain_pct(cap, rmse),
        "gain_vs_raw_pct": gain_pct(raw, rmse),
    }
