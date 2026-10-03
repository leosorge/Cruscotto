"""Quotazioni per la lista di osservazione, senza quantità patrimoniali."""
from datetime import date, timedelta
import pandas as pd

def normalize_history(raw):
    if isinstance(raw, pd.Series):
        frame = raw.rename('Close').to_frame()
    else:
        frame = pd.DataFrame(raw)
        if 'nav' in frame and 'date' in frame:
            frame = frame.set_index('date').rename(columns={'nav': 'Close'})
    if 'Close' not in frame or frame.empty:
        raise ValueError('Storico senza prezzi')
    frame.index = pd.to_datetime(frame.index, utc=True).tz_convert(None).normalize()
    frame['Close'] = pd.to_numeric(frame['Close'], errors='coerce')
    return frame[['Close']].dropna().sort_index()


def values(history, baseline, end):
    start_rows = history.loc[history.index <= pd.Timestamp(baseline)]
    end_rows = history.loc[history.index <= pd.Timestamp(end)]
    p0 = float(start_rows.iloc[-1]['Close']) if not start_rows.empty else None
    p1 = float(end_rows.iloc[-1]['Close']) if not end_rows.empty else None
    d0 = start_rows.index[-1].date().isoformat() if not start_rows.empty else None
    d1 = end_rows.index[-1].date().isoformat() if not end_rows.empty else None
    pct = (p1 / p0 - 1) * 100 if p0 and p1 else None
    return p0, p1, d0, d1, pct


def fetch_asset(asset, baseline, end):
    errors = []
    history = None
    source = 'N/D'
    start = baseline - timedelta(days=20)
    # Ricerca per ISIN: identifica la classe del fondo prima del fallback Yahoo.
    isin = asset.get('deltahedge_isin') or asset.get('isin', '')
    if len(isin) == 12 and isin[:2].isalpha():
        try:
            import mstarpy
            raw = mstarpy.Funds(term=isin).nav(start_date=start, end_date=end, frequency='daily')
            history = normalize_history(raw)
            source = 'Morningstar'
        except Exception as exc:
            errors.append('Morningstar: ' + str(exc)[:180])
    ticker = asset.get('ticker')
    if not ticker and asset.get('isin', '').endswith('.F'):
        ticker = asset['isin']
    if history is None and ticker:
        try:
            import yfinance as yf
            raw = yf.Ticker(ticker).history(start=start.isoformat(), end=(end + timedelta(days=1)).isoformat(), auto_adjust=False, timeout=12)
            history = normalize_history(raw)
            source = 'Yahoo: ' + ticker
        except Exception as exc:
            errors.append('Yahoo: ' + str(exc)[:180])
    row = {'Titolo': asset['name'], 'Banca': asset['bank'], 'ISIN': isin,
           'Valuta': asset.get('currency', 'EUR'), 'Prezzo iniziale': None,
           'Ultimo prezzo': None, 'Data iniziale': None, 'Data prezzo': None,
           'Variazione %': None, 'Fonte': source, 'Stato': 'Non disponibile',
           'Dettaglio': '; '.join(errors), 'Link fonte': asset.get('url', '')}
    if history is not None:
        p0, p1, d0, d1, pct = values(history, baseline, end)
        row.update({'Prezzo iniziale': p0, 'Ultimo prezzo': p1, 'Data iniziale': d0,
                    'Data prezzo': d1, 'Variazione %': pct,
                    'Stato': 'Disponibile' if pct is not None else 'Storico iniziale mancante'})
    return row
