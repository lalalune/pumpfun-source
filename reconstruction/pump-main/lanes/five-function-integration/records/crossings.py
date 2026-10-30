"""Additional actual post-complete crossings; the earlier boundary report stays intact."""
from pathlib import Path
import argparse, gzip, hashlib, json
import focused as shared


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', type=Path, required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(); assert not a.output.exists()
    images = dict(original=shared.ROOT/'evidence/original/pump/deployed.so',
                  control=a.control.resolve(), candidate=a.candidate.resolve())
    hashes = {name: shared.sha(path.read_bytes()) for name, path in images.items()}
    dependencies = shared.dependency_map(); inputs = shared.input_bindings(); rows = []
    report = dict(scope=__doc__, producer_sha256=shared.sha(Path(__file__).read_bytes()),
                  images_sha256=hashes, inputs_sha256=inputs, dependency_captures=dependencies,
                  excluded_log_pattern=shared.CU.pattern, cases=rows)
    for operation in ['buy_v3', 'buy_exact_quote_in_v3']:
        for mode in ['native', 'token', 'token2022']:
            case = dict(operation=operation, reserve_in=10**9, reserve_out=30000000000,
                        real_base=500000000, base_vault_amount=10**12, user_lamports=10**16,
                        amount=500000001 if operation == 'buy_v3' else 60000000000,
                        max_cost=10**12 if operation == 'buy_v3' else 1)
            if mode != 'native': case.update(token_quote=True, quote2022=mode == 'token2022', replace=13)
            row = dict(group='v3', driver='v3', name=operation+'_'+mode+'_post_complete_crossing', case=case,
                       fixture_origin='Existing v3 public run API with enough real post-complete quote reserves')
            runs = {}
            for role, image in images.items():
                runs[role] = shared.run(row, image)
                shared.check_loads(runs[role], hashes[role], dependencies, hashes['original'])
            rows.append(dict(case=row, runs=runs,
                             control_differences=shared.differences(runs['original'], runs['control']),
                             candidate_differences=shared.differences(runs['original'], runs['candidate'])))
            report.update(target_case_count=len(rows), target_execution_count=len(rows)*3,
                          bootstrap_execution_count=0,
                          signature_fields=sum(send['signature_verification']['signature_count']
                                               for item in rows for value in item['runs'].values() for send in value['sends']))
            a.output.write_bytes(gzip.compress(json.dumps(report, separators=(',', ':')).encode(), mtime=0))
            print(json.dumps(dict(case=row['name'], errors={role: value['target']['error'] for role, value in runs.items()},
                                  events={role: len(value['target']['events']) for role, value in runs.items()},
                                  candidate_differences=rows[-1]['candidate_differences'])), flush=True)
    assert inputs == shared.input_bindings()
    assert all(row['runs']['original']['target']['error'] is None for row in rows), 'Original crossing did not succeed; raw report retained'
    assert all(not row['candidate_differences'] for row in rows), 'Original/candidate mismatch; raw report retained'


if __name__ == '__main__': main()
