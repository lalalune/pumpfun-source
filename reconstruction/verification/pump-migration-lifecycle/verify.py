#!/usr/bin/env python3
"""Verify or deterministically replay a Pump migration lifecycle report."""

import argparse
import gzip
import json
from pathlib import Path

import lifecycle


def read_report(path):
    raw = path.read_bytes()
    if path.suffix == ".gz":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def verify(report, candidate):
    problems = []
    expected_hashes = lifecycle.program_hashes(candidate)
    if report.get("schema") != "pump-migration-lifecycle-v1":
        problems.append("schema")
    if report.get("program_sha256") != expected_hashes:
        problems.append("program_sha256")
    if report.get("fixture_sha256") != lifecycle.sha256_file(lifecycle.FIXTURE_PATH):
        problems.append("fixture_sha256")
    if report.get("idl_sha256") != lifecycle.sha256_file(lifecycle.IDL_PATH):
        problems.append("idl_sha256")

    planned = lifecycle.scenarios()
    planned_names = [case["name"] for case in planned]
    rows = report.get("cases", [])
    if [row.get("case") for row in rows] != planned_names:
        problems.append("case_membership_or_order")
    if report.get("case_count") != len(rows):
        problems.append("case_count")
    transaction_count = 0
    mismatch_cases = []
    oracle_mismatch_cases = []
    invariant_failure_cases = []
    rollback_failure_cases = []
    infrastructure_failure_cases = []
    for row in rows:
        transaction_count += len(row["original"]["receipts"])
        mismatches, comparison = lifecycle.compare_runs(row["original"], row["candidate"])
        if mismatches != row.get("mismatch_fields") or comparison != row.get("comparison"):
            problems.append(row["case"] + ":comparison")
        if mismatches:
            mismatch_cases.append(row["case"])
        observed = [receipt["outcome"] for receipt in row["original"]["receipts"]]
        expected = lifecycle.EXPECTED_OUTCOMES.get(row["case"])
        if observed != expected or expected != row.get("expected_original_outcomes"):
            oracle_mismatch_cases.append(row["case"])
        invariant = {
            "original": lifecycle.validate_lifecycle(row["original"]),
            "candidate": lifecycle.validate_lifecycle(row["candidate"]),
        }
        if invariant != row.get("invariant_failures"):
            problems.append(row["case"] + ":invariant_receipt")
        if any(invariant.values()):
            invariant_failure_cases.append(row["case"])
        if row.get("rollback_failures"):
            rollback_failure_cases.append(row["case"])
        if row.get("infrastructure_failures"):
            infrastructure_failure_cases.append(row["case"])
        if row.get("fixture_sha256") != report.get("fixture_sha256"):
            problems.append(row["case"] + ":fixture_binding")
        if row.get("program_sha256") != expected_hashes:
            problems.append(row["case"] + ":program_binding")

    summaries = {
        "transaction_count_per_image": transaction_count,
        "mismatch_cases": mismatch_cases,
        "oracle_mismatch_cases": oracle_mismatch_cases,
        "invariant_failure_cases": invariant_failure_cases,
        "rollback_failure_cases": rollback_failure_cases,
        "infrastructure_failure_cases": infrastructure_failure_cases,
    }
    for key, value in summaries.items():
        if report.get(key) != value:
            problems.append(key)
    controls = lifecycle.negative_control(report) if rows else {}
    if controls != {"error": True, "after": True} or report.get("negative_controls") != controls:
        problems.append("negative_controls")
    if any((mismatch_cases, oracle_mismatch_cases, invariant_failure_cases,
            rollback_failure_cases, infrastructure_failure_cases)):
        problems.append("qualification_failures")
    return problems


def main():
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
        replay["negative_controls"] = lifecycle.negative_control(replay)
        replay_equal = replay == report
        if not replay_equal:
            problems.append("deterministic_replay")
    print(json.dumps({"verified": not problems, "problems": problems,
                      "deterministic_replay_equal": replay_equal}, indent=2))
    return bool(problems)


if __name__ == "__main__":
    raise SystemExit(main())
