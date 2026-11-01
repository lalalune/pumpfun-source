#!/usr/bin/env python3
"""Re-run every case of this packet against the two images and compare with runtime/.

Usage (inside the packet folder): python3 verify.py --images '{"original": P, "candidate": P}'
Exit 0 when the image hashes match runtime/report.json.gz and the re-run receipts and
report are byte-identical to the packet's; exit 1 otherwise.
"""
import argparse, gzip, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def verify_manifest():
    """The packet pins every file it ships; check them before the producer runs."""
    manifest = json.loads((HERE / 'MANIFEST.json').read_text())
    # The loop below checks the files the manifest names; a file the packet ships
    # with no entry passes every check it makes. Compare the two sets first.
    manifest_paths = {entry['path'] for entry in manifest['files']}
    if len(manifest_paths) != len(manifest['files']):
        raise SystemExit('duplicate packet manifest path')
    entries = list(HERE.rglob('*'))
    # Python -B still reads cached bytecode; it must not bypass source admission.
    if any(p.is_symlink() or p.suffix in ('.pyc', '.pyo') for p in entries):
        raise SystemExit('packet contains a symlink or cached Python bytecode')
    packet_paths = {p.relative_to(HERE).as_posix() for p in entries
                    if p.is_file() and p != HERE / 'MANIFEST.json'
                    and p.name != '.DS_Store' and '.git' not in p.relative_to(HERE).parts}
    if manifest_paths != packet_paths:
        raise SystemExit('packet file set differs from MANIFEST.json: '
                         f'missing={sorted(packet_paths - manifest_paths)} '
                         f'extra={sorted(manifest_paths - packet_paths)}')

    for entry in manifest['files']:
        path = HERE / entry['path']
        data = path.read_bytes() if path.is_file() else None
        if (data is None or len(data) != entry['bytes']
                or hashlib.sha256(data).hexdigest() != entry['sha256']):
            raise SystemExit(f'packet member differs from MANIFEST.json: {entry["path"]}')


sys.dont_write_bytecode = True  # keep the packet folder unchanged
sys.path.insert(0, str(HERE))
verify_manifest()
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
