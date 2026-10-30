"""Rebuild actual maintained Fees, then execute the unchanged query validator."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
BUILD = ROOT / 'work/fees-query-native-build'
PROOF.mkdir(parents=True, exist_ok=True)
BUILD.mkdir(parents=True, exist_ok=True)
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
HYBRID = Path.home() / '.cache/pumpfun-reconstruction/toolchains/hybrid144'
env = dict(os.environ, RUSTC=str(HYBRID / 'rust/bin/rustc'),
           CARGO_HOME=str(BUILD / 'cargo-home'), CARGO_TARGET_DIR=str(BUILD / 'target'),
           CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse', CARGO_BUILD_JOBS='2',
           CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS='-Zremap-cwd-prefix=',
           CC=str(SDK / 'llvm/bin/clang'), AR=str(SDK / 'llvm/bin/llvm-ar'))
for key in ('RUSTFLAGS', 'CARGO_ENCODED_RUSTFLAGS', 'RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER'):
    env.pop(key, None)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as stream:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, timeout=900).returncode


inputs = [ROOT / 'Cargo.toml', ROOT / 'Cargo.lock']
inputs += [path for path in sorted((ROOT / 'programs/pump-fees').rglob('*')) if path.is_file()]
before = {path.relative_to(ROOT).as_posix(): sha(path) for path in inputs}
cargo = str(SDK / 'rust/bin/cargo')
assert run('fetch', [cargo, 'fetch', '--locked', '--manifest-path', str(ROOT / 'Cargo.toml')]) == 0
command = [cargo, 'build', '--locked', '--offline', '--release', '--target', 'sbpf-solana-solana',
           '--manifest-path', str(ROOT / 'Cargo.toml'), '-p', 'pump-fun-fees-candidate', '--lib']
build_rc = run('build', command)
assert build_rc == 0, 'actual maintained Fees native build failed; inspect build.log'
symbols = BUILD / 'target/sbpf-solana-solana/release/pump_fees_candidate.so'
candidate = BUILD / 'candidate.so'
subprocess.run([str(SDK / 'llvm/bin/llvm-objcopy'), '--strip-all', str(symbols), str(candidate)], check=True)
binding = {'scope': 'Actual diagnostic native build for VM tool validation, not qualified Linux exact-ELF reproduction.',
           'command': command, 'returncode': build_rc, 'source_sha256': before,
           'source_unchanged': all(sha(ROOT / name) == digest for name, digest in before.items()),
           'tool_sha256': {name: sha(path) for name, path in {'cargo': SDK / 'rust/bin/cargo',
                           'rustc': HYBRID / 'rust/bin/rustc', 'objcopy': SDK / 'llvm/bin/llvm-objcopy'}.items()},
           'candidate_sha256': sha(candidate), 'symbols_sha256': sha(symbols)}
assert binding['source_unchanged']
(PROOF / 'actual-build.json').write_text(json.dumps(binding, indent=2) + '\n')
for name, path in [('candidate.so', candidate), ('symbols.so', symbols)]:
    (PROOF / (name + '.gz')).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
output = PROOF / 'queries.json'
rc = run('queries', [sys.executable, '-B', 'scripts/validate_fee_handlers.py',
                     '--candidate', str(candidate), '--output', str(output)])
summary = {'actual_build_succeeded': True, 'actual_candidate_sha256': sha(candidate),
           'query_exit_code': rc, 'query_report_exists': output.is_file()}
if rc == 0 and output.is_file():
    report = json.loads(output.read_text())
    assert report['candidate_sha256'] == sha(candidate)
    assert report['case_count'] == len(report['cases']) and report['case_count'] > 10643
    assert not report['failures'] and report['mismatch_count'] == 0
    summary.update(actual_vm_cases=report['case_count'], actual_vm_mismatches=report['mismatch_count'])
    wrong = ROOT / 'evidence/original/mayhem/deployed.so'
    rejected = PROOF / 'wrong-program.json'
    wrong_rc = run('wrong-program', [sys.executable, '-B', 'scripts/validate_fee_handlers.py',
                                    '--candidate', str(wrong), '--output', str(rejected)])
    wrong_report = json.loads(rejected.read_text())
    assert wrong_report['candidate_sha256'] == sha(wrong) and wrong_report['mismatch_count'] > 0
    assert wrong_rc != 0
    summary.update(wrong_actual_program_rejected=True, wrong_program_mismatches=wrong_report['mismatch_count'])
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert rc == 0 and output.is_file(), 'documented Fees query workflow cannot load its retained case inputs'
