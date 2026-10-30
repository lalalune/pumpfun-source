"""Actual historical supported Pump build and external-cache seed admission."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
PROOF.mkdir(parents=True, exist_ok=True)
WORK = ROOT / 'work/actual-seed-flags'
WORK.mkdir()
REVISION = '75e2066c99a4f862f545cb66fda855e67d684a03'
PREFIX = 'repro/pump/main-contract-round38-20261027/primary/'
EXPECTED_TREE = 'fb436ff37d4ff6e0d05d7af8f2011b056b258511'
subprocess.run(['git', 'fetch', '--no-tags', 'origin', REVISION], cwd=ROOT, check=True, timeout=180)
tree = subprocess.check_output(['git', 'rev-parse', REVISION + ':' + PREFIX.rstrip('/')], cwd=ROOT, text=True).strip()
assert tree == EXPECTED_TREE
archive = subprocess.check_output(['git', 'archive', REVISION, PREFIX], cwd=ROOT)
source = WORK / 'round38-primary'
source.mkdir()
with tarfile.open(fileobj=io.BytesIO(archive)) as stream:
    for member in stream:
        if not member.isfile():
            continue
        relative = Path(member.name).relative_to(PREFIX.rstrip('/'))
        assert not relative.is_absolute() and '..' not in relative.parts
        destination = source / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(stream.extractfile(member).read())
        destination.chmod(member.mode)
assert hashlib.sha256((source / 'Cargo.toml').read_bytes()).hexdigest() == '7a1d296cd7b25bb0f6ea89a5fc7616f43a94fb75027fdc329e27f99305ae2dad'
assert hashlib.sha256((source / 'Cargo.lock').read_bytes()).hexdigest() == '8307bd5e79789b5190291ea014c2f5556e23fb9829fa2f68a7ede581235eae98'
SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
env = dict(os.environ, CARGO_HOME=str(Path.home() / '.cargo'),
           CARGO_REGISTRIES_CRATES_IO_PROTOCOL='sparse',
           RUSTC=str(SDK / 'rust/bin/rustc'), RUSTFLAGS='-Zremap-cwd-prefix=')
env.pop('CARGO_ENCODED_RUSTFLAGS', None)


def run(name, command, selected_env=env):
    with (PROOF / (name + '.log')).open('w') as log:
        return subprocess.run(command, cwd=ROOT, env=selected_env, stdout=log,
                              stderr=subprocess.STDOUT, timeout=900).returncode


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(source / 'Cargo.toml')]) == 0
libraries = WORK / 'target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)
command = [sys.executable, '-B', 'scripts/pump_build_verified.py', '--source-directory', str(source),
           '--workspace-layout', '--sdk', str(SDK), '--target-library-profile', 'linux-v1.44-sbpf',
           '--target-library-directory', str(libraries)]
cold, seeded = WORK / 'cold', WORK / 'seeded'
assert run('cold-build', command + ['--registry-home', str(Path.home() / '.cargo'), '--output', str(cold)]) == 0
first = json.loads((cold / 'build-comparison.json').read_text())
assert first['returncode'] == 0 and first['source_unchanged']
for name in ('build-comparison.json', 'build.log'):
    shutil.copyfile(cold / name, PROOF / ('cold-' + name))
for name in ('unstripped.so', 'candidate.so'):
    (PROOF / ('cold-' + name + '.gz')).write_bytes(gzip.compress((cold / name).read_bytes(), mtime=0))
seed_args = ['--registry-home', str(cold / 'cargo-home'), '--dependency-cache', str(WORK / 'cache'),
             '--dependency-cache-seed', str(cold), '--output', str(seeded)]
rc = run('seeded-build', command + seed_args)
summary = {'historical_source_revision': REVISION, 'historical_source_tree': tree,
           'actual_cold_build_succeeded': True, 'actual_seeded_exit_code': rc,
           'actual_cold_candidate_sha256': first['comparison']['candidate_sha256'],
           'recorded_cold_rustflags': first['environment'].get('RUSTFLAGS')}
if rc == 0:
    second = json.loads((seeded / 'build-comparison.json').read_text())
    assert second['dependency_cache']['status'] == 'hit'
    assert second['comparison']['candidate_sha256'] == first['comparison']['candidate_sha256']
    assert second['unstripped_sha256'] == first['unstripped_sha256']
    for name in ('build-comparison.json', 'build.log'):
        shutil.copyfile(seeded / name, PROOF / ('seeded-' + name))
    changed_env = dict(env, RUSTFLAGS='-Zremap-cwd-prefix= -Copt-level=2')
    rejected = WORK / 'wrong-flags'
    wrong = command + ['--registry-home', str(cold / 'cargo-home'), '--dependency-cache', str(WORK / 'wrong-cache'),
                       '--dependency-cache-seed', str(cold), '--output', str(rejected)]
    wrong_rc = run('wrong-flags', wrong, changed_env)
    assert wrong_rc != 0 and 'seed compiler flags differ' in (PROOF / 'wrong-flags.log').read_text()
    summary.update(seed_cache_hit=True, actual_elf_bytes_equal=True, changed_flags_rejected=True)
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert rc == 0, 'same actual compiler flags cannot seed the real clean producer build'
