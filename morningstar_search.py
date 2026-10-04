"""Resolve exact ISINs through Morningstar's current standard search API."""

# Explicit share-class identities verified against Morningstar fund pages.
# These are not inferred from Yahoo tickers (which may identify other classes).
VERIFIED_FUNDS = {
    "LU0171310443": {"securityID": "0P0001FJIH", "name": "BGF World Technology A2 USD (EUR)",
                     "source": "https://www.morningstarfunds.ie/ie/funds/snapshot/snapshot.aspx?id=0P0001FJIH"},
    "LU1046235906": {"securityID": "F00000T8RJ", "name": "Schroder Strategic Credit C Accumulation EUR Hedged",
                     "source": "https://global.morningstar.com/de/investments/fonds/F00000T8RJ/grafik"},
}


def verified_result(isin):
    identity = VERIFIED_FUNDS.get(isin)
    if identity is None:
        return None
    return [{"value": {"isin": isin, "investmentType": "FO",
                       "securityID": identity["securityID"], "name": identity["name"]}}]


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
            known = verified_result(term)
            if known is not None:
                return known
            # Funds only needs identity resolution. Do not request the obsolete
            # global field/filter catalogs before calling the current search API.
            payload = self.general_search(
                {"q": term, "limit": 100, "page": 1}, language=language)
            return exact_results(payload, term)

    return ExactIsinSession()
