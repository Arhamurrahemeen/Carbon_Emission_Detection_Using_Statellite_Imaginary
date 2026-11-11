"""Charts and the 3D map. Colours and rules come from DESIGN.md."""
import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk

INK, INK_SOFT, RULE, PAPER = "#1D2A2F", "#5B676C", "#E2DDD3", "#F6F4EF"
SAT, SAT_BRIGHT, FLAG, WARN, OK, MODEL = "#0F6B75", "#3FC6CF", "#B3261E", "#A15C00", "#2E6B3A", "#8A8F98"
FONT = "IBM Plex Sans, system-ui, sans-serif"

# Sentinel-2 cloudless mosaic by EOX (CC BY-NC-SA 4.0), draped on AWS Terrain Tiles. No API key needed.
S2_TILES = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2023_3857/default/g/{z}/{y}/{x}.jpg"
TERRAIN = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
ATTRIBUTION = "Imagery: Sentinel-2 cloudless by EOX IT Services (contains modified Copernicus Sentinel data). Terrain: AWS Terrain Tiles."


def _layout(fig, height, title=None):
    fig.update_layout(height=height, margin={"l": 8, "r": 8, "t": 40 if title else 8, "b": 8}, title=title,
                      title_font={"size": 15, "color": INK}, font={"family": FONT, "color": INK, "size": 13},
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      legend={"orientation": "h", "y": -0.18, "x": 0})
    fig.update_xaxes(gridcolor=RULE, zeroline=False)
    fig.update_yaxes(gridcolor=RULE, zeroline=False)
    return fig


def range_plot(est: dict, claim: float | None, metered: float | None, trace: float | None, period: str):
    """The proof: where the company's figure sits against what the satellite supports."""
    lo, hi, mid = est["interval_low"], est["interval_high"], est["estimate_gwh"]
    fig = go.Figure()
    fig.add_shape(type="rect", x0=lo, x1=hi, y0=-0.32, y1=0.32, fillcolor="rgba(15,107,117,0.16)", line={"color": SAT, "width": 1})
    fig.add_trace(go.Scatter(x=[mid], y=[0], mode="markers", marker={"symbol": "line-ns", "size": 30, "line": {"width": 3, "color": SAT}},
                             name=f"Satellite estimate {mid:,.0f} (80% range {lo:,.0f}–{hi:,.0f})"))
    if metered is not None:
        fig.add_trace(go.Scatter(x=[metered], y=[0], mode="markers", marker={"symbol": "diamond", "size": 13, "color": INK},
                                 name=f"Metered sales to the grid {metered:,.0f}"))
    if trace is not None:
        fig.add_trace(go.Scatter(x=[trace], y=[0], mode="markers", marker={"symbol": "circle-open", "size": 14, "line": {"width": 2, "color": MODEL}},
                                 name=f"Climate TRACE model {trace:,.0f} (calendar year)"))
    if claim is not None:
        inside = lo <= claim <= hi
        fig.add_trace(go.Scatter(x=[claim], y=[0], mode="markers", marker={"size": 16, "color": OK if inside else FLAG},
                                 name=f"Company says {claim:,.0f}"))
    xs = [v for v in (lo, hi, claim, metered, trace) if v is not None]
    pad = (max(xs) - min(xs)) * 0.12 + 1
    fig.update_xaxes(range=[max(0, min(xs) - pad), max(xs) + pad], title=None, ticksuffix=" GWh")
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig = _layout(fig, 230, f"{period}: does the company's figure fall inside what the satellite supports?")
    fig.update_layout(legend={"y": -0.35})
    return fig


def timeline(mon: pd.DataFrame, shutdowns: list[str]):
    fig = go.Figure()
    if "metered_gwh" in mon and mon["metered_gwh"].notna().any():
        fig.add_trace(go.Bar(x=mon["month"], y=mon["metered_gwh"], name="Metered sales to the grid (CPPA-G)", marker_color=INK, opacity=0.78))
    fig.add_trace(go.Scatter(x=mon["month"], y=mon["interval_high"], line={"width": 0}, showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=mon["month"], y=mon["interval_low"], fill="tonexty", fillcolor="rgba(15,107,117,0.16)",
                             line={"width": 0}, name="Satellite 80% range", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=mon["month"], y=mon["estimate_gwh"], name="Satellite estimate", line={"color": SAT, "width": 2.5}))
    thin = mon[mon["reason_codes"].fillna("").str.contains("W_FEW_OBS")]["month"]
    for m in thin:
        fig.add_vrect(x0=m, x1=m, line_width=7, line_color="rgba(161,92,0,0.18)")
    for m in shutdowns:
        if m in set(mon["month"]):
            fig.add_annotation(x=m, y=0, text="plant off", showarrow=True, arrowhead=0, ay=-34, font={"size": 11, "color": FLAG})
    fig.update_yaxes(title="GWh per month")
    return _layout(fig, 340, "Month by month: what the meter recorded and what the satellite saw")


def error_bars(p: dict):
    rows = [("Rule of thumb: plants run at 23% of capacity", p["baselines"]["capacity_heuristic"]["rmse"], MODEL),
            ("Raw satellite reading, no wind correction", p["baselines"]["raw_no2_linear"]["rmse"], MODEL),
            ("Our model: wind-corrected satellite plume", p["rmse"], SAT)]
    fig = go.Figure(go.Bar(x=[r[1] for r in rows], y=[r[0] for r in rows], orientation="h", marker_color=[r[2] for r in rows],
                           text=[f"{r[1]:,.0f} GWh" for r in rows], textposition="outside"))
    fig.update_xaxes(title="Typical monthly miss on months the model never saw (lower is better)", range=[0, max(r[1] for r in rows) * 1.25])
    fig.update_yaxes(autorange="reversed")
    return _layout(fig, 230)


