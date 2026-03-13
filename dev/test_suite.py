"""
test_suite.py — Pre-commit smoke tests for graph_generator_monthly.

Tests:
  1. Asset files exist at new paths (assets/)
  2. Data CSV exists at new path (data/)
  3. data_processing: date auto-detection works for both CSV formats
  4. data_processing: full pipeline runs on local CSV without crashing
  5. download_database: live download from Google Drive produces a valid CSV

Run from project root:
    python dev/test_suite.py
Output also written to dev/test_output.txt
"""

import os
import sys
import tempfile

# Write all output to both stdout and a log file
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "dev", "test_output.txt")
sys.path.insert(0, ROOT)

_lines = []

def log(msg=""):
    print(msg, flush=True)
    _lines.append(msg)
    flush_log()

def flush_log():
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(_lines) + "\n")

PASS = "  PASS"
FAIL = "  FAIL"
results = []

def check(label, condition, detail=""):
    status = PASS if condition else FAIL
    msg = f"{status}  {label}"
    if detail:
        msg += f"\n         {detail}"
    log(msg)
    results.append(condition)
    flush_log()

# ── 1. Asset files ─────────────────────────────────────────────────────────────
log("\n[1] Asset paths (assets/)")
for fname in ["logo_insivumeh.png", "waterco-logo.png", "IUCN_logo.png", "spinning-loading.gif"]:
    path = os.path.join(ROOT, "assets", fname)
    check(f"assets/{fname}", os.path.isfile(path))

# ── 2. Data CSV ────────────────────────────────────────────────────────────────
log("\n[2] Data CSV path (data/)")
import glob as _glob
_dated = _glob.glob(os.path.join(ROOT, "data", "insivumeh_*.csv"))
_legacy = os.path.join(ROOT, "data", "download-database.csv")
csv_path = _dated[0] if _dated else _legacy
check(
    "data/ contains insivumeh_*.csv or download-database.csv",
    bool(_dated) or os.path.isfile(_legacy),
    f"using: {os.path.basename(csv_path)}",
)

# ── 3. Date auto-detection ─────────────────────────────────────────────────────
log("\n[3] Date format auto-detection")
try:
    import pandas as pd
    from data_processing import read_and_prepare_data

    iso_rows = "fecha,Nombre,lluvia\n2024-03-01,STA,1.0\n2024-03-02,STA,2.0\n"
    dmy_rows = "fecha,Nombre,lluvia\n01/03/2024,STA,1.0\n02/03/2024,STA,2.0\n"

    for label, content in [("YYYY-MM-DD", iso_rows), ("DD/MM/YYYY", dmy_rows)]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp = f.name
        try:
            df = read_and_prepare_data(tmp)
            ok = pd.api.types.is_datetime64_any_dtype(df["fecha"])
            check(f"read_and_prepare_data handles {label}", ok)
        except Exception as e:
            check(f"read_and_prepare_data handles {label}", False, str(e))
        finally:
            os.unlink(tmp)
except Exception as e:
    check("import data_processing", False, str(e))

# ── 4. Full pipeline on local CSV ─────────────────────────────────────────────
log("\n[4] Full graph pipeline (local CSV — writes to temp dir)")
try:
    from data_processing import read_and_prepare_data, prepare_data_for_graphs, process_grouped_data

    df = read_and_prepare_data(csv_path)
    check("CSV read OK", len(df) > 0, f"{len(df)} rows loaded")

    grouped = prepare_data_for_graphs(df)
    groups = list(grouped)
    check("Stations grouped", len(groups) > 0, f"{len(groups)} stations in last-30-day window")

    name, group = groups[0]
    with tempfile.TemporaryDirectory() as tmpdir:
        img_dir = os.path.join(tmpdir, "img")
        html_dir = os.path.join(tmpdir, "html")
        os.makedirs(img_dir)
        os.makedirs(html_dir)
        try:
            result = process_grouped_data(name, group, img_dir, html_dir)
            has_keys = all(k in result for k in ["fecha", "lluvia", "tseca", "tmin", "tmax", "hum_rel"])
            html_files = os.listdir(html_dir)
            html_written = len(html_files) == 1
            check(f"process_grouped_data '{name}' returns correct keys", has_keys)
            check(f"Bokeh HTML written for '{name}'", html_written,
                  html_files[0] if html_files else "no files found")
        except Exception as e:
            check(f"process_grouped_data '{name}'", False, str(e))

except Exception as e:
    check("pipeline setup", False, str(e))

# ── 5. Live download ───────────────────────────────────────────────────────────
log("\n[5] Live Google Drive download")
try:
    from download_database import download_file_from_google_drive

    FILE_ID = "19gcM1e5rb-HvJ-MVhNSZgsinNhN0S79Y"
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        tmp_dest = f.name
    try:
        log("    downloading...")
        flush_log()
        success = download_file_from_google_drive(FILE_ID, tmp_dest)
        check("download returns True", success is True)
        size = os.path.getsize(tmp_dest)
        check("downloaded file > 1 KB", size > 1000, f"{size:,} bytes")
        with open(tmp_dest, "r", encoding="utf-8", errors="replace") as f:
            first_line = f.readline().strip()
        is_csv = "fecha" in first_line and "," in first_line
        check("content is CSV (has 'fecha' header)", is_csv, f"first line: {first_line[:100]}")
    finally:
        os.unlink(tmp_dest)
except Exception as e:
    check("download test", False, str(e))

# ── Summary ────────────────────────────────────────────────────────────────────
log(f"\n{'='*50}")
passed = sum(results)
total = len(results)
log(f"  {passed}/{total} checks passed")
if passed == total:
    log("  ALL TESTS PASSED - safe to commit")
else:
    log("  FAILURES DETECTED - do not commit until resolved")
log('='*50)
flush_log()
sys.exit(0 if passed == total else 1)
