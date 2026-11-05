from datetime import date
from unittest.mock import patch, Mock
import pandas as pd
from fund_sources import yahoo_serie, ft_serie
from quotes import fetch_asset

START, END = date(2025,12,1), date(2026,10,30)

def test_yahoo_uses_isin_and_dynamic_dates():
    data = pd.DataFrame({'Close':[10,12]}, index=pd.to_datetime(['2025-12-30','2026-10-29']))
    ticker = Mock(); ticker.history.return_value = data
    with patch('fund_sources.yf.Search') as search, patch('fund_sources.yf.Ticker',return_value=ticker):
        search.return_value.quotes=[{'quoteType':'MUTUALFUND','symbol':'TEST.F'}]
        s, source = yahoo_serie('LU1046235906',START,END)
        assert source == 'Yahoo:TEST.F' and len(s)==2
        assert search.call_args.args[0]=='LU1046235906'
        assert ticker.history.call_args.kwargs['end']=='2026-10-31'

def test_ft_dates_and_currency():
    page=Mock(status_code=200,text='"xid":"123"')
    ajax=Mock();ajax.json.return_value={'html':'<tr><th>Date</th><th>Close</th></tr><tr><td>Thursday, October 29, 2026</td><td>123.45</td></tr>'}
    with patch('fund_sources.requests.get',side_effect=[page,ajax]) as get:
        series,source=ft_serie('LU1046235906',START,END,'EUR')
        assert series.iloc[0]==123.45 and source=='FT:LU1046235906:EUR'
        assert get.call_args.kwargs['params']['endDate']=='2026/10/30'

def test_za_fallback_does_not_launch_morningstar():
    data=pd.Series([10,12],index=pd.to_datetime(['2025-12-30','2026-10-29']))
    with patch('quotes.yahoo_serie',return_value=(None,None)), patch('quotes.ft_serie',return_value=(data,'FT:test')), patch('quotes.fetch_nav') as morningstar:
        row=fetch_asset({'name':'test','bank':'za','isin':'LU1046235906'},date(2025,12,31),END)
        assert abs(row['Variazione %']-20)<1e-8
        morningstar.assert_not_called()

def test_no_data_stays_missing():
    with patch('quotes.yahoo_serie',return_value=(None,None)),patch('quotes.ft_serie',return_value=(None,None)):
        row=fetch_asset({'name':'test','bank':'za','isin':'LU1046235906'},START,END)
        assert row['Ultimo prezzo'] is None and row['Fonte']=='N/D'


def test_mm_and_ig_use_ft_without_a_ticker():
    data = pd.Series([10, 12], index=pd.to_datetime(['2025-12-30', '2026-10-29']))
    for bank in ('mm', 'IG'):
        with patch('quotes.yahoo_serie', return_value=(None, None)) as yahoo, \
             patch('quotes.ft_serie', return_value=(data, 'FT:test')) as ft, \
             patch('quotes.fetch_nav') as morningstar:
            row = fetch_asset({'name': 'test', 'bank': bank, 'isin': 'IE0009625199'}, date(2025,12,31), END)
            assert row['Ultimo prezzo'] == 12 and row['Fonte'] == 'FT:test'
            yahoo.assert_called_once()
            ft.assert_called_once()
            morningstar.assert_not_called()


def test_configured_ticker_avoids_browser_and_search():
    data = pd.DataFrame({'Close': [10, 12]}, index=pd.to_datetime(['2025-12-30', '2026-10-29']))
    ticker = Mock(); ticker.history.return_value = data
    with patch('yfinance.Ticker', return_value=ticker), patch('quotes.yahoo_serie') as search, \
         patch('quotes.fetch_nav') as morningstar:
        row = fetch_asset({'name': 'test', 'bank': 'mm', 'isin': 'IT0005618555', 'ticker': 'TEST.F'}, date(2025,12,31), END)
        assert row['Ultimo prezzo'] == 12 and row['Fonte'] == 'Yahoo: TEST.F'
        search.assert_not_called()
        morningstar.assert_not_called()


def test_invalid_isin_is_reported_without_remote_requests():
    with patch('quotes.yahoo_serie') as yahoo, patch('quotes.ft_serie') as ft, patch('quotes.fetch_nav') as morningstar:
        row = fetch_asset({'name': 'LHA', 'bank': 'mm', 'isin': 'IE000B2NLMV86'}, START, END)
        assert row['Ultimo prezzo'] is None and 'ISIN non valido' in row['Dettaglio']
        yahoo.assert_not_called(); ft.assert_not_called(); morningstar.assert_not_called()


def test_bond_is_not_requested_as_a_fund():
    with patch('quotes.yahoo_serie') as yahoo, patch('quotes.ft_serie') as ft, patch('quotes.fetch_nav') as morningstar:
        row = fetch_asset({'name': 'BTP', 'bank': 'mm', 'isin': 'IT0005565392',
                           'url': 'https://www.borsaitaliana.it/obbligazioni/btp-valore/scheda.html'}, START, END)
        assert row['Ultimo prezzo'] is None and 'fonte dedicata' in row['Dettaglio']
        yahoo.assert_not_called(); ft.assert_not_called(); morningstar.assert_not_called()


def test_morningstar_remains_last_fallback():
    raw = [{'date': '2025-12-30', 'nav': 10}, {'date': '2026-10-29', 'nav': 12}]
    with patch('quotes.yahoo_serie', return_value=(None, None)), \
         patch('quotes.ft_serie', return_value=(None, None)), patch('quotes.fetch_nav', return_value=raw):
        row = fetch_asset({'name': 'test', 'bank': 'mm', 'isin': 'IE0009625199'}, date(2025,12,31), END)
        assert row['Fonte'] == 'Morningstar' and row['Ultimo prezzo'] == 12
