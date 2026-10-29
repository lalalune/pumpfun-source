"""Reject legacy-loader captures that declare upgradeable metadata.

`scripts/verify_evidence.py` checks the legacy branch's payload hashes, owner
and genesis, but never reads `last_deploy_slot`, `upgrade_authority` or the
programdata keys. A legacy capture can therefore claim a deploy slot, an upgrade
authority and programdata bytes while still passing the archived gate.

The legacy loader stores the ELF in the program account and has no ProgramData
account, deployment slot or upgrade authority. This packet checks those fields
for every retained capture: legacy records must have null slot/authority and no
programdata keys; upgradeable records must carry an integer slot and an optional
valid 32-byte authority. No captured byte or archived report is rewritten.
"""
from pathlib import Path
import gzip
import hashlib
import json

P = Path(__file__).resolve().parent
REPO = next(
    parent for parent in P.parents
    if (parent / 'evidence/original/pump/deployed.so').is_file()
)
CAPTURES = (
    'evidence/original/pump',
    'evidence/original/pump_amm',
    'evidence/original/pump_fees',
    'evidence/original/mayhem',
    'evidence/dependencies/spl_token',
    'evidence/dependencies/spl_token_2022',
    'evidence/dependencies/associated_token',
    'evidence/dependencies/token_metadata',
    'evidence/dependencies/donation_relay',
)
LEGACY = frozenset({'evidence/dependencies/associated_token'})
LEGACY_OWNER = 'BPFLoader2111111111111111111111111111111111'
UPGRADEABLE_OWNER = 'BPFLoaderUpgradeab1e11111111111111111111111'
PROGRAMDATA_KEYS = ('programdata', 'programdata_sha256', 'programdata_bytes')
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
sha = lambda data: hashlib.sha256(data).hexdigest()


def b58decode(text):
    number = 0
    for character in text:
        number = number * 58 + ALPHABET.index(character)
    body = number.to_bytes((number.bit_length() + 7) // 8, 'big')
    return bytes(len(text) - len(text.lstrip('1'))) + body


def b58encode(data):
    number = int.from_bytes(data, 'big')
    text = ''
    while number:
        number, remainder = divmod(number, 58)
        text = ALPHABET[remainder] + text
    return '1' * (len(data) - len(data.lstrip(b'\0'))) + text


def validate(record, folder):
    failures = []
    loader = record.get('loader')
    if loader == 'legacy-v2':
        if record.get('last_deploy_slot') is not None:
            failures.append(folder + ' legacy deploy slot')
        if record.get('upgrade_authority') is not None:
            failures.append(folder + ' legacy upgrade authority')
        present = [key for key in PROGRAMDATA_KEYS if key in record]
        if present:
            failures.append(folder + ' legacy programdata keys: ' + ','.join(present))
        if record.get('owner') != LEGACY_OWNER:
            failures.append(folder + ' legacy owner')
    else:
        if not isinstance(record.get('last_deploy_slot'), int):
            failures.append(folder + ' upgradeable slot')
        authority = record.get('upgrade_authority')
        if authority is not None:
            try:
                key = b58decode(authority)
            except (ValueError, TypeError):
                key = b''
            if len(key) != 32 or b58encode(key) != authority:
                failures.append(folder + ' upgradeable authority')
        if any(key not in record for key in PROGRAMDATA_KEYS):
            failures.append(folder + ' upgradeable programdata keys')
        if record.get('owner') != UPGRADEABLE_OWNER:
            failures.append(folder + ' upgradeable owner')
    return failures


def check(root=REPO):
    root = Path(root).resolve()
    rows = []
    failures = []
    legacy = 0
    for folder in CAPTURES:
        record = json.loads((root / folder / 'capture.json').read_text())
        rows.append({
            'folder': folder,
            'loader': record.get('loader'),
            'owner': record.get('owner'),
            'last_deploy_slot': record.get('last_deploy_slot'),
            'upgrade_authority': record.get('upgrade_authority'),
            'programdata_keys_present': [k for k in PROGRAMDATA_KEYS if k in record],
        })
        row_failures = validate(record, folder)
        failures.extend(row_failures)
        legacy += record.get('loader') == 'legacy-v2'
    if failures:
        raise ValueError('; '.join(failures))
    assert len(rows) == 9
    assert legacy == 1
    assert sum(row['loader'] != 'legacy-v2' for row in rows) == 8
    return {
        'scope': 'Declared legacy/upgradeable metadata consistency; no captured byte re-read.',
        'captures': rows,
        'legacy_captures': legacy,
        'upgradeable_captures': len(rows) - legacy,
    }


def seal(packet=P):
    packet = Path(packet)
    report = check(REPO)
    (packet / 'observations.json.gz').write_bytes(
        gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0)
    )
    (packet / 'coverage-delta.json').write_text(
        json.dumps({
            'kind': 'tooling',
            'scope': 'Legacy capture metadata validation; no payload-byte claim.',
            'totals': {
                'captures': len(report['captures']),
                'legacy_captures': report['legacy_captures'],
                'upgradeable_captures': report['upgradeable_captures'],
            },
        }, indent=2) + '\n'
    )
    inventory = {
        str(path.relative_to(packet)): sha(path.read_bytes())
        for path in sorted(packet.rglob('*'))
        if path.is_file() and path.name != 'manifest.json'
        and '__pycache__' not in path.parts and path.suffix != '.pyc'
    }
    (packet / 'manifest.json').write_text(json.dumps(inventory, indent=2) + '\n')
    return report['legacy_captures']


if __name__ == '__main__':
    print(seal())
