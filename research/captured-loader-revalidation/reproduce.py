"""Exercise saved captured-loader admission using a real build and full shard."""
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
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=900)
    return result.returncode


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/captured-loader-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)
build = ROOT / 'work/captured-loader-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
                    '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
                    '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
                    '--target-library-directory', str(libraries), '--workspace-layout',
                    '--output', str(build)]) == 0, 'real producer build failed; inspect build.log'
comparison = build / 'build-comparison.json'
candidate = build / 'candidate.so'
for filename in ('build-comparison.json', 'build-attempt.json', 'build.log'):
    shutil.copyfile(build / filename, PROOF / filename)
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / (filename + '.gz')).write_bytes(gzip.compress((build / filename).read_bytes(), mtime=0))
command = [sys.executable, '-B', 'scripts/pump_validate_parallel.py',
           '--candidate', str(candidate), '--source-directory', str(build / 'source/programs/pump'),
           '--build-comparison', str(comparison), '--captured-loader',
           '--shards', '4', '--shard', '4', '--workers', '2']
saved = PROOF / 'executed.json.gz'
assert run('execute', command + ['--output', str(saved)]) == 0, 'real VM shard failed; inspect retained suite logs'
original = load(saved)
assert original['case_count'] == 2605 and len(original['suites']) == 11
assert len(original['loader_receipts']) == 11 and not original['mismatches']
validated = PROOF / 'validated.json.gz'
assert run('intact', command + ['--validate-existing', str(saved), '--output', str(validated)]) == 0
intact = load(validated)
assert intact['suites'] == original['suites']
preserved = intact['loader_receipts'] == original['loader_receipts']
name = sorted(original['loader_receipts'])[0]
receipt = ROOT / original['loader_receipts'][name]['path']
prior = receipt.read_bytes()
preserved_path = receipt.with_suffix('.preserved')
receipt.rename(preserved_path)
try:
    missing_rc = run('missing', command + ['--validate-existing', str(saved), '--output', str(PROOF / 'missing.json.gz')])
finally:
    preserved_path.rename(receipt)
receipt.write_bytes(prior + b'\n')
try:
    changed_rc = run('changed', command + ['--validate-existing', str(saved), '--output', str(PROOF / 'changed.json.gz')])
finally:
    receipt.write_bytes(prior)
summary = {'actual_build_candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
           'actual_vm_cases': original['case_count'], 'suites': len(original['suites']),
           'actual_loader_receipts': len(original['loader_receipts']),
           'loads': sum(row['load_count'] for row in original['loader_receipts'].values()),
           'intact_suite_results_unchanged': intact['suites'] == original['suites'],
           'intact_loader_receipts_preserved': preserved,
           'missing_receipt_rejected': missing_rc != 0,
           'changed_receipt_rejected': changed_rc != 0}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert preserved and missing_rc != 0 and changed_rc != 0, 'saved captured-loader evidence was lost or not admitted'
