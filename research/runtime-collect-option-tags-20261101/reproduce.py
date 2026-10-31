"""Actual captured account decoding versus the native collect-fee model."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess

p = argparse.ArgumentParser()
p.add_argument('--repo', type=Path, required=True)
p.add_argument('--host', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
spec = importlib.util.spec_from_file_location('fixture', a.repo / 'tests/test_pump_amm_collect_coin_creator_fee_captured.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
original_build = m.build


def build(c):
    metas, accounts, payload, keys = original_build(c)
    for role, offset, value in c.get('raw_patches', ()):
        key = keys[role]
        account = accounts[key]
        raw = bytearray(account.data)
        raw[offset:offset + len(value)] = value
        accounts[key] = m.Account(account.lamports, bytes(raw), account.owner)
    return metas, accounts, payload, keys


m.build = build
cases = []
for program in ('spl', 't22'):
    for role, offsets in (('mint', (0, 46)), ('vault', (72, 109, 129)), ('dest', (72, 109, 129))):
        for offset in offsets:
            for tag in (0, 1, 2):
                cases.append((f'{program}_{role}_{offset}_tag{tag}',
                              {'token_prog': program, 'amount': 0,
                               'raw_patches': [(role, offset, struct.pack('<I', tag))]}))
            width = 8 if role != 'mint' and offset == 109 else 32
            cases.append((f'{program}_{role}_{offset}_inactive_payload',
                          {'token_prog': program, 'amount': 0,
                           'raw_patches': [(role, offset + 4, bytes([0xA5]) * width)]}))
    for role, offset, extra in [('mint', 0, {'mint_init': 0}), ('vault', 129, {'vault_state': 0}),
                                ('dest', 129, {'dest_state': 0}), ('vault', 72, {'vault_owner': 'system'})]:
        cases.append((f'{program}_{role}_{offset}_precedence',
                      {'token_prog': program, 'amount': 0, **extra,
                       'raw_patches': [(role, offset, struct.pack('<I', 2))]}))
lines = subprocess.run([str(a.host)], input=''.join(m.host_line(c) + '\n' for _, c in cases),
                       text=True, capture_output=True, check=True).stdout.splitlines()
assert len(lines) == len(cases)
checker = m.PumpAmmCollectCoinCreatorFeeCapturedTests()
rows = []
for (name, case), answer in zip(cases, lines):
    captured = m.run_captured(case)
    try:
        checker.assert_matches(answer, captured)
        mismatch = None
    except AssertionError as error:
        mismatch = str(error)
    rows.append({'name': name, 'host': answer, 'captured_error': captured['error'],
                 'unchanged_accounts': captured['before'] == captured['after'], 'mismatch': mismatch})
result = {'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=a.repo, text=True).strip(),
          'captured_sha256': {str(path.relative_to(a.repo)): digest for path, digest in m.ELF_SHA256.items()},
          'host_sha256': hashlib.sha256(a.host.read_bytes()).hexdigest(),
          'cases': len(rows), 'mismatches': sum(r['mismatch'] is not None for r in rows), 'rows': rows}
a.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'cases': result['cases'], 'mismatches': result['mismatches']}))
