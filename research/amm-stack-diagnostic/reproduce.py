"""Actual AMM compiler frame diagnostic and prior-output publication proof."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROOF = ROOT / 'work/scoped-proof'
SWARM = ROOT / 'work/amm-frame-proof'
PROOF.mkdir(parents=True, exist_ok=True)
SWARM.mkdir()
os.environ['AMM_SELL_SWARM'] = str(SWARM)
os.environ['CARGO_REGISTRIES_CRATES_IO_PROTOCOL'] = 'sparse'
sys.path[:0] = [str(ROOT / 'scripts/amm_sell'), str(ROOT / 'scripts')]
import native_build as native
import sell_score
import window_elf_reader

with (PROOF / 'existing-publication-tests.log').open('w') as stream:
    subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/amm_sell/test_native_build_preservation.py')],
                   stdout=stream, stderr=subprocess.STDOUT, check=True)

SDK = Path.home() / '.cache/solana/v1.44/platform-tools'
HYBRID = Path.home() / '.cache/pumpfun-reconstruction/toolchains/hybrid144'
native.SDK.parent.mkdir(parents=True)
subprocess.run(['cp', '-cR', str(SDK), str(native.SDK)], check=True)
target = native.SDK / 'rust/lib/rustlib/sbpf-solana-solana'
if target.exists():
    shutil.rmtree(target)
shutil.copytree(HYBRID / 'rust/lib/rustlib/sbpf-solana-solana', target)
original = SWARM / 'infra/original/deployed.so'
original.parent.mkdir()
shutil.copyfile(ROOT / 'evidence/original/pump_amm/deployed.so', original)
native.recipe.stage(ROOT, native.PRISTINE)
env = dict(os.environ, CARGO_HOME=str(native.CARGO_HOME), RUSTC=str(native.SDK / 'rust/bin/rustc'))
with (PROOF / 'fetch.log').open('w') as stream:
    subprocess.run([str(native.SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(native.PRISTINE / 'Cargo.toml')], cwd=native.PRISTINE,
                   env=env, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=300)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {file.name: sha(file) for file in path.iterdir() if file.is_file()}


lane = SWARM / 'lanes/control'
first = native.build(lane, 'repeated', source_root=ROOT, jobs=2)
assert first['returncode'] == 0
out = Path(first['output_dir'])
prior = inventory(out)
first_score = sell_score.score(out)
assert first_score['windows_raw_equal'] == 785 and first_score['allocation_image_equal']
first_log = (out / 'build.log').read_text()
assert 'exceeded max offset' not in first_log
assert 'overwrites values in the frame' in first_log, 'qualified warning-bearing control changed'
shutil.copyfile(out / 'build.log', PROOF / 'baseline-build.log')
for name in ('candidate.so', 'symbols.so'):
    (PROOF / ('baseline-' + name + '.gz')).write_bytes(gzip.compress((out / name).read_bytes(), mtime=0))
probe = SWARM / 'oversized-sell.rs'
probe.write_bytes((ROOT / 'programs/pump-amm/src/instructions/swap/sell.rs').read_bytes() + b'''
#[no_mangle]
#[inline(never)]
pub extern "C" fn reconstruction_stack_frame_probe(index: usize) -> u64 {
    let mut frame = [0u8; 8192];
    unsafe {
        core::ptr::write_volatile(frame.as_mut_ptr().add(index & 8191), 7);
        core::ptr::read_volatile(frame.as_ptr().add(index & 8191)) as u64
            + core::ptr::read_volatile(frame.as_ptr().add(8191)) as u64
    }
}
''')
bad = native.build(lane, 'repeated', sell=probe, jobs=2)
bad_out = Path(bad['output_dir'])
bad_log = (bad_out / 'build.log').read_text()
shutil.copyfile(bad_out / 'build.log', PROOF / 'oversized-build.log')
warnings = [line for line in bad_log.splitlines() if 'exceeded max offset' in line]
assert warnings and any('reconstruction_stack_frame_probe' in line for line in warnings)
raw_symbols = lane / 'target/sbpf-solana-solana/release/pump_amm_recovered.so'
elf = window_elf_reader.Elf(raw_symbols)
functions = [row for row in elf.funcs if row['name'] == 'reconstruction_stack_frame_probe' and row['size'] > 0]
assert functions, 'diagnosed exported function was not retained in actual compiler output'
(PROOF / 'diagnosed-symbols.so.gz').write_bytes(gzip.compress(raw_symbols.read_bytes(), mtime=0))
preserved = inventory(out) == prior
rejected = bad['returncode'] != 0 and bad.get('compiler_returncode', bad['returncode']) == 0
recovered = native.build(lane, 'repeated', jobs=2)
assert recovered['returncode'] == 0 and recovered['candidate_sha256'] == first['candidate_sha256']
summary = {'actual_baseline': first, 'actual_diagnosed_attempt': bad,
           'actual_diagnostic_lines': warnings, 'retained_diagnosed_functions': functions,
           'diagnosed_symbols_gzip_sha256': sha(PROOF / 'diagnosed-symbols.so.gz'),
           'prior_published_outputs_preserved': preserved, 'diagnosed_attempt_rejected': rejected,
           'qualified_warning_control_still_accepted': recovered['returncode'] == 0,
           'baseline_raw_windows': first_score['windows_raw_equal'],
           'baseline_allocation_image_equal': first_score['allocation_image_equal']}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert preserved and rejected, 'compiler frame diagnostics still publish over prior valid AMM evidence'
