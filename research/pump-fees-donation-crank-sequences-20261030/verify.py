#!/usr/bin/env python3
"""Re-run every recorded crank sequence and compare with the packet receipts.

Usage: python3 verify.py --images '{"original": "<deployed.so>", "candidate": "<candidate.so>"}' [--root <repo>]
The dependency ELFs (donation_relay, spl_token, associated_token) are read from
<repo>/evidence/dependencies; without --root the repo is taken to be the one
holding <repo>/evidence/original/pump_fees/deployed.so.
Exit 0 = every receipt reproduced byte for byte; 1 = anything differs.
"""
import sys
sys.dont_write_bytecode = True
import argparse, gzip, json, pathlib
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import producer

def main():
    a = argparse.ArgumentParser(); a.add_argument('--images', required=True); a.add_argument('--root'); a = a.parse_args()
    images = json.loads(a.images)
    root = pathlib.Path(a.root) if a.root else pathlib.Path(images['original']).resolve().parents[3]
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    receipts = [json.loads(l) for l in gzip.decompress((HERE / 'runtime/receipts.jsonl.gz').read_bytes()).decode().splitlines()]
    fails = []
    for side, path in images.items():
        if producer.sha(path) != report['images'][side]: fails.append('image sha256 mismatch: ' + side)
    for name in producer.DEPS:
        p = root / 'evidence/dependencies' / name / 'deployed.so'
        if not p.exists() or producer.sha(p) != report['dependencies'][name]: fails.append('dependency sha256 mismatch: ' + name)
    if fails:
        print('\n'.join(fails)); sys.exit(1)
    if [c['name'] for c in producer.cases()] != [r['name'] for r in receipts]: print('case list differs from receipts'); sys.exit(1)
    rows, rebuilt = producer.build(root, images)
    for old, new in zip(receipts, rows):
        if json.loads(json.dumps(new, sort_keys=True)) != old: fails.append('receipt differs: ' + old['name'])
    if json.loads(json.dumps(rebuilt, sort_keys=True)) != report: fails.append('report differs')
    print('cases', len(rows), 'cranks', rebuilt['cranks'], 'original==candidate', rebuilt['matching_cases'], 'receipt mismatches', len(fails))
    for f in fails: print(f)
    sys.exit(1 if fails else 0)

if __name__ == '__main__':
    main()
