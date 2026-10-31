"""Exercise the actual receipt-verifier CLI with one genuine producer report.

The caller must first build a real candidate and run the unchanged producer.
This script creates only explicitly labelled negative copies of that report;
it never creates a positive report, compiler result or VM receipt.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8', newline='\n')


def recount(report):
    steps = [step for case in report['cases'] for step in case['steps']]
    signatures = [step['signature'] for step in steps]
    report['transaction_identity'] = {
        'transaction_count': len(steps),
        'unique_transaction_count': len(set(signatures)),
        'all_transactions_signature_verified': all(step['signature_verified'] for step in steps),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--expect', choices=('before', 'after'), required=True)
    args = parser.parse_args()
    repo, candidate, original_report = [path.resolve(strict=True) for path in (args.repo, args.candidate, args.report)]
    verifier = repo / 'reconstruction/verification/donation-relay-idl-lifecycle/verify_report.py'
    report = json.loads(original_report.read_text(encoding='utf-8'))
    assert [case['name'] for case in report['cases']] == ['stateful_lifecycle', 'admission_matrix']
    assert [len(case['steps']) for case in report['cases']] == [11, 16], 'a genuine complete 27-step producer control is required'
    assert report['transaction_identity']['transaction_count'] == 27
    assert report['transaction_identity']['unique_transaction_count'] == 27
    assert report['inputs']['candidate_elf']['sha256'] == sha(candidate)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)

    def invoke(path):
        command = [sys.executable, '-B', str(verifier), '--root', str(repo), '--candidate', str(candidate), '--report', str(path)]
        run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        result = {'command': command, 'returncode': run.returncode,
                  'stdout': run.stdout, 'stderr': run.stderr, 'report_sha256': sha(path)}
        try:
            result['verdict'] = json.loads(run.stdout)
        except json.JSONDecodeError:
            pass
        return result

    positive = invoke(original_report)
    if positive['returncode'] != 0 or positive.get('verdict', {}).get('problems') != []:
        canonical(output / 'positive-failure.json', positive)
        raise RuntimeError('the genuine complete producer control did not pass the actual verifier')
    negatives = {}

    for case_index, label in ((0, 'lifecycle'), (1, 'admission')):
        changed = copy.deepcopy(report)
        del changed['cases'][case_index]['steps'][-1]
        negatives['drop_' + label] = changed

        changed = copy.deepcopy(report)
        rows = changed['cases'][case_index]['steps']
        rows[0], rows[1] = rows[1], rows[0]
        negatives['reorder_' + label] = changed

        changed = copy.deepcopy(report)
        rows = changed['cases'][case_index]['steps']
        # Preserve every real transaction and unique signature; corrupt only
        # the logical step identity, making the named cohort ambiguous.
        rows[-1]['name'] = rows[0]['name']
        negatives['duplicate_label_' + label] = changed

    changed = copy.deepcopy(report)
    changed['cases'][0]['operation_order'].reverse()
    negatives['declared_order_contradiction'] = changed

    changed = copy.deepcopy(report)
    for case in changed['cases']:
        case['steps'] = case['steps'][:1]
    negatives['two_step_truncation'] = changed

    changed = copy.deepcopy(report)
    changed['cases'][0]['steps'].append(copy.deepcopy(changed['cases'][0]['steps'][0]))
    negatives['duplicate_real_signature_existing_guard'] = changed

    changed = copy.deepcopy(report)
    changed['cases'][1]['steps'] = []
    negatives['empty_case_existing_guard'] = changed

    results = {}
    errors = []
    for label, changed in negatives.items():
        recount(changed)
        path = output / (label + '.json')
        canonical(path, changed)
        result = invoke(path)
        results[label] = result
        already_rejected = label.endswith('_existing_guard')
        expected_status = 1 if args.expect == 'after' or already_rejected else 0
        if result['returncode'] != expected_status:
            errors.append(f'{label}: expected CLI {expected_status}, got {result["returncode"]}')
        if expected_status == 1 and not result.get('verdict', {}).get('problems'):
            errors.append(label + ': expected explicit verifier problem, not infrastructure failure')
    evidence = {
        'scope': 'Actual verifier CLI over a real freshly built candidate and genuine 27-step signed producer control; labelled negative copies only',
        'expectation': args.expect,
        'candidate_sha256': sha(candidate), 'positive_report_sha256': sha(original_report),
        'verifier_sha256': sha(verifier), 'positive': positive,
        'negative_copies': results, 'errors': errors,
        'vm_executions_in_this_probe': 0,
        'limits': 'The upstream producer supplies the real VM executions. This probe adds no transactions, program behavior coverage, binary identity or source reconstruction gain.',
    }
    canonical(output / 'evidence.json', evidence)
    print(json.dumps({'positive_returncode': positive['returncode'],
                      'negative_returncodes': {name: value['returncode'] for name, value in results.items()},
                      'errors': errors}, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
