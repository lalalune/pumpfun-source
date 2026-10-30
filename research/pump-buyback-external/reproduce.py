"""Compile actual Pump and compare the same ELF at internal/external paths."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
env = dict(os.environ, CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
           CARGO_BUILD_JOBS='2', RUSTC=str(SDK / 'rust/bin/rustc'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as log:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                              stderr=subprocess.STDOUT, timeout=1000).returncode


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/buyback-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)
build = ROOT / 'work/buyback-build'
assert run('build', [sys.executable, '-B', 'scripts/pump_build_verified.py',
            '--sdk', str(SDK), '--source-directory', str(ROOT / 'programs/pump'),
            '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
            '--target-library-directory', str(libraries), '--workspace-layout',
            '--output', str(build)]) == 0
for filename in ('build-attempt.json', 'build-comparison.json', 'build.log'):
    shutil.copyfile(build / filename, PROOF / filename)
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / (filename + '.gz')).write_bytes(gzip.compress((build / filename).read_bytes(), mtime=0))
command = [sys.executable, '-B', 'scripts/pump_buyback_recipient_differential.py']
internal = PROOF / 'internal.json'
assert run('internal', command + ['--candidate', str(build / 'candidate.so'), '--output', str(internal)]) == 0
control = json.loads(internal.read_text())
assert control['case_count'] == len(control['cases']) == 42 and not control['mismatches']
actual_sha = sha(build / 'candidate.so')
with tempfile.TemporaryDirectory(prefix='buyback-external-') as temporary:
    directory = Path(temporary).resolve()
    assert not directory.is_relative_to(ROOT)
    candidate = directory / 'candidate.so'
    shutil.copyfile(build / 'candidate.so', candidate)
    assert sha(candidate) == actual_sha
    external = PROOF / 'external.json'
    code = run('external', command + ['--candidate', str(candidate), '--output', str(external)])
    (PROOF / 'entry.json').write_text(json.dumps({'actual_external_returncode': code,
                                                 'output_exists': external.is_file()}, indent=2) + '\n')
    assert code == 0 and external.is_file(), 'valid external candidate rejected before VM replay'
    result = json.loads(external.read_text())
    assert result['cases'] == control['cases'] and not result['mismatches']
    assert result['bound_inputs_sha256'][str(candidate)] == actual_sha
    assert control['bound_inputs_sha256'][str((build / 'candidate.so').relative_to(ROOT))] == actual_sha
    assert sha(candidate) == actual_sha
    wrong = directory / 'wrong-program.so'
    shutil.copyfile(ROOT / 'evidence/original/mayhem/deployed.so', wrong)
    negative = PROOF / 'negative.json'
    negative_code = run('negative', command + ['--candidate', str(wrong), '--output', str(negative)])
    rejected = json.loads(negative.read_text())
    assert negative_code != 0 and len(rejected['cases']) == 42 and rejected['mismatches']
    summary = {'actual_candidate_sha256': actual_sha, 'internal_cases': 42,
               'external_cases': result['case_count'], 'all_case_outcomes_identical': result['cases'] == control['cases'],
               'external_bytes_preserved': sha(candidate) == actual_sha,
               'negative_returncode': negative_code, 'negative_mismatches': len(rejected['mismatches'])}
    (PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))
