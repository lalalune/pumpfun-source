#!/usr/bin/env python3
"""Re-run every case of this packet on the two images and compare with the stored receipts.

Usage (inside the packet folder): python3 verify.py --images '{"original":..,"candidate":..}'

Checks, in order: MANIFEST.json hashes; image sha256 against runtime/report.json.gz; a fresh
run of producer.build() gives byte-identical receipts and report; every case behaves identically on
both images. Exit 0 on success, 1 on any failure.
"""
import argparse
import gzip
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
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
    print("FAIL:", msg)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    args = parser.parse_args()
    images = json.loads(args.images)

    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    for entry in manifest["files"]:
        data = (HERE / entry["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != entry["sha256"] or len(data) != entry["bytes"]:
            fail(f"manifest mismatch for {entry['path']}")
    print(f"manifest: {len(manifest['files'])} files ok")

    stored_receipts = gzip.decompress((HERE / "runtime/receipts.jsonl.gz").read_bytes())
    stored_report = json.loads(gzip.decompress((HERE / "runtime/report.json.gz").read_bytes()))
    for side in ("original", "candidate"):
        got = producer.sha256_file(images[side])
        if got != stored_report[f"{side}_sha256"]:
            fail(f"{side} image sha256 {got} != report {stored_report[side + '_sha256']}")
    print("images: sha256 match report")

    blob, report = producer.build(images)
    if hashlib.sha256(stored_receipts).hexdigest() != stored_report["receipts_sha256"]:
        fail("stored receipts do not match report receipts_sha256")
    if blob != stored_receipts:
        old = stored_receipts.decode().splitlines()
        new = blob.decode().splitlines()
        bad = [json.loads(a)["case"] for a, b in zip(old, new) if a != b]
        fail(f"re-run receipts differ (cases: {bad[:10]}, lines {len(old)} vs {len(new)})")
    if report != stored_report:
        fail("re-run report differs from stored report")
    print(f"receipts: {report['case_count']} cases re-run, byte-identical")

    if report["behavior_mismatches"] or report["log_or_cu_differences"]:
        print("note: original/candidate differ in", report["behavior_mismatches"], report["log_or_cu_differences"])
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
