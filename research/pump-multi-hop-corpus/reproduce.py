"""Build actual current Pump and execute its catalogued 56-case CPI suite."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
env = dict(os.environ, CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
           CARGO_BUILD_JOBS='2', RUSTC=str(SDK / 'rust/bin/rustc'))


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as log:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                              stderr=subprocess.STDOUT, timeout=1000).returncode


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/multi-hop-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)
build = ROOT / 'work/multi-hop-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
            '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
            '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
            '--target-library-directory', str(libraries), '--workspace-layout',
            '--output', str(build)]) == 0
for filename in ('build-comparison.json', 'build-attempt.json', 'build.log'):
    shutil.copyfile(build / filename, PROOF / filename)
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / (filename + '.gz')).write_bytes(gzip.compress((build / filename).read_bytes(), mtime=0))

sys.path.insert(0, str(ROOT / 'scripts'))
import pump_validate_all
name, filename = next(row for row in pump_validate_all.SUITES if row[0] == 'multi_hop_curve_partial')
assert pump_validate_all.EXPECTED_CASES[name] == 56
script = ROOT / filename if filename.startswith(('repro/', 'research/')) else ROOT / 'scripts' / filename
output = PROOF / 'positive.json'
code = run('positive', [sys.executable, '-B', str(script), '--candidate', str(build / 'candidate.so'),
                        '--output', str(output)])
(PROOF / 'entry.json').write_text(json.dumps({'catalogued_path': filename, 'exists': script.is_file(),
                                             'actual_returncode': code}, indent=2) + '\n')
assert code == 0 and output.is_file(), 'catalogued current multi-hop suite cannot execute'
result = json.loads(output.read_text())
assert result['case_count'] == result['passed'] == len(result['cases']) == 56
assert all(not row['mismatches'] for row in result['cases'])
for row in result['cases']:
    assert row['original']['fresh_vm'] and row['candidate']['fresh_vm']

# An unchanged different captured program is a diagnostic negative input, never
# a claimed Pump reconstruction. The passing side above is genuinely compiled.
negative = PROOF / 'negative.json'
negative_code = run('negative', [sys.executable, '-B', str(script), '--candidate',
                    str(ROOT / 'evidence/original/mayhem/deployed.so'), '--output', str(negative)])
rejected = json.loads(negative.read_text())
assert negative_code != 0 and rejected['case_count'] == 56 and rejected['passed'] < 56
summary = {'actual_candidate_sha256': hashlib.sha256((build / 'candidate.so').read_bytes()).hexdigest(),
           'cases': result['case_count'], 'passed': result['passed'],
           'original_successes': sum(row['original']['error'] is None for row in result['cases']),
           'original_reaches_pump': sum(any('Program 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P invoke' in line
                                          for line in row['original']['logs']) for row in result['cases']),
           'negative_returncode': negative_code, 'negative_mismatches': 56 - rejected['passed']}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
