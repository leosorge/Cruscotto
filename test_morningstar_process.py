import os
from pathlib import Path
import tempfile
import threading
import unittest
from datetime import date
from unittest.mock import patch
from morningstar_process import fetch_nav


class ProcessTests(unittest.TestCase):
    def run_fake(self, source, timeout=10):
        with tempfile.TemporaryDirectory() as directory:
            session_stub = """import sys, types
search = types.ModuleType('mstarpy.search')
class Session:
    def __enter__(self): return self
    def __exit__(self, *args): pass
search.MorningstarSession = Session
sys.modules['mstarpy.search'] = search
"""
            Path(directory, "mstarpy.py").write_text(session_stub + source)
            with patch.dict(os.environ, {"PYTHONPATH": directory}):
                return fetch_nav("LU0503631557", date(2025,12,31), date(2026,10,4), timeout)

    def test_signal_from_streamlit_style_thread(self):
        result, errors = [], []
        def call():
            try:
                result.extend(self.run_fake("""import signal, threading
assert threading.current_thread() is threading.main_thread()
signal.signal(signal.SIGTERM, signal.SIG_DFL)
class Funds:
    def __init__(self, term, session=None): pass
    def nav(self, **kwargs):
        print('library diagnostic')
        return [{'date':'2025-12-31','nav':100}]
"""))
            except Exception as exc:
                errors.append(exc)
        thread = threading.Thread(target=call)
        thread.start()
        thread.join(20)
        self.assertFalse(thread.is_alive())
        self.assertEqual(errors, [])
        self.assertEqual(result[0]["nav"], 100)

    def test_provider_error_is_returned(self):
        with self.assertRaisesRegex(RuntimeError, "provider unavailable"):
            self.run_fake("raise ValueError('provider unavailable')")

    def test_timeout(self):
        with self.assertRaises(TimeoutError):
            self.run_fake("import time; time.sleep(30)", timeout=0.2)


if __name__ == "__main__":
    unittest.main()
