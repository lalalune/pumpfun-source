"""Compile a real host crate using the production AMM build environment.

Before the environment helper exists, execute the unchanged env-construction
AST statements from native_build.build. Compiler/Cargo outcomes are never mocked.
This is a host compiler probe, not an SBF reconstruction build.
"""
import ast
import contextlib
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

repo = Path(sys.argv[1]).resolve()
toolchain = Path(sys.argv[2]).resolve()
sys.path.insert(0, str(repo / 'scripts/amm_sell'))
import native_build
import cache_inputs
import sell_score


def environment(harness, target, staging, wrapper):
    values = dict(os.environ)
    values.pop('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', None)
    if wrapper:
        values['CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'] = str(wrapper)
    old = dict(os.environ)
    os.environ.clear(); os.environ.update(values)
    try:
        if hasattr(native_build, 'build_environment'):
            return native_build.build_environment(harness, target, staging, '', 1, None)
        function = next(n for n in ast.parse(Path(native_build.__file__).read_text()).body
                        if isinstance(n, ast.FunctionDef) and n.name == 'build')
        body = next(n for n in function.body if isinstance(n, ast.Try)).body
        start = next(i for i, n in enumerate(body) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == 'env' for t in n.targets))
        end = next(i for i, n in enumerate(body) if i > start and isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'started' for t in n.targets))
        module = ast.fix_missing_locations(ast.Module(body=body[start:end], type_ignores=[]))
        scope = dict(vars(native_build), harness=harness, target=target, staging=staging,
                     extra_root_flags='', jobs=1, link_script=None)
        exec(compile(module, str(native_build.__file__), 'exec'), scope)
        return scope['env']
    finally:
        os.environ.clear(); os.environ.update(old)


with tempfile.TemporaryDirectory(prefix='amm-real-cargo-') as folder:
    root = Path(folder)
    harness = root / 'harness'; harness.mkdir()
    (harness / 'rustc_wrapper.py').write_text(native_build.RUSTC_WRAPPER)
    (harness / 'rustc_wrapper.py').chmod(0o755)
    wrapper = root / 'workspace-wrapper.py'
    wrapper.write_text('#!' + sys.executable + '\nimport os,sys\n'
                       'compiler,*args=sys.argv[1:]\n'
                       'if "--crate-name" in args: args += ["--cfg", "ambient_override"]\n'
                       'os.execv(compiler,[compiler,*args])\n')
    wrapper.chmod(0o755)
    crate = root / 'crate'; (crate / 'src').mkdir(parents=True)
    (crate / 'Cargo.toml').write_text('[package]\nname="probe"\nversion="0.1.0"\nedition="2021"\n[workspace]\n')
    (crate / 'src/main.rs').write_text('#![allow(unexpected_cfgs)]\nfn main(){println!("{}",cfg!(ambient_override));}\n')
    # Only the tool directory layout is adapted; rustc and Cargo are official binaries.
    sdk = root / 'sdk'; (sdk / 'rust/bin').mkdir(parents=True)
    for name in ('rustc', 'rustdoc'):
        (sdk / 'rust/bin' / name).symlink_to(toolchain / name)
    native_build.SDK = sdk
    native_build.CARGO_HOME = root / 'cargo-home'
    subprocess.run([str(toolchain / 'cargo'), 'generate-lockfile', '--offline'], cwd=crate,
                   env=environment(harness, root / 'lock-target', root, None),
                   capture_output=True, text=True, check=True, timeout=20)
    swarm = root / 'swarm'; (swarm / 'infra/original').mkdir(parents=True)
    (swarm / 'infra/original/deployed.so').write_bytes(b'synthetic context input')
    observations = []
    for name, override in [('clean', None), ('ambient', wrapper)]:
        target = root / name
        env = environment(harness, target, root, override)
        old = os.environ.get('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER')
        try:
            if override: os.environ['CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'] = str(override)
            else: os.environ.pop('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', None)
            context = cache_inputs.context(swarm, repo / 'scripts/amm_sell', crate,
                                           Path(sell_score.elf_reader.__file__), False)
        finally:
            if old is None: os.environ.pop('CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER', None)
            else: os.environ['CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'] = old
        build = subprocess.run([str(toolchain / 'cargo'), 'build', '--release', '--offline'],
                               cwd=crate, env=env, text=True, capture_output=True, timeout=45)
        if build.returncode:
            raise SystemExit(build.stderr)
        result = subprocess.check_output([str(target / 'release/probe')], text=True).strip()
        observations.append({'case': name, 'output': result,
                             'cache_context_sha256': hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest(),
                             'wrapper_forwarded': 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER' in env})
    print(json.dumps({'native_source_sha256': hashlib.sha256(Path(native_build.__file__).read_bytes()).hexdigest(),
                      'cargo': subprocess.check_output([str(toolchain / 'cargo'), '--version'], text=True).strip(),
                      'rustc': subprocess.check_output([str(toolchain / 'rustc'), '--version'], text=True).strip(),
                      'observations': observations}, indent=2))
