#!/usr/bin/env python3
"""Re-run every case of this packet against the two images and compare with runtime/.

Usage (inside the packet folder): python3 verify.py --images '{"original": P, "candidate": P}'
Exit 0 when the image hashes match runtime/report.json.gz and the re-run receipts and
report are byte-identical to the packet's; exit 1 otherwise.
"""
import argparse, gzip, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the packet folder unchanged
sys.path.insert(0, str(HERE))
import producer  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True)
    a = ap.parse_args()
    images = json.loads(a.images)
    report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    receipts = gzip.decompress((HERE / 'runtime/receipts.jsonl.gz').read_bytes())
    ok = True
    for tag in ('original', 'candidate'):
        got = producer.sha_file(images[tag])
        if got != report['image_sha256'][tag]:
            print(f'FAIL image sha256 {tag}: {got} != {report["image_sha256"][tag]}'); ok = False
    if hashlib.sha256(receipts).hexdigest() != report['receipts_sha256']:
        print('FAIL receipts.jsonl.gz does not match receipts_sha256 in report'); ok = False
    if not ok:
        return 1
    rows = producer.produce(images)
    body = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    old = [json.loads(l) for l in receipts.decode().splitlines()]
    if len(old) != len(rows):
        print(f'FAIL case count {len(rows)} != {len(old)}'); ok = False
    for x, y in zip(old, rows):
        if x != y:
            fields = sorted(k for k in set(x) | set(y) if x.get(k) != y.get(k))
            print(f'FAIL case {x["case"]}: fields differ {fields}'); ok = False
    if body != receipts:
        print('FAIL re-run receipts bytes differ'); ok = False
    else:
        cmp = producer.image_compare(images)
        if cmp != report['image_compare']:
            print('FAIL image_compare differs'); ok = False
    if ok:
        print(json.dumps({'verified_cases': len(rows), 'behavior_match': report['behavior_match'],
                          'cu_delta_histogram': report['cu_delta_histogram']}))
        print('PASS')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
