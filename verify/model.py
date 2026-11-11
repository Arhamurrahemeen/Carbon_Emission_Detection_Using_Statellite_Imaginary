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


def loo_predictions(lab: pd.DataFrame) -> tuple[np.ndarray, float, float]:
    """Leave-one-out: each month predicted by a model fitted without it. Returns (predictions, q80, lag-1
    autocorrelation of the residuals in time order)."""
    lab = lab.sort_values("month").reset_index(drop=True)
    X, y = lab[FEATURES].to_numpy(), lab["generation_gwh"].to_numpy()
    preds = np.empty(len(lab))
    for i in range(len(lab)):
        keep = np.arange(len(lab)) != i
        preds[i] = max(0.0, _pipeline().fit(X[keep], y[keep]).predict(X[i:i + 1])[0])
    res = y - preds
    lag1 = float(np.corrcoef(res[:-1], res[1:])[0, 1]) if len(res) > 3 else 0.0
    return preds, float(np.quantile(np.abs(res), RULES["interval_level"])), lag1


def window_detection(lab: pd.DataFrame, window: int = 12, scales=(0.8, 0.6, 0.4, 1.0)) -> dict:
    """Annual-claim test on rolling 12-month windows of leave-one-out estimates. Monthly errors are combined in
    quadrature, inflated for positive autocorrelation (effective sample size), so a year is judged honestly."""
    lab = lab.sort_values("month").reset_index(drop=True)
    preds, q80, lag1 = loo_predictions(lab)
    inflate = (1 + lag1) / (1 - lag1) if 0 < lag1 < 0.95 else 1.0
    half = q80 * np.sqrt(window * inflate)
    hits = {s: [] for s in scales}
    for start in range(len(lab) - window + 1):
        est = preds[start:start + window].sum()
        actual = lab["generation_gwh"].iloc[start:start + window].sum()
        lo, hi = max(0.0, est - half), est + half
        for s in scales:
            hits[s].append(not (lo <= actual * s <= hi))
    mis = [h for s in scales if s < 1 for h in hits[s]]
    return {"n_windows": len(lab) - window + 1, "window_months": window, "half_width_gwh": float(half),
            "detection_rate": float(np.mean(mis)) if mis else None,
            "false_alarm_rate": float(np.mean(hits[1.0])) if 1.0 in hits and hits[1.0] else None,
            "by_scale": {str(s): float(np.mean(hits[s])) for s in scales if s < 1},
            "residual_lag1": lag1, "q80_monthly_gwh": q80}


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
