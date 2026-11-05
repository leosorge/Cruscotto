import json

import pytest
from streamlit.testing.v1 import AppTest

from asset_catalog import assets_from_rows, editor_rows, save_assets, load_assets_json


def sample_catalog():
    # L'anagrafica dell'utente è modificabile: i test usano dati indipendenti.
    return [dict(bank='mm' if i < 12 else 'IG' if i < 18 else 'za',
                 name=f'Titolo {i + 1}', isin='LU1046235906',
                 ticker='TEST.F', currency='EUR') for i in range(30)]


def test_report_with_only_one_bank_has_distinct_charts():
    from datetime import date
    from pathlib import Path
    import pandas as pd
    at = AppTest.from_file(str(Path(__file__).with_name('app.py'))).run(timeout=30)
    at.session_state['report'] = pd.DataFrame([{
        'N.': 1, 'Banca': 'mm', 'Titolo': 'Prova', 'Variazione %': 2.,
        'Ultimo prezzo': 102., 'Prezzo iniziale': 100.,
        'Fonte': 'Test', 'Data prezzo': '2026-11-05',
    }])
    at.session_state['period'] = (date(date.today().year, 1, 1), date.today())
    at.session_state['updated'] = 'test'
    at.multiselect[0].set_value(['mm']).run()
    assert not at.exception
    assert len(at.get('plotly_chart')) == 2


def test_edit_add_delete_and_atomic_save(tmp_path):
    originals = [dict(bank='mm', name='Primo', isin='LU1046235906', ticker='OLD.F', url='old'),
                 dict(bank='za', name='Secondo', isin='LU0171310443')]
    rows = editor_rows(originals)
    rows[0]['ISIN'] = 'IE0005380518'
    rows = rows[:1] + [dict(N=None, Banca='IG', Titolo='Nuovo', ISIN='LU0171310443', Valuta='EUR')]
    updated = assets_from_rows(rows, originals)
    assert len(updated) == 2
    assert updated[0]['isin'] == 'IE0005380518'
    assert updated[0]['ticker'] == '' and 'url' not in updated[0]
    assert updated[1]['name'] == 'Nuovo'
    path = tmp_path / 'titoli.json'
    path.write_text(json.dumps(originals))
    save_assets(path, updated, originals)
    assert json.loads(path.read_text()) == updated
    with pytest.raises(ValueError, match='altra sessione'):
        save_assets(path, originals, originals)


def test_validation_and_empty_catalog():
    with pytest.raises(ValueError, match='ISIN non valido'):
        assets_from_rows([dict(Banca='za', Titolo='Errore', ISIN='errato', Valuta='EUR')], [])
    assert assets_from_rows([], []) == []


def test_json_roundtrip_and_validation():
    from pathlib import Path
    assets = sample_catalog()
    assert load_assets_json(json.dumps(assets).encode('utf-8-sig')) == assets
    assert load_assets_json('[]') == []
    for invalid in ('{', '{}', '[1]', '[{"bank":"za"}]',
                    '[{"bank":"za","name":"Test","isin":"errato"}]'):
        with pytest.raises(ValueError):
            load_assets_json(invalid)


def test_explicit_delete_control(tmp_path):
    from pathlib import Path
    source = Path(__file__).parent
    (tmp_path / 'app.py').write_text((source / 'app.py').read_text())
    assets = sample_catalog()
    path = tmp_path / 'titoli.json'
    path.write_text(json.dumps(assets))
    at = AppTest.from_file(str(tmp_path / 'app.py')).run(timeout=30)
    at.toggle[0].set_value(True).run()
    next(b for b in at.button if b.label == 'Elimina titoli selezionati').click().run()
    assert at.warning and json.loads(path.read_text()) == assets
    next(m for m in at.multiselect if m.label == 'Titoli da eliminare').set_value([1, 3])
    at.session_state['catalog_editor_0'] = {
        'edited_rows': {1: {'Titolo': 'Nome aggiornato'}},
        'added_rows': [], 'deleted_rows': [],
    }
    next(b for b in at.button if b.label == 'Elimina titoli selezionati').click().run()
    assert not at.exception
    saved = json.loads(path.read_text())
    assert len(saved) == len(assets) - 2
    assert saved[0]['name'] == 'Nome aggiornato'
    assert assets[0]['name'] not in [a['name'] for a in saved]
    assert assets[2]['name'] not in [a['name'] for a in saved]
    at.toggle[0].set_value(False).run()
    assert at.dataframe[0].value['N.'].tolist() == list(range(1, 29))


def test_app_import_and_reject_invalid_file(tmp_path):
    from io import BytesIO
    from pathlib import Path
    from unittest.mock import patch
    source = Path(__file__).parent
    (tmp_path / 'app.py').write_text((source / 'app.py').read_text())
    assets = sample_catalog()
    path = tmp_path / 'titoli.json'
    path.write_text(json.dumps(assets))
    at = AppTest.from_file(str(tmp_path / 'app.py')).run(timeout=30)
    imported = [dict(bank='za', name='Dal PC', isin='LU0171310443', currency='EUR')]
    with patch('streamlit.file_uploader', return_value=BytesIO(json.dumps(imported).encode())):
        next(b for b in at.button if b.label == 'Applica JSON caricato').click().run()
    assert not at.exception
    assert json.loads(path.read_text()) == imported
    assert len(at.dataframe[0].value) == 1
    assert at.dataframe[0].value['Titolo'].tolist() == ['Dal PC']
    with patch('streamlit.file_uploader', return_value=BytesIO(b'not json')):
        next(b for b in at.button if b.label == 'Applica JSON caricato').click().run()
    assert not at.exception
    assert at.error
    assert json.loads(path.read_text()) == imported


def test_app_editor_save_and_numbering(tmp_path):
    # Run a copy so UI tests never write the user's actual catalog.
    from pathlib import Path
    source = Path(__file__).parent
    (tmp_path / 'app.py').write_text((source / 'app.py').read_text())
    assets = sample_catalog()
    path = tmp_path / 'titoli.json'
    path.write_text(json.dumps(assets))
    at = AppTest.from_file(str(tmp_path / 'app.py')).run(timeout=30)
    assert not at.exception
    assert at.dataframe[0].value['N.'].tolist() == list(range(1, 31))
    at.multiselect[0].set_value(['za']).run()
    assert len(at.dataframe[0].value) == 12
    assert at.dataframe[0].value['N.'].tolist() == list(range(19, 31))
    at.toggle[0].set_value(True).run()
    assert not at.exception
    key = 'catalog_editor_0'
    at.session_state[key] = {
        'edited_rows': {0: {'ISIN': 'IE0005380518'}},
        'added_rows': [{'Banca': 'za', 'Titolo': 'Nuovo', 'ISIN': 'LU0171310443', 'Valuta': 'EUR'}],
        'deleted_rows': [1],
    }
    next(b for b in at.button if b.label == 'Salva anagrafica').click().run()
    assert not at.exception
    saved = json.loads(path.read_text())
    assert len(saved) == 30
    assert saved[0]['isin'] == 'IE0005380518' and saved[0]['ticker'] == ''
    assert saved[-1]['name'] == 'Nuovo'
    assert assets[1]['name'] not in [a['name'] for a in saved]
    assert at.success
