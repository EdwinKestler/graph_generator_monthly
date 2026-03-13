"""
map_viewer.py

Generates a self-contained interactive Folium/Leaflet HTML map of all INSIVUMEH
meteorological stations, colour-coded by 30-day aggregated statistics.

Inputs
------
- CSV file path  : insivumeh_YYYYMMDD_YYYYMM_a_YYYYMM.csv  (YYYY-MM-DD dates)
                   or database.csv (DD/MM/YYYY dates)
- output_dir     : directory where the map file is saved

Outputs
-------
- <output_dir>/mapa_YYYYMMDD_YYYYMM.html   : self-contained Leaflet map
                                              (~500 KB, no server required)

Map layers (toggle via LayerControl)
-------------------------------------
1. Precipitación Total 30d          – circle radius + blue gradient
2. Temperatura Media 30d            – fixed radius, red-blue diverging
3. Temperatura Máxima 30d           – fixed radius, Reds colormap
4. Temperatura Mínima 30d           – fixed radius, Blues_r colormap
5. Humedad Relativa 30d             – fixed radius, YlGnBu colormap
6. Mapa de calor (Lluvia)           – HeatMap overlay (off by default)

Popup on each marker shows all aggregated stats for that station.

Dependencies: folium, matplotlib, pandas, numpy
(install via the graph_generator conda environment — see readme.md)
"""

import io
import base64
import os
from datetime import date
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.colors as mcolors
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import folium
from folium.plugins import HeatMap
from data_processing import detect_date_format


# ── Map defaults ────────────────────────────────────────────────────────────
GUATEMALA_CENTER = [15.5, -90.3]
DEFAULT_ZOOM = 7

# ── Variable display configuration ──────────────────────────────────────────
# Keys must match column names produced by build_station_summary().
VARIABLES: dict = {
    "lluvia_total": {
        "label": "Precipitación Total 30d (mm)",
        "unit": "mm",
        "cmap": "Blues",
        "radius_scale": True,   # radius encodes magnitude
        "rmin": 5,
        "rmax": 22,
    },
    "tseca_mean": {
        "label": "Temperatura Media 30d (°C)",
        "unit": "°C",
        "cmap": "RdYlBu_r",
        "radius_scale": False,
        "radius": 8,
    },
    "tmax_mean": {
        "label": "Temperatura Máx. 30d (°C)",
        "unit": "°C",
        "cmap": "Reds",
        "radius_scale": False,
        "radius": 8,
    },
    "tmin_mean": {
        "label": "Temperatura Mín. 30d (°C)",
        "unit": "°C",
        "cmap": "Blues_r",
        "radius_scale": False,
        "radius": 8,
    },
    "hum_rel_mean": {
        "label": "Humedad Relativa 30d (%)",
        "unit": "%",
        "cmap": "YlGnBu",
        "radius_scale": False,
        "radius": 8,
    },
}


# ── Data preparation ─────────────────────────────────────────────────────────

def build_station_summary(csv_path: str) -> pd.DataFrame:
    """
    Read the meteorological CSV and return one row per station with
    30-day aggregated statistics and geographic coordinates.

    Args:
        csv_path: Path to the CSV file.

    Returns:
        DataFrame with columns:
            Nombre, station_id, Latitud, Longitud, Altitud,
            lluvia_total, tseca_mean, tmin_mean, tmax_mean,
            hum_rel_mean, vel_viento_mean, dir_viento_mean,
            last_fecha, n_days

    Raises:
        ValueError: If the CSV has no rows with valid coordinates.
    """
    df = pd.read_csv(csv_path, header=0, low_memory=False)

    sample = str(df["fecha"].dropna().iloc[0]).strip()
    df["fecha"] = pd.to_datetime(df["fecha"], format=detect_date_format(sample))

    # Filter to the last 30 days from the dataset's most recent date
    max_date = df["fecha"].max()
    cutoff = max_date - pd.Timedelta(days=30)
    df = df[df["fecha"] >= cutoff].copy()

    # ── Aggregate per station ────────────────────────────────────────────────
    agg = (
        df.groupby("Nombre")
        .agg(
            lluvia_total=("lluvia", "sum"),
            tseca_mean=("tseca", "mean"),
            tmin_mean=("tmin", "mean"),
            tmax_mean=("tmax", "mean"),
            hum_rel_mean=("hum_rel", "mean"),
            vel_viento_mean=("vel_viento", "mean"),
            dir_viento_mean=("dir_viento", "mean"),
            last_fecha=("fecha", "max"),
            n_days=("fecha", "count"),
        )
        .reset_index()
    )

    # ── Geographic coordinates (constant per station) ────────────────────────
    geo = df.groupby("Nombre").agg(
        Latitud=("Latitud", "first"),
        Longitud=("Longitud", "first"),
        Altitud=("Altitud", "first"),
    )

    # ── Station ID column (differs between CSV variants) ─────────────────────
    id_col = "ID" if "ID" in df.columns else ("estacion" if "estacion" in df.columns else None)
    if id_col:
        geo = geo.join(df.groupby("Nombre")[id_col].first().rename("station_id"))

    summary = agg.join(geo, on="Nombre")
    summary = summary.dropna(subset=["Latitud", "Longitud"])

    if summary.empty:
        raise ValueError(
            "No stations with valid coordinates found in the CSV. "
            "Check that 'Latitud' and 'Longitud' columns are populated."
        )

    return summary


