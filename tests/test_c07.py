import numpy as np
import pandas as pd
import pytest

from verify.c07 import TREE_FEATURES, benchmark, classify, f1, threshold_baseline, train_tree_model


def _samples(n=400, seed=0):
    """Trees stay green all year (high NDVI p10). Crops are green in ONE quarter only, so a single-image
    threshold confuses them with trees; a year of features does not."""
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        tree = i % 2 == 0
        crop_q = rng.integers(0, 4)
        q = [rng.uniform(0.45, 0.7) if tree else (rng.uniform(0.5, 0.8) if k == crop_q else rng.uniform(0.1, 0.25))
             for k in range(4)]
        p10 = rng.uniform(0.35, 0.5) if tree else rng.uniform(0.05, 0.2)
        row = {f: rng.normal(0.2, 0.05) for f in TREE_FEATURES}
        row.update({"label": int(tree), "ndvi_p10": p10, "mean": float(np.mean(q)),
                    "q1": q[0], "q2": q[1], "q3": q[2], "q4": q[3],
                    "split": "train" if i < int(n * 0.7) else "test", "lon": 67 + i * 1e-3, "lat": 25.0})
        rows.append(row)
    return pd.DataFrame(rows)


def test_f1_perfect_and_empty():
    assert f1([1, 0, 1], [1, 0, 1]) == 1.0
    assert f1([0, 0], [0, 0]) == 0.0


def test_forest_beats_single_threshold_on_crop_confusion():
    r = benchmark(_samples(), hand=None)
    t = r["test"]
    assert t["rf_f1"] > t["baseline_tuned_f1"]
    assert t["gain_vs_tuned_pct"] == pytest.approx((t["rf_f1"] - t["baseline_tuned_f1"]) / t["baseline_tuned_f1"] * 100, abs=0.1)
    assert r["hand"] is None and r["n_train"] == 280 and r["n_test"] == 120


def test_threshold_baseline_reports_tuned_and_fixed():
    s = _samples()
    b = threshold_baseline(s[s.split == "train"], s[s.split == "test"])
    assert 0.10 <= b["tuned"]["threshold"] <= 0.80
    assert set(b) == {"tuned", "fixed_035"}


def test_hand_labels_scored_separately():
    s = _samples()
    hand = s[s.split == "test"].head(30)[["lon", "lat", "label"]].copy()
    hand_rows = s[s.split == "test"].head(30).assign(split="hand")
    r = benchmark(pd.concat([s, hand_rows]), hand=hand)
    assert r["hand"] is not None and r["hand"]["n"] == 30


def test_classify_returns_probabilities():
    s = _samples()
    m = train_tree_model(s[s.split == "train"])
    p = classify(m, s[s.split == "test"])
    assert p.shape == (120,) and ((p >= 0) & (p <= 1)).all()
