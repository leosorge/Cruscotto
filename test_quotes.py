import unittest
from datetime import date
from quotes import normalize_history, values

class QuotesTests(unittest.TestCase):
    def test_holiday_uses_previous_quote(self):
        h = normalize_history([{"date":"2025-12-31","nav":100},{"date":"2026-01-02","nav":110}])
        r = values(h, date(2026,1,1), date(2026,1,3))
        self.assertEqual(r[2], "2025-12-31")
        self.assertAlmostEqual(r[4], 10)
    def test_missing_baseline_stays_missing(self):
        h = normalize_history([{"date":"2026-01-02","nav":110}])
        self.assertIsNone(values(h,date(2026,1,1),date(2026,1,3))[4])

if __name__ == "__main__": unittest.main()
