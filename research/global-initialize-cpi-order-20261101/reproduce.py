"""Compare the native initialize model with signed captured-program execution."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile


def reproduce(repo, revision=None):
    spec = importlib.util.spec_from_file_location(
        'global_fixture', repo / 'tests/test_global_lifecycle_captured.py')
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    assert hashlib.sha256(fixture.ELF.read_bytes()).hexdigest() == fixture.ELF_SHA256
    cases = fixture.init_cases()
    checker = fixture.GlobalLifecycleCapturedTests()
    source_hashes = {}
    with tempfile.TemporaryDirectory(prefix='global-init-order-') as temporary:
        root = Path(temporary)
        for name in ('global_lifecycle.rs', 'global_lifecycle_host.rs'):
            relative = 'programs/pump/recovered/' + name
            raw = (subprocess.check_output(['git', 'show', revision + ':' + relative], cwd=repo)
                   if revision else (repo / relative).read_bytes())
            (root / name).write_bytes(raw)
            source_hashes[relative] = hashlib.sha256(raw).hexdigest()
        host = root / 'host'
        subprocess.run(['rustc', '--edition=2021', '-O', str(root / 'global_lifecycle_host.rs'),
                        '-o', str(host)], check=True)
        answers = subprocess.check_output([str(host)], text=True,
            input=''.join(row['line'] + '\n' for row in cases)).splitlines()
        assert len(answers) == len(cases)
        results = []
        for row, answer in zip(cases, answers):
            observed = row['run']()
            # Reuse the repository's state/error checker on this same execution.
            checked = dict(row, run=lambda observed=observed: observed)
            try:
                checker.assert_row(checked, answer)
            except AssertionError as error:
                mismatch = str(error)
            else:
                mismatch = None
            results.append({'name': row['name'], 'input': row['line'], 'host': answer,
                            'captured': observed, 'mismatch': mismatch})
    return {'revision': revision or 'working-tree', 'source_sha256': source_hashes,
            'captured_sha256': fixture.ELF_SHA256,
            'rustc': subprocess.check_output(['rustc', '--version'], text=True).strip(),
            'cases': len(results), 'mismatches': sum(row['mismatch'] is not None for row in results),
            'results': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--revision')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = reproduce(args.repo.resolve(), args.revision)
    args.output.write_text(json.dumps(result, indent=2,
        default=lambda value: value.hex() if isinstance(value, bytes) else str(value)) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'results'}, indent=2))
