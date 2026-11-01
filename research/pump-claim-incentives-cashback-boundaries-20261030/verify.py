#!/usr/bin/env python3
"""Independent re-check of this packet using only its own files and the two images.

  python3 verify.py --images '{"original": ".../deployed.so", "candidate": ".../candidate.so"}'

1. image sha256 must equal runtime/report.json.gz `images`;
2. receipt-file sha256 must equal the report;
3. every case in runtime/plan.json.gz is replayed on both images, and each new
   receipt must equal the recorded one byte for byte (error, logs, compute units,
   events, inner instructions, account after-state, tx);
4. the summary recomputed from the new receipts must equal the report.
Exit 0 on success, 1 on any difference. The execution code is imported from
producer.py in this folder (no repository files are read).
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True  # keep the packet folder free of __pycache__
CASES = 60  # cases this packet's plan publishes; README and runtime/report.json.gz name the same number


def load_producer():
    spec = importlib.util.spec_from_file_location('packet_producer', HERE / 'producer.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_manifest():
    """The packet pins every file it ships; read the digests before trusting any.

    Nothing used to read MANIFEST.json. producer.py was imported and executed,
    and the runtime files were replayed, without either matching the record the
    packet publishes beside them, so a packet whose producer or runtime file had
    drifted still replayed itself and still passed.
    """
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


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--images', required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    verify_manifest()
    p = load_producer()
    runtime = HERE / 'runtime'
    report = json.loads(gzip.decompress((runtime / 'report.json.gz').read_bytes()))
    cases = json.loads(gzip.decompress((runtime / 'plan.json.gz').read_bytes()))
    if len(cases) != CASES:
        print(f'FAIL: plan holds {len(cases)} cases, not {CASES}')
        return 1
    failures = []
    for name in ('original', 'candidate'):
        sha = hashlib.sha256(Path(images[name]).read_bytes()).hexdigest()
        if sha != report['images'][name]:
            failures.append(f'image {name}: sha256 {sha} != report {report["images"][name]}')
    if failures:
        print('\n'.join(failures))
        return 1
    replayed = 0
    for loader in p.LOADERS:
        fname = f'receipts-{loader}.jsonl.gz'
        blob = (runtime / fname).read_bytes()
        if hashlib.sha256(blob).hexdigest() != report['receipts'][fname]['sha256']:
            failures.append(f'{fname}: sha256 differs from report')
        recorded = [json.loads(line) for line in gzip.decompress(blob).decode().splitlines() if line]
        if len(recorded) != 2 * len(cases):
            failures.append(f'{fname}: {len(recorded)} receipts for {len(cases)} cases')
            break
        new = {name: p.run_plan(images[name], loader, cases) for name in ('original', 'candidate')}
        for i, c in enumerate(cases):
            for j, name in enumerate(('original', 'candidate')):
                fresh = json.loads(json.dumps({'loader': loader, 'image': name, **new[name][i]}, sort_keys=True))
                if fresh != recorded[2 * i + j]:
                    diff = [k for k in fresh if fresh[k] != recorded[2 * i + j].get(k)]
                    failures.append(f'{loader}/{name}/{c["case"]}: receipt differs in {diff}')
                replayed += 1
        summary = json.loads(json.dumps(p.summarize(cases, new['original'], new['candidate']), sort_keys=True))
        if summary != report['loaders'][loader]:
            failures.append(f'{loader}: recomputed summary differs from report')
    if failures:
        print('\n'.join(failures[:50]))
        print(f'FAIL: {len(failures)} difference(s)')
        return 1
    s = report['loaders']['upgradeable']
    print(json.dumps({'ok': True, 'cases': len(cases), 'receipts_replayed': replayed,
                      'behavior_mismatches': s['behavior_mismatches'],
                      'compute_units_equal_cases': s['compute_units_equal_cases'],
                      'logs_equal_cases': s['logs_equal_cases']}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
