"""Resolve exact ISINs through Morningstar's current standard search API."""


def exact_results(payload, isin):
    results = payload.get("results", [])
    matched = []
    for result in results:
        value = result.get("value", {})
        if value.get("isin") == isin and value.get("investmentType") in {"FO", "FE", "FC", "FV", "FM"}:
            if value.get("securityID"):
                matched.append(result)
    identifiers = {item["value"]["securityID"] for item in matched}
    if len(identifiers) != 1:
        raise ValueError(f"Ricerca Morningstar: ISIN {isin} non trovato o risultato ambiguo")
    return matched[:1]


def make_session():
    from mstarpy.search import MorningstarSession

    class ExactIsinSession(MorningstarSession):
        def screener_universe(self, term, language="en-gb", **kwargs):
            # Funds only needs identity resolution. Do not request the obsolete
            # global field/filter catalogs before calling the current search API.
            payload = self.general_search(
                {"q": term, "limit": 100, "page": 1}, language=language)
            return exact_results(payload, term)

    return ExactIsinSession()

