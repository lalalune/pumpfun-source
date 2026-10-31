#!/usr/bin/env python3
"""Independently verify a retained Donation Relay IDL lifecycle receipt."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


RELAY = "RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu"
ORIGINAL_SHA256 = "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563"
COMPUTE_RE = re.compile(r"Program \S+ consumed \d+ of \d+ compute units")

# The producer has no filtering mode: these ordered cohorts identify the two
# complete cases whose classifications and transaction totals are verified below.
PLANNED_STEPS = {
    "stateful_lifecycle": (
        "create", "resize_empty", "create_buffer", "write_buffer", "set_buffer",
        "resize_nonempty_rejected", "set_authority", "old_authority_write_rejected",
        "new_authority_write", "close", "repeated_close_rejected",
    ),
    "admission_matrix": (
        "write_before_initialization", "resize_before_initialization", "incorrect_owner",
        "short_account_header", "incorrect_discriminator", "insufficient_rent_buffer",
        "unauthorized_signer", "readonly_idl", "write_capacity_error",
        "noncanonical_valid_idl", "truncated_write_payload", "invalid_operation_tag",
        "missing_create_accounts", "oversized_setup_create", "oversized_resize_capped",
        "wrong_canonical_create",
    ),
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def manifest(base: Path, root: Path) -> tuple[dict[str, str], str]:
    rows = {path.relative_to(root).as_posix(): file_sha(path) for path in sorted(base.rglob("*")) if path.is_file()}
    digest = sha(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    return rows, digest


def comparable(row: dict[str, Any]) -> dict[str, Any]:
    def state(stage: str) -> dict[str, Any]:
        value = json.loads(json.dumps(row[stage]))
        value.pop(RELAY, None)
        return value

    return {
        "error": row["error"],
        "relevant_logs": [line for line in row["logs"] if not COMPUTE_RE.fullmatch(line)],
        "events": row["events"],
        "inner_instructions": row["inner_instructions"],
        "return_data": row["return_data"],
        "before": state("before"),
        "after": state("after"),
    }


def validate(report: dict[str, Any], root: Path, candidate: Path) -> list[str]:
    problems: list[str] = []
    if report.get("schema") != "donation-relay-idl-lifecycle-v1":
        problems.append("schema")
    if report.get("program") != RELAY:
        problems.append("program")
    original = root / "evidence/dependencies/donation_relay/deployed.so"
    if not original.is_file() or file_sha(original) != ORIGINAL_SHA256:
        problems.append("captured_elf_current")
    if report.get("inputs", {}).get("captured_elf", {}).get("sha256") != ORIGINAL_SHA256:
        problems.append("captured_elf_report")
    if not candidate.is_file() or report.get("inputs", {}).get("candidate_elf", {}).get("sha256") != file_sha(candidate):
        problems.append("candidate_elf")
    source_rows, source_digest = manifest(root / "programs/donation-relay", root)
    inputs = report.get("inputs", {})
    if inputs.get("source_manifest_sha256") != source_digest or inputs.get("source_files") != source_rows:
        problems.append("source_manifest")
    package = Path(__file__).resolve().parent
    package_rows = {path.relative_to(root).as_posix(): file_sha(path) for path in sorted(package.iterdir()) if path.is_file()}
    if inputs.get("test_package_files") != package_rows:
        problems.append("test_package_manifest")

    cases = report.get("cases", [])
    steps = [step for case in cases for step in case.get("steps", [])]
    if [case.get("name") for case in cases] != ["stateful_lifecycle", "admission_matrix"]:
        problems.append("case_membership")
    if report.get("case_count") != len(cases):
        problems.append("case_count")
    if any(not case.get("steps") for case in cases):
        problems.append("case_steps")
    for case in cases:
        planned = PLANNED_STEPS.get(case.get("name"))
        # Preserve the established empty-case diagnostic; every nonempty case
        # must also retain its complete ordered producer cohort.
        if planned is None or not case.get("steps"):
            continue
        names = [step.get("name") for step in case["steps"]]
        if names != list(planned):
            problems.append("case_step_membership:" + case["name"])
        if case["name"] == "stateful_lifecycle" and case.get("operation_order") != names:
            problems.append("operation_order")
    if any(case.get("classification") != "equal_observed_behavior" or case.get("problems") for case in cases):
        problems.append("case_classification")
    if report.get("matching_cases") != len(cases) or report.get("different_cases"):
        problems.append("case_summary")
    for step in steps:
        if step.get("mismatches"):
            problems.append("recorded_mismatch:" + step.get("name", "unknown"))
        if comparable(step["original"]) != comparable(step["candidate"]):
            problems.append("recomputed_mismatch:" + step.get("name", "unknown"))
        if not step.get("signature_verified"):
            problems.append("unverified_signature:" + step.get("name", "unknown"))
        for side in ("original", "candidate"):
            row = step[side]
            if row["error"] is not None and row.get("rollback_non_fee_changes"):
                problems.append("rollback:" + step.get("name", "unknown") + ":" + side)
    signatures = [step.get("signature") for step in steps]
    identities = report.get("transaction_identity", {})
    if identities.get("transaction_count") != len(steps):
        problems.append("transaction_count")
    if identities.get("unique_transaction_count") != len(set(signatures)) or len(signatures) != len(set(signatures)):
        problems.append("transaction_uniqueness")
    if not identities.get("all_transactions_signature_verified"):
        problems.append("signature_summary")
    controls = report.get("negative_controls", {})
    if not controls.get("all_detected") or not all(controls.get("detected", {}).values()):
        problems.append("negative_controls")
    if set(controls.get("detected", {})) != {"account_state", "error", "event_payload"}:
        problems.append("negative_control_membership")
    if set(report.get("supported_operations", [])) != {"Create", "CreateBuffer", "Write", "SetBuffer", "SetAuthority", "Close", "Resize"}:
        problems.append("operation_matrix")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    raw = args.report.read_bytes()
    report = json.loads(raw)
    canonical = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    problems = validate(report, args.root.resolve(), args.candidate.resolve())
    if raw != canonical:
        problems.append("noncanonical_json")
    print(json.dumps({"report_sha256": sha(raw), "problems": problems}, indent=2, sort_keys=True))
    raise SystemExit(1 if problems else 0)


if __name__ == "__main__":
    main()
