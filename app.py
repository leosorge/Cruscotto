from datetime import date, datetime
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from quotes import fetch_asset

st.set_page_config(page_title='Finance · IG / mm / za', page_icon='📊', layout='wide')
st.title('Finance · Cruscotto')
st.caption('Lista di osservazione · IG / mm / za · 25 titoli')
assets = json.loads(Path(__file__).with_name('titoli.json').read_text())
st.info('Quantità convenzionale: 1 per titolo. Il cruscotto confronta prezzi e variazioni; non calcola il valore del patrimonio. Le variazioni dei prezzi non includono cedole o distribuzioni.')
with st.sidebar:
    st.header('Periodo e filtri')
    start = st.date_input('Data di confronto', date(date.today().year, 1, 1), max_value=date.today())
    end = st.date_input('Data finale', date.today(), min_value=start, max_value=date.today())
    banks = st.multiselect('Banche', ['IG', 'mm', 'za'], default=['IG', 'mm', 'za'])
    update = st.button('Aggiorna quotazioni', type='primary', width='stretch')
    st.caption('Il prezzo iniziale è l’ultima quotazione disponibile entro la data di confronto. Ogni prezzo riporta la propria data.')
if update:
    rows = []
    progress = st.progress(0, text='Recupero quotazioni')
    for i, asset in enumerate(assets):
        progress.progress(i / len(assets), text=f"{asset['bank']} · {asset['name']}")
        try:
            rows.append(fetch_asset(asset, start, end))
        except Exception as exc:
            rows.append({'Titolo': asset['name'], 'Banca': asset['bank'], 'Stato': 'Errore', 'Dettaglio': str(exc)[:200]})
    progress.empty()
    st.session_state['report'] = pd.DataFrame(rows)
    st.session_state['period'] = (start, end)
    st.session_state['updated'] = datetime.now().isoformat(timespec='seconds')
if 'report' not in st.session_state:
    st.write('Premi Aggiorna quotazioni per recuperare i dati.')
    st.dataframe(pd.DataFrame([{'Banca': a['bank'], 'Titolo': a['name'], 'Valuta': a.get('currency', 'EUR')} for a in assets if a['bank'] in banks]), hide_index=True, width='stretch')
else:
    frame = st.session_state['report'].copy()
    for col in ['Variazione %', 'Ultimo prezzo', 'Prezzo iniziale']:
        if col not in frame: frame[col] = None
    frame = frame[frame['Banca'].isin(banks)]
    st.caption(f"Recupero: {st.session_state['updated']} · Periodo del report: {st.session_state['period'][0]} – {st.session_state['period'][1]}")
    if st.session_state['period'] != (start, end):
        st.warning('Il periodo selezionato è cambiato. Premi Aggiorna per ricalcolare il report.')
    c1, c2, c3 = st.columns(3)
    c1.metric('Titoli selezionati', len(frame))
    c2.metric('Prezzi disponibili', int(frame['Ultimo prezzo'].notna().sum()))
    c3.metric('Variazioni disponibili', int(frame['Variazione %'].notna().sum()))
    tabs = st.tabs(['Tutti', 'IG', 'mm', 'za'])
    for label, tab in zip(['Tutti', 'IG', 'mm', 'za'], tabs):
        with tab:
            shown = frame if label == 'Tutti' else frame[frame.Banca == label]
            valid = shown.dropna(subset=['Variazione %']).sort_values('Variazione %')
            if not valid.empty:
                fig = px.bar(valid, x='Variazione %', y='Titolo', color='Banca', orientation='h', hover_data=['Fonte', 'Data prezzo'], height=max(400, len(valid)*32))
                fig.add_vline(x=0)
                st.plotly_chart(fig, width='stretch')
            else:
                st.warning('Nessuna variazione disponibile per questa selezione.')
            st.dataframe(shown, hide_index=True, width='stretch')
    st.download_button('Scarica report CSV', frame.to_csv(index=False).encode('utf-8-sig'), 'finance_report.csv', 'text/csv')
    with st.expander('Riepilogo per banca'):
        st.caption('Media aritmetica delle variazioni disponibili, senza ponderazione patrimoniale.')
        st.dataframe(frame.groupby('Banca')['Variazione %'].agg(['count', 'mean', 'min', 'max']))
    st.caption('I titoli senza storico restano N/D. I link Borsa presenti nei notebook sono conservati per controllo manuale; nessun prezzo viene dedotto da testo generico della pagina.')
