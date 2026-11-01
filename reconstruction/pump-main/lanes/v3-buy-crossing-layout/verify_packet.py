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


def manifest_pairs(pairs):
    """A repeated path is ambiguous even when its final digest is correct."""
    rows = {}
    for name, digest in pairs:
        require(name not in rows, 'duplicate packet manifest path: ' + name)
        rows[name] = digest
    return rows


SECTIONS = ('.rodata', '.data.rel.ro')


def check_sections(audit):
    """Require both applied data sections to be compared, and to be equal.

    all() over the mapping is true when the mapping is empty or when a section
    key is missing, so the expected key set is pinned before the comparison.
    """
    sections = audit.get('sections_equal')
    require(isinstance(sections, dict) and set(sections) == set(SECTIONS),
            'applied data section set changed')
    require(all(value is True for value in sections.values()), 'applied data sections changed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--signatures', action='store_true', help='Requires solders==0.27.1')
    args = parser.parse_args()
    # Hashing only the listed names leaves every other file in the folder
    # unread: a packet that gained a file the manifest never lists still
    # verified, and that file is exactly what a reader would not check.
    entries = list(HERE.rglob('*'))
    require(not any(p.is_symlink() or p.suffix in ('.pyc', '.pyo') for p in entries),
            'packet holds a symlink or cached bytecode')
    rows = json.loads((HERE / 'manifest.json').read_bytes(), object_pairs_hook=manifest_pairs)
    require(isinstance(rows, dict), 'packet manifest must be a path mapping')
    shipped = {p.relative_to(HERE).as_posix() for p in entries
               if p.is_file() and p != HERE / 'manifest.json'}
    require(set(rows) == shipped, 'packet file set differs from manifest.json')
    for name, digest in rows.items():
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
    check_sections(audit)
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
