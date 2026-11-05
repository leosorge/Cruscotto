from datetime import date, datetime
from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st
from quotes import fetch_asset
from asset_catalog import editor_rows, assets_from_rows, save_assets, load_assets_json

st.set_page_config(page_title='Finance · IG / mm / za', page_icon='📊', layout='wide')
st.title('Finance · Cruscotto')
st.caption('Fondi IG / mm / za · Yahoo e FT per ISIN · Morningstar come fonte alternativa per IG e mm')
catalog_path = Path(__file__).with_name('titoli.json')
assets = json.loads(catalog_path.read_text(encoding='utf-8'))


def catalog_updated():
    for key in ('report', 'period', 'updated', 'catalog_baseline'):
        st.session_state.pop(key, None)
    st.session_state['catalog_revision'] = st.session_state.get('catalog_revision', 0) + 1
    st.session_state['catalog_saved'] = True


st.caption(f'Lista di osservazione · IG / mm / za · {len(assets)} titoli')
st.info('Quantità convenzionale: 1 per titolo. Il cruscotto confronta prezzi e variazioni; non calcola il valore del patrimonio. Le variazioni dei prezzi non includono cedole o distribuzioni.')
with st.sidebar:
    st.header('Periodo e filtri')
    start = st.date_input('Data di confronto', date(date.today().year, 1, 1), max_value=date.today())
    end = st.date_input('Data finale', date.today(), min_value=start, max_value=date.today())
    banks = st.multiselect('Banche', ['IG', 'mm', 'za'], default=['IG', 'mm', 'za'])
    update = st.button('Aggiorna quotazioni', type='primary', width='stretch')
    st.caption('Il prezzo iniziale è l’ultima quotazione disponibile entro la data di confronto. Ogni prezzo riporta la propria data.')
    editing = st.toggle('Modifica anagrafica')
    st.subheader('Anagrafica sul PC')
    st.download_button('Salva JSON sul PC', json.dumps(assets, ensure_ascii=False, indent=2),
                       'titoli.json', 'application/json')
    st.caption('Scarica l’ultima anagrafica salvata. Se stai modificando la tabella, premi prima Salva anagrafica.')
    with st.form('import_catalog'):
        upload = st.file_uploader('Carica JSON dal PC', type=['json'])
        st.caption('Il caricamento sostituisce tutta l’anagrafica del server, condivisa con gli altri utenti, e scarta le modifiche non salvate nell’editor. Non importa quotazioni.')
        import_submitted = st.form_submit_button('Applica JSON caricato')
    if import_submitted:
        if upload is None:
            st.error('Seleziona un file JSON dal tuo PC.')
        else:
            try:
                imported_assets = load_assets_json(upload.getvalue())
                save_assets(catalog_path, imported_assets, assets)
            except (ValueError, OSError) as exc:
                st.error(str(exc))
            else:
                catalog_updated()
                st.rerun()
if st.session_state.pop('catalog_saved', False):
    st.success('Anagrafica salvata. Aggiorna le quotazioni per i nuovi dati.')
if editing:
    if 'catalog_baseline' not in st.session_state:
        st.session_state['catalog_baseline'] = assets
    baseline = st.session_state['catalog_baseline']
    st.subheader('Modifica titoli')
    st.caption('Modifica le celle; usa la riga vuota in fondo per aggiungere un titolo. Per cancellare usa il comando Elimina titoli sotto la tabella. I numeri seguono l’ordine dell’anagrafica e vengono ricalcolati dopo il salvataggio.')
    st.info('Se cambi ISIN, il ticker e il link della vecchia classe vengono rimossi. Puoi indicare un nuovo ticker nella stessa modifica. Il salvataggio aggiorna titoli.json sul server; su hosting con disco temporaneo, scarica anche una copia JSON.')
    with st.form('catalog_form'):
        edited = st.data_editor(
            pd.DataFrame(editor_rows(baseline), columns=['N', 'Banca', 'Titolo', 'ISIN', 'Valuta', 'Ticker']),
            num_rows='dynamic', hide_index=True, width='stretch', disabled=['N'],
            column_config={
                'N': st.column_config.NumberColumn('N.', format='%d', width=62),
                'Banca': st.column_config.SelectboxColumn(options=['IG', 'mm', 'za'], required=True, width=74),
                'Titolo': st.column_config.TextColumn(required=True, width=324),
                'ISIN': st.column_config.TextColumn(width=190),
                'Valuta': st.column_config.TextColumn(default='EUR', required=True, width=74),
                'Ticker': st.column_config.TextColumn('Ticker Yahoo', width=270),
            }, key='catalog_editor_' + str(st.session_state.get('catalog_revision', 0)))
        submitted = st.form_submit_button('Salva anagrafica')
        st.markdown('**Elimina titoli**')
        to_delete = st.multiselect(
            'Titoli da eliminare', options=list(range(1, len(baseline) + 1)),
            format_func=lambda n: f"{n}. {baseline[n - 1]['bank']} · {baseline[n - 1]['name']}",
            key='delete_assets_' + str(st.session_state.get('catalog_revision', 0)))
        st.caption('Il pulsante elimina le voci scelte e salva anche le altre modifiche presenti nella tabella.')
        delete_submitted = st.form_submit_button('Elimina titoli selezionati')
    if delete_submitted and not to_delete:
        st.warning('Seleziona almeno un titolo da eliminare.')
    if submitted or (delete_submitted and to_delete):
        try:
            records = edited.to_dict('records')
            if delete_submitted:
                records = [row for row in records if row.get('N') not in to_delete]
            updated_assets = assets_from_rows(records, baseline)
            save_assets(catalog_path, updated_assets, baseline)
        except (ValueError, OSError) as exc:
            st.error(str(exc))
        else:
            catalog_updated()
            st.rerun()
    st.stop()
