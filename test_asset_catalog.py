import json

import pytest
from streamlit.testing.v1 import AppTest

from asset_catalog import assets_from_rows, editor_rows, save_assets


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


def test_app_editor_save_and_numbering(tmp_path):
    # Run a copy so UI tests never write the user's actual catalog.
    from pathlib import Path
    source = Path(__file__).parent
    (tmp_path / 'app.py').write_text((source / 'app.py').read_text())
    assets = json.loads((source / 'titoli.json').read_text())
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
