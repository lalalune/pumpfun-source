"""Replay the maintained build-bound two-curve CLI with actual compiler/VM outputs."""
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
    with (PROOF / (name + '.log')).open('w') as stream:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, timeout=1000).returncode


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/two-curve-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)
build = ROOT / 'work/two-curve-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
            '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
            '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
            '--target-library-directory', str(libraries), '--workspace-layout',
            '--output', str(build)]) == 0
for filename in ('build-attempt.json', 'build-comparison.json', 'build.log'):
    shutil.copyfile(build / filename, PROOF / filename)
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / (filename + '.gz')).write_bytes(gzip.compress((build / filename).read_bytes(), mtime=0))

command = [sys.executable, '-B', 'scripts/pump_tokenkeg_two_curve_differential.py',
           '--build-report', str(build / 'build-comparison.json'),
           '--source-directory', str(build / 'source/programs/pump')]
positive = PROOF / 'positive.json.gz'
code = run('positive', command + ['--candidate', str(build / 'candidate.so'), '--output', str(positive)])
(PROOF / 'entry.json').write_text(json.dumps({'actual_cli_returncode': code,
                                             'output_exists': positive.is_file()}, indent=2) + '\n')
assert code == 0 and positive.is_file(), 'maintained two-curve producer-bound CLI cannot execute'
result = json.loads(gzip.decompress(positive.read_bytes()))
assert result['case_count'] == len(result['cases']) == 20
assert result['original_successes'] == 16 and result['original_pump_cpi_cases'] == 18
assert result['verified_outer_signatures'] == 40 and result['inputs_unchanged']
assert all(not row['mismatches'] for row in result['cases'])
assert all(row[side]['fresh_vm'] for row in result['cases'] for side in ('original', 'candidate'))
actual_sha = hashlib.sha256((build / 'candidate.so').read_bytes()).hexdigest()
binding = result['provenance']['compiled_candidate_binding']
assert result['candidate_sha256'] == binding['candidate_sha256'] == actual_sha
actual_report = json.loads((build / 'build-comparison.json').read_text())
assert binding['actual_source_sha256'] == actual_report['source_sha256']

# Preserve source/build admission: neither a different real ELF paired with the
# genuine report nor a missing real attempt may produce a passing VM report.
wrong = PROOF / 'wrong-image.json.gz'
wrong_rc = run('wrong-image', command + ['--candidate', str(ROOT / 'evidence/original/mayhem/deployed.so'),
                                       '--output', str(wrong)])
assert wrong_rc != 0 and not wrong.exists()
attempt = build / 'build-attempt.json'
saved_attempt = build / 'preserved-build-attempt.json'
attempt.rename(saved_attempt)
missing = PROOF / 'missing-attempt.json.gz'
try:
    missing_rc = run('missing-attempt', command + ['--candidate', str(build / 'candidate.so'),
                                                  '--output', str(missing)])
finally:
    saved_attempt.rename(attempt)
assert missing_rc != 0 and not missing.exists()
summary = {'actual_candidate_sha256': actual_sha, 'cases': 20, 'matching_cases': 20,
           'original_successes': 16, 'original_pump_cpi_cases': 18,
           'verified_outer_signatures': 40, 'source_bound_inputs': len(binding['actual_source_sha256']),
           'wrong_image_rejected': wrong_rc != 0, 'missing_attempt_rejected': missing_rc != 0}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
