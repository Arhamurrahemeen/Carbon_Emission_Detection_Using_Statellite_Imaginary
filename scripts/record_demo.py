"""Record the backup demo video of the local app, with captions burned in.

Run the app first:  python -m streamlit run app/streamlit_app.py --server.port 8599
Then:               python scripts/record_demo.py [--url http://localhost:8599] [--out demo.mp4]
Needs: pip install playwright; python -m playwright install chromium; ffmpeg on PATH.
"""
import argparse
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

W, H = 1920, 1080

OVERLAY_JS = """
(() => {
  if (document.getElementById('demo-cap')) return;
  const s = document.createElement('style');
  s.textContent = `
    #demo-cap{position:fixed;left:50%;bottom:36px;transform:translateX(-50%);max-width:1400px;
      background:rgba(29,42,47,.92);color:#fff;font:500 26px/1.4 'IBM Plex Sans',system-ui,sans-serif;
      padding:14px 28px;border-radius:6px;z-index:99999;text-align:center;transition:opacity .4s}
    #demo-card{position:fixed;inset:0;background:#F6F4EF;color:#1D2A2F;z-index:100000;display:flex;
      flex-direction:column;align-items:center;justify-content:center;gap:18px;transition:opacity .6s;
      font-family:'IBM Plex Sans',system-ui,sans-serif;text-align:center}
    #demo-card h1{font-size:64px;font-weight:600;margin:0}
    #demo-card p{font-size:28px;color:#5B676C;margin:0;max-width:1300px}`;
  document.head.appendChild(s);
  const c = document.createElement('div'); c.id = 'demo-cap'; c.style.opacity = 0;
  document.body.appendChild(c);
})();
"""


def caption(page, text, hold):
    page.evaluate("""t => { const c = document.getElementById('demo-cap');
        c.style.opacity = 0; setTimeout(() => { c.textContent = t; c.style.opacity = t ? 1 : 0; }, 400); }""", text)
    time.sleep(hold)


def warm_up(page):
    """Scroll the whole page once so Streamlit renders every chart and the map loads its tiles."""
    page.locator(".js-plotly-plot").first.wait_for(timeout=60000)
    for _ in range(12):
        page.evaluate("""() => { window.scrollBy(0, 600); document.querySelectorAll('*').forEach(e => {
            if (e.scrollHeight > e.clientHeight + 50 && getComputedStyle(e).overflowY.match(/auto|scroll/)) e.scrollTop += 600; }); }""")
        time.sleep(0.5)
    time.sleep(3)
    page.evaluate("() => document.querySelectorAll('*').forEach(e => { if (e.scrollTop) e.scrollTop = 0; })")
    time.sleep(3)


def card(page, title, sub, hold, warmup=None):
    page.evaluate("""([t, s]) => { let d = document.getElementById('demo-card');
        if (!d) { d = document.createElement('div'); d.id = 'demo-card'; document.body.appendChild(d); }
        d.innerHTML = `<h1>${t}</h1><p>${s}</p>`; d.style.opacity = 1; }""", [title, sub])
    t0 = time.time()
    if warmup:
        warmup()
    time.sleep(max(hold, 5 - (time.time() - t0)))
    page.evaluate("() => { const d = document.getElementById('demo-card'); d.style.opacity = 0; setTimeout(() => d.remove(), 700); }")
    time.sleep(0.8)


def scroll_to(page, text, block="start"):
    """Smooth-scroll so the element containing `text` sits at the top (or centre) of the screen."""
    page.get_by_text(text, exact=False).first.evaluate(
        f"el => el.scrollIntoView({{behavior: 'smooth', block: '{block}'}})")
    time.sleep(1.5)


def scroll_top(page):
    page.evaluate("() => document.querySelectorAll('*').forEach(e => { if (e.scrollTop) e.scrollTo({top: 0, behavior: 'smooth'}); })")
    time.sleep(1.5)


def open_tab(page, name):
    page.get_by_role("tab", name=name).click()
    time.sleep(2.5)
    page.evaluate(OVERLAY_JS)


def run(url, video_dir):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                                  record_video_dir=video_dir, record_video_size={"width": W, "height": H})
        page = ctx.new_page()
        page.goto(url)
        page.get_by_role("tab", name="Verdict").wait_for(timeout=60000)
        page.evaluate(OVERLAY_JS)
        # Title card covers the page while charts and map tiles load behind it.
        card(page, "Green Claims Check",
             "Checking a company's green claims against what satellites actually see.<br>Team 13 · IU3048 · BattleVerse 2026", 0,
             warmup=lambda: warm_up(page))

        caption(page, "A bank is reviewing a loan to Sahiwal Coal Power Plant (1,320 MW). Are its published figures true?", 5)
        caption(page, "Three numbers for FY2026: our satellite estimate, the official grid meter, and what the company says.", 6)
        caption(page, "The meter is the official grid sales record (CPPA-G). We use it to train and test the satellite. "
                      "Most factories have no public meter, which is why the satellite is needed.", 8)
        scroll_to(page, "Does the company", "center")
        caption(page, "Teal band: the range the satellite supports. The company's figure sits outside it, so: refer for review. "
                      "It flags a mismatch, not wrongdoing.", 8)

        scroll_to(page, "The plant from space")
        caption(page, "Sentinel-5P measures NO2 over the plant on every clear pass. Wind tells us which way the plume blew.", 7)
        caption(page, "Teal column: CO2 estimated from the satellite. Grey: Climate TRACE's model. The ring shows where the plume went.", 7)
        page.get_by_text("Plant and tree contracts").click()
        time.sleep(4)
        caption(page, "The same company claims tree offsets. Arcs run to the farms it pays to plant trees.", 6)

        scroll_to(page, "Each claim, checked")
        caption(page, "Each claim in the report is checked against an independent source, in plain words (challenge C12).", 7)

        scroll_top(page)
        open_tab(page, "Tree contracts")
        caption(page, "Sentinel-2 checks every tree plot. Green: trees seen alive. Grey: no trees seen.", 6)
        caption(page, "The factory pays the farmer only for trees the satellite sees alive. The rest is held.", 6)

        open_tab(page, "Reliability (C04)")
        caption(page, "Impossible or weak inputs are refused with a reason, never answered with a confident number (challenge C04).", 8)

        open_tab(page, "Model test (C07)")
        caption(page, "Tested on 9 months the model never saw: 61.7% lower error than the capacity rule, 30.4% lower than raw NO2 (challenge C07).", 8)
        caption(page, "FY2026: satellite 5,896 GWh vs meter 6,138 GWh, 3.9% low.", 6)
        scroll_to(page, "Tree check: random forest")
        caption(page, "Tree classifier: 11.6% better than a greenness threshold, short of our 15% target. We report it as it is.", 7)
        caption(page, "", 0.5)

        card(page, "Free satellite data. Any plant in Pakistan.",
             "Sentinel-5P · Sentinel-2 · ERA5 wind · CPPA-G metered sales<br>Team 13 · IU3048", 5)
        video = page.video.path()
        ctx.close()
        browser.close()
    return Path(video)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://localhost:8599")
    ap.add_argument("--out", default="demo.mp4")
    a = ap.parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg not found on PATH. Install it and open a new terminal.")
    with tempfile.TemporaryDirectory() as tmp:
        webm = run(a.url, tmp)
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-i", str(webm), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out)
