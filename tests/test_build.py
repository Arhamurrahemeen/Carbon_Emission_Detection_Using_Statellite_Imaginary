import json
import shutil
from pathlib import Path

import pandas as pd

from verify.build import build, claim_detection

REPO = Path(__file__).resolve().parents[1]
OUTPUTS = ["monthly.csv", "verdicts.csv", "cross_checks.csv", "tree_passes.csv", "guard_results.csv", "metrics.json"]


def _fresh_root(tmp_path: Path) -> Path:
    (tmp_path / "data" / "manual").mkdir(parents=True)
    for f in ("sites.csv", "plots.csv", "assumptions.csv"):
        shutil.copy(REPO / "data" / "manual" / f, tmp_path / "data" / "manual" / f)
    return tmp_path


def test_build_on_empty_data_is_fully_synthetic_and_complete(tmp_path):
    root = _fresh_root(tmp_path)
    metrics = build(root)
    for f in OUTPUTS:
        assert (root / "outputs" / f).exists(), f
    m = json.loads((root / "outputs" / "metrics.json").read_text())
    assert m["sources"]["overpasses_sahiwal"] == "synthetic"
    assert m["sources"]["labels"] == "synthetic"
    assert metrics["pollution"]["sahiwal"]["n_test"] > 0
    v = pd.read_csv(root / "outputs" / "verdicts.csv")
    assert v["status"].isin(["OK", "LOW_CONFIDENCE", "REJECTED"]).all()
    emissions = v[v["kind"] == "emissions"]
    assert emissions["data_flags"].str.contains("synthetic").all()
    g = pd.read_csv(root / "outputs" / "guard_results.csv")
    assert len(g) == 8 and (g["passed"]).all()


def test_claim_detection_rates():
    recs = [
        {"kind": "emissions", "status": "OK", "verdict": "INCONSISTENT", "claim_scale": 0.6},
        {"kind": "emissions", "status": "OK", "verdict": "INCONSISTENT", "claim_scale": 0.8},
        {"kind": "emissions", "status": "OK", "verdict": "CONSISTENT", "claim_scale": 1.0},
        {"kind": "emissions", "status": "LOW_CONFIDENCE", "verdict": "CANNOT_VERIFY", "claim_scale": 0.4},
    ]
    d = claim_detection(recs)
    assert d["detection_rate"] == 1.0 and d["false_alarm_rate"] == 0.0
    assert d["by_scale"]["0.6"] == 1.0 and d["n_misstated"] == 2 and d["n_true"] == 1