def _view(lat, lon, zoom, pitch=50, bearing=-18):
    return pdk.ViewState(latitude=lat, longitude=lon, zoom=zoom, pitch=pitch, bearing=bearing)


def _rgb(hex_, a=230):
    h = hex_.lstrip("#")
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)] + [a]


def plume_rose(plume: pd.DataFrame, lat: float, lon: float, sectors: int = 16, km: float = 10.0) -> pd.DataFrame:
    """Sum the plant's own NO2 by wind direction: one column per compass sector, 10 km out, tallest where the plume goes most."""
    import numpy as np
    dy = (plume["lat"] - lat) * 111.32
    dx = (plume["lon"] - lon) * 111.32 * np.cos(np.radians(lat))
    sec = (np.round(np.degrees(np.arctan2(dx, dy)) % 360 / (360 / sectors)) % sectors).astype(int)
    tot = plume.assign(sec=sec).groupby("sec").agg(e=("enhancement", "sum"), n=("enhancement", "size")).reindex(range(sectors), fill_value=0)
    share = tot["e"] / tot["e"].sum() if tot["e"].sum() else tot["e"]
    b = np.radians(tot.index * 360 / sectors)
    names = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    return pd.DataFrame({
        "lat": lat + km * np.cos(b) / 111.32, "lon": lon + km * np.sin(b) / (111.32 * np.cos(np.radians(lat))),
        "h": 300 + 4500 * share / share.max() if share.max() else 300,
        "color": [_rgb(SAT_BRIGHT, int(90 + 165 * v / share.max())) if share.max() else _rgb(SAT_BRIGHT, 90) for v in share],
        "name": [f"Plume towards {names[i]}" for i in tot.index],
        "label": [f"{v * 100:.0f}% of the plant's NO2 over 24 months · {int(n)} satellite passes" for v, n in zip(share, tot["n"])],
    })


def map_deck(site: dict, plume: pd.DataFrame, co2_t: float | None, trace_t: float | None,
             plots: pd.DataFrame | None, mode: str, satellite: bool) -> pdk.Deck:
    lat, lon = float(site["lat"]), float(site["lon"])
    accent = SAT_BRIGHT if satellite else SAT
    layers = []
    if satellite:
        layers.append(pdk.Layer("TerrainLayer", elevation_data=TERRAIN, texture=S2_TILES,
                                elevation_decoder={"rScaler": 0, "gScaler": 0, "bScaler": 0, "offset": 0},  # flat: plume hexagons start at 0 m and would sit under real terrain
                                min_zoom=0, max_zoom=11, mesh_max_error=200, strategy="no-overlap"))  # flat plane: coarse mesh, few tiles
    cols = []
    if co2_t:
        cols.append({"lon": lon - 0.025, "lat": lat, "t": co2_t, "color": _rgb(SAT, 255), "name": "Satellite-based CO2 estimate",
                     "label": f"{co2_t / 1e6:,.1f} million tonnes a year (estimated, not measured)"})
    if trace_t:
        cols.append({"lon": lon + 0.025, "lat": lat, "t": trace_t, "color": _rgb(MODEL), "name": "Climate TRACE model",
                     "label": f"{trace_t / 1e6:,.1f} million tonnes a year (modelled)"})
    if cols:
        layers.append(pdk.Layer("ColumnLayer", data=pd.DataFrame(cols), get_position="[lon, lat]", get_elevation="t",
                                elevation_scale=0.0018, radius=1300, get_fill_color="color", pickable=True, extruded=True))
    if mode == "plant" and len(plume):
        layers.append(pdk.Layer("ColumnLayer", data=plume_rose(plume, lat, lon), get_position="[lon, lat]", get_elevation="h",
                                radius=1400, get_fill_color="color", pickable=True, extruded=True))
        view = _view(lat, lon, 9.6)
    else:
        view = _view(lat, lon, 9.6)
    if mode == "contracts" and plots is not None and len(plots):
        p = plots.copy()
        p["color"] = p["alive"].map(lambda a: _rgb(OK) if a else _rgb(MODEL))
        p["name"] = "Tree plot " + p["plot_id"] + " (" + p["farmer"] + ", invented)"
        p["label"] = p["trees_planted"].map("{:,} trees contracted".format) + " · " + p["alive"].map({True: "trees seen alive", False: "no trees seen"})
        p["src_lon"], p["src_lat"] = lon, lat
        layers.append(pdk.Layer("ArcLayer", data=p, get_source_position="[src_lon, src_lat]", get_target_position="[lon, lat]",
                                get_source_color=_rgb(accent), get_target_color="color", get_width=3, pickable=False))
        layers.append(pdk.Layer("ColumnLayer", data=p, get_position="[lon, lat]", get_elevation="trees_planted", elevation_scale=6,
                                radius=9000, get_fill_color="color", pickable=True, extruded=True))
        view = _view((lat + p["lat"].mean()) / 2, (lon + p["lon"].mean()) / 2, 5.4, pitch=45, bearing=-10)
    return pdk.Deck(layers=layers, initial_view_state=view, map_style=None if satellite else "light",
                    map_provider=None if satellite else "carto",
                    tooltip={"html": "<b>{name}</b><br/>{label}", "style": {"fontFamily": FONT, "fontSize": "13px"}})
