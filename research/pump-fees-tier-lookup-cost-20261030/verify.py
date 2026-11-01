#!/usr/bin/env python3
"""Independent re-check of this packet: replays every receipt on both images.

usage (from the packet folder): python3 verify.py --images '{"original": p, "candidate": p}'
--images also accepts a path to a file holding that JSON object.
Exit 0 = every image hash, step result, compute unit and the report match; 1 = any difference.
"""
import sys
sys.dont_write_bytecode = True
import argparse, gzip, hashlib, json, pathlib

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


sys.path.insert(0, str(HERE))
verify_manifest()
import producer  # noqa: E402


def fail(msg):
    print('FAIL: ' + msg)
    sys.exit(1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--images', required=True)
    a = p.parse_args()
    images = producer.load_images(a.images)
    rt = HERE / 'runtime'
    rec_bytes = (rt / 'receipts.jsonl.gz').read_bytes()
    rep_bytes = (rt / 'report.json.gz').read_bytes()
    receipts = [json.loads(l) for l in gzip.decompress(rec_bytes).splitlines()]
    report = json.loads(gzip.decompress(rep_bytes))

    for n in ['original', 'candidate']:
        got = hashlib.sha256(pathlib.Path(images[n]).read_bytes()).hexdigest()
        if got != report['image_sha256'][n]:
            fail(f'{n} image sha256 {got} != report {report["image_sha256"][n]}')

    cases = [r['case'] for r in receipts]
    if cases != json.loads(json.dumps(producer.cases())):
        fail('receipt case list differs from producer.cases()')

    # replay every step on both images and compare with the stored receipt
    bad = 0
    for r in receipts:
        for side in ['original', 'candidate']:
            got = producer.run_case(images[side], r['case'])
            for i, st in enumerate(r['steps']):
                if got[i] != st[side]:
                    bad += 1
                    print(f'mismatch {r["case"]["name"]} step {i} ({st["label"]}) on {side}')
    if bad:
        fail(f'{bad} replayed steps differ from the receipts')

    # rebuild the runtime files from the stored cases and compare bytes
    new_rec, new_rep = producer.encode(*producer.produce(images, cases))
    if new_rec != rec_bytes:
        fail('rebuilt receipts.jsonl.gz differs')
    if new_rep != rep_bytes:
        fail('rebuilt report.json.gz differs')
    print(json.dumps({'ok': True, 'cases': report['case_count'], 'steps': report['step_count'],
                      'behavior_mismatched_cases': report['behavior_mismatched_cases'],
                      'cu_mismatched_cases': report['cu_mismatched_cases']}))
    sys.exit(0)


if __name__ == '__main__':
    main()
