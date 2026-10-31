"""Run the unchanged quote-control producer, then admit its actual receipt twice.

This exercises the production receipt consumer, not the complete build-bound
44-suite CLI. No reconstructed program is compiled and no cases are added.
"""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(repo / 'scripts'))
    import pump_validate_parallel as consumer
    from pump_amm_reusable_harness import pin_program

    original = repo / 'evidence/original/pump/deployed.so'
    wrong = repo / 'evidence/original/pump_fees/deployed.so'
    producer = repo / 'scripts/pump_quote_control_fresh_differential.py'
    input_before = {str(path.relative_to(repo)): digest(path)
                    for path in (original, wrong, producer,
                                 repo / 'scripts/pump_validate_all.py')}
    with tempfile.TemporaryDirectory(prefix='quote-control-repin-') as temporary:
        copied = Path(temporary) / 'same-image.so'
        shutil.copyfile(original, copied)
        first, second = pin_program(original), pin_program(copied)
        assert first != second and first.read_bytes() == second.read_bytes()
        receipt_path = args.output / 'receipt.json.gz'
        command = [sys.executable, '-B', str(producer), '--candidate', str(first),
                   '--output', str(receipt_path)]
        run = subprocess.run(command, cwd=repo, capture_output=True, text=True,
                             check=True, timeout=180)
        (args.output / 'producer.log').write_text(run.stdout + run.stderr, encoding='utf-8')
        receipt_bytes = receipt_path.read_bytes()
        receipt = json.loads(gzip.decompress(receipt_bytes))

        def admit(document, candidate=first, oracle=original, suite='quote_control'):
            try:
                count = consumer.validate_result(suite, document, candidate, oracle)
                return {'accepted': True, 'count': count}
            except (AssertionError, KeyError, TypeError, ValueError) as error:
                return {'accepted': False, 'error_type': type(error).__name__,
                        'error': str(error)}

        controls = {
            'different_candidate': admit(receipt, wrong),
            'different_original': admit(receipt, first, wrong),
            'different_suite': admit(receipt, suite='administration'),
        }
        for label, mutate in (
            ('wrong_candidate_hash', lambda r: r.update(candidate_sha256='0' * 64)),
            ('wrong_original_hash', lambda r: r.update(original_sha256='0' * 64)),
            ('missing_case', lambda r: r['results'].pop()),
            ('duplicate_case', lambda r: r['results'][1].update(case=r['results'][0]['case'])),
            ('changed_outcome', lambda r: r['results'][0]['candidate'].update(error='changed retained error')),
            ('missing_comparison_field', lambda r: r['results'][0]['candidate'].pop('before_accounts')),
            ('changed_comparison_keys', lambda r: r['compare_keys'].pop()),
            ('signature_bool_as_integer', lambda r: r['results'][0]['candidate']['signature_verification'].__setitem__(0, 1)),
            ('enabled_bool_as_integer', lambda r: r['results'][0]['candidate'].update(sigverify_enabled=1)),
            ('lamports_integer_as_float', lambda r: next(v for v in r['results'][0]['candidate']['before_accounts'].values() if v is not None).update(
                lamports=float(next(v for v in r['results'][0]['candidate']['before_accounts'].values() if v is not None)['lamports']))),
        ):
            changed = copy.deepcopy(receipt)
            mutate(changed)
            controls[label] = admit(changed)
        legacy = copy.deepcopy(receipt)
        legacy.pop('candidate_sha256', None)
        legacy.pop('original_sha256', None)
        summary = {
            'base': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=repo, text=True).strip(),
            'producer_returncode': run.returncode,
            'case_count': receipt['cases'],
            'mismatches': receipt['mismatches'],
            'original_sha256': digest(original),
            'first_pin': str(first), 'second_pin': str(second),
            'first_admission': admit(receipt),
            'same_byte_second_pin_admission': admit(receipt, second),
            'negative_controls': controls,
            'legacy_first_admission': admit(legacy),
            'legacy_second_admission': admit(legacy, second),
            'source_sha256': input_before,
            'inputs_unchanged': all(digest(repo / path) == value for path, value in input_before.items()),
            'receipt_sha256': hashlib.sha256(receipt_bytes).hexdigest(),
            'receipt_unchanged_by_admission': receipt_path.read_bytes() == receipt_bytes,
            'case_records_sha256': hashlib.sha256(json.dumps(receipt['results'], sort_keys=True,
                                                              separators=(',', ':')).encode()).hexdigest(),
            'scope': __doc__,
        }
    (args.output / 'results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
