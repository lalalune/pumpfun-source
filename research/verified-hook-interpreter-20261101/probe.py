"""Actual offline generic builds through every verified-builder Python hook."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv

FILES = [f'scripts/{name}.py' for name in (
    'pump_build_verified', 'pump_dependency_cache', 'pump_text_layout',
    'pump_target_library_profile', 'pump_data_order', 'source_manifest_guard',
    'build_source_manifest', 'compare', 'analyze', 'probe_report',
    'pump_compare_function_bytes', 'pump_exact_body_inventory',
    'pump_quote_control_function_match', 'pump_physical_source_wrapper',
    'pump_text_layout_rustc', 'pump_text_layout_linker')]
FILES += ['scripts/pump_text_layout_default.ld', 'reconstruction/harness/instruction_stream.py']
LAUNCHERS = ['scripts/'+name+'.sh' for name in (
    'pump_physical_source_wrapper', 'pump_text_layout_rustc', 'pump_text_layout_linker')]
CAPTURE = 'evidence/original/pump/deployed.so'
FIXTURES = ['scripts/fixtures/cargo-index-case/'+name for name in
            ('Inflector-0.11.4.crate', 'inflector-index.jsonl')]
CODE = ('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{VALUE}\n'
        '#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
MANIFEST = ('[package]\nname="pump-recovered"\nversion="0.1.0"\nedition="2021"\n'
            '[lib]\ncrate-type=["cdylib","lib"]\nDEPENDENCIES\n'
            '[profile.release]\npanic="abort"\nlto=false\ncodegen-units=1\n[workspace]\n')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes())
            for p in sorted(root.rglob('*')) if p.is_file()}


def run(repo, sdk, output, revision=None):
    repo, sdk, output = [Path(p).resolve() for p in (repo, sdk, output)]
    output.mkdir(parents=True, exist_ok=False)
    existing = [name for name in [*FILES, *LAUNCHERS, *FIXTURES, CAPTURE] if (repo/name).is_file()]
    originals = {name: sha((repo/name).read_bytes()) for name in existing}
    sources = {}
    for name in [*FILES, *LAUNCHERS]:
        if revision:
            result = subprocess.run(['git', '-C', str(repo), 'show', revision+':'+name], capture_output=True)
            if result.returncode and name in LAUNCHERS:
                continue
            result.check_returncode()
            sources[name] = result.stdout
        else:
            sources[name] = (repo/name).read_bytes()
    tools = {name: sdk/name for name in ('rust/bin/cargo', 'rust/bin/rustc', 'llvm/bin/llvm-objcopy')}
    result = {'source_sha256': {name: sha(raw) for name, raw in sources.items()},
              'tool_sha256': {name: sha(path.read_bytes()) for name, path in tools.items()},
              'cases': {}, 'image_executions': 0}
    archive, index = [(repo/name).read_bytes() for name in FIXTURES]
    if sha(archive) != 'fe438c63458706e03479442743baae6c88256498e6431708f6dfc520a26515d3' or sha(index) != 'cb2b8f9cd2baa2934fa604108cd792b30f83b4ba32de329607046984d2213957':
        raise ValueError('retained official crate/index fixture differs')
    result['registry_fixture_sha256'] = dict(zip(FIXTURES, [sha(archive), sha(index)]))
    result['rustc_version'] = subprocess.check_output([str(tools['rust/bin/rustc']), '-vV'], text=True, encoding='utf-8').strip()
    with tempfile.TemporaryDirectory(prefix='verified-hook-proof-') as temporary:
        root = Path(temporary).resolve()
        for name, raw in sources.items():
            dest = root/name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
            dest.chmod((repo/name).stat().st_mode & 0o777)
        capture = root/CAPTURE
        capture.parent.mkdir(parents=True)
        shutil.copyfile(repo/CAPTURE, capture)
        selected_environment = root/'selected Python'
        # A loose symlink is canonicalized by some Python distributions. An
        # actual venv preserves the selected interpreter and tests its route.
        venv.EnvBuilder(with_pip=False).create(selected_environment)
        selected = selected_environment/'bin/python'
        with_python, without_python = root/'with-python', root/'without-python'
        with_python.mkdir()
        without_python.mkdir()
        (with_python/'python3').symlink_to(selected)
        source, cargo, registry = [root/name for name in ('source', 'cargo-home', 'registry')]
        (source/'src').mkdir(parents=True)
        cargo.mkdir()
        registry.mkdir()
        # Use the repository's unchanged official archive/index fixture. Cargo
        # extracts it normally; the seed path independently checks its archive.
        index_cache = b'\x03\x02\0\0\0offline-fixture\0' + b''.join(
            json.loads(row)['vers'].encode()+b'\0'+row+b'\0' for row in index.splitlines())
        cargo_inputs = {}
        for namespace in ('index.crates.io-1949cf8c6b5b557f', 'index.crates.io-6f17d22bba15001f'):
            entries = {'registry/cache/'+namespace+'/Inflector-0.11.4.crate': archive,
                       'registry/index/'+namespace+'/.cache/in/fl/inflector': index_cache,
                       'registry/index/'+namespace+'/config.json': b'{"dl":"https://static.crates.io/crates","api":"https://crates.io"}'}
            for name, raw in entries.items():
                path = cargo/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
                cargo_inputs[name] = sha(raw)
        order = root/'order.ld'
        order.write_text((root/'scripts/pump_text_layout_default.ld').read_text(encoding='utf-8').replace(
            '  .text : { *(.text*) } :text', '  .text : {\n    *(.text*)\n  } :text'), encoding='utf-8')
        env = dict(os.environ, CARGO_HOME=str(cargo), RUSTC=str(tools['rust/bin/rustc']))

        def prepare(cached):
            deps = '[dependencies]\nInflector={version="=0.11.4",default-features=false}' if cached else ''
            (source/'Cargo.toml').write_text(MANIFEST.replace('DEPENDENCIES', deps), encoding='utf-8')
            code = CODE.replace('VALUE', 'inflector::cases::snakecase::is_snake_case("fixed_name") as u64' if cached else '27')
            if cached:
                code = code.split('#[panic_handler]')[0]  # The real dependency links std's handler.
            (source/'src/lib.rs').write_text(code, encoding='utf-8')
            lock = subprocess.run([str(tools['rust/bin/cargo']), 'generate-lockfile', '--offline'],
                                  cwd=source, env=env, capture_output=True, timeout=30)
            lock.check_returncode()

        def build(name, *, path_python, ordered=False, cached=False, cache_name='cache', seed=None):
            before, dep_before = inventory(source), inventory(cargo/'registry/src')
            cargo_before = inventory(cargo)
            cache_before = inventory(root/cache_name) if cached else {}
            out = root/name
            command = [str(selected), '-B', str(root/'scripts/pump_build_verified.py'),
                '--source-directory', str(source), '--sdk', str(sdk),
                '--registry-home', str(cargo if cached else registry), '--output', str(out)]
            if ordered:
                command += ['--text-section-order', str(order)]
            if cached:
                command += ['--dependency-cache', str(root/cache_name)]
            if seed:
                command += ['--dependency-cache-seed', str(seed)]
            child_env = dict(env, PATH=str(with_python if path_python else without_python),
                             PUMP_VERIFIED_PYTHON=str(root/'unselected-python'))
            process = subprocess.run(command, env=child_env, capture_output=True, timeout=120)
            log = (out/'build.log').read_bytes() if (out/'build.log').is_file() else b''
            (output/(name+'.log')).write_bytes(log)
            (output/(name+'.stderr')).write_bytes(process.stderr)
            attempt = json.loads((out/'build-attempt.json').read_bytes()) if (out/'build-attempt.json').is_file() else {}
            report = json.loads((out/'build-comparison.json').read_bytes()) if (out/'build-comparison.json').is_file() else None
            candidate = out/'candidate.so'
            row = {'returncode': process.returncode, 'path_contains_python3': path_python,
                   'compiler_returncode': attempt.get('returncode'),
                   'missing_python_diagnostic': b'python3: No such file or directory' in log+process.stderr,
                   'comparison_published': report is not None,
                   'candidate_sha256': sha(candidate.read_bytes()) if candidate.exists() else None,
                   'source_unchanged': before == inventory(source),
                   'dependency_inputs_unchanged': all(sha((cargo/name).read_bytes()) == digest for name, digest in cargo_inputs.items()) and
                       all(inventory(cargo/'registry/src').get(name) == digest for name, digest in dep_before.items()),
                   'cargo_home_created_files': sorted(set(inventory(cargo))-set(cargo_before)),
                   'existing_cache_unchanged': cache_before == inventory(root/cache_name) if cache_before else None,
                   'selected_python_recorded': attempt.get('environment', {}).get('PUMP_VERIFIED_PYTHON') == str(selected),
                   'wrapper_launcher_bound': attempt.get('source_wrapper_launcher_sha256') == sha(sources[LAUNCHERS[0]]) if LAUNCHERS[0] in sources else None,
                   'cache_status': report.get('dependency_cache', {}).get('status') if report else None,
                   'text_launcher_bindings': {Path(n).name: digest for n, digest in report.get('text_layout', {}).get('helper_sha256', {}).items() if n.endswith('.sh')} if report else {},
                   'seed_launcher_refused': b'seed compiler wrapper launcher differs' in process.stderr,
                   'seed_python_refused': b'seed compiler wrapper Python differs' in process.stderr}
            if report and cached:
                manifests = list((root/cache_name).glob('*/MANIFEST.json'))
                if manifests:
                    context = json.loads(manifests[0].read_bytes())['context']
                    row['cache_launcher_bound'] = context.get('wrapper_launcher_sha256') == attempt.get('source_wrapper_launcher_sha256') and 'wrapper_launcher_sha256' in context
                    row['cache_selected_python_bound'] = context.get('wrapper_python') == str(selected)
            result['cases'][name] = row
            return out

        prepare(False)
        for ordered in (False, True):
            for path_python in (True, False):
                build(('ordered' if ordered else 'ordinary')+('-path' if path_python else '-empty'),
                      path_python=path_python, ordered=ordered)
        prepare(True)
        seed = build('cache-cold-path', path_python=True, cached=True)
        build('cache-warm-path', path_python=True, cached=True)
        build('cache-cold-empty', path_python=False, cached=True, cache_name='empty-path-cache')
        build('cache-warm-empty', path_python=False, cached=True)
        build('cache-import-empty', path_python=False, cached=True, cache_name='import-cache', seed=seed)
        original_seed = (seed/'build-comparison.json').read_bytes()
        if LAUNCHERS[0] in sources:
            for key, name in [('source_wrapper_launcher_sha256', 'launcher'), ('environment', 'python')]:
                altered = json.loads(original_seed)
                if name == 'launcher':
                    altered[key] = '0'*64
                else:
                    altered[key]['PUMP_VERIFIED_PYTHON'] = str(root/'wrong-python')
                (seed/'build-comparison.json').write_text(json.dumps(altered), encoding='utf-8')
                build('seed-mismatch-'+name, path_python=False, cached=True, cache_name='mismatch-'+name, seed=seed)
            (seed/'build-comparison.json').write_bytes(original_seed)
        result['copied_capture_unchanged'] = sha(capture.read_bytes()) == originals[CAPTURE]
    result['caller_inputs_unchanged'] = originals == {name: sha((repo/name).read_bytes()) for name in originals}
    result['tools_unchanged'] = result['tool_sha256'] == {name: sha(path.read_bytes()) for name, path in tools.items()}
    (output/'results.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    return result


def validate(result, expect):
    for name, row in result['cases'].items():
        mismatch = name.startswith('seed-mismatch-')
        success = not mismatch and (expect == 'fixed' or row['path_contains_python3'])
        if (row['comparison_published'] != success or (row['returncode'] == 0) != success
                or not row['source_unchanged'] or not row['dependency_inputs_unchanged']
                or row['existing_cache_unchanged'] is False):
            raise AssertionError('unexpected build result: '+name)
        if expect == 'base' and not success and not row['missing_python_diagnostic']:
            raise AssertionError('missing original hook failure: '+name)
        if expect == 'fixed' and success:
            if not row['selected_python_recorded'] or not row['wrapper_launcher_bound']:
                raise AssertionError('missing launcher attribution: '+name)
            if name.startswith('cache-') and not (row['cache_launcher_bound'] and row['cache_selected_python_bound']):
                raise AssertionError('missing cache launcher identity: '+name)
            if name.startswith('ordered-') and len(row['text_launcher_bindings']) != 2:
                raise AssertionError('missing linker/rustc launcher bindings: '+name)
    cases = result['cases']
    if expect == 'fixed':
        for name in ('ordinary-empty', 'ordered-path', 'ordered-empty'):
            if cases[name]['candidate_sha256'] != cases['ordinary-path']['candidate_sha256']:
                raise AssertionError('ordinary or ordered artifact changed: '+name)
        for name in ('cache-warm-path', 'cache-cold-empty', 'cache-warm-empty', 'cache-import-empty'):
            if cases[name]['candidate_sha256'] != cases['cache-cold-path']['candidate_sha256']:
                raise AssertionError('cache artifact changed: '+name)
        for name in ('cache-warm-path', 'cache-warm-empty', 'cache-import-empty'):
            if cases[name]['cache_status'] != 'hit':
                raise AssertionError('cache reuse not exercised: '+name)
        for name in ('launcher', 'python'):
            if not cases['seed-mismatch-'+name]['seed_'+name+'_refused']:
                raise AssertionError('seed route mismatch admitted: '+name)
    if not all(result[name] for name in ('copied_capture_unchanged', 'caller_inputs_unchanged', 'tools_unchanged')):
        raise AssertionError('input mutation')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--sdk', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    args = parser.parse_args()
    result = run(args.repo, args.sdk, args.output, args.revision)
    validate(result, args.expect)
    print(json.dumps(result, indent=2))
