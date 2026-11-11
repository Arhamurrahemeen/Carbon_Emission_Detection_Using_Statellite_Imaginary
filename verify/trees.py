"""Tree-offset plots: quarterly satellite pass -> verified / failed / cloudy / no_imagery / invalid, and payouts.
Money moves only on a verified pass. The tree/not-tree probability comes from the C07 classifier (verify.c07)."""
import math

import pandas as pd

from verify.gate import check_cloud, check_ndvi
from verify.rules import RULES


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and math.isnan(v))


def verify_pass(row: dict, latest_imagery: str, tree_prob: float | None) -> tuple[str, list[str]]:
    ndvi, cloud = row.get("ndvi"), row.get("cloud")
    if str(row["date"]) > latest_imagery or (_blank(ndvi) and _blank(cloud)):
        return "no_imagery", ["W_NO_IMAGERY"]
    bad = check_ndvi(ndvi) + check_cloud(cloud)
    if bad:
        return "invalid", bad
    if cloud > RULES["max_plot_cloud"]:
        return "cloudy", ["W_CLOUDY"]
    if tree_prob is None:
        return "no_imagery", ["W_NO_IMAGERY"]  # no classifier features for this pass yet
    return ("verified", []) if tree_prob >= RULES["tree_prob"] else ("failed", [])


def payout(trees: int, status: str) -> dict:
    due = float(trees * RULES["price_per_tree_year"] / RULES["passes_per_year"])
    zero = {"released": 0.0, "held": 0.0}
    if status == "verified":
        return {"released": due, "held": 0.0}  # the factory pays the farmer, only for trees seen alive
    if status in ("failed", "invalid"):
        return {**zero, "held": due}
    return zero


def verified_trees(plots: pd.DataFrame, latest_status: dict[str, str]) -> int:
    ok = plots["plot_id"].map(latest_status).eq("verified")
    return int(plots.loc[ok, "trees_planted"].sum())
