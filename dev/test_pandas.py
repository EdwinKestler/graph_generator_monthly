with open("dev/pandas_log.txt", "w") as f:
    f.write("start\n")
    f.flush()
    try:
        import pandas as pd
        f.write(f"pandas ok: {pd.__version__}\n")
    except Exception as e:
        f.write(f"pandas error: {e}\n")
    f.write("end\n")
