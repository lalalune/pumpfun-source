#!/usr/bin/env python3
"""Independent re-check of this packet.

Run inside the packet folder:  python3 verify.py --images '{"original": P, "candidate": P}'

1. MANIFEST.json: every listed file exists with the recorded sha256 and size.
2. The two images hash to the sha256 values recorded in runtime/report.json.gz.
3. Every case in runtime/receipts.jsonl.gz is re-executed with producer.py's own
   case list and runner on the original, the rebuilt and the control image; the
   regenerated receipts and report must equal the stored ones byte for byte.
Exit 0 on success, 1 on any mismatch.
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
    print('FAIL:', msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--images', required=True)
    images = json.loads(ap.parse_args().images)

    man = json.loads((HERE / 'MANIFEST.json').read_text())
    for f in man['files']:
        b = (HERE / f['path']).read_bytes()
        if hashlib.sha256(b).hexdigest() != f['sha256'] or len(b) != f['bytes']:
            fail('manifest mismatch: ' + f['path'])
    print('manifest ok: %d files' % len(man['files']))

    stored_receipts = gzip.decompress((HERE / 'runtime/receipts.jsonl.gz').read_bytes())
    stored_report = json.loads(gzip.decompress((HERE / 'runtime/report.json.gz').read_bytes()))
    for k, p in images.items():
        got = hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
        if got != stored_report['image_sha256'][k]:
            fail('%s image sha256 %s != recorded %s' % (k, got, stored_report['image_sha256'][k]))
    print('image sha256 ok')

    receipts, rows, control, sites = producer.produce(images)
    body = ''.join(producer.dumps(r) + '\n' for r in receipts).encode()
    if body != stored_receipts:
        old = stored_receipts.splitlines(); new = body.splitlines()
        bad = [json.loads(o)['case']['name'] for o, n in zip(old, new) if o != n]
        fail('receipts differ (%d vs %d lines; differing cases: %s)' % (len(old), len(new), bad[:10]))
    rep = producer.summarize(images, receipts, rows, control, sites)
    rep['receipts_sha256'] = producer.sha(body)
    if json.loads(json.dumps(rep)) != stored_report:
        fail('report differs')
    print('re-executed %d cases / %d steps: receipts and report identical' % (rep['case_count'], rep['step_count']))
    print('same_behavior %d/%d, cu_equal %d, path-normalized logs %d, control==candidate %d' % (
        rep['same_behavior'], rep['step_count'], rep['cu_equal'], rep['same_logs_path_normalized'],
        rep['control']['steps_equal_to_candidate']))
    sys.exit(0)


if __name__ == '__main__':
    main()