def build_station_history(csv_path: str) -> dict:
    """
    Read the full CSV and return monthly aggregated history per station.

    Args:
        csv_path: Path to the meteorological CSV file.

    Returns:
        dict mapping station Nombre (str) → DataFrame with columns:
            month, lluvia_total, tseca_mean, tmin_mean, tmax_mean, hum_rel_mean
        sorted by month ascending.
    """
    df = pd.read_csv(csv_path, header=0, low_memory=False)
    sample = str(df["fecha"].dropna().iloc[0]).strip()
    df["fecha"] = pd.to_datetime(df["fecha"], format=detect_date_format(sample))
    df["month"] = df["fecha"].dt.to_period("M").dt.to_timestamp()

    history = {}
    for name, group in df.groupby("Nombre"):
        monthly = (
            group.groupby("month")
            .agg(
                lluvia_total=("lluvia", "sum"),
                tseca_mean=("tseca", "mean"),
                tmin_mean=("tmin", "mean"),
                tmax_mean=("tmax", "mean"),
                hum_rel_mean=("hum_rel", "mean"),
            )
            .reset_index()
            .sort_values("month")
        )
        history[name] = monthly
    return history


def _build_sparklines(history: dict) -> dict:
    """Pre-generate base64 sparkline PNGs for every station in history."""
    return {name: _sparkline_b64(df) for name, df in history.items()}


def _sparkline_b64(monthly_df: pd.DataFrame) -> str:
    """
    Render a small dual-axis monthly chart and return it as a base64 PNG string.

    Left axis  – monthly rainfall total (blue bars).
    Right axis – monthly mean temperature (orange line).
    Returns empty string if the dataframe has fewer than 2 months.
    """
    if monthly_df is None or len(monthly_df) < 2:
        return ""

    months = monthly_df["month"]
    lluvia = monthly_df["lluvia_total"].fillna(0)
    temp   = monthly_df["tseca_mean"]

    fig, ax1 = plt.subplots(figsize=(3.8, 1.8), dpi=90)

    # Rainfall bars (left axis)
    ax1.bar(months, lluvia, width=20, color="#4a90d9", alpha=0.75)
    ax1.set_ylabel("mm", fontsize=7, color="#4a90d9")
    ax1.tick_params(axis="y", labelsize=6, labelcolor="#4a90d9")
    ax1.tick_params(axis="x", labelsize=6, rotation=45)
    ax1.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%y"))

    # Temperature line (right axis)
    if temp.notna().any():
        ax2 = ax1.twinx()
        ax2.plot(months, temp, color="#e05a2b", linewidth=1.2,
                 marker="o", markersize=2)
        ax2.set_ylabel("°C", fontsize=7, color="#e05a2b")
        ax2.tick_params(axis="y", labelsize=6, labelcolor="#e05a2b")

    fig.tight_layout(pad=0.3)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=90)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


# ── Colour / radius helpers ──────────────────────────────────────────────────

def _value_to_hex(value, vmin: float, vmax: float, cmap_name: str) -> str:
    """Map a scalar to a hex colour string using a matplotlib colormap."""
    if pd.isna(value) or vmin == vmax:
        return "#aaaaaa"
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax, clip=True)
    cmap = matplotlib.colormaps[cmap_name]
    rgba = cmap(norm(float(value)))
    return mcolors.to_hex(rgba)


