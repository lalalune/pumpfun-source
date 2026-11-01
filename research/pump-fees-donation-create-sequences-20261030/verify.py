#!/usr/bin/env python3
"""Independently re-run every receipt in this packet and compare.

Run from the packet folder:  python3 verify.py --images '{"original": "...", "candidate": "..."}'
(--images may also be a path to a JSON file.) Uses only the files in this
folder and the two images. Exit 0 = every check passed, 1 = any failure.
"""
import sys

sys.dont_write_bytecode = True

import argparse
import gzip
import hashlib
import json
import pathlib

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


def fail(message):
    print("FAIL:", message)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    args = parser.parse_args()
    raw = args.images
    images = json.loads(pathlib.Path(raw).read_text() if pathlib.Path(raw).is_file() else raw)

    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    for entry in manifest["files"]:
        data = (HERE / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"] or len(data) != entry["bytes"]:
            fail(f"manifest mismatch for {entry['path']}")

    blob = gzip.decompress((HERE / "runtime/receipts.jsonl.gz").read_bytes())
    report = json.loads(gzip.decompress((HERE / "runtime/report.json.gz").read_bytes()))
    if hashlib.sha256(blob).hexdigest() != report["receipts_sha256"]:
        fail("receipts sha256 differs from report")
    for side in ["original", "candidate"]:
        digest = producer.sha256_file(images[side])
        if digest != report[f"{side}_sha256"]:
            fail(f"{side} image sha256 {digest} != recorded {report[side + '_sha256']}")

    stored = [json.loads(line) for line in blob.decode().splitlines()]
    cases = producer.cases()
    if [c["name"] for c in cases] != [r["case"] for r in stored]:
        fail("case list differs from receipts")
    failures = 0
    for case, receipt in zip(cases, stored):
        for side in ["original", "candidate"]:
            replay = json.loads(json.dumps(producer.run_case(images[side], case), sort_keys=True))
            if replay != receipt[side]:
                failures += 1
                for a, b in zip(replay, receipt[side]):
                    if a != b:
                        diff = sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))
                        print(f"  {case['name']} step {a.get('i')} {side}: fields {diff} differ from receipt")
                        break
                else:
                    print(f"  {case['name']} {side}: step count differs from receipt")

    receipts, summary = producer.produce(images)
    if summary != report["cases"]:
        fail("recomputed per-case summary differs from report")
    if failures:
        fail(f"{failures} replay(s) differ from receipts")
    print(f"OK: {len(stored)} cases, {report['transaction_count']} transactions per image replayed; "
          f"behavior mismatches {len(report['behavior_mismatches'])}, log/CU differences {len(report['log_or_cu_differences'])}")
    sys.exit(0)


if __name__ == "__main__":
    main()
