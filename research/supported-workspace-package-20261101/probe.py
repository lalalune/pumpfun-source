"""Actual offline supported-builder package selection; no emitted image execution."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

BASE = '60a42309a4908577f0a386513eeaee6cd6f84f42'
FILES = ['scripts/build_supported_sbpf_candidate.py', 'scripts/build_source_manifest.py',
         'scripts/supported_sbpf_policies/v1.53.json']
CODE = ('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{37}\n'
        '#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
MANIFEST = ('[package]\nname="selected-root-package"\nversion="0.1.0"\nedition="2021"\n'
            '[lib]\nname="requested_output"\ncrate-type=["cdylib"]\n'
            '[profile.release]\npanic="abort"\noverflow-checks=true\nlto=false\ncodegen-units=1\n')
CASES = ('standalone', 'implicit_root', 'explicit_root', 'sibling_default',
         'all_default', 'selected_member', 'path_dependency')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(path):
    return {p.relative_to(path).as_posix(): sha(p) for p in sorted(path.rglob('*')) if p.is_file()}


def run(repo, tools, output, revision=None):
    repo, tools, output = [Path(p).resolve() for p in (repo, tools, output)]
    output.mkdir(parents=True, exist_ok=False)
    originals = {name: sha(repo/name) for name in [*FILES, 'evidence/original/pump/deployed.so']}
    sdk = tools/'v1.53/platform-tools'
    stripper = tools/'v1.52/platform-tools/llvm/bin/llvm-objcopy'
    tool_paths = [sdk/'rust/bin/cargo', sdk/'rust/bin/rustc', stripper]
    result = {'base': revision or BASE, 'source_sha256': {}, 'tool_sha256':
              {p.relative_to(tools).as_posix(): sha(p) for p in tool_paths},
              'cases': {}, 'image_executions': 0}
    with tempfile.TemporaryDirectory(prefix='supported-package-') as temporary:
        root = Path(temporary).resolve()
        cohort = root/'repo'
        for name in FILES:
            data = (subprocess.check_output(['git', '-C', str(repo), 'show', revision+':'+name])
                    if revision else (repo/name).read_bytes())
            destination = cohort/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            result['source_sha256'][name] = sha(destination)
        reference = cohort/'evidence/original/pump/deployed.so'
        reference.parent.mkdir(parents=True)
        shutil.copyfile(repo/'evidence/original/pump/deployed.so', reference)
        spec = importlib.util.spec_from_file_location('supported_package_probe', cohort/FILES[0])
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        cargo_home = root/'cargo-home'
        (cargo_home/'registry').mkdir(parents=True)
        env = {'PATH': os.environ['PATH'], 'CARGO_HOME': str(cargo_home)}

        def clean(text):
            return text.replace(str(root), 'OWNED').replace(str(tools), 'SDK_CACHE')

        for label in CASES:
            source = cohort/label
            (source/'src').mkdir(parents=True)
            workspace = '[workspace]\n'
            if label != 'standalone':
                workspace += 'members=["sibling"]\n'
                sibling = source/'sibling'
                (sibling/'src').mkdir(parents=True)
                dependency = label == 'path_dependency'
                sibling_kind = 'lib' if dependency else 'cdylib'
                (sibling/'Cargo.toml').write_text('[package]\nname="sibling-package"\nversion="0.1.0"\nedition="2021"\n'
                    '[lib]\nname="unrelated_output"\ncrate-type=["'+sibling_kind+'"]\n', encoding='utf-8')
                (sibling/'src/lib.rs').write_text('#![no_std]\npub const VALUE:u64=37;\n' if dependency else CODE.replace('{37}', '{41}'), encoding='utf-8')
            if label == 'explicit_root':
                workspace += 'default-members=["."]\n'
            elif label in ('sibling_default', 'path_dependency'):
                workspace += 'default-members=["sibling"]\n'
            elif label in ('all_default', 'selected_member'):
                workspace += 'default-members=[".","sibling"]\n'
            dependencies = '[dependencies]\nunrelated_output={package="sibling-package",path="sibling"}\n' if label == 'path_dependency' else ''
            (source/'Cargo.toml').write_text(MANIFEST+workspace+dependencies, encoding='utf-8')
            (source/'src/lib.rs').write_text(CODE.replace('{37}', '{unrelated_output::VALUE}') if label == 'path_dependency' else CODE, encoding='utf-8')
            lock = subprocess.run([str(sdk/'rust/bin/cargo'), 'generate-lockfile', '--offline',
                                   '--manifest-path', str(source/'Cargo.toml')], env=dict(env, RUSTC=str(sdk/'rust/bin/rustc')),
                                  capture_output=True, timeout=30)
            lock.check_returncode()
            selected = source/'sibling' if label == 'selected_member' else source
            package = 'sibling-package' if label == 'selected_member' else 'selected-root-package'
            before, cache_before = inventory(source), inventory(cargo_home)
            out = root/(label+'-adapter')
            arguments = ['--manifest', str(selected/'Cargo.toml'), '--program', 'pump',
                         '--artifact-name', 'candidate.so', '--output', str(out), '--tools-version', 'v1.53']
            if label == 'selected_member':
                arguments += ['--extra-input', str(source)]
            planned = builder.plan(builder.parser().parse_args(arguments), cohort, env, cache_root=tools)
            code = builder.execute(planned, env)
            attempt = json.loads((out/'build-attempt.json').read_text(encoding='utf-8'))
            (output/(label+'.build.log')).write_bytes((out/'build.log').read_bytes())
            # Same unmodified source and recipe, with explicit package selection,
            # provide a real compiler control in a separate target directory.
            control = root/(label+'-control')
            control_env = dict(env, **planned['environment'])
            control_env.update(CARGO_HOME=str(cargo_home), CARGO_TARGET_DIR=str(control/'target'))
            direct = [str(sdk/'rust/bin/cargo'), 'build', '--manifest-path', str(selected/'Cargo.toml'),
                      '--package', package, '--release', '--target', 'sbpf-solana-solana', '--locked', '--offline']
            compiled = subprocess.run(direct, env=control_env, cwd=source, capture_output=True, timeout=90)
            (output/(label+'.control.stderr')).write_bytes(compiled.stderr)
            control_hash = None
            if compiled.returncode == 0:
                lib = 'unrelated_output' if label == 'selected_member' else 'requested_output'
                subprocess.run([str(stripper), '--strip-all', str(control/'target/sbpf-solana-solana/release'/(lib+'.so')),
                                str(control/'candidate.so')], capture_output=True, check=True, timeout=30)
                control_hash = sha(control/'candidate.so')
            candidate = out/'artifacts/candidate.so'
            result['cases'][label] = {
                'adapter_exit': code, 'compile_exit': attempt.get('compile_returncode'), 'stage': attempt['stage'],
                'error': json.loads(clean(json.dumps(attempt.get('error')))),
                'comparison_published': (out/'build-comparison.json').is_file(),
                'candidate_sha256': sha(candidate) if candidate.exists() else None,
                'compiled_cdylibs': sorted(p.name for p in (out/'target/sbpf-solana-solana/release').glob('*.so')),
                'selected_package': package, 'command': json.loads(clean(json.dumps(planned['command']))),
                'direct_explicit_package_exit': compiled.returncode, 'direct_candidate_sha256': control_hash,
                'caller_source_preserved': before == inventory(source),
                'caller_cache_preserved': all(inventory(cargo_home).get(name) == digest
                                              for name, digest in cache_before.items()),
                'caller_cache_created_files': sorted(set(inventory(cargo_home))-set(cache_before)),
                'effective_source_preserved': attempt.get('source_unchanged') is True,
                'staged_manifests_equal': all((out/'source'/p.relative_to(cohort)).read_bytes() == p.read_bytes()
                                            for p in source.rglob('Cargo.toml')),
                'staged_lock_equal': (out/'source'/source.relative_to(cohort)/'Cargo.lock').read_bytes() == (source/'Cargo.lock').read_bytes(),
                'path_dependency_compiled': any((out/'target/sbpf-solana-solana/release/deps').glob('libunrelated_output*.rlib'))}
        result['capture_preserved'] = sha(reference) == originals['evidence/original/pump/deployed.so']
    result['caller_inputs_preserved'] = originals == {name: sha(repo/name) for name in originals}
    result['tools_preserved'] = result['tool_sha256'] == {p.relative_to(tools).as_posix(): sha(p) for p in tool_paths}
    result['rustc_version'] = subprocess.check_output([str(sdk/'rust/bin/rustc'), '-vV'], text=True, encoding='utf-8').strip()
    (output/'results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


def validate(result, expect):
    for label, row in result['cases'].items():
        failure = expect == 'base' and label in ('sibling_default', 'path_dependency')
        if (row['adapter_exit'] != (1 if failure else 0) or row['compile_exit'] != 0 or
                row['comparison_published'] == failure or row['direct_explicit_package_exit'] != 0):
            raise AssertionError('unexpected result: '+label)
        if failure:
            if row['error']['type'] != 'FileNotFoundError':
                raise AssertionError('missing actual artifact-selection failure: '+label)
        elif row['candidate_sha256'] != row['direct_candidate_sha256']:
            raise AssertionError('selected artifact changed: '+label)
        if not all(row[key] for key in ('caller_source_preserved', 'caller_cache_preserved',
                   'effective_source_preserved', 'staged_manifests_equal', 'staged_lock_equal')):
            raise AssertionError('input changed: '+label)
        if expect == 'fixed':
            command = row['command']
            if command[command.index('--package')+1] != row['selected_package']:
                raise AssertionError('wrong explicit package: '+label)
    if not result['cases']['path_dependency']['path_dependency_compiled']:
        raise AssertionError('path dependency not compiled')
    if not all(result[key] for key in ('capture_preserved', 'caller_inputs_preserved', 'tools_preserved')):
        raise AssertionError('caller/tool mutation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', required=True, type=Path)
    parser.add_argument('--tools', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    args = parser.parse_args()
    record = run(args.repo, args.tools, args.output, args.revision)
    validate(record, args.expect)
    print(json.dumps({'expected': args.expect, 'cases': len(record['cases']),
                      'adapter_codes': {name: row['adapter_exit'] for name, row in record['cases'].items()}}))
