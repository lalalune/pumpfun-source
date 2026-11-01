#!/usr/bin/env python3
"""Independently verify or replay a cross-program fee lifecycle report."""
from __future__ import annotations

import argparse
import gzip
import importlib.util
import sys
import json
from pathlib import Path

_SOURCE = Path(__file__).resolve().parent / "lifecycle.py"
_BYTES = _SOURCE.read_bytes()
_SPEC = importlib.util.spec_from_file_location("lifecycle", _SOURCE)
if _SPEC is None:
    raise RuntimeError("cannot load lifecycle source")
lifecycle = importlib.util.module_from_spec(_SPEC)
lifecycle.__dict__["_ADMITTED_SOURCE_BYTES"] = _BYTES
sys.modules[_SPEC.name] = lifecycle
exec(compile(_BYTES, str(_SOURCE), "exec", dont_inherit=True), lifecycle.__dict__)


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field: " + key)
        result[key] = value
    return result


def read_report(path: Path) -> dict:
    raw = path.read_bytes()
    def reject_constant(value):
        raise ValueError("non-finite JSON constant: " + value)
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw,
                      object_pairs_hook=unique_fields, parse_constant=reject_constant)


def expected_program_hashes(candidate: Path) -> dict:
    rows = {name: lifecycle.base.file_sha(path) for name, path in lifecycle.base.CAPTURED.items()}
    rows["pump_candidate"] = lifecycle.base.file_sha(candidate)
    return rows


def expected_classification(mismatches, receipt_failures, invariant_failures, infrastructure) -> str:
    if infrastructure:
        return "infrastructure_failure"
    if invariant_failures["original"] or receipt_failures["original"]:
        return "unsupported_fixture"
    if mismatches or invariant_failures["candidate"] or receipt_failures["candidate"]:
        return "different_behavior"
    return "equal_observed_behavior"


def verify(report: dict, candidate: Path) -> list[str]:
    if type(report) is not dict:
        return ["report-object"]
    try:
        lifecycle.recheck_inputs()
        lifecycle.checked_steps()
        return _verify(report, candidate)
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OSError) as error:
        return ["malformed-or-changed-input:" + type(error).__name__]


