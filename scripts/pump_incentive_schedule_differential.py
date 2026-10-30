#!/usr/bin/env python3
"""Signed offline Pump schedule boundaries; captured ELF versus compiled source.

The authority and funded accounts are synthetic local fixtures. This does not
establish live authority, reachable historical state, or exhaustive equivalence.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import gzip
import hashlib
import json
import random
import re
from pathlib import Path

import pump_incentives_admin_differential as fixture

FIELDS = ("before", "after", "error", "events", "inner", "return")


def cases():
    yield from fixture.cases()
    rng = random.Random(20261026)
    for index in range(256):
        start = rng.choice([-20, 0, 1, 9, 10, 11, 20, 40])
        period = rng.choice([-1, 0, 1, 2, 10, 86400])
        yield {
            "name": f"schedule-grid-{index}",
            "now": rng.choice([-1, 0, 9, 10, 11, 20, 40, 100]),
            "old_start": start,
            "old_end": start + rng.choice([0, 1, 29, 30, 31, 59]),
            "old_day": rng.choice([0, 1, 2, 10]),
            "start": rng.choice([0, start, start + 1, 20, 40]),
            "end": start + rng.choice([0, 1, 29, 30, 31, 59]),
            "day": period,
            "index": rng.choice([0, 1, 28, 29, 30, 31, 2**64 - 1]),
            "supply": rng.choice([0, 1, 1000, 2**64 - 1]),
            "supplies": list(range(30)),
            "volumes": list(range(100, 130)),
        }
    for field in ("start", "end", "day", "old_start", "old_end"):
        for value in (-(2**63), -(2**63) + 1, 2**63 - 2, 2**63 - 1):
            yield {"name": f"signed-limit-{field}-{value}", field: value}


def panic_messages(result):
    return [line.split("\n", 1)[-1] for line in result["logs"]
            if line.startswith("Program log: panicked at ")]


def anchor_diagnostics(result):
    # Preserve numeric compared values and error details, while allowing the
    # reconstructed source to retain its own natural file/line coordinates.
    return [re.sub(r" thrown in .*?:\d+\.", ".", line)
            for line in result["logs"]
            if line.startswith(("Program log: AnchorError",
                                "Program log: Left:", "Program log: Right:"))]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--build-comparison", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    candidate_sha = sha(args.candidate)
    build = json.loads(args.build_comparison.read_text()) if args.build_comparison else None
    if build:
        assert build["comparison"]["candidate_sha256"] == candidate_sha
        assert all(sha(fixture.ROOT / p) == digest
                   for p, digest in build["source_sha256"].items())
    inputs = {str(p.relative_to(fixture.ROOT)): sha(p) for p in (
        Path(__file__).resolve(), Path(fixture.__file__).resolve())}
    rows = []
    for case in cases():
        original = fixture.run(case)
        candidate = fixture.run(case, args.candidate)
        differences = [key for key in FIELDS if original[key] != candidate[key]]
        if panic_messages(original) != panic_messages(candidate):
            differences.append("panic_message")
        if anchor_diagnostics(original) != anchor_diagnostics(candidate):
            differences.append("anchor_diagnostics")
        assert original["transaction_base64"] == candidate["transaction_base64"]
        rows.append({"case": case, "original": original, "candidate": candidate,
                     "differences": differences})
    assert candidate_sha == sha(args.candidate)
    assert all(sha(fixture.ROOT / p) == digest for p, digest in inputs.items())
    if build:
        assert all(sha(fixture.ROOT / p) == digest
                   for p, digest in build["source_sha256"].items())
    report = {
        "scope": __doc__, "candidate_sha256": sha(args.candidate),
        "original_sha256": sha(fixture.ORIGINAL),
        "inputs_sha256": inputs,
        "build_comparison_sha256": sha(args.build_comparison) if build else None,
        "compiled_source_sha256": build["source_sha256"] if build else None,
        "case_count": len(rows),
        "mismatches": [r["case"]["name"] for r in rows if r["differences"]],
        "original_successes": sum(r["original"]["error"] is None for r in rows),
        "cases": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(json.dumps(report).encode(), mtime=0))
    print(json.dumps({k: report[k] for k in
                      ("case_count", "original_successes", "mismatches")}))
    if report["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
