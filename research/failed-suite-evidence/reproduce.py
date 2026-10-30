"""Real build/VM proof that nonzero suites retain their complete failure output."""
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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, command):
    with (PROOF / (name + '.log')).open('w') as stream:
        return subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                              stderr=subprocess.STDOUT, timeout=1000).returncode


def load(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/failure-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)


def build(name, primary):
    output = ROOT / 'work' / ('failure-build-' + name)
    assert run('build-' + name, [sys.executable, '-B', 'scripts/pump_build_verified.py',
               '--sdk', str(SDK), '--source-directory', str(primary),
               '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
               '--target-library-directory', str(libraries), '--workspace-layout',
               '--output', str(output)]) == 0, 'actual producer build failed'
    for filename in ('build-comparison.json', 'build-attempt.json', 'build.log'):
        shutil.copyfile(output / filename, PROOF / (name + '-' + filename))
    for filename in ('candidate.so', 'unstripped.so'):
        (PROOF / (name + '-' + filename + '.gz')).write_bytes(gzip.compress((output / filename).read_bytes(), mtime=0))
    return output


def command(build):
    return [sys.executable, '-B', 'scripts/pump_validate_parallel.py',
            '--candidate', str(build / 'candidate.so'),
            '--source-directory', str(build / 'source/programs/pump'),
            '--build-comparison', str(build / 'build-comparison.json'),
            '--captured-loader', '--shards', '4', '--shard', '4', '--workers', '1']


positive = build('positive', ROOT / 'programs/pump')
positive_report = PROOF / 'positive.json.gz'
assert run('positive-shard', command(positive) + ['--output', str(positive_report)]) == 0
positive_result = load(positive_report)
assert positive_result['case_count'] == 2605 and len(positive_result['suites']) == 11
assert not positive_result['mismatches'] and len(positive_result['loader_receipts']) == 11

# A test-owned source copy changes only initialize's successful handler result.
# The genuine producer records these exact inputs; no comparison receipt is edited.
negative_source = ROOT / 'work/failure-negative-source'
shutil.copytree(ROOT / 'programs/pump', negative_source,
                ignore=shutil.ignore_patterns('target', '__pycache__'))
source = negative_source / 'src/lib.rs'
prior = source.read_text()
needle = 'pub fn initialize(ctx:Context<Initialize>)->Result<()>{global_init::execute(ctx)}'
replacement = 'pub fn initialize(ctx:Context<Initialize>)->Result<()>{let _ = ctx; Err(anchor_lang::solana_program::program_error::ProgramError::Custom(777).into())}'
assert prior.count(needle) == 1
source.write_text(prior.replace(needle, replacement))
shutil.copyfile(source, PROOF / 'negative-lib.rs')
negative = build('negative', negative_source)
assert sha(positive / 'candidate.so') != sha(negative / 'candidate.so')

# First demonstrate that the unchanged child genuinely writes all failure cases.
direct = PROOF / 'direct-global-init.json'
direct_rc = run('direct-negative', [sys.executable, '-B', 'scripts/pump_with_captured_loader.py',
                '--receipt', str(PROOF / 'direct-loader.json'),
                'scripts/pump_global_init_differential.py', '--candidate', str(negative / 'candidate.so'),
                '--output', str(direct)])
direct_result = load(direct)
assert direct_rc != 0 and direct_result['case_count'] == len(direct_result['cases']) == 40
assert direct_result['mismatches']

aggregate = PROOF / 'negative.json.gz'
aggregate_rc = run('negative-shard', command(negative) + ['--output', str(aggregate)])
assert aggregate_rc != 0 and not aggregate.exists()
failure = load(aggregate.with_name(aggregate.name + '.failed.json'))
assert not failure['complete'] and any(row['suite'] == 'global_init' for row in failure['errors'])
evidence = failure.get('failed_suite_outputs', {}).get('global_init')
retained_result = None
if evidence:
    actual = ROOT / evidence['path']
    assert sha(actual) == evidence['sha256']
    assert actual.stat().st_size == evidence['bytes'] and evidence['returncode'] == direct_rc
    retained_result = load(actual)
    assert retained_result == direct_result, 'complete real failed case/state output differs'
summary = {'positive_candidate_sha256': sha(positive / 'candidate.so'),
           'negative_candidate_sha256': sha(negative / 'candidate.so'),
           'positive_cases': positive_result['case_count'], 'positive_suites': len(positive_result['suites']),
           'direct_negative_returncode': direct_rc, 'aggregate_negative_returncode': aggregate_rc,
           'negative_cases': len(direct_result['cases']), 'negative_mismatches': direct_result['mismatches'],
           'failed_output_retained': evidence is not None,
           'complete_actual_case_outcomes_preserved': retained_result == direct_result}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert evidence is not None, 'real nonzero child output was deleted with its temporary directory'