def _verify(report: dict, candidate: Path) -> list[str]:
    problems = []
    if report.get("schema") != "pump-cross-program-fee-lifecycle-v1":
        problems.append("schema")
    expected_ids = {
        "pump": str(lifecycle.PUMP), "pump_amm": str(lifecycle.AMM),
        "pump_fees": str(lifecycle.FEES), "spl_token": str(lifecycle.TOKEN),
        "associated_token": str(lifecycle.ATA),
    }
    if not lifecycle.same_json(report.get("program_ids"), expected_ids):
        problems.append("program_ids")
    if not lifecycle.same_json(report.get("program_sha256"), expected_program_hashes(candidate)):
        problems.append("program_sha256")
    if report.get("idl_sha256") != {
        "pump": lifecycle.base.sha(lifecycle.base.IDL_BYTES),
        "pump_amm": lifecycle.base.sha(lifecycle.AMM_IDL_BYTES),
    }:
        problems.append("idl_sha256")
    if report.get("fixture_sha256") != lifecycle.base.sha(lifecycle.TRADE_FIXTURE_BYTES):
        problems.append("fixture_sha256")
    candidate_hash = lifecycle.base.file_sha(candidate)
    provenance, source_binding = lifecycle.candidate_binding(candidate_hash)
    if (not lifecycle.same_json(report.get("candidate_provenance"), provenance)
            or report.get("candidate_provenance_sha256")
            != lifecycle.base.sha(lifecycle.CANDIDATE_PROVENANCE_BYTES)):
        problems.append("candidate_provenance")
    if provenance.get("candidate_sha256") != candidate_hash:
        problems.append("candidate_provenance_binary")
    if provenance.get("schema") == "pump-cross-program-candidate-provenance-v1":
        prior = provenance["prior_qualification"]
        prior_path = lifecycle.ROOT / prior["path"]
        if not prior_path.is_file() or lifecycle.base.file_sha(prior_path) != prior.get("sha256"):
            problems.append("prior_qualification_hash")
        else:
            prior_report = read_report(prior_path)
            if (prior_report.get("schema") != prior.get("schema")
                    or prior_report.get("program_sha256", {}).get("pump_candidate")
                    != prior.get("candidate_sha256")
                    or prior_report.get("transaction_count_per_image")
                    != prior.get("transaction_count_per_image")
                    or prior_report.get("mismatch_cases") != prior.get("mismatch_cases")):
                problems.append("prior_qualification_content")
    elif provenance.get("schema") not in ("captured-original-control-v1", "supplied-candidate-input-v1"):
        problems.append("candidate_provenance_unknown")
    if not lifecycle.same_json(report.get("source_binding"), source_binding):
        problems.append("source_binding")
    expected_inputs = dict(lifecycle.LOADED_INPUT_SHA256)
    if not lifecycle.same_json(report.get("producer_input_sha256"), expected_inputs):
        problems.append("producer_input_sha256")
    sources, source_digest = lifecycle.source_manifest()
    if (not lifecycle.same_json(report.get("source_files"), sources)
            or report.get("source_manifest_sha256") != source_digest):
        problems.append("source_manifest")

    original = report.get("original")
    candidate_run = report.get("candidate")
    if not isinstance(original, dict) or not isinstance(candidate_run, dict):
        return problems + ["runs"]
    planned_names = [step["name"] for step in lifecycle.STEPS]
    expected_operations = {
        step["name"]: "+".join(operation["op"] for operation in step["operations"])
        for step in lifecycle.STEPS
    }
    all_signatures = {"original": [], "candidate": []}
    for side, run in (("original", original), ("candidate", candidate_run)):
        receipts = run.get("receipts", [])
        if [row.get("step") for row in receipts] != planned_names:
            problems.append(side + ":step_membership")
        for row, plan in zip(receipts, lifecycle.STEPS):
            if (not lifecycle.same_json(row.get("operations"), plan["operations"])
                    or row.get("operation") != expected_operations[plan["name"]]):
                problems.append(side + ":" + plan["name"] + ":operation_plan")
            all_signatures[side].append(row.get("signature"))
        if len(all_signatures[side]) != len(set(all_signatures[side])):
            problems.append(side + ":duplicate_signature")

    mismatches, comparison = lifecycle.compare_runs(original, candidate_run)
    if (not lifecycle.same_json(report.get("mismatch_fields"), mismatches)
            or not lifecycle.same_json(report.get("comparison"), comparison)):
        problems.append("comparison")
    receipt_failures = {
        "original": lifecycle.validate_run(original),
        "candidate": lifecycle.validate_run(candidate_run),
    }
    if not lifecycle.same_json(report.get("receipt_failures"), receipt_failures):
        problems.append("receipt_failures")
    invariant_failures = {
        "original": lifecycle.lifecycle_invariants(original),
        "candidate": lifecycle.lifecycle_invariants(candidate_run),
    }
    if not lifecycle.same_json(report.get("invariant_failures"), invariant_failures):
        problems.append("invariant_failures")
    infrastructure = [
        f"{side}:{row['step']}"
        for side, run in (("original", original), ("candidate", candidate_run))
        for row in run["receipts"] if lifecycle.base.failure_class(row.get("error")) == "infrastructure"
    ]
    if not lifecycle.same_json(report.get("infrastructure_failures"), infrastructure):
        problems.append("infrastructure_failures")
    classification = expected_classification(
        mismatches, receipt_failures, invariant_failures, infrastructure
    )
    if report.get("classification") != classification:
        problems.append("classification")
    if type(report.get("transaction_count_per_image")) is not int or report["transaction_count_per_image"] != lifecycle.EXPECTED_TRANSACTION_COUNT:
        problems.append("transaction_count_per_image")
    multi = sum(len(step["operations"]) > 1 for step in lifecycle.STEPS)
    if type(report.get("multi_instruction_transactions_per_image")) is not int or report["multi_instruction_transactions_per_image"] != multi:
        problems.append("multi_instruction_transactions_per_image")
    controls = lifecycle.negative_controls(report)
    expected_controls = {"error": True, "after": True, "events": True, "inner_instructions": True}
    if not lifecycle.same_json(controls, expected_controls) or not lifecycle.same_json(report.get("negative_controls"), controls):
        problems.append("negative_controls")
    if classification != "equal_observed_behavior":
        problems.append("qualification_failure:" + classification)
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args()
    report = read_report(args.report)
    problems = verify(report, args.candidate.resolve())
    replay_equal = None
    if args.replay and not problems:
        replay = lifecycle.run_suite(args.candidate.resolve())
        replay["negative_controls"] = lifecycle.negative_controls(replay)
        replay_equal = replay == report
        if not replay_equal:
            problems.append("deterministic_replay")
    print(json.dumps({
        "verified": not problems,
        "problems": problems,
        "deterministic_replay_equal": replay_equal,
    }, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
