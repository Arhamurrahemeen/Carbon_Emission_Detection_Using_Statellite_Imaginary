"""One output record per request. Status comes from reason codes: E_ rejects, W_ lowers confidence."""
import itertools
from datetime import datetime, timezone

_counter = itertools.count(1)

# Never present on a REJECTED record: nothing was estimated.
ESTIMATE_FIELDS = (
    "estimate_gwh", "interval_low", "interval_high", "co2_low_t", "co2_high_t",
    "verdict", "gap_pct", "valid_overpasses",
)


def status_for(codes: list[str]) -> str:
    if any(c.startswith("E_") for c in codes):
        return "REJECTED"
    if any(c.startswith("W_") for c in codes):
        return "LOW_CONFIDENCE"
    return "OK"


def make_record(kind: str, codes: list[str], message: str, **fields) -> dict:
    status = status_for(codes)
    record = {
        "request_id": f"r-{next(_counter):04d}",
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "kind": kind,
        "status": status,
        "reason_codes": list(codes),
        "message": message,
        **fields,
    }
    if status == "REJECTED":
        for f in ESTIMATE_FIELDS:
            record.pop(f, None)
    return record
