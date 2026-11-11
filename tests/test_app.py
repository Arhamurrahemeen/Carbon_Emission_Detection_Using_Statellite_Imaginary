"""Every tab renders from the committed outputs without an exception, for both plants, and every C04 button works."""
from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")


def test_all_tabs_render_for_both_plants():
    at = AppTest.from_file(APP, default_timeout=90).run()
    assert not at.exception, at.exception
    assert len(at.tabs) == 5
    at.selectbox[0].set_value("hub").run()
    assert not at.exception, at.exception


def test_contracts_view_and_plain_map():
    at = AppTest.from_file(APP, default_timeout=90).run()
    at.radio[0].set_value("Plant and tree contracts").run()
    at.toggle[0].set_value(False).run()
    assert not at.exception, at.exception


def test_every_guard_button():
    at = AppTest.from_file(APP, default_timeout=90).run()
    for i in range(len(at.button)):
        at.button[i].click().run()
        assert not at.exception, at.exception


def test_plume_rose_puts_the_plume_where_the_wind_blows():
    import sys
    import pandas as pd
    sys.path.insert(0, str(Path(APP).parent))
    import charts
    lat, lon = 30.0, 73.0
    ne = pd.DataFrame({"lat": [lat + 0.06] * 5 + [lat - 0.09], "lon": [lon + 0.07] * 5 + [lon], "enhancement": [2e-5] * 5 + [1e-5]})
    r = charts.plume_rose(ne, lat, lon)
    assert len(r) == 16 and r.loc[r["h"].idxmax(), "name"] == "Plume towards NE"
