"""Conversione e salvataggio dell'anagrafica modificabile."""
import json
import os
from pathlib import Path
import re
import tempfile


def load_assets_json(data):
    """Legge un backup senza perdere ticker, link o identificativi alternativi."""
    try:
        payload = json.loads(data.decode('utf-8-sig') if isinstance(data, bytes) else data)
    except (ValueError, UnicodeError) as exc:
        raise ValueError('Il file non contiene un JSON valido in formato UTF-8.') from exc
    if not isinstance(payload, list):
        raise ValueError('Il JSON deve contenere un elenco di titoli, come il file esportato dall’app.')
    for position, asset in enumerate(payload, 1):
        if not isinstance(asset, dict) or any(not isinstance(v, str) for v in asset.values()):
            raise ValueError(f'Riga {position}: ogni titolo deve contenere campi testuali.')
        if not asset.get('name', '').strip() or asset.get('bank') not in ('IG', 'mm', 'za'):
            raise ValueError(f'Riga {position}: indicare titolo e banca (IG, mm o za).')
    # Usa gli stessi controlli dell’editor; conserva il formato originale dei backup.
    assets_from_rows(editor_rows(payload), payload)
    return payload


def editor_rows(assets):
    return [dict(N=i, Banca=a['bank'], Titolo=a['name'],
                 ISIN=a.get('deltahedge_isin') or a.get('isin', ''),
                 Valuta=a.get('currency', 'EUR'), Ticker=a.get('ticker', ''))
            for i, a in enumerate(assets, 1)]


def assets_from_rows(rows, originals):
    result = []
    for position, row in enumerate(rows, 1):
        def value(key):
            raw = row.get(key)
            return '' if raw is None or str(raw) in ('nan', '<NA>') else str(raw).strip()

        number = row.get('N')
        original = originals[int(number) - 1].copy() if number is not None and str(number) not in ('nan', '<NA>') else {}
        bank, name = value('Banca'), value('Titolo')
        isin, currency, ticker = value('ISIN').upper(), value('Valuta').upper(), value('Ticker')
        if bank not in ('IG', 'mm', 'za') or not name:
            raise ValueError(f'Riga {position}: indicare banca e titolo.')
        if isin and not re.fullmatch(r'[A-Z]{2}[A-Z0-9]{9}[0-9]', isin):
            raise ValueError(f'Riga {position}: ISIN non valido (servono 12 caratteri).')
        if not re.fullmatch(r'[A-Z]{3}', currency):
            raise ValueError(f'Riga {position}: indicare una valuta di tre lettere, per esempio EUR.')
        if not isin and not ticker:
            raise ValueError(f'Riga {position}: indicare un ISIN o un ticker Yahoo.')
        old_isin = original.get('deltahedge_isin') or original.get('isin', '')
        if isin != old_isin:
            # Un ticker o link della vecchia classe può restituire prezzi errati.
            if ticker == original.get('ticker', ''):
                ticker = ''
            original.pop('url', None)
        if not isin and not ticker:
            raise ValueError(f'Riga {position}: indicare un ISIN o un nuovo ticker Yahoo.')
        original.pop('deltahedge_isin', None)
        original.update(bank=bank, name=name, isin=isin, currency=currency, ticker=ticker)
        result.append(original)
    return result


def save_assets(path, assets, expected):
    """Sostituzione atomica; rifiuta modifiche basate su una versione superata."""
    path = Path(path)
    if json.loads(path.read_text(encoding='utf-8')) != expected:
        raise ValueError('Anagrafica modificata da un’altra sessione. Ricarica la pagina prima di riprovare.')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.titoli-', suffix='.json', delete=False) as output:
            temporary = output.name
            json.dump(assets, output, ensure_ascii=False, indent=2)
            output.write('\n')
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
