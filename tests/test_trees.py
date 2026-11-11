import pandas as pd

from verify.trees import payout, verified_trees, verify_pass

LATEST = "2026-11-10"


def test_impossible_ndvi_is_invalid():
    assert verify_pass({"date": "2026-08-10", "ndvi": 1.8, "cloud": 0.0}, LATEST, 0.9) == ("invalid", ["E_NDVI_RANGE"])


def test_impossible_cloud_is_invalid():
    assert verify_pass({"date": "2026-08-10", "ndvi": 0.5, "cloud": 1.4}, LATEST, 0.9) == ("invalid", ["E_SAT_RANGE"])


def test_cloudy_waits():
    assert verify_pass({"date": "2026-08-10", "ndvi": 0.6, "cloud": 0.9}, LATEST, 0.9) == ("cloudy", ["W_CLOUDY"])


def test_future_or_missing_image_is_pending():
    assert verify_pass({"date": "2027-02-10"}, LATEST, None) == ("no_imagery", ["W_NO_IMAGERY"])
    assert verify_pass({"date": "2026-08-10", "ndvi": None, "cloud": None}, LATEST, None) == ("no_imagery", ["W_NO_IMAGERY"])


def test_classifier_decides_alive_or_not():
    assert verify_pass({"date": "2026-08-10", "ndvi": 0.5, "cloud": 0.1}, LATEST, 0.8) == ("verified", [])
    assert verify_pass({"date": "2026-08-10", "ndvi": 0.5, "cloud": 0.1}, LATEST, 0.2) == ("failed", [])


def test_payouts():
    assert payout(1200, "verified") == {"released": 120000.0, "held": 0.0}  # factory pays the farmer, only for living trees
    assert payout(1200, "failed")["held"] == 120000.0
    assert payout(1200, "invalid")["held"] == 120000.0
    assert payout(1200, "cloudy") == {"released": 0.0, "held": 0.0}


def test_verified_trees_counts_only_verified_plots():
    plots = pd.DataFrame({"plot_id": ["a", "b", "c"], "trees_planted": [1000, 2000, 500]})
    assert verified_trees(plots, {"a": "verified", "b": "failed", "c": "verified"}) == 1500
