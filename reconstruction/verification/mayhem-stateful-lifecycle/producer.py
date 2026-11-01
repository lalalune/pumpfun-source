#!/usr/bin/env python3
"""Produce deterministic paired receipts for persistent Mayhem lifecycles."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

HERE = Path(__file__).resolve().parent
_path = HERE / "admission.py"
_raw = _path.read_bytes()
_admission = {"__file__": str(_path), "__name__": "mayhem_admission"}
exec(compile(_raw, str(_path), "exec", dont_inherit=True), _admission)
lifecycle = _admission["source_module"]("mayhem_stateful_lifecycle", HERE / "lifecycle.py")
ROOT, lifecycle_plan, run_image, sha256_bytes = lifecycle.ROOT, lifecycle.lifecycle_plan, lifecycle.run_image, lifecycle.sha256_bytes
bound_inputs = _admission["bound_inputs"]
recheck_inputs = lifecycle.recheck_inputs
outside_repository = _admission["outside_repository"]
if sha256_bytes(_raw) != lifecycle.LOADED_INPUT_SHA256[_path.relative_to(ROOT).as_posix()]:
    raise ValueError("admission source changed during import")
if "_ADMITTED_SOURCE_BYTES" in globals() and sha256_bytes(_ADMITTED_SOURCE_BYTES) != lifecycle.LOADED_INPUT_SHA256[Path(__file__).relative_to(ROOT).as_posix()]:
    raise ValueError("producer source changed during import")

ORIGINAL = ROOT / "evidence/original/mayhem/deployed.so"
ORIGINAL_SHA256 = "a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb"
CANDIDATE_SHA256 = "9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d"


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_line(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def source_tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def produce(candidate: Path, output: Path, original_control: bool = False) -> dict:
    recheck_inputs()
    outside_repository(output)
    candidate = candidate.resolve()
    if not candidate.is_file():
        raise ValueError(f"candidate is not a regular file: {candidate}")
    if sha256_file(ORIGINAL) != ORIGINAL_SHA256:
        raise ValueError("captured Mayhem original hash mismatch")
    expected = ORIGINAL_SHA256 if original_control else CANDIDATE_SHA256
    if sha256_file(candidate) != expected:
        raise ValueError(f"candidate hash is not the qualified {'control' if original_control else 'rebuild'}")
    output.mkdir(parents=True, exist_ok=False)

    original_rows = run_image(ORIGINAL)
    candidate_rows = run_image(candidate)
    recheck_inputs()
    if sha256_file(candidate) != expected:
        raise ValueError("candidate image changed during execution")
    if len(original_rows) != len(candidate_rows):
        raise AssertionError("paired execution count differs")
    rows = []
    for original, rebuilt in zip(original_rows, candidate_rows, strict=True):
        case_id = f"{original['lifecycle']}/{original['step']}"
        if case_id != f"{rebuilt['lifecycle']}/{rebuilt['step']}":
            raise AssertionError("paired execution order differs")
        rows.append({"case_id": case_id, "original": original, "candidate": rebuilt})

    receipt_path = output / "receipts.jsonl"
    receipt_path.write_text("".join(canonical_line(row) for row in rows), encoding="utf-8", newline="\n")
    input_paths = bound_inputs()
    inputs = dict(lifecycle.LOADED_INPUT_SHA256)
    mayhem_sources = [path for path in input_paths if path.is_relative_to(ROOT / "programs/mayhem")]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()
    report = {
        "schema": "mayhem-stateful-lifecycle-report-v1",
        "scope": "Persistent signed Mayhem execution on independent LiteSVM instances; synthetic preinitialized canonical PDAs, captured dependency CPIs, no initialization claim.",
        "source_commit": commit,
        "mode": "original_vs_original" if original_control else "original_vs_candidate",
        "original": {"path": str(ORIGINAL.relative_to(ROOT)), "sha256": ORIGINAL_SHA256, "bytes": ORIGINAL.stat().st_size},
        "candidate": {"path": str(candidate), "sha256": sha256_file(candidate), "bytes": candidate.stat().st_size},
        "input_sha256": inputs,
        "mayhem_source_files": len(mayhem_sources),
        "mayhem_source_tree_sha256": source_tree_sha256(mayhem_sources),
        "fixture_classification": "synthetic_preinitialized",
        "plan": lifecycle_plan(),
        "receipt_file": receipt_path.name,
        "receipt_sha256": sha256_file(receipt_path),
        "observed_case_count": len(rows),
        "observed_signed_transactions": len(rows) * 2,
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    recheck_inputs()
    if sha256_file(candidate) != expected:
        raise ValueError("candidate image changed during publication")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--original-control", action="store_true")
    args = parser.parse_args()
    report = produce(args.candidate, args.output, args.original_control)
    print(json.dumps({key: report[key] for key in ("mode", "observed_case_count", "observed_signed_transactions", "receipt_sha256")}, sort_keys=True))


if __name__ == "__main__":
    main()
