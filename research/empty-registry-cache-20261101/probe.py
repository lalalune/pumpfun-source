"""Offline cache preparation and supported build integration; no image execution."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = '599891304e83e853ec723dc1417550bef4e1c074'
PRODUCER = 'scripts/prepare_locked_cargo_home.py'
CONSUMER_FILES = ['scripts/build_supported_sbpf_candidate.py', 'scripts/build_source_manifest.py',
                  'scripts/supported_sbpf_policies/v1.53.json']
PROFILE = '[profile.release]\npanic="abort"\noverflow-checks=true\nlto=false\ncodegen-units=1\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def files(root):
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}


def reproduce(repo, tools, revision=None, consumer_revision=BASE):
    result = {'base': BASE, 'revision': revision or 'working-tree', 'consumer_revision': consumer_revision,
              'build_cases': {}, 'cache_controls': {}}
    sdk = tools/'v1.53/platform-tools'
    with tempfile.TemporaryDirectory(prefix='empty-registry-cache-') as temporary:
        root = Path(temporary).resolve()
        code, cohort = root/'code', root/'repo'
        for name in [PRODUCER, *CONSUMER_FILES]:
            selected = revision if name == PRODUCER else consumer_revision
            raw = (subprocess.check_output(['git', '-C', str(repo), 'show', selected+':'+name])
                   if selected else (repo/name).read_bytes())
            path = code/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        result['source_sha256'] = {name: sha((code/name).read_bytes()) for name in [PRODUCER, *CONSUMER_FILES]}
        spec = importlib.util.spec_from_file_location('empty_cache_supported', code/CONSUMER_FILES[0])
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        (cohort/'scripts').mkdir(parents=True)
        shutil.copyfile(code/CONSUMER_FILES[1], cohort/CONSUMER_FILES[1])
        reference = cohort/'evidence/original/pump/deployed.so'
        reference.parent.mkdir(parents=True)
        shutil.copyfile(repo/'evidence/original/pump/deployed.so', reference)
        seed = root/'seed-home'
        seed.mkdir()
        env = {'PATH': os.environ['PATH'], 'CARGO_HOME': str(seed)}

        def clean(text):
            return text.replace(str(root), 'OWNED').replace(str(tools), 'SDK_CACHE')

        def prepare(lock, output, home=seed):
            run = subprocess.run([sys.executable, '-B', str(code/PRODUCER), '--lockfile', str(lock),
                                  '--output', str(output)], env=dict(env, CARGO_HOME=str(home)),
                                 capture_output=True, text=True, timeout=30)
            return {'returncode': run.returncode, 'stdout': clean(run.stdout), 'stderr': clean(run.stderr)}

        for label in ('dependency_free', 'local_path_only'):
            crate = cohort/label
            (crate/'src').mkdir(parents=True)
            manifest = ('[package]\nname="empty-cache-build"\nversion="0.1.0"\nedition="2021"\n'
                        '[lib]\nname="empty_cache_build"\ncrate-type=["cdylib"]\n'+PROFILE+'[workspace]\n')
            value = '0'
            if label == 'local_path_only':
                manifest += 'members=["helper"]\n[dependencies]\nlocal-helper={path="helper"}\n'
                (crate/'helper/src').mkdir(parents=True)
                (crate/'helper/Cargo.toml').write_text('[package]\nname="local-helper"\nversion="0.1.0"\nedition="2021"\n')
                (crate/'helper/src/lib.rs').write_text('#![no_std]\npub fn value()->u64{7}\n')
                value = 'local_helper::value()'
            (crate/'Cargo.toml').write_text(manifest)
            (crate/'src/lib.rs').write_text('#![no_std]\n#[no_mangle]pub extern "C" fn entrypoint(_: *const u8)->u64{'+value+'}\n'
                '#[panic_handler]fn panic(_: &core::panic::PanicInfo)->!{loop{}}\n')
            lock = subprocess.run([str(sdk/'rust/bin/cargo'), 'generate-lockfile', '--offline'],
                                  cwd=crate, env=env, capture_output=True, text=True, timeout=30)
            if lock.returncode:
                raise RuntimeError(lock.stderr)
            prepared = root/(label+'-prepared')
            row = {'lockfile': (crate/'Cargo.lock').read_text(), 'lock_returncode': lock.returncode,
                   'prepare': prepare(crate/'Cargo.lock', prepared), 'registry_exists': (prepared/'registry').is_dir(),
                   'cache_files': files(prepared), 'manifest': json.loads((prepared/'cache-manifest.json').read_text())}
            before = files(crate)
            admitted_plans = []

            def build(home, output):
                child_env = dict(env, CARGO_HOME=str(home))
                args = builder.parser().parse_args(['--manifest', str(crate/'Cargo.toml'), '--program', 'pump',
                    '--artifact-name', 'probe.so', '--tools-version', 'v1.53', '--output', str(output)])
                try:
                    planned = builder.plan(args, cohort, child_env, cache_root=tools)
                except ValueError as error:
                    return {'plan_error': str(error), 'output_created': output.exists()}
                admitted_plans.append(planned)
                status = builder.execute(planned, child_env)
                attempt = json.loads((output/'build-attempt.json').read_text())
                result['tool_sha256'] = {str(Path(k).relative_to(tools)): v for k, v in planned['tool_sha256'].items()}
                return {'returncode': status, 'compile_returncode': attempt['compile_returncode'], 'stage': attempt['stage'],
                        'source_unchanged': attempt.get('source_unchanged'),
                        'candidate_sha256': attempt.get('stripped_output', {}).get('sha256'),
                        'build_log': clean((output/'build.log').read_text())}

            row['pipeline'] = build(prepared, root/(label+'-pipeline'))
            # Diagnostic control differs only by ensuring the empty registry root.
            control = root/(label+'-control-home')
            shutil.copytree(prepared, control)
            (control/'registry').mkdir(exist_ok=True)
            row['empty_registry_control'] = build(control, root/(label+'-control-build'))
            # Plain Cargo already accepts either prepared layout. Prove that
            # the failure is the adapter's admission, not Cargo's cache format.
            plain_home = root/(label+'-plain-home')
            shutil.copytree(prepared, plain_home)
            plain_target = root/(label+'-plain-target')
            plain_env = dict(env, **admitted_plans[-1]['environment'])
            plain_env.update(CARGO_HOME=str(plain_home), CARGO_TARGET_DIR=str(plain_target))
            plain = subprocess.run([str(sdk/'rust/bin/cargo'), 'build', '--manifest-path', str(crate/'Cargo.toml'),
                '--release', '--target', 'sbpf-solana-solana', '--locked', '--offline'],
                cwd=crate, env=plain_env, capture_output=True, text=True, timeout=90)
            plain_hash = None
            if plain.returncode == 0:
                image = plain_target/'sbpf-solana-solana/release/empty_cache_build.so'
                stripped = root/(label+'-plain.so')
                subprocess.run([str(tools/'v1.52/platform-tools/llvm/bin/llvm-objcopy'), '--strip-all',
                                str(image), str(stripped)], check=True, capture_output=True)
                plain_hash = sha(stripped.read_bytes())
            row['plain_cargo'] = {'returncode': plain.returncode, 'candidate_sha256': plain_hash,
                                  'stderr': clean(plain.stderr)}
            row['caller_source_preserved'] = before == files(crate)
            row['prepared_files_preserved'] = row['cache_files'] == files(prepared)
            result['build_cases'][label] = row

        # Retained real archive/index bytes exercise nonempty selection unchanged.
        fixture = repo/'scripts/fixtures/cargo-index-case'
        archive = (fixture/'Inflector-0.11.4.crate').read_bytes()
        entries = [json.loads(line) for line in (fixture/'inflector-index.jsonl').read_bytes().splitlines()]
        sparse = b'\x03\x02\x00\x00\x00retained-control\0'+b''.join(
            entry['vers'].encode()+b'\0'+json.dumps(entry, separators=(',', ':')).encode()+b'\0' for entry in entries)
        home = root/'nonempty-home'
        namespace = 'index.crates.io-1949cf8c6b5b557f'
        for relative, raw in [(f'registry/cache/{namespace}/Inflector-0.11.4.crate', archive),
                              (f'registry/index/{namespace}/.cache/in/fl/inflector', sparse),
                              (f'registry/index/{namespace}/config.json', b'{"dl":"https://static.crates.io/crates"}')]:
            path = home/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        source_before = files(home)
        lock = root/'registry.lock'
        lock_text = ('version=3\n[[package]]\nname="Inflector"\nversion="0.11.4"\n'
                     'source="registry+https://github.com/rust-lang/crates.io-index"\nchecksum="'+sha(archive)+'"\n')
        lock.write_text(lock_text)
        out = root/'nonempty-prepared'
        normal = prepare(lock, out, home)
        normal.update(files=files(out), registry_exists=(out/'registry').is_dir(),
                      manifest=json.loads((out/'cache-manifest.json').read_text()))
        result['cache_controls']['nonempty'] = normal
        previous = files(out)
        occupied = prepare(lock, out, home)
        occupied['preserved'] = previous == files(out)
        result['cache_controls']['occupied_output'] = occupied
        for name, content, cache in [('missing_archive', lock_text, seed),
            ('unsupported_registry', lock_text.replace('https://github.com/rust-lang/crates.io-index', 'https://invalid.example/index'), home)]:
            lock.write_text(content)
            output = root/name
            failure = prepare(lock, output, cache)
            failure['output_created'] = output.exists()
            result['cache_controls'][name] = failure
        result['cache_sources_preserved'] = source_before == files(home)
        result['rustc_version'] = subprocess.check_output([str(sdk/'rust/bin/rustc'), '--version', '--verbose'], text=True)
        result['cargo_version'] = subprocess.check_output([str(sdk/'rust/bin/cargo'), '--version'], text=True)
    return result


def check(result, expected):
    for row in result['build_cases'].values():
        assert row['prepare']['returncode'] == 0 and row['manifest']['packages'] == [], row
        assert row['caller_source_preserved'] and row['prepared_files_preserved'], row
        control = row['empty_registry_control']
        assert control['returncode'] == 0 and control['source_unchanged'] is True, control
        assert row['plain_cargo']['returncode'] == 0, row
        assert row['plain_cargo']['candidate_sha256'] == control['candidate_sha256'], row
        pipeline = row['pipeline']
        if expected == 'base':
            assert not row['registry_exists'] and 'offline registry cache' in pipeline['plan_error'], row
            assert pipeline['output_created'] is False, row
        else:
            assert row['registry_exists'] and pipeline['returncode'] == 0, row
            assert pipeline['source_unchanged'] is True and pipeline['candidate_sha256'] == control['candidate_sha256'], row
    controls = result['cache_controls']
    assert controls['nonempty']['returncode'] == 0 and controls['nonempty']['registry_exists'], controls
    assert controls['occupied_output']['returncode'] != 0 and controls['occupied_output']['preserved'], controls
    for name in ('missing_archive', 'unsupported_registry'):
        assert controls[name]['returncode'] != 0 and not controls[name]['output_created'], controls[name]
    assert result['cache_sources_preserved']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--tools', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision')
    parser.add_argument('--consumer-revision', default=BASE)
    parser.add_argument('--expect', choices=('base', 'fixed'), required=True)
    args = parser.parse_args()
    result = reproduce(args.repo.resolve(), args.tools.resolve(), args.revision, args.consumer_revision)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    check(result, args.expect)
    print(json.dumps({'expected': args.expect, 'build_cases': len(result['build_cases']),
                      'cache_controls': len(result['cache_controls'])}))
