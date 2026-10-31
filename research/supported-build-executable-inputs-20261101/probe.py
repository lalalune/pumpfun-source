"""Actual pinned v1.53 supported adapter with a source build-script helper."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo, tools = map(lambda value: Path(value).resolve(), sys.argv[1:])
script = repo/'scripts/build_supported_sbpf_candidate.py'
spec = importlib.util.spec_from_file_location('supported_mode_probe', script)
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
sdk = tools/'v1.53/platform-tools'
stripper = tools/'v1.52/platform-tools/llvm/bin/llvm-objcopy'
rows = {}
with tempfile.TemporaryDirectory(prefix='.supported-mode-', dir=repo) as temporary:
    root = Path(temporary)
    registry = root/'cargo-home'
    (registry/'registry').mkdir(parents=True)
    env = {'PATH': os.environ['PATH'], 'CARGO_HOME': str(registry)}
    for name, mode in [('executable', 0o755), ('nonexecutable', 0o644)]:
        source = root/name
        (source/'src').mkdir(parents=True)
        (source/'tools').mkdir()
        (source/'Cargo.toml').write_text('[package]\nname="input-mode-probe"\nversion="0.1.0"\nedition="2021"\n[lib]\nname="input_mode_probe"\ncrate-type=["cdylib"]\n[profile.release]\npanic="abort"\noverflow-checks=true\nlto=false\ncodegen-units=1\n[workspace]\n')
        (source/'Cargo.lock').write_text('version = 3\n\n[[package]]\nname = "input-mode-probe"\nversion = "0.1.0"\n')
        (source/'src/lib.rs').write_text('#![no_std]\ninclude!(concat!(env!("OUT_DIR"),"/generated.rs"));\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{VALUE}\n#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
        (source/'build.rs').write_text('fn main(){let result=std::process::Command::new("./tools/generate.sh").output().expect("run executable input");assert!(result.status.success());std::fs::write(std::path::Path::new(&std::env::var("OUT_DIR").unwrap()).join("generated.rs"),result.stdout).unwrap();}\n')
        helper = source/'tools/generate.sh'
        helper.write_text('#!/bin/sh\nprintf "pub const VALUE: u64=37;\\n"\n')
        helper.chmod(mode)
        output = root/(name+'-adapter')
        args = builder.parser().parse_args(['--manifest', str(source/'Cargo.toml'), '--program', 'mayhem',
                                           '--artifact-name', 'probe.so', '--output', str(output),
                                           '--tools-version', 'v1.53', '--extra-input', str(helper)])
        planned = builder.plan(args, repo, env, cache_root=tools)
        # A direct build of the same original source is the independent control.
        control = root/(name+'-control')
        control.mkdir()
        control_env = dict(env, **planned['environment'])
        control_env.update(CARGO_HOME=str(registry), CARGO_TARGET_DIR=str(control/'target'))
        command = [str(sdk/'rust/bin/cargo'), 'build', '--manifest-path', str(source/'Cargo.toml'),
                   '--release', '--target', 'sbpf-solana-solana', '--locked', '--offline']
        direct = subprocess.run(command, cwd=source, env=control_env, capture_output=True, text=True, timeout=90)
        control_hash = None
        if direct.returncode == 0:
            original_binary = control/'target/sbpf-solana-solana/release/input_mode_probe.so'
            subprocess.run([str(stripper), '--strip-all', str(original_binary), str(control/'candidate.so')], check=True)
            control_hash = hashlib.sha256((control/'candidate.so').read_bytes()).hexdigest()
        status = builder.execute(planned, env)
        attempt = json.loads((output/'build-attempt.json').read_text())
        staged_helper = output/'source'/helper.relative_to(repo)
        row = {'control_returncode': direct.returncode, 'control_candidate_sha256': control_hash,
               'control_stderr': direct.stderr, 'adapter_returncode': status,
               'adapter_stage': attempt['stage'], 'adapter_compile_returncode': attempt['compile_returncode'],
               'source_helper_mode': oct(helper.stat().st_mode & 0o777),
               'staged_helper_mode': oct(staged_helper.stat().st_mode & 0o777),
               'source_unchanged': attempt.get('source_unchanged'),
               'build_log': (output/'build.log').read_text() if (output/'build.log').is_file() else None,
               'error': attempt.get('error')}
        if (output/'artifacts/probe.so').is_file():
            row['adapter_candidate_sha256'] = hashlib.sha256((output/'artifacts/probe.so').read_bytes()).hexdigest()
        rows[name] = row
print(json.dumps({'compiler': subprocess.check_output([str(sdk/'rust/bin/rustc'), '--version'], text=True).strip(),
                  'rows': rows}, indent=2))
