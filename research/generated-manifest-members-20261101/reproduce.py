#!/usr/bin/env python3
"""Run actual static generators and compare their manifest admission with the root checker."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

GENERATORS = ('analyze_program', 'deep_disassembly', 'deep_section_analysis', 'bytecode_signatures')
SOURCE_NAMES = [name + '.py' for name in GENERATORS] + [
    'analyze.py', 'window_elf_reader.py', 'revalidate_all.py']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repository', type=Path)
    parser.add_argument('--revision', help='read exact source bytes from this Git revision')
    parser.add_argument('--expect', choices=('before', 'fixed'), required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--compare', type=Path, help='compare unchanged payloads with a previous run')
    args = parser.parse_args()
    root = args.repository.resolve()
    source_bytes = {}
    for name in SOURCE_NAMES:
        relative = 'scripts/' + name
        source_bytes[relative] = subprocess.check_output(['git', '-C', str(root), 'show',
            args.revision + ':' + relative]) if args.revision else (root / relative).read_bytes()
    evidence = {p.relative_to(root).as_posix(): p.read_bytes()
                for p in (root / 'evidence').rglob('*') if p.is_file()}
    original_hashes = {name: sha(data) for name, data in evidence.items()}
    results = []
    with tempfile.TemporaryDirectory(prefix='generated-manifest-proof-') as temporary:
        workspace = Path(temporary)
        cohort = workspace / 'source'
        for name, data in {**source_bytes, **evidence}.items():
            path = cohort / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        spec = importlib.util.spec_from_file_location('canonical_revalidation', cohort/'scripts/revalidate_all.py')
        canonical = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(canonical)
        for generator in GENERATORS:
            output = workspace / generator
            command = [sys.executable, '-I', '-B', str(cohort/'scripts'/f'{generator}.py'),
                       '--output', str(output)]
            if generator != 'bytecode_signatures':
                command += ['--program', 'mayhem']
            run = subprocess.run(command, cwd=cohort, capture_output=True, text=True, timeout=120)
            assert run.returncode == 0, (generator, run.stderr)
            original = (output/'manifest.json').read_bytes()
            manifest = json.loads(original)
            artifact = 'summary.json'

            def duplicate(key, value):
                return ('{\n  '+key+': '+json.dumps(value)+',\n'+original.decode().lstrip()[1:]).encode()

            variants = {
                'clean': original,
                'contradictory_duplicate': duplicate(json.dumps(artifact), '0'*64),
                'identical_duplicate': duplicate(json.dumps(artifact), manifest[artifact]),
                'escaped_duplicate': duplicate('"\\u0073ummary.json"', '0'*64),
                'escaped_unique': original.replace(b'"summary.json"', b'"\\u0073ummary.json"', 1),
                'unique_wrong_digest': json.dumps({**manifest, artifact: '0'*64}).encode(),
                'malformed_json': b'{',
            }
            payloads = {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.name != 'manifest.json'}
            rows = []
            for label, data in variants.items():
                (output/'manifest.json').write_bytes(data)
                admitted = canonical.check_manifest(output)
                cli = {}
                duplicate_case = label.endswith('_duplicate')
                success = label in ('clean', 'escaped_unique') or (duplicate_case and args.expect == 'before')
                for mode, flags in (('normal', []), ('optimized', ['-O']), ('docstrings_removed', ['-OO'])):
                    verified = subprocess.run([sys.executable, '-I', '-B', *flags,
                        str(output/'verify.py')], cwd=output, capture_output=True, text=True, timeout=30)
                    assert (verified.returncode == 0) == success, (generator, label, mode, verified.stderr)
                    says_pass = 'All checks passed.' in verified.stdout
                    assert says_pass == success, (generator, label, mode)
                    if duplicate_case and args.expect == 'fixed':
                        assert 'duplicate manifest key: summary.json' in verified.stdout
                    cli[mode] = {'exit': verified.returncode, 'says_pass': says_pass}
                expected_status = ('manifest_parse_error' if duplicate_case or label == 'malformed_json'
                                   else 'fail' if label == 'unique_wrong_digest' else 'pass')
                assert admitted['status'] == expected_status, (generator, label, admitted)
                rows.append({'variant': label, 'canonical_status': admitted['status'],
                             'canonical_errors': admitted['errors'], 'generated_cli': cli})
                assert payloads == {p.name: sha(p.read_bytes()) for p in output.iterdir()
                                    if p.name != 'manifest.json'}
            (output/'manifest.json').write_bytes(original)
            results.append({'generator': generator,
                'generator_sha256': sha(source_bytes['scripts/'+generator+'.py']),
                'verifier_sha256': payloads.pop('verify.py'),
                'analysis_payload_sha256': payloads, 'cases': rows})
        assert all((cohort/name).read_bytes() == data for name, data in {**source_bytes, **evidence}.items())
    assert all(sha((root/name).read_bytes()) == value for name, value in original_hashes.items())
    if not args.revision:
        assert all((root/name).read_bytes() == data for name, data in source_bytes.items())
    result = {'source_revision': args.revision or subprocess.check_output(
        ['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip(),
        'source_sha256': {name: sha(data) for name, data in source_bytes.items()},
        'capture_sha256': {name: digest for name, digest in original_hashes.items() if name.endswith('/deployed.so')},
        'scope': 'Actual static generation from retained captures; owned manifest-only variants; no VM/program/compiler execution.',
        'original_and_private_inputs_unchanged': True, 'results': results}
    if args.compare:
        previous = json.loads(args.compare.read_text())
        assert previous['capture_sha256'] == result['capture_sha256']
        for old, new in zip(previous['results'], results):
            assert old['generator'] == new['generator']
            assert old['analysis_payload_sha256'] == new['analysis_payload_sha256']
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'generators': len(results), 'verifier_invocations': 84,
                      'expect': args.expect, 'inputs_unchanged': True}))


if __name__ == '__main__':
    main()
