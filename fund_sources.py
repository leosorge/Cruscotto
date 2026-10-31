"""Yahoo ISIN search and FT fallback adapted from Untitled64."""
import re, io
from datetime import timedelta
import requests
import pandas as pd
import yfinance as yf
TICKER_MANUALI = {}
HDR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}

# ---------------- FONTE 1: YAHOO ----------------
def yahoo_serie(isin, start, end):
    """Restituisce una Series di NAV (indice = data) o None."""
    candidati = []
    if isin in TICKER_MANUALI:
        candidati.append(TICKER_MANUALI[isin])
    else:
        try:
            res = yf.Search(isin, max_results=10).quotes
            for q in res:
                if q.get("quoteType") in ("MUTUALFUND", "ETF"):
                    candidati.append(q["symbol"])
        except Exception as e:
            print(f"  [Yahoo] ricerca fallita per {isin}: {e}")
    for t in candidati:
        try:
            h = yf.Ticker(t).history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(),
                                     auto_adjust=False, timeout=15)
            if not h.empty:
                s = h["Close"].dropna()
                s.index = pd.to_datetime(s.index).tz_localize(None).normalize()
                return s, f"Yahoo:{t}"
        except Exception as e:
            print(f"  [Yahoo] {t}: {e}")
    return None, None

# ---------------- FONTE 2: FT MARKETS ----------------
def ft_serie(isin, start, end, currency="EUR"):
    try:
        base = "https://markets.ft.com/data/funds/tearsheet/historical"
        simboli = [f"{isin}:{currency}"]
        for sym in simboli:
            r = requests.get(base, params={"s": sym}, headers=HDR, timeout=15)
            if r.status_code != 200:
                continue
            m = re.search(r'&quot;xid&quot;:&quot;(\d+)&quot;', r.text) or \
                re.search(r'"xid":"(\d+)"', r.text)
            if not m:
                continue
            xid = m.group(1)
            ajax = "https://markets.ft.com/data/equities/ajax/get-historical-prices"
            r2 = requests.get(ajax, params={"startDate": start.strftime("%Y/%m/%d"),
                                            "endDate": end.strftime("%Y/%m/%d"),
                                            "symbol": xid},
                              headers=HDR, timeout=15)
            html = r2.json().get("html", "")
            if not html:
                continue
            df = pd.read_html(io.StringIO(f"<table>{html}</table>"))[0]
            pat = r"[A-Z][a-z]+ \d{1,2}, \d{4}"
            date = df["Date"].astype(str).str.extract(f"({pat})")[0]
            s = pd.Series(df["Close"].astype(float).values,
                          index=pd.to_datetime(date, format="%B %d, %Y"))
            s = s.sort_index().dropna()
            if not s.empty:
                return s, f"FT:{sym}"
    except Exception as e:
        print(f"  [FT] {isin}: {e}")
    return None, None

