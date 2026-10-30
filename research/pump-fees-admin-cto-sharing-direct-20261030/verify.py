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
sys.path.insert(0, str(HERE))
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
    listed = {entry["path"] for entry in manifest["files"]}
    present = {str(p.relative_to(HERE)) for p in HERE.rglob("*") if p.is_file() and p.name != "MANIFEST.json"}
    if listed != present:
        fail(f"manifest file set differs: missing {sorted(present - listed)}, extra {sorted(listed - present)}")
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
    expected = {"behavior_mismatches": [s["case"] for s in summary if not s["behavior_match"]],
                "log_or_cu_differences": [s["case"] for s in summary if not (s["logs_identical"] and s["cu_equal"])]}
    for key, value in expected.items():
        if report[key] != value:
            fail(f"report {key} differs from recomputation")
    if failures:
        fail(f"{failures} replay(s) differ from receipts")
    print(f"OK: {len(stored)} cases, {report['transaction_count']} transactions per image replayed; "
          f"behavior mismatches {len(report['behavior_mismatches'])}, log/CU differences {len(report['log_or_cu_differences'])}")
    sys.exit(0)


if __name__ == "__main__":
    main()
