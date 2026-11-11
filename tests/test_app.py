"""Every app page renders from the committed outputs without an exception, and every C04 button works."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py")
PAGES = ["Company check", "Tree contracts", "Reliability (C04)", "Model vs baseline (C07)", "Log"]


@pytest.mark.parametrize("page", PAGES)
def test_page_renders(page):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, at.exception


def test_hub_company_page_renders():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.selectbox[0].set_value("hub").run()
    assert not at.exception, at.exception


def test_every_guard_button():
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value("Reliability (C04)").run()
    for i in range(len(at.button)):
        at.button[i].click().run()
        assert not at.exception, at.exception
