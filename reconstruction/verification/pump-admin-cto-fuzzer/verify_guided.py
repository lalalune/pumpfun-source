#!/usr/bin/env python3
"""Independently verify behavior-guided Admin CTO campaign evidence."""
from __future__ import annotations

import argparse
import copy
import gzip
import hashlib
import io
import json
import math
import sys
import types
import uuid
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_pfile = HERE / "corpus.py"
_praw = _pfile.read_bytes()
_pname = "_pump_guided_verify_corpus_" + uuid.uuid4().hex
P = types.ModuleType(_pname)
P.__file__ = str(_pfile)
P.__source_path__ = str(_pfile)
P.__source_sha256__ = hashlib.sha256(_praw).hexdigest()
sys.modules[_pname] = P
try:
    exec(compile(_praw, str(_pfile), "exec", dont_inherit=True, optimize=0), P.__dict__)
finally:
    sys.modules.pop(_pname, None)
C = P.source_module("guided_verify_case_model", HERE / "case_model.py")
E = P.source_module("guided_verify_executor", HERE / "executor.py",
                    imports={"case_model": C, "corpus": P})
R = P.source_module("guided_verify_reducer", HERE / "reducer.py",
                    imports={"case_model": C, "executor": E, "corpus": P})
B = P.source_module("guided_verify_behavior", HERE / "behavior.py",
                    imports={"case_model": C, "executor": E})

SCHEMA = "pump-admin-cto-guided-verification-v1"
CAMPAIGN_SCHEMA = "pump-admin-cto-guided-campaign-v1"
PRODUCERS = (
    HERE / "case_model.py", HERE / "executor.py", HERE / "reducer.py",
    HERE / "corpus.py", HERE / "behavior.py", HERE / "campaign.py",
    HERE / "verify_report.py", HERE / "guided_campaign.py", HERE / "verify_guided.py",
    ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py",
    E.L.IDL_PATH, E.L.CONFIG_PATH, ROOT / "scripts/pump_differential_output.py",
)
RUNTIME_SOURCE_HASHES = dict(E.RUNTIME_SOURCE_HASHES)
for _module in (P, C, E, R, B):
    _path, _digest = _module.__source_path__, _module.__source_sha256__
    if _path in RUNTIME_SOURCE_HASHES and RUNTIME_SOURCE_HASHES[_path] != _digest:
        raise ValueError("source bytes changed between private graph loads: " + _path)
    RUNTIME_SOURCE_HASHES[_path] = _digest
RUNTIME_SOURCE_HASHES[str(Path(__file__).resolve())] = globals().get(
    "__source_sha256__", hashlib.sha256(Path(__file__).read_bytes()).hexdigest())


def _input_paths(original: Path, candidate: Path) -> dict[str, Path]:
    paths = {"pump_original": Path(original), "pump_candidate": Path(candidate)}
    paths.update({"dependency_" + name: path for name, path in E.L.CAPTURED.items()
                  if name != "pump_original"})
    paths.update({"producer_" + path.relative_to(ROOT).as_posix().replace("/", "__"): path
                  for path in PRODUCERS})
    return paths


def _inventory(root: Path) -> dict:
    return P.report_files_digest(root)


def _document(root: Path, name: str, inventory: dict, *, compressed=False):
    entry = inventory["files"].get(name)
    if entry is None:
        raise ValueError("missing report document: " + name)
    raw = P.regular_bytes(root / name, root=root)
    if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
        raise ValueError("report document changed: " + name)
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as handle:
            raw = handle.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("receipt decompression limit")
        def constant(value):
            raise ValueError("nonfinite JSON constant: " + value)
        def number(value):
            result = float(value)
            if not math.isfinite(result):
                raise ValueError("nonfinite JSON number")
            return result
        return json.loads(raw, object_pairs_hook=P._pairs,
                          parse_constant=constant, parse_float=number)
    return P.read_json(root / name)


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


def _same(left, right) -> bool:
    return E.same_json(left, right)