def _value_to_radius(value, vmin: float, vmax: float,
                     rmin: float = 5, rmax: float = 22) -> float:
    """Scale value → marker radius using square-root scaling."""
    if pd.isna(value) or vmin >= vmax:
        return rmin
    sq = np.sqrt(max(float(value) - vmin, 0.0))
    sq_max = np.sqrt(max(vmax - vmin, 0.0))
    if sq_max == 0:
        return rmin
    return rmin + (sq / sq_max) * (rmax - rmin)


# ── Popup HTML ───────────────────────────────────────────────────────────────

def _popup_html(row: pd.Series, hist_b64: str = "") -> str:
    """Build the HTML content displayed when a station marker is clicked."""
    name = str(row["Nombre"]).replace("_", " ")
    station_id = row.get("station_id", "—")
    altitud = row.get("Altitud")
    last_fecha = row.get("last_fecha")

    def fmt(val, unit="", decimals=1):
        if pd.isna(val):
            return "—"
        return f"{val:.{decimals}f}&nbsp;{unit}".strip()

    last_str = (
        pd.Timestamp(last_fecha).strftime("%Y-%m-%d")
        if not pd.isna(last_fecha)
        else "—"
    )

    rows_html = "".join([
        f"<tr><td colspan='2' style='font-size:13px;font-weight:bold;"
        f"padding-bottom:4px'>{name}</td></tr>",
        f"<tr><td style='color:#666'>ID</td><td>{station_id}</td></tr>",
        f"<tr><td style='color:#666'>Altitud</td><td>{fmt(altitud, 'm', 0)}</td></tr>",
        f"<tr><td style='color:#666'>Última fecha</td><td>{last_str}</td></tr>",
        "<tr><td colspan='2'><hr style='margin:4px 0;border-color:#ddd'></td></tr>",
        f"<tr><td>Lluvia total 30d</td><td><b>{fmt(row.get('lluvia_total'), 'mm')}</b></td></tr>",
        f"<tr><td>Temp. media</td><td>{fmt(row.get('tseca_mean'), '°C')}</td></tr>",
        f"<tr><td>Temp. mínima</td><td>{fmt(row.get('tmin_mean'), '°C')}</td></tr>",
        f"<tr><td>Temp. máxima</td><td>{fmt(row.get('tmax_mean'), '°C')}</td></tr>",
        f"<tr><td>Hum. relativa</td><td>{fmt(row.get('hum_rel_mean'), '%')}</td></tr>",
        f"<tr><td>Viento medio</td>"
        f"<td>{fmt(row.get('vel_viento_mean'), 'km/h')}"
        f" @ {fmt(row.get('dir_viento_mean'), '°', 0)}</td></tr>",
        f"<tr><td>Días registrados</td><td>{int(row.get('n_days', 0))}</td></tr>",
    ])

    chart_html = ""
    if hist_b64:
        chart_html = (
            "<tr><td colspan='2' style='padding-top:6px'>"
            "<div style='font-size:10px;color:#555;margin-bottom:2px'>"
            "Historial mensual &mdash; lluvia (azul) / temp. (naranja)</div>"
            f"<img src='data:image/png;base64,{hist_b64}' "
            "style='width:100%;border-radius:3px'></td></tr>"
        )

    return (
        "<div style='font-family:sans-serif;font-size:12px;"
        "min-width:210px;max-width:380px'>"
        f"<table style='border-collapse:collapse;width:100%'>"
        f"{rows_html}{chart_html}</table>"
        "</div>"
    )


# ── Layer builder ─────────────────────────────────────────────────────────────

