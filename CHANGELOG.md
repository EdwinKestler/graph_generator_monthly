# Changelog

All notable changes to **Generador de Gráficas Mensual** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning follows [Semantic Versioning](https://semver.org/).

---

## [1.0.0] — 2026-03-13

### Added
- **Interactive station map** (`map_viewer.py`): Folium/Leaflet HTML map of the full INSIVUMEH
  network with 5 toggle layers (precipitation, mean/max/min temperature, relative humidity) and
  a precipitation heat-map overlay.
- **Historical popup charts**: each station marker now embeds a dual-axis monthly history chart
  (rainfall bars + temperature line) rendered inline as a base64 PNG.
- **GitHub Actions CI/CD** (`.github/workflows/build.yml`): automatic Windows EXE build on every
  push to `main`; tagged `v*.*.*` pushes also create a GitHub Release with the EXE attached.
- **Conda environment file** (`environment.yml`): reproducible Python 3.11 + conda-forge
  environment replacing manual dependency management.
- **MIT License** (`LICENSE`).

### Changed
- Matplotlib PNG charts now use **data-driven y-axis limits** (precipitation and temperature
  ranges scale with the actual data, preventing clipping on extreme-event days).
- Bokeh HTML charts likewise changed to data-driven y-axis limits (previously hardcoded to
  precipitation 0–90 mm and temperature −5–40 °C).
- `matplotlib.use('Agg')` is now set in `monthly_graph.py` before any pyplot import, preventing
  crash on headless/background-thread rendering.
- `requirements.txt` rewritten from broken UTF-16 encoding to UTF-8; removed unused
  `google-auth` and `google-api-python-client` entries.
- Window title updated to **"Generador de Gráficas Mensual v1.0.0"** (added version, fixed
  accent, corrected spelling).

### Fixed
- **Path traversal** in `graph_generation.py` and `data_processing.py`: station names are now
  sanitised with `os.path.basename()` before use in output file paths.
- **Stored HTML injection** in `map_viewer.py`: station names and IDs are escaped with
  `html.escape()` before embedding in Folium popup HTML.
- **Missing HTTP timeout** in `download_database.py`: all `requests.Session.get()` calls now
  use `timeout=(15, 120)` to prevent infinite hangs on slow connections.
- UI text corrections: "Porfavor" → "Por favor", "Selecionar" → "Seleccionar",
  "genrar" → "generar".

### Security
- Path traversal prevention (see Fixed above).
- XSS prevention via `html.escape()` on all user-controlled data embedded in HTML output.

---

## [0.x] — Pre-release development

Single-threaded prototype using Bokeh only; no map viewer, no background threads, no CI.
See `archive/` for historical scripts.
