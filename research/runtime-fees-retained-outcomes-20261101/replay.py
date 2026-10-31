"""Exercise the real Fees aggregate CLI with retained real producer receipts.

Child adapters replay evidence; they do not claim another VM execution.
"""
import argparse
import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def replay(repo, corpus, mode, revision=None):
    script = repo / 'scripts/fees_validate_all.py'
    source = (subprocess.check_output(['git', 'show', revision + ':scripts/fees_validate_all.py'],
                                     cwd=repo).decode() if revision else script.read_text())
    tree = ast.parse(source)
    suites = next(ast.literal_eval(node.iter) for node in ast.walk(tree)
                  if isinstance(node, ast.For) and isinstance(node.iter, ast.List))
    raw = corpus.read_bytes()
    receipt = json.loads(gzip.decompress(raw) if raw.startswith(b'\x1f\x8b') else raw)
    selected = copy.deepcopy(receipt['suites'])
    original_case = selected['administration']['cases'][0]
    other_case = selected['administration']['cases'][1]
    if original_case['original']['error'] == other_case['candidate']['error']:
        raise ValueError('need two actually incompatible administrative outcomes')
    mutation = {'target_case': original_case['case'], 'candidate_source_case': other_case['case'],
                'original_error': original_case['original']['error'],
                'replacement_error': other_case['candidate']['error']}
    if mode == 'contradiction':
        original_case['candidate'] = copy.deepcopy(other_case['candidate'])
    with tempfile.TemporaryDirectory(prefix='fees-consumer-replay-') as temporary:
        root = Path(temporary)
        scripts = root / 'scripts'
        scripts.mkdir()
        (scripts / script.name).write_text(source)
        for relative in ('scripts/serial_suite_process.py', 'scripts/pump_amm_reusable_harness.py',
                         'scripts/pump_differential_output.py', 'reconstruction/harness/build_process.py'):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(repo / relative, target)
        original = root / 'evidence/original/pump_fees/deployed.so'
        original.parent.mkdir(parents=True)
        shutil.copyfile(repo / 'evidence/original/pump_fees/deployed.so', original)
        for name, child in suites:
            retained = root / (name + '.json')
            retained.write_text(json.dumps(selected[name]))
            adapter = (
                'import argparse,hashlib,json,pathlib\n'
                'p=argparse.ArgumentParser();p.add_argument("--candidate");p.add_argument("--output");a=p.parse_args()\n'
                f'raw=pathlib.Path({str(retained)!r}).read_bytes();d=json.loads(raw)\n'
                'assert hashlib.sha256(pathlib.Path(a.candidate).read_bytes()).hexdigest()==d["candidate_sha256"]\n'
                'pathlib.Path(a.output).write_bytes(raw)\n')
            (scripts / child).write_text(adapter)
        output = root / 'aggregate.json'
        previous = b'previous aggregate sentinel\n'
        output.write_bytes(previous)
        completed = subprocess.run([sys.executable, '-B', str(scripts / script.name),
                                    '--candidate', str(original), '--output', str(output)],
                                   text=True, capture_output=True, timeout=180)
        published = output.read_bytes()
        report = json.loads(published) if published != previous else None
        return {'mode': mode, 'revision': revision or 'working-tree',
                'consumer_sha256': hashlib.sha256(source.encode()).hexdigest(),
                'corpus_sha256': hashlib.sha256(raw).hexdigest(),
                'input_cases': sum(len(s['cases']) for s in selected.values()),
                'exit_code': completed.returncode, 'stdout': completed.stdout,
                'stderr': completed.stderr, 'prior_output_preserved': published == previous,
                'published_cases': report['case_count'] if report else None,
                'published_mismatches': report['mismatches'] if report else None,
                'mutation': mutation if mode == 'contradiction' else None,
                'published_contradiction': bool(report and mode == 'contradiction'
                    and report['suites']['administration']['cases'][0]['original']['error'] !=
                    report['suites']['administration']['cases'][0]['candidate']['error'])}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--corpus', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--revision')
    args = parser.parse_args()
    rows = [replay(args.repo.resolve(), args.corpus, mode, args.revision)
            for mode in ('control', 'contradiction')]
    args.output.write_text(json.dumps(rows, indent=2) + '\n')
    print(json.dumps(rows, indent=2))
