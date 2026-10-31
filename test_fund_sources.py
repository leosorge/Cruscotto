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
