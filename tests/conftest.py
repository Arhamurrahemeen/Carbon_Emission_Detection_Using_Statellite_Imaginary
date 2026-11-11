import pandas as pd
import pytest


@pytest.fixture
def sites():
    return pd.DataFrame(
        [
            {"site_id": "sahiwal", "lat": 30.7142, "lon": 73.2380, "capacity_mw": 1320, "ef_low": 0.80, "ef_high": 0.95},
            {"site_id": "hub", "lat": 24.9147, "lon": 66.6888, "capacity_mw": 2612, "ef_low": 0.80, "ef_high": 0.95},
        ]
    )
