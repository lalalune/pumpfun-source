#!/usr/bin/env python3
"""Independently re-checks this packet using only its files and the two pump images.

  python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}'

1. The image sha256 values must equal the ones recorded in runtime/report.json.gz.
2. Every file in MANIFEST.json must match its sha256 and size, and every receipt part
   must match the sha256 recorded in the report.
3. The stored plan (runtime/plan.json.gz: instruction data and account metas per step)
   is replayed on both images in fresh LiteSVM instances. Every receipt field, including
   logs and compute units, must equal the stored receipt.
4. The summary is recomputed from the replayed receipts and must equal the stored report.
Exits 0 on success and 1 on any difference.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the packet free of __pycache__


def load_producer():
    spec = importlib.util.spec_from_file_location('packet_producer', HERE / 'producer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fail(message):
    print('FAIL: ' + message)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--images', required=True)
    images = json.loads(ap.parse_args().images)
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))

    for name in ('original', 'candidate'):
        sha = hashlib.sha256(Path(images[name]).read_bytes()).hexdigest()
        if sha != report['images'][name]:
            fail(f'{name} image sha256 {sha} != recorded {report["images"][name]}')

    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    for entry in manifest['files']:
        data = (HERE / entry['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry['sha256'] or len(data) != entry['bytes']:
            fail(f'manifest mismatch: {entry["path"]}')
    listed = {e['path'] for e in manifest['files']}
    present = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and p.name != 'MANIFEST.json'
               and '__pycache__' not in p.parts}
    if listed != present:
        fail(f'manifest file set differs: missing {sorted(present - listed)}, extra {sorted(listed - present)}')

    stored = []
    for part in report['parts']:
        data = (HERE / part['file']).read_bytes()
        if hashlib.sha256(data).hexdigest() != part['sha256']:
            fail(f'receipt part sha256 mismatch: {part["file"]}')
        rows = [json.loads(line) for line in gzip.decompress(data).decode().splitlines()]
        if len(rows) != part['count']:
            fail(f'receipt count mismatch in {part["file"]}')
        stored += rows

    producer = load_producer()
    plan_rows = json.loads(gzip.decompress((HERE / 'runtime/plan.json.gz').read_bytes()))
    plan = [(row['case'], row['steps']) for row in plan_rows]
    _, replayed = producer.produce(images, plan)
    if len(replayed) != len(stored):
        fail(f'receipt count {len(replayed)} != stored {len(stored)}')
    bad = 0
    for new, old in zip(replayed, stored):
        if new != old:
            keys = sorted(k for k in set(new) | set(old) if new.get(k) != old.get(k))
            print(f'receipt differs: {old["image"]} {old["case"]}/{old["variant"]}: {keys}')
            bad += 1
    if bad:
        fail(f'{bad} receipts differ on replay')

    summary = producer.summarize(report['images'], replayed, report['error_names'])
    for key, value in summary.items():
        if report.get(key) != value:
            fail(f'report field {key} differs from recomputed summary')
    if report['receipt_count'] != len(replayed):
        fail('receipt_count differs')

    print(json.dumps({'ok': True, 'cases': report['case_count'], 'steps': report['step_count'],
                      'receipts': len(replayed), 'behavior_mismatches': len(report['mismatched_steps']),
                      'compute_units_equal_steps': report['compute_units_equal_steps'],
                      'logs_equal_steps': report['logs_equal_steps']}))
    sys.exit(0)


if __name__ == '__main__':
    main()
