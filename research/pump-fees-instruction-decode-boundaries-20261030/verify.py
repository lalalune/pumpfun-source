#!/usr/bin/env python3
"""Independently re-check this packet using only its own files and the two images.

1. MANIFEST.json sha256/bytes for every listed file, and no unlisted file.
2. Image sha256 values equal the ones recorded in runtime/report.json.gz.
3. Replays every step of runtime/plan.json.gz on both images (fresh LiteSVM per step)
   and requires each receipt (behavior fields, logs and CU) to equal
   runtime/receipts.jsonl.gz byte for byte after canonical JSON encoding.
4. Recomputes the report from plan + replayed receipts and requires it to equal
   runtime/report.json.gz.
5. Requires each bisected length boundary to hold on both images: n-1 -> 102, n -> panic.
Exit 0 when everything holds, 1 otherwise.
"""
import argparse, gzip, hashlib, json, pathlib, sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import producer  # noqa: E402


def fail(msg):
    print('FAIL: ' + msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--images', required=True)
    a = ap.parse_args()
    images = json.loads(a.images)

    man = json.loads((HERE / 'MANIFEST.json').read_text())
    listed = set()
    for f in man['files']:
        b = (HERE / f['path']).read_bytes()
        if hashlib.sha256(b).hexdigest() != f['sha256'] or len(b) != f['bytes']:
            fail('manifest mismatch for ' + f['path'])
        listed.add(f['path'])
    present = {str(p.relative_to(HERE)) for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    if present - listed - {'MANIFEST.json'}:
        fail('unlisted files: %s' % sorted(present - listed - {'MANIFEST.json'}))

    rt = HERE / 'runtime'
    plan = json.loads(gzip.decompress((rt / 'plan.json.gz').read_bytes()))
    report = json.loads(gzip.decompress((rt / 'report.json.gz').read_bytes()))
    stored = [json.loads(l) for l in gzip.decompress((rt / 'receipts.jsonl.gz').read_bytes()).decode().splitlines()]

    shas = {k: producer.sha(images[k]) for k in ('original', 'candidate')}
    for k in shas:
        if shas[k] != report[k + '_sha256']:
            fail('%s image sha256 %s != report %s' % (k, shas[k], report[k + '_sha256']))

    replay = producer.run_plan(plan, images)
    if len(replay) != len(stored):
        fail('step count %d != %d' % (len(replay), len(stored)))
    bad = [(r['case'], r['label']) for r, s in zip(replay, stored) if producer.dumps(r) != producer.dumps(s)]
    if bad:
        fail('%d receipts differ, first %s' % (len(bad), bad[0]))

    if producer.report(plan, replay, shas) != report:
        fail('recomputed report differs')

    by = {(r['case'], r['label']): r for r in replay}
    for case, name, lo, hi in plan['length_boundaries']:
        for side in ('original', 'candidate'):
            below = by[(case, '%s-len-%d' % (name, lo))][side]
            at = by[(case, '%s-len-%d' % (name, hi))][side]
            if producer.code(below['error']) != '102' or not producer.panics(at):
                fail('length boundary %s %s %d/%d does not hold on %s' % (case, name, lo, hi, side))

    print(json.dumps({'ok': True, 'steps': len(replay), 'receipts': 2 * len(replay),
                      'behavior_mismatch': len(report['behavior_mismatch_steps']),
                      'log_or_cu_mismatch': len(report['log_or_cu_mismatch_steps'])}))
    sys.exit(0)


if __name__ == '__main__':
    main()
