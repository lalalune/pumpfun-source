"""Run the verified builder on tiny offline sources; never execute its artifacts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


FILES = [f'scripts/{name}.py' for name in (
    'pump_build_verified', 'pump_dependency_cache', 'pump_text_layout',
    'pump_target_library_profile', 'pump_data_order', 'source_manifest_guard',
    'build_source_manifest', 'compare', 'analyze', 'probe_report',
    'pump_compare_function_bytes', 'pump_exact_body_inventory',
    'pump_quote_control_function_match', 'pump_physical_source_wrapper')]
FILES += ['reconstruction/harness/instruction_stream.py']
CAPTURE = 'evidence/original/pump/deployed.so'
MANIFEST = '''[package]
name="pump-recovered"
version="0.1.0"
edition="2021"
[lib]
crate-type=["cdylib","lib"]
{dependencies}
[profile.release]
panic="abort"
lto=false
codegen-units=1
[workspace]
'''
CODE = '''#![no_std]
#[deprecated(note="{message}")] fn old(x:u64)->u64{{x.wrapping_add(1)}}
#[no_mangle] pub extern "C" fn entrypoint(x:*const u64)->u64{{old(unsafe{{core::ptr::read_volatile(x)}}){dependency}}}
#[panic_handler] fn panic(_: &core::panic::PanicInfo)->!{{loop{{}}}}
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


def run_probe(repo, sdk, output, revision=None):
    repo, sdk, output = [Path(p).resolve() for p in (repo, sdk, output)]
    output.mkdir(parents=True, exist_ok=False)
    files = list(FILES)
    launcher = 'scripts/pump_physical_source_wrapper.sh'
    # New current builders execute the selected-Python launcher. Historical
    # revisions still use the original direct Python hook.
    if revision:
        present = subprocess.run(['git', '-C', str(repo), 'cat-file', '-e', revision+':'+launcher],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    else:
        present = (repo/launcher).is_file()
    if present:
        files.append(launcher)
    original = {p: sha((repo/p).read_bytes()) for p in [*files, CAPTURE]}
    results = {'implementation_sha256': {}, 'cases': {}, 'runtime_executions': 0}
    tools = {name: sdk/name for name in ('rust/bin/cargo', 'rust/bin/rustc',
                                      'llvm/bin/llvm-objcopy')}
    results['tool_sha256'] = {name: sha(path.read_bytes()) for name, path in tools.items()}
    results['rustc_version'] = subprocess.check_output(
        [str(tools['rust/bin/rustc']), '-vV'], text=True, encoding='utf-8').strip()
    with tempfile.TemporaryDirectory(prefix='verified-log-utf8-') as temporary:
        root = Path(temporary).resolve()
        for name in files:
            data = subprocess.check_output(['git', '-C', str(repo), 'show',
                revision+':'+name]) if revision else (repo/name).read_bytes()
            destination = root/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
            destination.chmod((repo/name).stat().st_mode & 0o777)
            results['implementation_sha256'][name] = sha(data)
        capture = root/CAPTURE
        capture.parent.mkdir(parents=True)
        shutil.copyfile(repo/CAPTURE, capture)
        source, vendor, cargo = root/'source', root/'vendor', root/'cargo-home'
        dep = vendor/'log-dependency-0.1.0'
        for directory in (source/'src', dep/'src', cargo):
            directory.mkdir(parents=True)
        (dep/'Cargo.toml').write_text(
            '[package]\nname="log-dependency"\nversion="0.1.0"\nedition="2021"\n', encoding='utf-8')
        (dep/'src/lib.rs').write_text('#![no_std]\npub fn value()->u64{3}\n', encoding='utf-8')
        (dep/'.cargo-checksum.json').write_text(json.dumps({'files': inventory(dep), 'package': None}), encoding='utf-8')
        (cargo/'config.toml').write_text(
            '[source.crates-io]\nreplace-with="fixture"\n[source.fixture]\ndirectory='+json.dumps(str(vendor))+'\n', encoding='utf-8')
        env = dict(os.environ, CARGO_HOME=str(cargo), RUSTC=str(tools['rust/bin/rustc']),
                   LC_ALL='C', PYTHONCOERCECLOCALE='0')
        # The dependency-free mode needs a real empty registry root, but no
        # source replacement. Cache mode uses the explicitly owned config.
        registry = root/'registry'
        registry.mkdir()

        def prepare(cached):
            deps = '[dependencies]\nlog-dependency="=0.1.0"' if cached else ''
            (source/'Cargo.toml').write_text(MANIFEST.format(dependencies=deps), encoding='utf-8')
            (source/'src/lib.rs').write_text(CODE.format(message='cafe', dependency=''), encoding='utf-8')
            result = subprocess.run([str(tools['rust/bin/cargo']), 'generate-lockfile', '--offline'],
                cwd=source, env=dict(env, PYTHONUTF8='1'), capture_output=True, timeout=30)
            if result.returncode:
                raise RuntimeError(result.stderr.decode('utf-8', errors='replace'))

        def build(name, *, utf8, message, failure=False, cached=False, cache_name='cache'):
            code = CODE.format(message=message, dependency='+log_dependency::value()' if cached else '')
            if failure:
                code += 'compile_error!('+json.dumps(message, ensure_ascii=False)+');\n'
            (source/'src/lib.rs').write_text(code, encoding='utf-8')
            before, dependencies = inventory(source), inventory(vendor)
            cache_before = inventory(root/cache_name) if cached else {}
            config = (cargo/'config.toml').read_bytes()
            build_output = root/name
            command = [sys.executable, '-B', '-X', 'utf8='+str(utf8),
                str(root/'scripts/pump_build_verified.py'), '--source-directory', str(source),
                '--sdk', str(sdk), '--registry-home', str(cargo if cached else registry),
                '--output', str(build_output)]
            if cached:
                command += ['--dependency-cache', str(root/cache_name)]
            mode = subprocess.check_output([sys.executable, '-X', 'utf8='+str(utf8), '-c',
                'import json,locale,sys;print(json.dumps([locale.getencoding(),sys.flags.utf8_mode]))'],
                env=dict(env, PYTHONUTF8=str(utf8)), text=True, encoding='utf-8')
            result = subprocess.run(command, env=dict(env, PYTHONUTF8=str(utf8)),
                                    capture_output=True, timeout=120)
            log = (build_output/'build.log').read_bytes()
            (output/(name+'.log')).write_bytes(log)
            (output/(name+'.stderr')).write_bytes(result.stderr)
            receipt = json.loads((build_output/'build-attempt.json').read_text(encoding='utf-8'))
            report_path = build_output/'build-comparison.json'
            report = json.loads(report_path.read_text(encoding='utf-8')) if report_path.exists() else None
            compiled = build_output/'target/sbf-solana-solana/release/pump_recovered.so'
            published = build_output/'candidate.so'
            row = {'locale': json.loads(mode), 'wrapper_returncode': result.returncode,
                   'compiler_returncode': receipt.get('returncode'),
                   'raw_log_sha256': sha(log), 'log_hash_recorded': receipt.get('build_log_sha256') == sha(log),
                   'log_contains_message': message.encode('utf-8') in log,
                   'decode_error': b'UnicodeDecodeError' in result.stderr,
                   'compiled_sha256': sha(compiled.read_bytes()) if compiled.exists() else None,
                   'candidate_sha256': sha(published.read_bytes()) if published.exists() else None,
                   'comparison_published': report is not None,
                   'source_unchanged': before == inventory(source),
                   'dependency_inputs_unchanged': dependencies == inventory(vendor) and config == (cargo/'config.toml').read_bytes(),
                   'recorded_source_unchanged': receipt.get('source_unchanged'),
                   'stack_gate_passed': receipt.get('stack_diagnostic_gate_passed'),
                   'cache_status': report.get('dependency_cache', {}).get('status') if report else None}
            row['existing_cache_unchanged'] = cache_before == inventory(root/cache_name) if cache_before else None
            results['cases'][name] = row

        prepare(False)
        for message in ('cafe', 'caf\u00e9'):
            for failure in (False, True):
                label = ('unicode' if message != 'cafe' else 'ascii')+('-failure' if failure else '-warning')
                for utf8 in (1, 0):
                    build(label+'-'+str(utf8), utf8=utf8, message=message, failure=failure)
        prepare(True)
        build('cache-seed-1', utf8=1, message='caf\u00e9', cached=True)
        build('cache-hit-0', utf8=0, message='caf\u00e9', cached=True)
        build('cache-miss-0', utf8=0, message='caf\u00e9', cached=True, cache_name='fresh-cache')
        for utf8 in (1, 0):
            build('cache-failure-'+str(utf8), utf8=utf8, message='caf\u00e9', cached=True, failure=True)
        results['copied_capture_unchanged'] = sha(capture.read_bytes()) == original[CAPTURE]
    results['caller_inputs_unchanged'] = original == {p: sha((repo/p).read_bytes()) for p in original}
    results['tools_unchanged'] = results['tool_sha256'] == {name: sha(path.read_bytes()) for name, path in tools.items()}
    (output/'results.json').write_text(json.dumps(results, indent=2)+'\n', encoding='utf-8')
    return results


def validate(result, expect):
    defective = {'unicode-warning-0', 'unicode-failure-0',
                 'cache-hit-0', 'cache-miss-0', 'cache-failure-0'}
    for name, row in result['cases'].items():
        broken = expect == 'base' and name in defective
        failed = 'failure' in name
        expected_code = None if broken else (1 if name.startswith('cache-failure') else 101) if failed else 0
        if (row['decode_error'] != broken or row['compiler_returncode'] != expected_code
                or row['comparison_published'] != (not failed and not broken)
                or row['log_hash_recorded'] != (not broken)
                or not row['log_contains_message'] or not row['source_unchanged']
                or not row['dependency_inputs_unchanged'] or row['existing_cache_unchanged'] is False):
            raise AssertionError('unexpected compiler/receipt outcome: '+name)
    cases = result['cases']
    for name in ('ascii-warning-0', 'unicode-warning-1', 'unicode-warning-0'):
        if expect == 'fixed' or name not in defective:
            if cases[name]['candidate_sha256'] != cases['ascii-warning-1']['candidate_sha256']:
                raise AssertionError('different diagnostic-control output: '+name)
    if expect == 'fixed':
        for name in ('cache-hit-0', 'cache-miss-0'):
            if cases[name]['candidate_sha256'] != cases['cache-seed-1']['candidate_sha256']:
                raise AssertionError('different cache-control output: '+name)
        if cases['cache-hit-0']['cache_status'] != 'hit':
            raise AssertionError('verified cache reuse was not exercised')
    for name in ('copied_capture_unchanged', 'caller_inputs_unchanged', 'tools_unchanged'):
        if not result[name]:
            raise AssertionError('input changed: '+name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    args = parser.parse_args()
    result = run_probe(args.repo, args.sdk, args.output, args.revision)
    validate(result, args.expect)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
