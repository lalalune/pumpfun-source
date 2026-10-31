"""Run the actual producer/verifier CLIs over signed local captured-ELF controls.

This probes receipt transport, not reconstructed source or successful trades.
Each producer invokes two real LiteSVM instances with normal owned signatures.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'work/scoped-proof'
CAPTURE = ROOT / 'evidence/original/mayhem/deployed.so'
ORIGINAL_SHA = 'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb'
MODES = (
    ('buy_v2', 'mayhem_buy_v2_differential.py', 'verify_mayhem_buy_v2.py', []),
    ('sell_v2', 'mayhem_sell_v2_differential.py', 'verify_mayhem_sell_v2.py', []),
    ('buy_pump_swap', 'mayhem_pump_swap_differential.py', 'verify_mayhem_pump_swap.py', ['--instruction', 'buy_pump_swap']),
    ('sell_pump_swap', 'mayhem_pump_swap_differential.py', 'verify_mayhem_pump_swap.py', ['--instruction', 'sell_pump_swap']),
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def run(script, *arguments):
    command = [sys.executable, '-B', str(ROOT / 'scripts' / script), *map(str, arguments)]
    env = dict(os.environ)
    env.pop('PYTHONOPTIMIZE', None)
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, encoding='utf-8',
                            errors='replace', capture_output=True, timeout=180)
    return {'command': command, 'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    assert sha(CAPTURE) == ORIGINAL_SHA
    transition = json.loads((HERE / 'proposed-asset-transition.json').read_text())
    current = {name: sha(ROOT / name) for name in transition['before']}
    stage = next((key for key in ('before', 'after') if current == transition[key]), None)
    if stage is None:
        raise RuntimeError('producer source differs from both reviewed revisions')
    OUT.mkdir(parents=True, exist_ok=False)
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    results = []
    errors = []
    for mode, producer, verifier, extra in MODES:
        directory = OUT / mode
        directory.mkdir()
        records = {}
        for label, filename in (('plain', 'report.json'), ('gzip', 'report.json.gz'), ('repeat', 'repeat.json.gz')):
            path = directory / filename
            produced = run(producer, '--candidate', CAPTURE, '--cases', HERE / 'cases.json',
                           '--family', 'native', *extra, '--output', path)
            record = {'producer': produced}
            records[label] = record
            save(directory / (label + '-commands.json'), record)
            if produced['returncode'] != 0 or not path.is_file():
                raise RuntimeError(f'{mode}/{label} genuine producer failed: {produced}')
            wire = path.read_bytes()
            compressed = wire.startswith(b'\x1f\x8b')
            raw = gzip.decompress(wire) if compressed else wire
            report = json.loads(raw)
            assert report['case_count'] == 1 and report['signed_transactions'] == 2
            assert not report['mismatches'] and report['successful_original_cases'] == 0
            assert report['candidate_sha256'] == report['original_sha256'] == ORIGINAL_SHA
            assert all(pair[side]['signature_verified'] and pair[side]['error'] is not None
                       for pair in report['cases'] for side in ('original', 'candidate'))
            verified_path = directory / (label + '-verified.json')
            verified = run(verifier, '--receipts', path, '--candidate', CAPTURE, '--output', verified_path)
            record.update({'verifier': verified, 'compressed': compressed,
                           'wire_sha256': sha(path), 'decoded_sha256': hashlib.sha256(raw).hexdigest(),
                           'real_vm_sends': 2})
            save(directory / (label + '-commands.json'), record)
            expected_gzip = label != 'plain' and stage == 'after'
            if compressed != expected_gzip:
                errors.append(f'{mode}/{label}: unexpected compression={compressed}')
            expected_status = 0 if label == 'plain' or stage == 'after' else 1
            if verified['returncode'] != expected_status:
                errors.append(f'{mode}/{label}: verifier expected {expected_status}, got {verified["returncode"]}')
            elif expected_status == 1:
                if 'BadGzipFile' not in verified['stderr'] or verified_path.exists():
                    errors.append(f'{mode}/{label}: expected suffix-decoder failure before publication')
            else:
                verdict = json.loads(verified_path.read_bytes())
                if verdict['verified_signed_transactions'] != 2 or verdict['mismatches']:
                    errors.append(f'{mode}/{label}: verifier did not admit the real signed pair')
            if compressed and wire[4:8] != bytes(4):
                errors.append(f'{mode}/{label}: gzip mtime is not deterministic')
        if len({row['decoded_sha256'] for row in records.values()}) != 1:
            errors.append(mode + ': plain and compressed report contents differ')
        if records['gzip']['wire_sha256'] != records['repeat']['wire_sha256']:
            errors.append(mode + ': repeated gzip-named outputs are not deterministic')
        results.append({'mode': mode, 'records': records})
    summary = {'revision': revision, 'stage': stage, 'producer_sha256': current,
        'capture_sha256': ORIGINAL_SHA, 'modes': results, 'errors': errors,
        'real_vm_sends': 24,
        'scope': 'Actual signed local captured-image control; receipt producer/verifier transport only',
        'limits': 'Owned paused rejection only; no successful-trade, source-reconstruction, whole-ELF or security claim'}
    save(OUT / 'summary.json', summary)
    print(json.dumps({'stage': stage, 'real_vm_sends': 24,
        'verifier_statuses': {row['mode']: {name: value['verifier']['returncode']
             for name, value in row['records'].items()} for row in results}, 'errors': errors}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
