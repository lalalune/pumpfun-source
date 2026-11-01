#!/usr/bin/env python3
"""Run captured-original-guided Admin CTO differential campaigns."""
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
SELF_SHA256 = globals().get("__source_sha256__")
if SELF_SHA256 is None:
    SELF_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_pfile = HERE / "corpus.py"
if _pfile.is_symlink():
    raise ValueError("corpus source must not be a symlink")
_pbytes = _pfile.read_bytes()
P = types.ModuleType("_pump_guided_corpus_bootstrap")
P.__file__ = str(_pfile)
P.__source_path__ = str(_pfile)
P.__source_sha256__ = hashlib.sha256(_pbytes).hexdigest()
exec(compile(_pbytes, str(_pfile), "exec", dont_inherit=True, optimize=0), P.__dict__)
C = P.source_module("guided_case_model", HERE / "case_model.py")
E = P.source_module("guided_executor", HERE / "executor.py",
                    imports={"case_model": C, "corpus": P})
R = P.source_module("guided_reducer", HERE / "reducer.py",
                    imports={"case_model": C, "executor": E, "corpus": P})
B = P.source_module("guided_behavior", HERE / "behavior.py",
                    imports={"case_model": C, "executor": E})

SCHEMA = "pump-admin-cto-guided-campaign-v1"
PRODUCERS = (
    HERE / "case_model.py", HERE / "executor.py", HERE / "reducer.py",
    HERE / "corpus.py", HERE / "behavior.py", HERE / "campaign.py",
    HERE / "verify_report.py", HERE / "guided_campaign.py", HERE / "verify_guided.py",
    ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py",
    E.L.IDL_PATH, E.L.CONFIG_PATH, ROOT / "scripts/pump_differential_output.py",
)


def loaded_source_hashes() -> dict[str, str]:
    result = {str(Path(__file__).absolute()): SELF_SHA256}
    for module in (P, C, E, R, B):
        path, value = module.__source_path__, module.__source_sha256__
        if path in result and result[path] != value:
            raise ValueError("different loaded source versions: " + path)
        result[path] = value
    for table in (E.RUNTIME_SOURCE_HASHES, R.RUNTIME_SOURCE_HASHES):
        for path, value in table.items():
            if path in result and result[path] != value:
                raise ValueError("different loaded source versions: " + path)
            result[path] = value
    return result


def require_loaded_sources(snapshot=None) -> None:
    loaded = loaded_source_hashes()
    for path, value in loaded.items():
        if P.file_sha(Path(path)) != value:
            raise ValueError("loaded producer source changed: " + path)
    if snapshot is not None:
        declared = {str(path): snapshot.hashes[name] for name, path in snapshot.sources.items()}
        if not set(loaded).issubset(declared) or any(declared[path] != value for path, value in loaded.items()):
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


def _negative_controls(result: dict) -> dict:
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


def _write_reduction(publisher, case, result, evaluation, seed, program_sha256,
                     max_trials: int) -> dict:
    reduction = R.reduce_case(case, evaluation, max_trials=max_trials)
    rejected = R.validate_reduction(reduction, case, result)
    rejected += E.validate_result(reduction["result"], reduction["case"])
    if rejected:
        raise ValueError("invalid reduction witness: " + repr(rejected))
    name = reduction["reduced_case_id"]
    publisher.write_json(f"counterexamples/{name}/case.json", reduction["case"])
    publisher.write_json(f"counterexamples/{name}/reduction.json.gz", reduction, compressed=True)
    publisher.write_json(f"counterexamples/{name}/manifest.json", {
        "schema": "pump-admin-cto-counterexample-manifest-v1",
        "original_seed": seed, "original_case_id": case["case_id"],
        "reduced_case_id": name, "program_sha256": program_sha256,
        "replay": "campaign.py replay --case case.json --original ORIGINAL.so --candidate CANDIDATE.so",
        "minimality": reduction["minimality"],
    })
    return reduction


