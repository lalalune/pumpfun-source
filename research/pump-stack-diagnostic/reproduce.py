"""Actually compile normal/oversized Pump inputs and check producer publication."""
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


assert run('fetch', [str(SDK / 'rust/bin/cargo'), 'fetch', '--locked',
                    '--manifest-path', str(ROOT / 'programs/pump/Cargo.toml')]) == 0
libraries = ROOT / 'work/frame-target-libraries'
shutil.copytree(ROOT / 'reconstruction/toolchain/linux-v1.44-x86_64/rust/lib/rustlib/sbpf-solana-solana/lib', libraries)
(libraries / 'self-contained').mkdir(exist_ok=True)


def build(name, primary):
    output = ROOT / 'work' / ('frame-build-' + name)
    code = run(name, [sys.executable, '-B', 'scripts/pump_build_verified.py',
               '--sdk', str(SDK), '--source-directory', str(primary),
               '--target', 'sbpf-solana-solana', '--target-library-profile', 'linux-v1.44-sbpf',
               '--target-library-directory', str(libraries), '--workspace-layout',
               '--output', str(output)])
    for filename in ('build-attempt.json', 'build.log', 'build-comparison.json'):
        if (output / filename).is_file():
            shutil.copyfile(output / filename, PROOF / (name + '-' + filename))
    return code, output, json.loads((output / 'build-attempt.json').read_text())


normal_code, normal, normal_attempt = build('normal', ROOT / 'programs/pump')
normal_log = (normal / 'build.log').read_text()
assert normal_code == 0 and normal_attempt['returncode'] == 0 and normal_attempt['source_unchanged']
assert 'exceeded max offset' not in normal_log
assert (normal / 'build-comparison.json').is_file()
for filename in ('candidate.so', 'unstripped.so'):
    (PROOF / ('normal-' + filename + '.gz')).write_bytes(gzip.compress((normal / filename).read_bytes(), mtime=0))

# A private source iteration makes the real fixed backend diagnose an exported
# frame. It never changes maintained Rust or patches any compiler output.
negative = ROOT / 'work/frame-negative-source'
shutil.copytree(ROOT / 'programs/pump', negative, ignore=shutil.ignore_patterns('target', '__pycache__'))
source = negative / 'src/lib.rs'
source.write_bytes(source.read_bytes() + b'''
#[no_mangle]
#[inline(never)]
pub extern "C" fn reconstruction_pump_stack_frame_probe(index: usize) -> u64 {
    let mut frame = [0u8; 8192];
    unsafe {
        core::ptr::write_volatile(frame.as_mut_ptr().add(index & 8191), 7);
        core::ptr::read_volatile(frame.as_ptr().add(index & 8191)) as u64
            + core::ptr::read_volatile(frame.as_ptr().add(8191)) as u64
    }
}
''')
shutil.copyfile(source, PROOF / 'negative-lib.rs')
bad_code, bad, bad_attempt = build('oversized', negative)
bad_log = (bad / 'build.log').read_text()
warnings = [line.strip() for line in bad_log.splitlines() if 'exceeded max offset' in line]
assert any('reconstruction_pump_stack_frame_probe' in line and '8192' in line and '4096' in line
           for line in warnings), 'actual fixed compiler did not diagnose the intended frame'
assert bad_attempt['returncode'] == 0 and bad_attempt['source_unchanged']
raw = bad / 'target/sbpf-solana-solana/release/pump_recovered.so'
sys.path.insert(0, str(ROOT / 'scripts'))
from window_elf_reader import Elf
functions = [row for row in Elf(raw).funcs
             if row['name'] == 'reconstruction_pump_stack_frame_probe' and row['size'] > 0]
assert functions, 'diagnosed exported code was not retained in actual compiler output'
(PROOF / 'oversized-compiler-output.so.gz').write_bytes(gzip.compress(raw.read_bytes(), mtime=0))
published = [name for name in ('unstripped.so', 'candidate.so', 'build-comparison.json')
             if (bad / name).exists()]
summary = {'normal_cli_returncode': normal_code,
           'normal_candidate_sha256': sha(normal / 'candidate.so'),
           'normal_other_frame_warnings_accepted': 'overwrites values in the frame' in normal_log,
           'actual_oversized_compiler_returncode': bad_attempt['returncode'],
           'oversized_cli_returncode': bad_code,
           'actual_diagnostic_lines': warnings, 'retained_diagnosed_functions': functions,
           'raw_diagnosed_elf_sha256': sha(raw), 'oversized_published_files': published,
           'diagnostic_gate_passed': bad_attempt.get('stack_diagnostic_gate_passed')}
(PROOF / 'result.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2))
assert bad_code != 0 and not published, 'diagnosed compiler output is still published as a successful build'
assert bad_attempt['stack_diagnostic_gate_passed'] is False and bad_attempt['stack_warnings'] == warnings
