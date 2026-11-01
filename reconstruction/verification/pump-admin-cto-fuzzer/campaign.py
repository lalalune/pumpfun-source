#!/usr/bin/env python3
"""Run, replay, and retain deterministic Pump Admin CTO fuzz campaigns."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import types
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Bind the bytes that were compiled before any local dependency can run.
SELF_SHA256 = globals().get("__source_sha256__")
if SELF_SHA256 is None:
    SELF_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_pfile = HERE / "corpus.py"
if _pfile.is_symlink():
    raise ValueError("corpus source must not be a symlink")
_pbytes = _pfile.read_bytes()
P = types.ModuleType("_pump_fuzz_corpus_bootstrap")
P.__file__ = str(_pfile)
P.__source_path__ = str(_pfile)
P.__source_sha256__ = hashlib.sha256(_pbytes).hexdigest()
exec(compile(_pbytes, str(_pfile), "exec", dont_inherit=True, optimize=0), P.__dict__)
C = P.source_module("case_model", HERE / "case_model.py")
E = P.source_module("executor", HERE / "executor.py")
R = P.source_module("reducer", HERE / "reducer.py")

SCHEMA = "pump-admin-cto-fuzz-campaign-v2"
PRODUCERS = (
    HERE / "case_model.py", HERE / "executor.py", HERE / "reducer.py",
    HERE / "corpus.py", HERE / "campaign.py", HERE / "verify_report.py",
    ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py",
    E.L.IDL_PATH, E.L.CONFIG_PATH, ROOT / "scripts/pump_differential_output.py",
)


def loaded_source_hashes() -> dict[str, str]:
    result = {str(Path(__file__).absolute()): SELF_SHA256}
    for module in (P, C, E, R):
        path, digest = module.__source_path__, module.__source_sha256__
        if path in result and result[path] != digest:
            raise ValueError("different loaded source versions: " + path)
        result[path] = digest
    for table in (E.RUNTIME_SOURCE_HASHES, R.RUNTIME_SOURCE_HASHES):
        for path, digest in table.items():
            if path in result and result[path] != digest:
                raise ValueError("different loaded source versions: " + path)
            result[path] = digest
    return result


def require_loaded_sources(snapshot=None) -> None:
    loaded = loaded_source_hashes()
    for path, digest in loaded.items():
        if P.file_sha(Path(path)) != digest:
            raise ValueError("loaded producer source changed: " + path)
    if snapshot is not None:
        declared = {str(path): snapshot.hashes[name] for name, path in snapshot.sources.items()}
        if not set(loaded).issubset(declared) or any(declared[path] != digest for path, digest in loaded.items()):
            raise ValueError("snapshot does not bind every executed source module")


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True,
                          stdout=subprocess.PIPE, text=True).stdout.strip()


def declared_inputs(original: Path, candidate: Path) -> dict[str, Path]:
    paths = {"pump_original": Path(original), "pump_candidate": Path(candidate)}
    paths.update({"dependency_" + name: path for name, path in E.L.CAPTURED.items()
                  if name != "pump_original"})
    paths.update({"producer_" + path.relative_to(ROOT).as_posix().replace("/", "__"): path
                  for path in PRODUCERS})
    return paths


def _images(snapshot: P.InputSnapshot) -> dict[str, Path]:
    return {name: snapshot.paths["dependency_" + name]
            for name in E.L.CAPTURED if name != "pump_original"}


def _case_summary(result: dict) -> dict:
    row = {"case_id": result["case_id"], "classification": result["classification"],
           "reason": result.get("reason"), "execution_sha256": E.execution_identity(result)}
    if "original" in result:
        row.update(
            transaction_count=len(result["original"]["receipts"]),
            original_outcomes=[item["outcome"] for item in result["original"]["receipts"]],
            candidate_outcomes=[item["outcome"] for item in result["candidate"]["receipts"]],
            mismatch_fields=result["mismatch_fields"],
            diagnostic_difference_fields=sorted({field for item in result["comparison"]
                                                 for field in item["diagnostic_difference_fields"]}),
        )
    return row


def negative_controls(result: dict) -> dict:
    if "original" not in result:
        return {"available": False}
    checks = {}
    for field, mutate in (
        ("error", lambda run: run["receipts"][0].update(error="negative-control")),
        ("events", lambda run: run["receipts"][0]["events"].append("negative-control")),
        ("after", lambda run: run["receipts"][0]["after"].update({"negative-control": None})),
    ):
        changed = copy.deepcopy(result["candidate"])
        mutate(changed)
        differences, _ = E.compare_runs(result["original"], changed)
        checks[field] = any(item.endswith(":" + field) for item in differences)
    return {"available": True, "detected": checks, "all_detected": all(checks.values())}


def run_campaign(*, original: Path, candidate: Path, output: Path, seed: int, count: int,
                 start_index: int = 0,
                 expected_original_sha256: str | None = None,
                 expected_candidate_sha256: str | None = None,
                 detailed_receipts: bool = True, reduce_mismatches: bool = True,
                 reduction_budget: int = 500, after_case=None) -> dict:
    if type(count) is not int or not 1 <= count <= 1_000:
        raise ValueError("campaign count must be between 1 and 1000")
    if type(detailed_receipts) is not bool or type(reduce_mismatches) is not bool:
        raise ValueError("campaign switches must be booleans")
    if type(reduction_budget) is not int or not 1 <= reduction_budget <= 10_000:
        raise ValueError("reduction budget must be between 1 and 10000")
    require_loaded_sources()
    cases = C.generate_corpus(seed, count, start_index)
    frozen_cases = copy.deepcopy(cases)
    if expected_original_sha256 not in (None, E.CANONICAL_ORIGINAL_SHA256):
        raise ValueError("original hash must name the captured Pump image")
    expected = {"pump_original": E.CANONICAL_ORIGINAL_SHA256}
    if expected_candidate_sha256:
        expected["pump_candidate"] = expected_candidate_sha256
    inputs = declared_inputs(original, candidate)
    attempt = {"campaign_schema": SCHEMA, "seed": seed, "start_index": start_index,
               "count": count,
               "case_manifest_sha256": hashlib.sha256(C.canonical(cases)).hexdigest()}
    with P.CampaignPublisher(output, attempt) as publisher:
        publisher.write_json("cases.json", cases)
        with P.InputSnapshot(inputs, expected) as snapshot:
            require_loaded_sources(snapshot)
            images = _images(snapshot)
            results, summaries, reductions = [], [], []
            for index, case in enumerate(cases):
                result = E.execute_case(case, snapshot.paths["pump_original"],
                                        snapshot.paths["pump_candidate"], images)
                if after_case is not None:
                    after_case(index, copy.deepcopy(case), copy.deepcopy(result))
                failures = E.validate_result(result, case, images=images)
                if failures:
                    publisher.write_json(f"rejected/{index:04d}.json", {"failures": failures, "result": result})
                    raise ValueError("invalid executed case receipt: " + repr(failures))
                results.append(result)
                summaries.append(_case_summary(result))
                if detailed_receipts:
                    publisher.write_json(f"receipts/{index:04d}-{case['case_id']}.json.gz",
                                         result, compressed=True)
                else:
                    publisher.write_json(f"progress/{index:04d}-{case['case_id']}.json",
                                         summaries[-1])
                if result["classification"] == "different_behavior" and reduce_mismatches:
                    def evaluation(value):
                        outcome = E.execute_case(value, snapshot.paths["pump_original"],
                                                 snapshot.paths["pump_candidate"], images)
                        rejected = E.validate_result(outcome, value, images=images)
                        if rejected:
                            raise ValueError("invalid reduction execution: " + repr(rejected))
                        return outcome
                    reduction = R.reduce_case(case, evaluation, max_trials=reduction_budget)
                    rejected = R.validate_reduction(reduction, case, result)
                    rejected += E.validate_result(reduction["result"], reduction["case"], images=images)
                    if rejected:
                        raise ValueError("invalid reduction witness: " + repr(rejected))
                    reductions.append(reduction)
                    name = reduction["reduced_case_id"]
                    publisher.write_json(f"counterexamples/{name}/case.json", reduction["case"])
                    publisher.write_json(f"counterexamples/{name}/reduction.json.gz",
                                         reduction, compressed=True)
                    publisher.write_json(f"counterexamples/{name}/manifest.json", {
                        "schema": "pump-admin-cto-counterexample-manifest-v1",
                        "original_seed": seed, "original_case_id": case["case_id"],
                        "reduced_case_id": name, "program_sha256": {
                            "original": snapshot.hashes["pump_original"],
                            "candidate": snapshot.hashes["pump_candidate"],
                        },
                        "replay": "campaign.py replay --case case.json --original ORIGINAL.so --candidate CANDIDATE.so",
                        "minimality": reduction["minimality"],
                    })
            if cases != frozen_cases:
                raise ValueError("case manifest changed during execution")
            require_loaded_sources(snapshot)
            changed = snapshot.changed_sources()
            if changed:
                raise RuntimeError(f"declared inputs changed during campaign: {json.dumps(changed, sort_keys=True)}")
            counts = Counter(row["classification"] for row in results)
            executed = [row for row in results if "original" in row]
            control = negative_controls(executed[0]) if executed else {"available": False}
            artifact_sha256 = publisher.write_manifest()
            summary = {
                "schema": SCHEMA, "tested_git_sha": _git("rev-parse", "HEAD"),
                "upstream_sha": _git("merge-base", "HEAD", "origin/main"),
                "seed": seed, "start_index": start_index, "case_count": count,
                "case_manifest_sha256": attempt["case_manifest_sha256"],
                "artifact_manifest_sha256": artifact_sha256,
                "program_sha256": {"original": snapshot.hashes["pump_original"],
                                   "candidate": snapshot.hashes["pump_candidate"]},
                "all_input_sha256": snapshot.hashes,
                "classification_counts": {name: counts.get(name, 0) for name in (
                    "equal_observed_behavior", "different_behavior", "unsupported_fixture",
                    "infrastructure_failure")},
                "transaction_count_per_image": sum(len(row["original"]["receipts"]) for row in executed),
                "executed_case_count": len(executed),
                "original_successful_case_count": sum(all(receipt["error"] is None
                    for receipt in row["original"]["receipts"]) for row in executed),
                "negative_controls": control,
                "runtime_verified": bool(executed) and not counts.get("infrastructure_failure", 0)
                                    and control.get("all_detected") is True,
                "verification_scope": "executed-corpus",
                "reduced_counterexample_count": len(reductions),
                "detailed_receipts": detailed_receipts,
                "cases": summaries,
            }
            summary["summary_sha256"] = hashlib.sha256(P.canonical_json(summary)).hexdigest()
            publisher.write_json("summary.json", summary)
            publisher.commit({"summary_sha256": summary["summary_sha256"],
                              "artifact_manifest_sha256": artifact_sha256,
                              "classification_counts": summary["classification_counts"]})
            return summary


def replay_case(case_path: Path, original: Path, candidate: Path,
                expected_original: str | None = None,
                expected_candidate: str | None = None) -> dict:
    require_loaded_sources()
    case = C.validate_case(P.read_json(case_path))
    if expected_original not in (None, E.CANONICAL_ORIGINAL_SHA256):
        raise ValueError("original hash must name the captured Pump image")
    expected = {"pump_original": E.CANONICAL_ORIGINAL_SHA256}
    if expected_candidate:
        expected["pump_candidate"] = expected_candidate
    with P.InputSnapshot(declared_inputs(original, candidate), expected) as snapshot:
        require_loaded_sources(snapshot)
        result = E.execute_case(case, snapshot.paths["pump_original"],
                                snapshot.paths["pump_candidate"], _images(snapshot))
        if snapshot.changed_sources():
            raise RuntimeError("declared inputs changed during replay")
        require_loaded_sources(snapshot)
        failures = E.validate_result(result, case, images=_images(snapshot))
        if failures:
            raise ValueError("invalid replay receipt: " + repr(failures))
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="write a deterministic case manifest to stdout")
    generate.add_argument("--seed", type=int, required=True)
    generate.add_argument("--count", type=int, required=True)
    generate.add_argument("--start-index", type=int, default=0)
    run = sub.add_parser("run", help="execute and atomically publish a bounded campaign")
    run.add_argument("--original", type=Path, required=True)
    run.add_argument("--candidate", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    run.add_argument("--seed", type=int, required=True)
    run.add_argument("--count", type=int, required=True)
    run.add_argument("--start-index", type=int, default=0)
    run.add_argument("--expected-original-sha256")
    run.add_argument("--expected-candidate-sha256")
    run.add_argument("--omit-detailed-receipts", action="store_true")
    run.add_argument("--no-reduce", action="store_true")
    run.add_argument("--reduction-budget", type=int, default=500)
    run.add_argument("--allow-mismatches", action="store_true")
    replay = sub.add_parser("replay", help="execute one retained case")
    replay.add_argument("--case", type=Path, required=True)
    replay.add_argument("--original", type=Path, required=True)
    replay.add_argument("--candidate", type=Path, required=True)
    replay.add_argument("--expected-original-sha256")
    replay.add_argument("--expected-candidate-sha256")
    args = parser.parse_args()
    if args.command == "generate":
        print(json.dumps(C.generate_corpus(args.seed, args.count, args.start_index), sort_keys=True, indent=2))
        return 0
    if args.command == "replay":
        result = replay_case(args.case, args.original, args.candidate,
                             args.expected_original_sha256, args.expected_candidate_sha256)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if result["classification"] not in ("infrastructure_failure",) else 1
    summary = run_campaign(
        original=args.original, candidate=args.candidate, output=args.output,
        seed=args.seed, count=args.count, start_index=args.start_index,
        expected_original_sha256=args.expected_original_sha256,
        expected_candidate_sha256=args.expected_candidate_sha256,
        detailed_receipts=not args.omit_detailed_receipts,
        reduce_mismatches=not args.no_reduce, reduction_budget=args.reduction_budget,
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    failed = (summary["classification_counts"]["infrastructure_failure"]
              or not summary["negative_controls"].get("all_detected", False)
              or (summary["classification_counts"]["different_behavior"] and not args.allow_mismatches))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
