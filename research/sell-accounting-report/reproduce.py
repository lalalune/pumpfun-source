"""Actual Rust arithmetic hosts and captured SBF producer/consumer workflow."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
BUILD = ROOT / 'work/sell-accounting-proof'
PROOF.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as stream:
        return subprocess.run(command, cwd=ROOT, stdout=stream,
                              stderr=subprocess.STDOUT, timeout=300).returncode


with (PROOF / 'rustc-version.txt').open('w') as stream:
    subprocess.run(['rustc', '--version', '--verbose'], stdout=stream, check=True)
hosts = {}
for name in ('constant_product', 'sell_accounting'):
    hosts[name] = BUILD / name
    assert run('compile-' + name, ['rustc', '--edition=2021', '-O',
                str(ROOT / 'programs/pump/recovered' / (name + '_host.rs')),
                '-o', str(hosts[name])]) == 0
curve = PROOF / 'fresh-curve-report.json'
assert run('producer', [sys.executable, '-B', 'scripts/pump_validate_constant_product.py',
                       '--host', str(hosts['constant_product']), '--output', str(curve)]) == 0
actual = json.loads(curve.read_text())
assert actual['case_count'] == len(actual['cases']) == 161
assert actual['successful_comparisons'] == 160 and not actual['mismatches']
consumer = [sys.executable, '-B', 'scripts/pump_validate_sell_accounting.py',
            '--host', str(hosts['sell_accounting'])]
# Preserve the actual old interface failure as well as the proposed report connection.
legacy_rc = run('legacy-consumer', consumer + ['--output', str(PROOF / 'legacy.json')])
output = PROOF / 'accounting.json'
rc = run('connected-consumer', consumer + ['--curve-report', str(curve), '--output', str(output)])
summary = {'actual_producer_cases': actual['case_count'],
           'actual_producer_comparisons': actual['successful_comparisons'],
           'actual_curve_report_sha256': sha(curve), 'legacy_consumer_exit': legacy_rc,
           'connected_consumer_exit': rc}
if rc == 0:
    result = json.loads(output.read_text())
    assert result['case_count'] == len(result['cases']) == 206 and not result['mismatches']
    assert all(row['match'] for row in result['cases'])
    assert result['fixture_report_sha256'] == sha(curve)
    wrong_dir = BUILD / 'wrong-model'
    wrong_dir.mkdir()
    for name in ('sell_accounting.rs', 'sell_accounting_host.rs'):
        shutil.copyfile(ROOT / 'programs/pump/recovered' / name, wrong_dir / name)
    source = wrong_dir / 'sell_accounting.rs'
    text = source.read_text()
    assert text.count('+ 9999') == 1
    source.write_text(text.replace('+ 9999', '+ 0'))
    wrong_host = BUILD / 'floor-model'
    assert run('compile-wrong-model', ['rustc', '--edition=2021', '-O', str(wrong_dir / 'sell_accounting_host.rs'), '-o', str(wrong_host)]) == 0
    wrong_output = PROOF / 'wrong-model.json'
    wrong_rc = run('wrong-model', [sys.executable, '-B', 'scripts/pump_validate_sell_accounting.py',
                   '--host', str(wrong_host), '--curve-report', str(curve), '--output', str(wrong_output)])
    wrong_result = json.loads(wrong_output.read_text())
    assert wrong_rc != 0 and wrong_result['mismatches']
    rejected = []
    for name in ('wrong-original', 'missing-case', 'wrong-count', 'failed-comparison'):
        changed = json.loads(curve.read_text())
        if name == 'wrong-original':
            changed['original_sha256']['pump'] = sha(ROOT / 'evidence/original/mayhem/deployed.so')
        elif name == 'missing-case':
            changed['cases'].pop()
        elif name == 'wrong-count':
            changed['successful_comparisons'] += 1
        else:
            next(row for row in changed['cases'] if row['compared'])['match'] = False
        path = PROOF / (name + '.input.json')
        path.write_text(json.dumps(changed) + '\n')
        target = PROOF / (name + '.output.json')
        negative_rc = run(name, consumer + ['--curve-report', str(path), '--output', str(target)])
        assert negative_rc != 0 and not target.exists()
        rejected.append(name)
    summary.update(actual_accounting_cases=result['case_count'], actual_accounting_mismatches=0,
                   wrong_native_model_rejected=True, wrong_native_model_mismatches=len(wrong_result['mismatches']),
                   invalid_reports_rejected=rejected)
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert rc == 0, 'sell accounting cannot consume the genuine current arithmetic producer report'