def verify_guided(report_dir: Path, original: Path, candidate: Path,
                  *, reexecute: bool = False) -> dict:
    failures, warnings, reexecuted_observations, reexecuted_cases = [], [], 0, 0
    result = {"schema": SCHEMA, "valid": False, "runtime_verified": False,
              "failures": failures, "warnings": warnings,
              "pool_count": 0, "selected_case_count": 0,
              "verified_observation_count": 0, "verified_receipt_count": 0,
              "reexecuted_observation_count": 0, "reexecuted_case_count": 0}
    try:
        if type(reexecute) is not bool:
            raise ValueError("reexecute flag must be boolean")
        report_dir = Path(report_dir).absolute()
        initial_inventory = _inventory(report_dir)
        summary = _document(report_dir, "summary.json", initial_inventory)
        attempt = _document(report_dir, "attempt.json", initial_inventory)
        complete = _document(report_dir, "complete.json", initial_inventory)
        pool = _document(report_dir, "pool.json", initial_inventory)
        selection = _document(report_dir, "selection.json", initial_inventory)
        selected = _document(report_dir, "cases.json", initial_inventory)
        summary_fields = {
            "schema", "tested_git_sha", "upstream_sha", "seed", "start_index",
            "pool_count", "corpus_limit", "pool_manifest_sha256",
            "selected_manifest_sha256", "selection_sha256", "artifact_manifest_sha256",
            "program_sha256", "all_input_sha256", "observation_counts",
            "selected_behavior_class_count", "unguided_behavior_class_count",
            "retained_behavior_class_gain", "selected_case_count",
            "classification_counts", "transaction_count_per_image",
            "original_successful_case_count", "negative_controls", "runtime_verified",
            "verification_scope", "reduced_counterexample_count", "cases", "summary_sha256",
        }
        if type(summary) is not dict or set(summary) != summary_fields:
            raise ValueError("summary fields")
        if (summary["schema"] != CAMPAIGN_SCHEMA
                or summary["verification_scope"] != "guided-executed-corpus"
                or type(summary["runtime_verified"]) is not bool):
            raise ValueError("summary scope")
        unsigned = dict(summary)
        embedded = unsigned.pop("summary_sha256")
        if embedded != hashlib.sha256(P.canonical_json(unsigned)).hexdigest():
            failures.append("summary-hash")
        attempt_fields = {"campaign_schema", "seed", "start_index", "pool_count",
                          "corpus_limit", "pool_manifest_sha256", "schema", "status",
                          "output_name"}
        if (type(attempt) is not dict or set(attempt) != attempt_fields
                or attempt["schema"] != P.SCHEMA or attempt["status"] != "in_progress"
                or attempt["campaign_schema"] != CAMPAIGN_SCHEMA
                or attempt["output_name"] != report_dir.name):
            raise ValueError("attempt context")
        for name in ("seed", "start_index", "pool_count", "corpus_limit", "pool_manifest_sha256"):
            if not _same(attempt[name], summary[name]):
                failures.append("attempt-summary:" + name)
        expected_complete = dict(
            attempt, status="complete", summary_sha256=summary["summary_sha256"],
            artifact_manifest_sha256=summary["artifact_manifest_sha256"],
            selection_sha256=summary["selection_sha256"],
            classification_counts=summary["classification_counts"])
        if not _same(expected_complete, complete):
            failures.append("completion-receipt")
        artifact_manifest = P.verify_artifacts(report_dir, summary["artifact_manifest_sha256"])

        pool_count, limit = summary["pool_count"], summary["corpus_limit"]
        if (type(pool_count) is not int or not 1 <= pool_count <= B.MAX_POOL_CASES
                or type(limit) is not int or not 1 <= limit <= min(B.MAX_CORPUS_CASES, pool_count)):
            raise ValueError("campaign bounds")
        expected_pool = C.generate_corpus(summary["seed"], pool_count, summary["start_index"])
        if not _same(pool, expected_pool):
            failures.append("pool-plan")
        if len(pool) != len({case["case_id"] for case in pool}):
            failures.append("duplicate-case-id")
        if hashlib.sha256(C.canonical(pool)).hexdigest() != summary["pool_manifest_sha256"]:
            failures.append("pool-manifest-hash")

        paths = _input_paths(original, candidate)
        declared = summary["all_input_sha256"]
        if type(declared) is not dict or set(declared) != set(paths):
            raise ValueError("input-set")
        initial_inputs = {name: hashlib.sha256(P.regular_bytes(path)).hexdigest()
                          for name, path in paths.items()}
        if not _same(initial_inputs, declared):
            failures.extend("input-hash:" + name for name in paths
                            if initial_inputs[name] != declared.get(name))
        if declared["pump_original"] != E.CANONICAL_ORIGINAL_SHA256:
            failures.append("canonical-original")
        if not _same(summary["program_sha256"],
                     {"original": declared["pump_original"], "candidate": declared["pump_candidate"]}):
            failures.append("program-hashes")
        for path, value in RUNTIME_SOURCE_HASHES.items():
            if hashlib.sha256(P.regular_bytes(path)).hexdigest() != value:
                failures.append("loaded-source:" + path)

        expected_artifacts = {"pool.json", "selection.json", "cases.json"}
        observations = []
        for index, case in enumerate(pool):
            name = f"observations/{index:04d}-{case['case_id']}.json.gz"
            expected_artifacts.add(name)
            observation = _document(report_dir, name, initial_inventory, compressed=True)
            observations.append(observation)
            failures.extend(f"observation-{index}:" + item
                            for item in B.validate_observation(observation, case))
        result["verified_observation_count"] = len(observations)
        expected_selection = B.select_corpus(pool, observations, limit)
        if not _same(selection, expected_selection):
            failures.append("selection-recomputation")
        expected_selected = B.selected_cases(pool, expected_selection)
        if not _same(selected, expected_selected):
            failures.append("selected-cases")
        if hashlib.sha256(C.canonical(selected)).hexdigest() != summary["selected_manifest_sha256"]:
            failures.append("selected-manifest-hash")
        for name in ("selection_sha256", "selected_behavior_class_count",
                     "unguided_behavior_class_count"):
            if not _same(summary[name], expected_selection[name]):
                failures.append("summary-selection:" + name)
        gain = (expected_selection["selected_behavior_class_count"]
                - expected_selection["unguided_behavior_class_count"])
        if summary["retained_behavior_class_gain"] != gain:
            failures.append("retained-class-gain")

        observation_counts = Counter(row["classification"] for row in observations)
        expected_observation_counts = {name: observation_counts.get(name, 0) for name in
                                       ("observed_behavior", "unsupported_fixture", "infrastructure_failure")}
        if not _same(summary["observation_counts"], expected_observation_counts):
            failures.append("observation-counts")

        retained_results = []
        rows = summary["cases"]
        if type(rows) is not list or len(rows) != len(selected):
            raise ValueError("selected summary count")
        for rank, case in enumerate(selected):
            name = f"receipts/{rank:04d}-{case['case_id']}.json.gz"
            expected_artifacts.add(name)
            execution = _document(report_dir, name, initial_inventory, compressed=True)
            retained_results.append(execution)
            failures.extend(f"receipt-{rank}:" + item for item in E.validate_result(execution, case))
            if not _same(_case_summary(execution), rows[rank]):
                failures.append(f"receipt-summary:{rank}")
        result["verified_receipt_count"] = len(retained_results)

        actual_observations, actual_results = observations, retained_results
        if reexecute and not failures:
            with P.InputSnapshot(paths, declared) as snapshot:
                images = {name: snapshot.paths["dependency_" + name]
                          for name in E.L.CAPTURED if name != "pump_original"}
                actual_observations = []
                for index, case in enumerate(pool):
                    value = B.observe_case(case, snapshot.paths["pump_original"], images)
                    reexecuted_observations += 1
                    if not _same(value, observations[index]):
                        failures.append(f"observation-reexecution:{index}")
                    actual_observations.append(value)
                actual_results = []
                for rank, case in enumerate(selected):
                    value = E.execute_case(case, snapshot.paths["pump_original"],
                                           snapshot.paths["pump_candidate"], images)
                    reexecuted_cases += 1
                    if not _same(value, retained_results[rank]):
                        failures.append(f"differential-reexecution:{rank}")
                    actual_results.append(value)
                if snapshot.changed_sources():
                    failures.append("inputs-changed-during-reexecution")

        classifications = ("equal_observed_behavior", "different_behavior",
                           "unsupported_fixture", "infrastructure_failure")
        counts = Counter(row["classification"] for row in actual_results)
        expected_counts = {name: counts.get(name, 0) for name in classifications}
        if not _same(summary["classification_counts"], expected_counts):
            failures.append("classification-counts")
        executed = [row for row in actual_results if "original" in row]
        controls = _negative_controls(executed[0]) if executed else {"available": False}
        if not _same(summary["negative_controls"], controls):
            failures.append("negative-controls")
        aggregates = {
            "selected_case_count": len(selected),
            "transaction_count_per_image": sum(len(row["original"]["receipts"]) for row in executed),
            "original_successful_case_count": sum(all(item["error"] is None
                for item in row["original"]["receipts"]) for row in executed),
        }
        for name, value in aggregates.items():
            if summary[name] != value:
                failures.append(name)
        expected_runtime = (bool(executed)
                            and expected_observation_counts["infrastructure_failure"] == 0
                            and expected_counts["infrastructure_failure"] == 0
                            and controls.get("all_detected") is True)
        if summary["runtime_verified"] is not expected_runtime:
            failures.append("runtime-summary")

        manifests = sorted(name for name in initial_inventory["files"]
                           if name.startswith("counterexamples/") and name.endswith("/manifest.json"))
        if len(manifests) != summary["reduced_counterexample_count"]:
            failures.append("reduction-count")
        for name in manifests:
            prefix = name.rsplit("/", 1)[0]
            expected_artifacts.update((name, prefix + "/case.json", prefix + "/reduction.json.gz"))
            manifest = _document(report_dir, name, initial_inventory)
            reduced_case = _document(report_dir, prefix + "/case.json", initial_inventory)
            reduction = _document(report_dir, prefix + "/reduction.json.gz", initial_inventory, compressed=True)
            original_case = next((case for case in selected
                                  if case["case_id"] == manifest.get("original_case_id")), None)
            original_result = next((row for row in actual_results
                                    if row["case_id"] == manifest.get("original_case_id")), None)
            if (manifest.get("schema") != "pump-admin-cto-counterexample-manifest-v1"
                    or original_case is None or original_result is None
                    or manifest.get("reduced_case_id") != reduced_case.get("case_id")
                    or not _same(manifest.get("program_sha256"), summary["program_sha256"])
                    or not _same(reduction.get("case"), reduced_case)):
                failures.append("reduction-manifest:" + prefix)
            else:
                failures.extend("reduction:" + item for item in
                                R.validate_reduction(reduction, original_case, original_result))
        if set(artifact_manifest["files"]) != expected_artifacts:
            failures.append("artifact-membership")
        final_inputs = {name: hashlib.sha256(P.regular_bytes(path)).hexdigest()
                        for name, path in paths.items()}
        if not _same(initial_inputs, final_inputs):
            failures.append("inputs-changed")
        if not _same(initial_inventory, _inventory(report_dir)):
            failures.append("report-changed")
        result["pool_count"] = len(pool)
        result["selected_case_count"] = len(selected)
        result["runtime_verified"] = expected_runtime and not failures
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            OverflowError, EOFError) as error:
        failures.append("report-admission:" + type(error).__name__ + ":" + str(error))
    result.update(valid=not failures, failures=sorted(set(failures)),
                  reexecuted_observation_count=reexecuted_observations,
                  reexecuted_case_count=reexecuted_cases)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reexecute", action="store_true")
    args = parser.parse_args()
    result = verify_guided(args.report, args.original, args.candidate,
                           reexecute=args.reexecute)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