def run_guided_campaign(*, original: Path, candidate: Path, output: Path,
                        seed: int, pool_count: int, corpus_limit: int,
                        start_index: int = 0,
                        expected_original_sha256: str | None = None,
                        expected_candidate_sha256: str | None = None,
                        reduce_mismatches: bool = True,
                        reduction_budget: int = 500,
                        after_observation=None, after_case=None) -> dict:
    if type(pool_count) is not int or not 1 <= pool_count <= B.MAX_POOL_CASES:
        raise ValueError(f"pool count must be between 1 and {B.MAX_POOL_CASES}")
    if type(corpus_limit) is not int or not 1 <= corpus_limit <= min(B.MAX_CORPUS_CASES, pool_count):
        raise ValueError("corpus limit is outside the bounded pool")
    if type(reduce_mismatches) is not bool:
        raise ValueError("reduce_mismatches must be boolean")
    if type(reduction_budget) is not int or not 1 <= reduction_budget <= 10_000:
        raise ValueError("reduction budget must be between 1 and 10000")
    require_loaded_sources()
    pool = C.generate_corpus(seed, pool_count, start_index)
    frozen_pool = copy.deepcopy(pool)
    if expected_original_sha256 not in (None, E.CANONICAL_ORIGINAL_SHA256):
        raise ValueError("original hash must name the captured Pump image")
    expected = {"pump_original": E.CANONICAL_ORIGINAL_SHA256}
    if expected_candidate_sha256:
        expected["pump_candidate"] = expected_candidate_sha256
    attempt = {
        "campaign_schema": SCHEMA, "seed": seed, "start_index": start_index,
        "pool_count": pool_count, "corpus_limit": corpus_limit,
        "pool_manifest_sha256": hashlib.sha256(C.canonical(pool)).hexdigest(),
    }
    with P.CampaignPublisher(output, attempt) as publisher:
        publisher.write_json("pool.json", pool)
        with P.InputSnapshot(declared_inputs(original, candidate), expected) as snapshot:
            require_loaded_sources(snapshot)
            images = _images(snapshot)
            observations = []
            for index, case in enumerate(pool):
                observation = B.observe_case(case, snapshot.paths["pump_original"], images)
                if after_observation is not None:
                    after_observation(index, copy.deepcopy(case), copy.deepcopy(observation))
                rejected = B.validate_observation(observation, case)
                if rejected:
                    publisher.write_json(f"rejected/observation-{index:04d}.json",
                                         {"failures": rejected, "observation": observation})
                    raise ValueError("invalid original observation: " + repr(rejected))
                observations.append(observation)
                publisher.write_json(f"observations/{index:04d}-{case['case_id']}.json.gz",
                                     observation, compressed=True)
            selection = B.select_corpus(pool, observations, corpus_limit)
            selected = B.selected_cases(pool, selection)
            publisher.write_json("selection.json", selection)
            publisher.write_json("cases.json", selected)
            results, summaries, reductions = [], [], []
            program_sha256 = {"original": snapshot.hashes["pump_original"],
                              "candidate": snapshot.hashes["pump_candidate"]}
            for rank, case in enumerate(selected):
                result = E.execute_case(case, snapshot.paths["pump_original"],
                                        snapshot.paths["pump_candidate"], images)
                if after_case is not None:
                    after_case(rank, copy.deepcopy(case), copy.deepcopy(result))
                rejected = E.validate_result(result, case, images=images)
                if rejected:
                    publisher.write_json(f"rejected/differential-{rank:04d}.json",
                                         {"failures": rejected, "result": result})
                    raise ValueError("invalid differential receipt: " + repr(rejected))
                results.append(result)
                summaries.append(_case_summary(result))
                publisher.write_json(f"receipts/{rank:04d}-{case['case_id']}.json.gz",
                                     result, compressed=True)
                if result["classification"] == "different_behavior" and reduce_mismatches:
                    def evaluation(value):
                        outcome = E.execute_case(value, snapshot.paths["pump_original"],
                                                 snapshot.paths["pump_candidate"], images)
                        failures = E.validate_result(outcome, value, images=images)
                        if failures:
                            raise ValueError("invalid reduction execution: " + repr(failures))
                        return outcome
                    reductions.append(_write_reduction(
                        publisher, case, result, evaluation, seed, program_sha256,
                        reduction_budget))
            if pool != frozen_pool:
                raise ValueError("pool changed during execution")
            require_loaded_sources(snapshot)
            changed = snapshot.changed_sources()
            if changed:
                raise RuntimeError("declared inputs changed during campaign: "
                                   + json.dumps(changed, sort_keys=True))
            counts = Counter(row["classification"] for row in results)
            executed = [row for row in results if "original" in row]
            control = _negative_controls(executed[0]) if executed else {"available": False}
            artifact_sha256 = publisher.write_manifest()
            observation_counts = Counter(row["classification"] for row in observations)
            summary = {
                "schema": SCHEMA,
                "tested_git_sha": _git("rev-parse", "HEAD"),
                "upstream_sha": _git("merge-base", "HEAD", "origin/main"),
                "seed": seed, "start_index": start_index,
                "pool_count": pool_count, "corpus_limit": corpus_limit,
                "pool_manifest_sha256": attempt["pool_manifest_sha256"],
                "selected_manifest_sha256": hashlib.sha256(C.canonical(selected)).hexdigest(),
                "selection_sha256": selection["selection_sha256"],
                "artifact_manifest_sha256": artifact_sha256,
                "program_sha256": program_sha256,
                "all_input_sha256": snapshot.hashes,
                "observation_counts": {name: observation_counts.get(name, 0) for name in
                                       ("observed_behavior", "unsupported_fixture", "infrastructure_failure")},
                "selected_behavior_class_count": selection["selected_behavior_class_count"],
                "unguided_behavior_class_count": selection["unguided_behavior_class_count"],
                "retained_behavior_class_gain": (selection["selected_behavior_class_count"]
                                                  - selection["unguided_behavior_class_count"]),
                "selected_case_count": len(selected),
                "classification_counts": {name: counts.get(name, 0) for name in (
                    "equal_observed_behavior", "different_behavior", "unsupported_fixture",
                    "infrastructure_failure")},
                "transaction_count_per_image": sum(len(row["original"]["receipts"]) for row in executed),
                "original_successful_case_count": sum(all(receipt["error"] is None
                    for receipt in row["original"]["receipts"]) for row in executed),
                "negative_controls": control,
                "runtime_verified": bool(executed) and not observation_counts.get("infrastructure_failure", 0)
                                    and not counts.get("infrastructure_failure", 0)
                                    and control.get("all_detected") is True,
                "verification_scope": "guided-executed-corpus",
                "reduced_counterexample_count": len(reductions),
                "cases": summaries,
            }
            summary["summary_sha256"] = hashlib.sha256(P.canonical_json(summary)).hexdigest()
            publisher.write_json("summary.json", summary)
            publisher.commit({
                "summary_sha256": summary["summary_sha256"],
                "artifact_manifest_sha256": artifact_sha256,
                "selection_sha256": selection["selection_sha256"],
                "classification_counts": summary["classification_counts"],
            })
            return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--pool-count", type=int, required=True)
    parser.add_argument("--corpus-limit", type=int, required=True)
    parser.add_argument("--start-index", type=int, default=0)
    parser.add_argument("--expected-original-sha256")
    parser.add_argument("--expected-candidate-sha256")
    parser.add_argument("--no-reduce", action="store_true")
    parser.add_argument("--reduction-budget", type=int, default=500)
    parser.add_argument("--allow-mismatches", action="store_true")
    args = parser.parse_args()
    summary = run_guided_campaign(
        original=args.original, candidate=args.candidate, output=args.output,
        seed=args.seed, pool_count=args.pool_count, corpus_limit=args.corpus_limit,
        start_index=args.start_index,
        expected_original_sha256=args.expected_original_sha256,
        expected_candidate_sha256=args.expected_candidate_sha256,
        reduce_mismatches=not args.no_reduce, reduction_budget=args.reduction_budget,
    )
    print(json.dumps(summary, sort_keys=True, indent=2))
    failed = (summary["observation_counts"]["infrastructure_failure"]
              or summary["classification_counts"]["infrastructure_failure"]
              or not summary["negative_controls"].get("all_detected", False)
              or (summary["classification_counts"]["different_behavior"]
                  and not args.allow_mismatches))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
