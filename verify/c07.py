"""C07 (heuristic baseline showdown) for the tree check: random forest on a year of Sentinel-2 features vs a single
NDVI threshold on one quarterly image. The baseline gets its best threshold (tuned on training points) and the
0.35 the Shajar demo used. Scored on the WorldCover test split and, separately, on the team's hand labels:
WorldCover is itself a Sentinel-2 model, so beating it on its own labels is partly circular."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

TREE_FEATURES = ["ndvi_p10", "ndvi_p25", "ndvi_p50", "ndvi_p75", "ndvi_p90", "ndvi_stdDev", "mean",
                 "B2", "B3", "B4", "B8", "B11", "B12", "ndmi"]
QUARTERS = ("q1", "q2", "q3", "q4")


def f1(y_true, y_pred) -> float:
    return float(f1_score(y_true, y_pred, zero_division=0))


def train_tree_model(train: pd.DataFrame) -> RandomForestClassifier:
    return RandomForestClassifier(n_estimators=200, random_state=7, class_weight="balanced").fit(train[TREE_FEATURES], train["label"])


def classify(model, rows: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(rows[TREE_FEATURES])[:, 1]


def _quarter_f1(df, t) -> float:
    return float(np.mean([f1(df["label"], (df[q] >= t).astype(int)) for q in QUARTERS]))


def threshold_baseline(train: pd.DataFrame, test: pd.DataFrame) -> dict:
    grid = np.round(np.arange(0.10, 0.801, 0.01), 2)
    best = max(grid, key=lambda t: _quarter_f1(train, t))
    return {"tuned": {"threshold": float(best), "f1": _quarter_f1(test, best)},
            "fixed_035": {"f1": _quarter_f1(test, 0.35)}}


def _gain(a, b) -> float | None:
    return round((a - b) / b * 100, 1) if b else None


def _score(model, train, rows) -> dict:
    rf = f1(rows["label"], (classify(model, rows) >= 0.5).astype(int))
    base = threshold_baseline(train, rows)
    return {"n": int(len(rows)), "rf_f1": rf, "baseline_tuned_f1": base["tuned"]["f1"],
            "baseline_threshold": base["tuned"]["threshold"], "baseline_fixed_f1": base["fixed_035"]["f1"],
            "gain_vs_tuned_pct": _gain(rf, base["tuned"]["f1"]), "gain_vs_fixed_pct": _gain(rf, base["fixed_035"]["f1"])}


def benchmark(samples: pd.DataFrame, hand: pd.DataFrame | None) -> dict:
    train, test = samples[samples["split"] == "train"], samples[samples["split"] == "test"]
    model = train_tree_model(train)
    out = {"test": _score(model, train, test), "hand": None, "n_train": int(len(train)), "n_test": int(len(test)),
           "answer_key": "ESA WorldCover v200 tree class + team hand labels"}
    if hand is not None and len(hand):
        pts = samples[samples["split"] == "hand"].drop(columns="label").round({"lon": 5, "lat": 5})
        lab = hand.round({"lon": 5, "lat": 5})[["lon", "lat", "label"]]
        rows = pts.merge(lab, on=["lon", "lat"], how="inner")
        if len(rows):
            out["hand"] = _score(model, train, rows)
    return out
