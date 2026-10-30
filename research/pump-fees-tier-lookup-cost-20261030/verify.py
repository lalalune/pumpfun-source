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
sys.path.insert(0, str(HERE))
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
