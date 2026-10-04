import unittest
from morningstar_search import exact_results, verified_result


class SearchTests(unittest.TestCase):
    def test_verified_identity_is_exact_and_unknown_is_not_guessed(self):
        result = verified_result("LU1046235906")
        self.assertEqual(result[0]["value"]["securityID"], "F00000T8RJ")
        self.assertEqual(exact_results({"results": result}, "LU1046235906"), result)
        self.assertIsNone(verified_result("LU0503631557"))

    def test_rejects_different_share_class(self):
        with self.assertRaises(ValueError):
            exact_results({"results": [{"value": {"isin": "OTHER", "investmentType": "FO", "securityID": "F1"}}]}, "LU0503631557")

    def test_exact_isin_and_fund_type(self):
        item = {"value": {"isin": "LU0503631557", "investmentType": "FO", "securityID": "F1"}}
        self.assertEqual(exact_results({"results": [item]}, "LU0503631557"), [item])

    def test_ambiguous_identifiers_rejected(self):
        items = [{"value": {"isin": "LU0503631557", "investmentType": "FO", "securityID": code}} for code in ("F1", "F2")]
        with self.assertRaises(ValueError):
            exact_results({"results": items}, "LU0503631557")


if __name__ == "__main__":
    unittest.main()
