#!/usr/bin/env python3
"""Independent re-verification for pump-global-admin-sequences-20261030.

Uses only the packet files and the two Pump program images:
- MANIFEST.json lists every packet file except itself with matching sha256/bytes.
  No manifest path is listed twice and no packet member is a symlink or
  cached bytecode.
- runtime/report.json.gz part entries match the receipt part files (sha256, bytes, count).
- Both images hash to the values recorded in the report.
- Every stored receipt transaction parses and all signatures verify.
- Every failed step leaves the Global account byte-identical (rollback).
- All 29 cases are re-executed on both images; every re-executed receipt
  (transaction bytes, error, Global before/after, events, inner instructions,
  logs, compute units) must equal the stored receipt.
- The report summary is recomputed from the receipts and must equal the stored one.
- Compute-unit deltas and log differences are recomputed directly from the
  receipts and must match the report.

Usage (from this packet directory):
  python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'
Exit status 0 = pass, 1 = fail.
"""
import argparse
import base64
import gzip
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def fail(message):
    print(f'FAIL: {message}')
    sys.exit(1)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True)
    images = json.loads(ap.parse_args().images)

    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    paths = [e['path'] for e in manifest['files']]
    if len(set(paths)) != len(paths):
        fail('duplicate packet manifest path')
    entries = list(HERE.rglob('*'))
    # Python -B still reads cached bytecode; it must not bypass source admission.
    if any(p.is_symlink() or p.suffix in ('.pyc', '.pyo') for p in entries):
        fail('packet contains a symlink or cached Python bytecode')
    listed = set(paths)
    present = {p.relative_to(HERE).as_posix() for p in entries
               if p.is_file() and p != HERE / 'MANIFEST.json'}
    if listed != present:
        fail(f'manifest set differs: missing {sorted(present - listed)} extra {sorted(listed - present)}')
    for e in manifest['files']:
        data = (HERE / e['path']).read_bytes()
        if sha(data) != e['sha256'] or len(data) != e['bytes']:
            fail(f'manifest mismatch {e["path"]}')

    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    for name in ('original', 'candidate'):
        if sha(Path(images[name]).read_bytes()) != report['images'][name]:
            fail(f'image sha256 mismatch for {name}')

    stored = []
    for part in report['parts']:
        data = (HERE / part['file']).read_bytes()
        if sha(data) != part['sha256'] or len(data) != part['bytes']:
            fail(f'part mismatch {part["file"]}')
        rows = [json.loads(l) for l in gzip.decompress(data).decode().splitlines() if l]
        if len(rows) != part['count']:
            fail(f'part count {part["file"]}')
        stored.extend(rows)
    if len(stored) != report['receipt_count']:
        fail('receipt count')

    from solders.transaction import Transaction
    for r in stored:
        tag = f"{r['image']}/{r['case']}/{r['step']}"
        tx = Transaction.from_bytes(base64.b64decode(r['transaction_base64']))
        # all() is true for an empty result list, so a receipt whose
        # signature vector was stripped would pass the bare all().
        results = tx.verify_with_results()
        if not results or not all(results):
            fail(f'{tag}: signature verification')
        if r['error'] is not None and r['global_before_hex'] != r['global_after_hex']:
            fail(f'{tag}: failed step changed Global')

    # Direct recomputation of the compute-unit and log comparison.
    pairs = {}
    for r in stored:
        pairs.setdefault((r['case'], r['step']), {})[r['image']] = r
    cu_equal = sum(1 for p in pairs.values() if p['original']['compute_units'] == p['candidate']['compute_units'])
    logs_equal = sum(1 for p in pairs.values() if p['original']['logs'] == p['candidate']['logs'])
    if cu_equal != report['compute_units_equal_steps'] or logs_equal != report['logs_equal_steps']:
        fail('compute-unit / log equality counts')
    for (case, step), p in pairs.items():
        o, c = p['original'], p['candidate']
        if o['logs'] == c['logs']:
            continue
        extra = sum(len(a) - len(b) for a, b in zip(o['logs'], c['logs'])
                    if a != b and a.startswith('Program log: AnchorError thrown in '))
        if len(o['logs']) != len(c['logs']) or extra != 14 * sum(
                1 for a, b in zip(o['logs'], c['logs']) if a != b and a.startswith('Program log: AnchorError')):
            fail(f'{case}/{step}: unexpected log difference shape')

    sys.dont_write_bytecode = True
    sys.path.insert(0, str(HERE))
    import producer
    shas, fresh = producer.produce(images, report['error_names'])
    if shas != report['images']:
        fail('producer image hashes')
    if len(fresh) != len(stored):
        fail('re-executed receipt count')
    for a, b in zip(fresh, stored):
        if a != b:
            keys = [k for k in a if a.get(k) != b.get(k)]
            fail(f"{b['image']}/{b['case']}/{b['step']}: re-execution differs in {keys}")
    summary = producer.summarize(shas, fresh, report['error_names'])
    for key, value in summary.items():
        if report[key] != value:
            fail(f'report field {key} differs from recomputation')
    print(f"PASS: {report['case_count']} cases, {report['step_count']} steps, {len(stored)} receipts re-executed "
          f"on both images; behavior mismatches {report['mismatches']}; compute units equal on "
          f"{cu_equal}/{report['step_count']} steps; logs equal on {logs_equal}/{report['step_count']} steps")


if __name__ == '__main__':
    main()
