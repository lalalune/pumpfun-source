#!/usr/bin/env python3
"""Fail-closed replay verifier for a generated Mayhem boundary report."""

import argparse
import gzip
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import producer  # noqa: E402


def fail(message):
    print("FAIL: " + message)
    raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--images", required=True)
    parser.add_argument("--runtime", type=pathlib.Path, default=HERE / "runtime")
    args = parser.parse_args()
    images = {name: pathlib.Path(path) for name, path in json.loads(args.images).items()}
    runtime = args.runtime.resolve()

    plan = json.loads(gzip.decompress((runtime / "plan.json.gz").read_bytes()))
    report = json.loads(gzip.decompress((runtime / "report.json.gz").read_bytes()))
    stored = [json.loads(line) for line in gzip.decompress((runtime / "receipts.jsonl.gz").read_bytes()).splitlines()]

    if producer.canonical(plan) != producer.canonical(producer.make_plan()):
        fail("stored plan differs from producer.make_plan()")

    for side in ("original", "candidate"):
        actual = producer.sha256(images[side])
        expected = report["provenance"][side + "_sha256"]
        if actual != expected:
            fail(f"{side} image sha256 {actual} != {expected}")

    replay = producer.run(plan, images)
    if len(replay) != len(stored):
        fail(f"receipt count {len(replay)} != {len(stored)}")
    differing = [(a["case"], a["label"]) for a, b in zip(replay, stored)
                 if producer.canonical(a) != producer.canonical(b)]
    if differing:
        fail(f"{len(differing)} receipts differ; first={differing[0]}")

    recomputed = producer.build_report(plan, replay, report["provenance"])
    if recomputed != report:
        fail("recomputed report differs")
    if not all(report["negative_controls"].values()):
        fail("a comparator negative control did not detect its mutation")

    print(json.dumps({
        "ok": True,
        "steps": len(replay),
        "executions": len(replay) * 2,
        "behavior_mismatches": len(report["behavior_mismatch_steps"]),
        "log_mismatches": len(report["log_mismatch_steps"]),
        "compute_unit_mismatches": len(report["compute_unit_mismatch_steps"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
