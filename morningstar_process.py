"""Run Morningstar in a fresh interpreter's main thread, outside Streamlit."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile


def fetch_nav(isin, start, end, timeout=90):
    with tempfile.TemporaryDirectory(prefix="cruscotto-nav-") as directory:
        output = Path(directory) / "result.json"
        command = [sys.executable, str(Path(__file__).with_name("morningstar_worker.py")),
                   isin, start.isoformat(), end.isoformat(), str(output)]
        child = subprocess.Popen(command, stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL, start_new_session=os.name == "posix")
        try:
            child.wait(timeout=timeout)
            if not output.exists():
                raise RuntimeError(f"Processo Morningstar terminato senza risultato (codice {child.returncode})")
            payload = json.loads(output.read_text(encoding="utf-8"))
            if payload.get("error"):
                raise RuntimeError(payload["error"])
            if child.returncode:
                raise RuntimeError(f"Processo Morningstar terminato con codice {child.returncode}")
            return payload["data"]
        except subprocess.TimeoutExpired as exc:
            raise TimeoutError(f"Morningstar: tempo massimo di {timeout} secondi superato") from exc
        finally:
            # Also clean up browser descendants left behind by a failed worker.
            if os.name == "posix":
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            elif child.poll() is None:
                child.kill()
            child.wait()
