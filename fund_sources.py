"""Yahoo ISIN search and FT fallback adapted from Untitled64."""
from html import unescape
import io
import re
from datetime import timedelta
import requests
import pandas as pd
import yfinance as yf
from lxml import html as html_parser
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

def yahoo_ticker_history(symbol, start, end, currency, isin="", search_isin=""):
    ticker = yf.Ticker(symbol)
    if isin:
        if search_isin and search_isin != isin:
            raise ValueError(f"{symbol} identifica {search_isin}, richiesto {isin}")
        if not search_isin and ticker.info.get("isin") != isin:
            raise ValueError(f"ISIN {isin} non confermato da Yahoo per {symbol}")
    history = ticker.history(start=start.isoformat(),
                             end=(end + timedelta(days=1)).isoformat(),
                             auto_adjust=False, timeout=15)
    if history.empty:
        raise ValueError(f"Storico assente per {symbol}")
    actual_currency = ticker.history_metadata.get("currency")
    if actual_currency != currency:
        raise ValueError(f"Valuta di {symbol}: {actual_currency or 'non confermata'}, richiesta {currency}")
    return history


def yahoo_serie(isin, start, end, currency="EUR", exclude=None):
    errors = []
    for quote in yf.Search(isin, max_results=10).quotes:
        symbol = quote.get("symbol")
        if not symbol or symbol == exclude or quote.get("quoteType") not in ("MUTUALFUND", "ETF"):
            continue
        try:
            history = yahoo_ticker_history(symbol, start, end, currency, isin, quote.get("isin"))
            return history, f"Yahoo: {symbol}"
        except Exception as exc:
            errors.append(str(exc))
    raise ValueError(errors[0] if errors else f"Nessun risultato per {isin}")


def ft_serie(isin, start, end, currency="EUR"):
    symbol = f"{isin}:{currency}"
    base = "https://markets.ft.com/data/funds/tearsheet/historical"
    page = requests.get(base, params={"s": symbol}, headers=HDR, timeout=15)
    page.raise_for_status()
    document = html_parser.fromstring(page.content)
    # Verifica il simbolo mostrato nella testata dello strumento, ignorando
    # il parametro richiesto nell'URL e i simboli presenti nei menu.
    labels = document.xpath("//*[contains(@class, 'mod-tearsheet-overview__header__symbol')]")
    if {label.text_content().strip() for label in labels} != {symbol}:
        raise ValueError(f"Simbolo {symbol} non confermato nella scheda FT")
    identifiers = set(re.findall(r'"xid"\s*:\s*"?(\d+)"?', unescape(page.text)))
    if len(identifiers) != 1:
        raise ValueError("Identificativo storico FT assente o ambiguo")
    xid, = identifiers
    ajax = "https://markets.ft.com/data/equities/ajax/get-historical-prices"
    response = requests.get(ajax, params={"startDate": start.strftime("%Y/%m/%d"),
                                         "endDate": end.strftime("%Y/%m/%d"),
                                         "symbol": xid}, headers=HDR, timeout=15)
    response.raise_for_status()
    table = response.json().get("html", "")
    if not table:
        raise ValueError("Storico FT assente")
    frame = pd.read_html(io.StringIO(f"<table>{table}</table>"))[0]
    dates = frame["Date"].astype(str).str.extract(r"([A-Z][a-z]+ \d{1,2}, \d{4})")[0]
    series = pd.Series(frame["Close"].astype(float).values,
                       index=pd.to_datetime(dates, format="%B %d, %Y"))
    return series.sort_index().dropna(), f"FT: {symbol}"