st.session_state.pop('catalog_baseline', None)
if update:
    rows = []
    progress = st.progress(0, text='Recupero quotazioni')
    for i, asset in enumerate(assets):
        progress.progress(i / len(assets), text=f"{asset['bank']} · {asset['name']}")
        try:
            rows.append(fetch_asset(asset, start, end))
        except Exception as exc:
            rows.append({'Titolo': asset['name'], 'Banca': asset['bank'], 'ISIN': asset.get('deltahedge_isin') or asset.get('isin', ''), 'Stato': 'Errore', 'Dettaglio': str(exc)[:200]})
        rows[-1] = {'N.': i + 1, **rows[-1]}
    progress.empty()
    st.session_state['report'] = pd.DataFrame(rows) if rows else pd.DataFrame(columns=['N.', 'Titolo', 'Banca', 'ISIN'])
    st.session_state['period'] = (start, end)
    st.session_state['updated'] = datetime.now().isoformat(timespec='seconds')
if 'report' not in st.session_state:
    st.write('Premi Aggiorna quotazioni per recuperare i dati.')
    st.dataframe(pd.DataFrame([{'N.': i, 'Banca': a['bank'], 'Titolo': a['name'], 'ISIN': a.get('deltahedge_isin') or a.get('isin', ''), 'Valuta': a.get('currency', 'EUR')} for i, a in enumerate(assets, 1) if a['bank'] in banks]), hide_index=True, width='stretch',
                 column_config={
                     'N.': st.column_config.NumberColumn(format='%d', width=62),
                     'Banca': st.column_config.TextColumn(width=74),
                     'Titolo': st.column_config.TextColumn(width=324),
                     'ISIN': st.column_config.TextColumn(width=190),
                     'Valuta': st.column_config.TextColumn(width=74),
                 })
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
                st.plotly_chart(fig, width='stretch', key=f'chart_{label}')
            else:
                st.warning('Nessuna variazione disponibile per questa selezione.')
            st.dataframe(shown, hide_index=True, width='stretch')
    st.download_button('Scarica report CSV', frame.to_csv(index=False).encode('utf-8-sig'), 'finance_report.csv', 'text/csv')
    if 'Stato' in frame:
        missing = frame[frame['Stato'] != 'Disponibile']
        if not missing.empty:
            st.warning(f'{len(missing)} titoli senza quotazioni complete. Apri “Motivi dei dati mancanti” per i dettagli.')
            with st.expander('Motivi dei dati mancanti'):
                columns = [c for c in ['N.', 'Titolo', 'ISIN', 'Stato', 'Dettaglio'] if c in missing]
                st.dataframe(missing[columns], hide_index=True, width='stretch')
    with st.expander('Riepilogo per banca'):
        st.caption('Media aritmetica delle variazioni disponibili, senza ponderazione patrimoniale.')
        st.dataframe(frame.groupby('Banca')['Variazione %'].agg(['count', 'mean', 'min', 'max']))
    st.caption('I titoli senza storico restano N/D. I link Borsa presenti nei notebook sono conservati per controllo manuale; nessun prezzo viene dedotto da testo generico della pagina.')

