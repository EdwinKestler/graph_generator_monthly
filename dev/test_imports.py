import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
LOG = os.path.join(ROOT, "dev", "import_log.txt")

lines = []
def log(msg):
    print(msg, flush=True)
    lines.append(msg)
    with open(LOG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

log("testing imports one by one...")

try:
    import pandas as pd
    log(f"  PASS  pandas {pd.__version__}")
except Exception as e:
    log(f"  FAIL  pandas: {e}")

try:
    import bokeh
    log(f"  PASS  bokeh {bokeh.__version__}")
except Exception as e:
    log(f"  FAIL  bokeh: {e}")

try:
    from bokeh.plotting import figure, output_file, save
    log("  PASS  bokeh.plotting")
except Exception as e:
    log(f"  FAIL  bokeh.plotting: {e}")

try:
    from bokeh.models import Range1d, LinearAxis, HoverTool
    log("  PASS  bokeh.models")
except Exception as e:
    log(f"  FAIL  bokeh.models: {e}")

try:
    from data_processing import read_and_prepare_data
    log("  PASS  data_processing")
except Exception as e:
    log(f"  FAIL  data_processing: {e}")

log("done")
