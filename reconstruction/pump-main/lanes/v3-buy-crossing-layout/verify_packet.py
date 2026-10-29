#!/usr/bin/env python3
"""Check retained scores and signed replay receipts; does not compile or run a VM."""
import argparse
import base64
import gzip
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(name):
    data = (HERE / name).read_bytes()
    return json.loads(gzip.decompress(data) if name.endswith('.gz') else data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--signatures', action='store_true', help='Requires solders==0.27.1')
    args = parser.parse_args()
    for name, digest in read('manifest.json').items():
        require(hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name)
    summary = read('SUMMARY.json')
    scores = {k: read(k + '-score.json.gz')['windows'] for k in ('control', 'candidate', 'experimental')}
    require(all(len(v) == 1035 for v in scores.values()), 'window count')
    require(all(set(v) == set(scores['control']) for v in scores.values()), 'window inventory')
    for cohort, windows in scores.items():
        for field in ('normalized', 'raw'):
            actual = sum(v[field] for v in windows.values())
            require(actual == summary['scores'][cohort][field], cohort + ' count')
            gains = {k for k, v in windows.items() if v[field] and not scores['control'][k][field]}
            losses = {k for k, v in windows.items() if not v[field] and scores['control'][k][field]}
            expected_gains = {str(int(v, 16)) for v in summary['scores'][cohort][field + '_gains']}
            expected_losses = {str(int(v, 16)) for v in summary['scores'][cohort][field + '_losses']}
            require(gains == expected_gains and losses == expected_losses, cohort + ' memberships')
            if cohort == 'candidate':
                require(not gains and not losses, 'applied source must preserve every membership')
    require(scores['experimental'][str(0x147ba0)]['normalized'], 'experimental target')
    require(not scores['experimental'][str(0xa868)]['raw'], 'experimental raw restriction')
    for cohort in ('candidate', 'experimental'):
        audit = read(cohort + '-audit.json')
        require(audit['callee_order_preserved'] and audit['callee_multiset_preserved'], 'call targets changed')
        require(len(audit['calls']['candidate']) == 29, 'call count')
    audit = read('candidate-audit.json')
    require(all(audit['sections_equal'].values()), 'applied data sections changed')
    require(len(audit['changed_symbols']) == 1 and not audit['added_symbols'], 'applied function scope')
    runtime = read('runtime.json.gz')
    require(len(runtime['rows']) == 153, 'runtime case count')
    require(sum(r['case'].get('case_group') == 'crossing' for r in runtime['rows']) == 36, 'crossing count')
    require(hashlib.sha256(gzip.decompress((HERE / 'fixture.json.gz').read_bytes())).hexdigest() == runtime['fixture_sha256'], 'fixture hash')
    for cohort in ('control', 'candidate', 'experimental'):
        require(runtime['images'][cohort] == summary['images'][cohort]['candidate_sha256'], 'runtime image binding')
    if args.signatures:
        from solders.transaction import Transaction
    fields = ('error', 'accounts', 'inner_instructions', 'event_payloads', 'return_data')
    meter = re.compile(r'Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units')
    count = 0
    for row in runtime['rows']:
        receipts = row['receipts']
        require(set(receipts) == {'original', 'control', 'candidate', 'experimental'}, 'receipt cohorts')
        original = receipts['original']
        logs = lambda r: [line for line in r['logs'] if not meter.fullmatch(line)]
        for receipt in receipts.values():
            require(all(receipt[f] == original[f] for f in fields), 'execution difference')
            require(logs(receipt) == logs(original), 'ordered log difference')
            if args.signatures:
                results = Transaction.from_bytes(base64.b64decode(receipt['transaction_base64'])).verify_with_results()
                require(bool(results) and all(results), 'transaction signature')
            count += 1
    require(count == 612, 'execution count')
    print(json.dumps({'files': 'verified', 'applied_memberships': '1024 normalized / 277 raw, no losses',
                      'experimental': '1025 normalized / 276 raw; NOT applied',
                      'cases': 153, 'receipts': count, 'signatures_checked': args.signatures}))


if __name__ == '__main__':
    main()