def _add_variable_layer(
    m: folium.Map,
    summary: pd.DataFrame,
    var_key: str,
    show: bool = False,
    sparklines: dict = None,
) -> None:
    """Add a FeatureGroup layer to the map for one variable."""
    cfg = VARIABLES[var_key]
    valid = summary[var_key].dropna()
    vmin = float(valid.min()) if len(valid) else 0.0
    vmax = float(valid.max()) if len(valid) else 1.0

    fg = folium.FeatureGroup(name=cfg["label"], show=show)

    for _, row in summary.iterrows():
        lat, lon = row["Latitud"], row["Longitud"]
        value = row.get(var_key)

        color = _value_to_hex(value, vmin, vmax, cfg["cmap"])

        if cfg["radius_scale"]:
            radius = _value_to_radius(
                value, vmin, vmax, cfg.get("rmin", 5), cfg.get("rmax", 22)
            )
        else:
            radius = cfg.get("radius", 8)

        tooltip_text = (
            f"{str(row['Nombre']).replace('_', ' ')}: "
            f"{value:.1f} {cfg['unit']}"
            if not pd.isna(value)
            else str(row["Nombre"]).replace("_", " ")
        )

        hist_b64 = (sparklines or {}).get(row["Nombre"], "")
        popup_width = 390 if hist_b64 else 270

        folium.CircleMarker(
            location=[lat, lon],
            radius=radius,
            color="white",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(_popup_html(row, hist_b64), max_width=popup_width),
            tooltip=tooltip_text,
        ).add_to(fg)

    fg.add_to(m)


# ── Main entry point ──────────────────────────────────────────────────────────

def generate_map(summary: pd.DataFrame, output_dir: str, history: dict = None) -> str:
    """
    Build a self-contained Folium/Leaflet HTML map of all stations.

    Args:
        summary   : Output of build_station_summary().
        output_dir: Directory where map.html will be saved (created if missing).
        history   : Optional output of build_station_history(). When provided,
                    each station popup includes an embedded monthly history chart.

    Returns:
        Absolute path to the saved map.html file.
    """
    os.makedirs(output_dir, exist_ok=True)

    run_date   = date.today().strftime('%Y%m%d')
    data_month = pd.Timestamp(summary['last_fecha'].max()).strftime('%Y%m')
    map_name   = f"mapa_{run_date}_{data_month}.html"

    sparklines = _build_sparklines(history) if history else {}

    m = folium.Map(location=GUATEMALA_CENTER, zoom_start=DEFAULT_ZOOM, tiles=None)

    # ── Base tile layers ─────────────────────────────────────────────────────
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services"
            "/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Satélite (Esri)",
    ).add_to(m)
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services"
            "/World_Topo_Map/MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Topografía (Esri)",
    ).add_to(m)

    # ── Variable marker layers (first one visible by default) ────────────────
    for i, var_key in enumerate(VARIABLES):
        _add_variable_layer(m, summary, var_key, show=(i == 0), sparklines=sparklines)

    # ── Precipitation heatmap (toggle) ───────────────────────────────────────
    heat_data = [
        [row["Latitud"], row["Longitud"], float(row["lluvia_total"])]
        for _, row in summary.iterrows()
        if not pd.isna(row["lluvia_total"]) and row["lluvia_total"] > 0
    ]
    if heat_data:
        fg_heat = folium.FeatureGroup(name="Mapa de calor (Lluvia)", show=False)
        HeatMap(heat_data, radius=35, blur=25, max_zoom=10).add_to(fg_heat)
        fg_heat.add_to(m)

    # ── Layer control ────────────────────────────────────────────────────────
    folium.LayerControl(collapsed=False).add_to(m)

    # ── Title banner ─────────────────────────────────────────────────────────
    title_html = """
    <div style="position:fixed;top:10px;left:50%;transform:translateX(-50%);
                z-index:1000;background:white;padding:7px 18px;border-radius:6px;
                box-shadow:0 2px 8px rgba(0,0,0,.3);font-family:sans-serif;
                font-size:13px;white-space:nowrap;">
        <b>Red Meteorológica Nacional &mdash; INSIVUMEH</b>
        <span style="color:#666;font-size:11px"> &bull; Últimos 30 días</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # ── Legend hint ──────────────────────────────────────────────────────────
    legend_html = """
    <div style="position:fixed;bottom:30px;left:10px;z-index:1000;
                background:white;padding:6px 12px;border-radius:6px;
                box-shadow:0 2px 6px rgba(0,0,0,.25);font-family:sans-serif;
                font-size:11px;color:#333;line-height:1.6">
        <b>Cómo usar</b><br>
        • Activa una capa en el panel superior derecho<br>
        • Haz clic en un marcador para ver estadísticas<br>
        • Pasa el cursor para ver el valor rápido
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    out_path = os.path.join(output_dir, map_name)
    m.save(out_path)
    return os.path.abspath(out_path)
