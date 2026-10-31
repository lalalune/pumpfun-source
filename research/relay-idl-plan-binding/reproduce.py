#!/usr/bin/env python3
"""Build real Relay bytes, replay 27 signed steps, then probe receipt admission."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
PACKAGE = ROOT / 'reconstruction/verification/donation-relay-idl-lifecycle'
OUT = ROOT / 'work/scoped-proof'
BUILD = ROOT / 'work/relay-plan-build'
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
VERIFIERS = {
    '4baf2b53c46f5907e443158296131cad479f65c02e4ef80a1b983ff64d79ebf0': 'before',
    '95899a34aced0d0dc1ac77041092fe1c9f821569d2ec296687180c23d661c501': 'after',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(label, command, env=None, timeout=1200):
    command = [str(part) for part in command]
    print(label, command, flush=True)
    with (OUT / (label + '.log')).open('w') as log:
        result = subprocess.run(command, cwd=ROOT, env=env, stdout=log,
                                stderr=subprocess.STDOUT, timeout=timeout)
    save(label + '-command.json', {'command': command, 'returncode': result.returncode})
    if result.returncode:
        print((OUT / (label + '.log')).read_text(errors='replace'), flush=True)
        raise RuntimeError(f'{label} returned {result.returncode}')


def main():
    if sys.platform != 'darwin' or platform.machine() != 'arm64':
        raise SystemExit('use the authenticated native macOS arm64 v1.44 SDK')
    OUT.mkdir(parents=True, exist_ok=False)
    verifier_sha = digest(PACKAGE / 'verify_report.py')
    expectation = VERIFIERS[verifier_sha]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    source_before = subprocess.check_output(['git', 'status', '--porcelain', '--',
                                            'programs/donation-relay'], cwd=ROOT, text=True)
    assert not source_before, source_before
    env = dict(os.environ, RUSTC=str(SDK / 'rust/bin/rustc'),
               CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
               SOLANA_PLATFORM_TOOLS=str(SDK))
    env.pop('CARGO_NET_OFFLINE', None)
    save('environment.json', {
        'revision': revision, 'host': platform.platform(), 'machine': platform.machine(),
        'python': sys.version, 'expectation': expectation, 'verifier_sha256': verifier_sha,
        'sdk_archive_sha256': '66e20d135fddd70ff519baf7ff320d762957f9aedf93a50e23756db23ad79351',
        'sdk_authentication': 'Caller authenticates official archive SHA256 and runs bootstrap --sdk-check full before this proof',
        'tools': {name: digest(SDK / name) for name in ('rust/bin/rustc', 'rust/bin/cargo', 'llvm/bin/llvm-objcopy')},
        'package_files': {path.name: digest(path) for path in sorted(PACKAGE.iterdir()) if path.is_file()},
    })
    run('rustc-version', [SDK / 'rust/bin/rustc', '-vV'], env)
    run('cargo-version', [SDK / 'rust/bin/cargo', '-V'], env)
    run('locked-fetch', [SDK / 'rust/bin/cargo', 'fetch', '--locked', '--manifest-path',
                         ROOT / 'programs/donation-relay/Cargo.toml'], env)
    assert not BUILD.exists(), 'use a fresh checkout or remove only your earlier build output'
    run('candidate-build', ['sh', PACKAGE / 'build_candidate.sh', ROOT, BUILD], env)
    candidate = BUILD / 'donation_relay_candidate.so'
    raw_candidate = BUILD / 'target/sbpf-solana-solana/release/donation_relay_source_proposal.so'
    save('candidate.json', {'stripped_sha256': digest(candidate), 'raw_sha256': digest(raw_candidate),
                            'limits': 'Ordinary pinned native Mac SBF build; no exact deployed ELF identity claim'})
    for label, path in (('candidate.so.gz', candidate), ('raw-candidate.so.gz', raw_candidate)):
        (OUT / label).write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    python = [sys.executable, '-B']
    for name in ('report-one.json', 'report-two.json'):
        run(name[:-5], python + [PACKAGE / 'producer.py', '--root', ROOT,
                                '--candidate', candidate, '--output', OUT / name], env)
    assert (OUT / 'report-one.json').read_bytes() == (OUT / 'report-two.json').read_bytes()
    run('receipt-probe', python + [HERE / 'probe_real_reports.py', '--repo', ROOT,
        '--candidate', candidate, '--report', OUT / 'report-one.json',
        '--output', OUT / 'negative-probes', '--expect', expectation], env)
    run('existing-lifecycle-tests', python + ['-m', 'unittest',
        'reconstruction/verification/donation-relay-idl-lifecycle/test_lifecycle.py'], env)
    source_after = subprocess.check_output(['git', 'status', '--porcelain', '--',
                                           'programs/donation-relay'], cwd=ROOT, text=True)
    assert not source_after, source_after
    save('summary.json', {'revision': revision, 'expectation': expectation,
        'logical_transactions_per_report': 27, 'reports': 2, 'byte_identical_repeat': True,
        'original_and_candidate_vm_sends_per_report': 54,
        'candidate_sha256': digest(candidate), 'report_sha256': digest(OUT / 'report-one.json'),
        'source_tree_unchanged': True,
        'limits': 'Finite signed IDL differential and saved-receipt admission only; no new contract behavior, whole-program equivalence or security claim'})
    print((OUT / 'receipt-probe.log').read_text(), flush=True)


if __name__ == '__main__':
    main()
