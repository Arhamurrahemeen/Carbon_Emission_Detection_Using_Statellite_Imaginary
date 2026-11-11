"""Load every input. Any real file that is missing is replaced by a labelled stand-in, and `sources` says which
(real / synthetic / shajar_export). Nothing here touches the network."""
from pathlib import Path
import zlib

import pandas as pd

from verify import synthetic

SATELLITE_MONTHS = [str(p) for p in pd.period_range("2018-07", "2026-09", freq="M")]


def _csv(path: Path) -> pd.DataFrame | None:
    if path.exists() and path.stat().st_size > 0:
        df = pd.read_csv(path)
        return df if len(df) else None
    return None


def load_inputs(root: Path) -> dict:
    root = Path(root)
    manual, raw = root / "data" / "manual", root / "data" / "raw"
    sites = pd.read_csv(manual / "sites.csv")
    sources, overpasses = {}, {}
    for s in sites.itertuples():
        df = _csv(raw / f"overpasses_{s.site_id}.csv")
        sources[f"overpasses_{s.site_id}"] = "real" if df is not None else "synthetic"
        overpasses[s.site_id] = df if df is not None else synthetic.make_overpasses(s.site_id, SATELLITE_MONTHS, seed=zlib.crc32(s.site_id.encode()) % 100)
    labels = _csv(raw / "generation_monthly.csv")
    passes = _csv(raw / "plot_passes.csv")
    samples = _csv(raw / "c07_samples.csv")
    claims = _csv(manual / "claims.csv")
    sources.update({
        "labels_file": "real" if labels is not None else "missing",
        "plot_passes": "real" if passes is not None else "shajar_export",
        "c07_samples": "real" if samples is not None else "synthetic",
        "claims": "real" if claims is not None else "synthetic",
    })
    return {
        "sites": sites,
        "overpasses": overpasses,
        "real_labels": labels,
        "plots": pd.read_csv(manual / "plots.csv"),
        "plot_passes": passes if passes is not None else synthetic.shajar_plot_passes(),
        "c07_samples": samples if samples is not None else synthetic.make_c07_samples(),
        "c07_hand": _csv(raw / "c07_hand_labels.csv"),
        "climate_trace": _csv(raw / "climate_trace.csv"),
        "claims": claims,
        "assumptions_path": manual / "assumptions.csv",
        "sources": sources,
    }
