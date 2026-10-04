"""CLI worker: imports and initializes mstarpy only in MainThread."""
from contextlib import redirect_stdout
from datetime import date
import json
import os
from pathlib import Path
import sys


def main():
    isin, start, end, destination = sys.argv[1:]
    # Community Cloud has no display server; mstarpy supports these flags.
    flags = os.environ.get("SELENIUM_CHROME_FLAGS", "").split()
    for flag in ("--headless=new", "--disable-dev-shm-usage"):
        if flag not in flags:
            flags.append(flag)
    os.environ["SELENIUM_CHROME_FLAGS"] = " ".join(flags)
    try:
        with redirect_stdout(sys.stderr):
            import mstarpy
            from morningstar_search import make_session
            with make_session() as session:
                raw = mstarpy.Funds(term=isin, session=session).nav(
                    start_date=date.fromisoformat(start),
                    end_date=date.fromisoformat(end), frequency="daily")
            # Use pandas' JSON serializer for timestamps and numpy values.
            import pandas as pd
            data = json.loads(pd.DataFrame(raw).to_json(orient="records", date_format="iso"))
        payload = {"data": data}
        code = 0
    except Exception as exc:
        payload = {"error": f"{type(exc).__name__}: {exc}"}
        code = 1
    Path(destination).write_text(json.dumps(payload), encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
