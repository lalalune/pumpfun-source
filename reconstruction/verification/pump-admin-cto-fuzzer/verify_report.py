#!/usr/bin/env python3
"""Independently admit retained Pump Admin CTO fuzz evidence."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import os
import stat
import sys
import types
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_corpus_path = HERE / "corpus.py"
_corpus_raw = _corpus_path.read_bytes()
_corpus_name = "_pump_fuzz_corpus_" + uuid.uuid4().hex
P = types.ModuleType(_corpus_name)
P.__file__ = str(_corpus_path)
P.__source_path__ = str(_corpus_path)
P.__source_sha256__ = hashlib.sha256(_corpus_raw).hexdigest()
sys.modules[_corpus_name] = P
try:
    exec(compile(_corpus_raw, str(_corpus_path), "exec"), P.__dict__)
finally:
    sys.modules.pop(_corpus_name, None)
C = P.source_module("case_model", HERE / "case_model.py")
E = P.source_module("executor", HERE / "executor.py", imports={"case_model": C, "corpus": P})
R = P.source_module("reducer", HERE / "reducer.py", imports={"case_model": C, "executor": E, "corpus": P})

SCHEMA = "pump-admin-cto-fuzz-verification-v1"
PRODUCERS = (
    HERE / "case_model.py", HERE / "executor.py", HERE / "reducer.py",
    HERE / "corpus.py", HERE / "campaign.py", HERE / "verify_report.py",
    ROOT / "reconstruction/verification/pump-admin-cto-stateful/lifecycle.py",
    E.L.IDL_PATH, E.L.CONFIG_PATH, ROOT / "scripts/pump_differential_output.py",
)
RUNTIME_SOURCE_HASHES = dict(E.RUNTIME_SOURCE_HASHES)
for _module in (P, C, E, R):
    _path, _digest = _module.__source_path__, _module.__source_sha256__
    if _path in RUNTIME_SOURCE_HASHES and RUNTIME_SOURCE_HASHES[_path] != _digest:
        raise ValueError("source bytes changed between private graph loads: " + _path)
    RUNTIME_SOURCE_HASHES[_path] = _digest
for _path, _digest in getattr(R, "RUNTIME_SOURCE_HASHES", {}).items():
    if _path in RUNTIME_SOURCE_HASHES and RUNTIME_SOURCE_HASHES[_path] != _digest:
        raise ValueError("reducer private graph source disagrees: " + _path)
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


def _read(path):
    """Read a stable regular file without following a final symbolic link."""
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("nonregular input: " + str(path))
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        raw = handle.read()
        after = os.fstat(handle.fileno())
    current = path.lstat()
    signature = lambda value: (value.st_dev, value.st_ino, value.st_size,
                               value.st_mtime_ns, value.st_ctime_ns, value.st_mode)
    if (not stat.S_ISREG(current.st_mode) or signature(before) != signature(after)
            or signature(after) != signature(current)):
        raise ValueError("input changed while reading: " + str(path))
    return raw


def _inventory(root):
    root = Path(root)
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError("report must be an ordinary directory")
    rows = {}
    for path in sorted(root.rglob("*")):
        mode = path.lstat().st_mode
        name = path.relative_to(root).as_posix()
        if stat.S_ISDIR(mode):
            rows[name + "/"] = "directory"
        elif stat.S_ISREG(mode):
            rows[name] = hashlib.sha256(_read(path)).hexdigest()
        else:
            raise ValueError("report contains link or special file: " + name)
    return rows


def _json(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def number(value):
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("nonfinite JSON number")
        return result
    def constant(value):
        raise ValueError("nonfinite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_float=number, parse_constant=constant)


def _document(root, name, inventory, *, compressed=False):
    raw = _read(root / name)
    if hashlib.sha256(raw).hexdigest() != inventory.get(name):
        raise ValueError("report input changed: " + name)
    if compressed:
        with gzip.GzipFile(fileobj=io.BytesIO(raw)) as handle:
            raw = handle.read(64 * 1024 * 1024 + 1)
        if len(raw) > 64 * 1024 * 1024:
            raise ValueError("receipt decompression limit")
    return _json(raw)


def _reclassify(result: dict, case=None) -> tuple[str, list[str]]:
    case = result.get("case") if case is None else case
    failures = E.validate_result(result, case)
    return result.get("classification", "infrastructure_failure"), failures


def _summary_row(result: dict) -> dict:
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
    import copy
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


def _nonnegative(value):
    return type(value) is int and value >= 0


def verify_campaign(report_dir: Path, original: Path, candidate: Path,
                    *, reexecute: bool = False, provenance_only: bool = False) -> dict:
    failures, warnings, retained, reexecuted = [], [], {}, 0
    result = {"schema": SCHEMA, "valid": False, "runtime_verified": False,
              "failures": [], "warnings": warnings, "case_count": 0,
              "verified_receipt_count": 0, "reexecuted_case_count": 0,
              "verification_scope": "invalid"}
    try:
        if type(reexecute) is not bool or type(provenance_only) is not bool:
            raise ValueError("verification flags must be bool")
        report_dir = Path(report_dir).absolute()
        initial_inventory = _inventory(report_dir)
        summary = _document(report_dir, "summary.json", initial_inventory)
        complete = _document(report_dir, "complete.json", initial_inventory)
        attempt = _document(report_dir, "attempt.json", initial_inventory)
        cases = _document(report_dir, "cases.json", initial_inventory)
        if (type(summary) is not dict or type(complete) is not dict
                or type(attempt) is not dict or type(cases) is not list):
            raise ValueError("report document shapes")
        summary_fields = {"schema", "tested_git_sha", "upstream_sha", "seed", "start_index", "case_count",
                          "case_manifest_sha256", "artifact_manifest_sha256", "program_sha256",
                          "all_input_sha256", "classification_counts", "transaction_count_per_image",
                          "executed_case_count", "original_successful_case_count", "negative_controls",
                          "runtime_verified", "verification_scope", "reduced_counterexample_count",
                          "detailed_receipts", "cases", "summary_sha256"}
        if set(summary) != summary_fields:
            raise ValueError("summary fields")
        if type(summary["runtime_verified"]) is not bool or summary["verification_scope"] != "executed-corpus":
            raise ValueError("producer runtime scope")
        if set(attempt) != {"campaign_schema", "seed", "start_index", "count", "case_manifest_sha256",
                            "schema", "status", "output_name"}:
            raise ValueError("attempt fields")
        if (attempt["schema"] != P.SCHEMA or attempt["status"] != "in_progress"
                or attempt["campaign_schema"] != "pump-admin-cto-fuzz-campaign-v2"
                or attempt["output_name"] != report_dir.name):
            raise ValueError("attempt context")
        for name, summary_name in (("seed", "seed"), ("start_index", "start_index"),
                                   ("count", "case_count"), ("case_manifest_sha256", "case_manifest_sha256")):
            if not E.same_json(attempt[name], summary[summary_name]):
                raise ValueError("attempt/summary binding: " + name)
        expected_complete = dict(attempt, status="complete", summary_sha256=summary["summary_sha256"],
                                 artifact_manifest_sha256=summary["artifact_manifest_sha256"],
                                 classification_counts=summary["classification_counts"])
        if not E.same_json(expected_complete, complete):
            raise ValueError("completion/attempt binding")
        if summary.get("schema") != "pump-admin-cto-fuzz-campaign-v2":
            failures.append("summary-schema")
        embedded = summary.get("summary_sha256")
        unsigned = dict(summary)
        unsigned.pop("summary_sha256", None)
        if embedded != hashlib.sha256(P.canonical_json(unsigned)).hexdigest():
            failures.append("summary-hash")
        if complete.get("status") != "complete" or complete.get("summary_sha256") != embedded:
            failures.append("completion-receipt")
        artifact_manifest = P.verify_artifacts(report_dir, summary["artifact_manifest_sha256"])
        count = summary.get("case_count")
        if type(count) is not int or not 1 <= count <= 1000:
            raise ValueError("case count must be 1..1000")
        expected_cases = C.generate_corpus(summary["seed"], count, summary["start_index"])
        if not E.same_json(cases, expected_cases):
            failures.append("case-manifest-plan")
        if len({c["case_id"] for c in cases}) != count or len(cases) != count:
            failures.append("case-count")
        rows = summary.get("cases")
        if type(rows) is not list or len(rows) != count:
            raise ValueError("case summary count")
        if hashlib.sha256(C.canonical(cases)).hexdigest() != summary.get("case_manifest_sha256"):
            failures.append("case-manifest-hash")
        if type(summary.get("detailed_receipts")) is not bool:
            raise ValueError("detailed receipt flag")
        for name in ("transaction_count_per_image", "executed_case_count", "original_successful_case_count", "reduced_counterexample_count"):
            if not _nonnegative(summary.get(name)):
                raise ValueError("summary count type: " + name)
        result["case_count"] = len(cases)
        paths = _input_paths(original, candidate)
        declared = summary.get("all_input_sha256")
        if type(declared) is not dict or set(paths) != set(declared):
            raise ValueError("input-set")
        initial_inputs = {name: hashlib.sha256(_read(path)).hexdigest() for name, path in paths.items()}
        if declared.get("pump_original") != E.CANONICAL_ORIGINAL_SHA256:
            failures.append("canonical-original-image")
        if not E.same_json(initial_inputs, declared):
            failures.extend("input-hash:" + name for name in paths if initial_inputs[name] != declared.get(name))
        for path, digest in RUNTIME_SOURCE_HASHES.items():
            if hashlib.sha256(_read(path)).hexdigest() != digest:
                failures.append("loaded-source-hash:" + path)
        if not E.same_json(summary.get("program_sha256"),
                           {"original": declared["pump_original"], "candidate": declared["pump_candidate"]}):
            failures.append("program-hash-summary")
        expected_artifacts = {"cases.json"}
        if summary["detailed_receipts"]:
            for index, case in enumerate(cases):
                name = f"receipts/{index:04d}-{case['case_id']}.json.gz"
                expected_artifacts.add(name)
                execution = _document(report_dir, name, initial_inventory, compressed=True)
                retained[case["case_id"]] = execution
                failures.extend(f"receipt-{index}:" + item for item in E.validate_result(execution, case))
                if not E.same_json(_summary_row(execution), rows[index]):
                    failures.append(f"receipt-summary:{index}")
        elif not reexecute and not provenance_only:
            failures.append("detailed-receipts-or-reexecution-required")
        else:
            warnings.append("compact report: retained transaction receipts absent")
        if not summary["detailed_receipts"]:
            for index, case in enumerate(cases):
                name = f"progress/{index:04d}-{case['case_id']}.json"
                expected_artifacts.add(name)
                if not E.same_json(_document(report_dir, name, initial_inventory), rows[index]):
                    failures.append(f"progress-summary:{index}")
        actual_results = dict(retained)
        if reexecute and not failures:
            with P.InputSnapshot(paths, declared) as snapshot:
                images = {name: snapshot.paths["dependency_" + name]
                          for name in E.L.CAPTURED if name != "pump_original"}
                for index, case in enumerate(cases):
                    execution = E.execute_case(case, snapshot.paths["pump_original"],
                                               snapshot.paths["pump_candidate"], images)
                    reexecuted += 1
                    failures.extend(f"reexecution-{index}:" + item for item in E.validate_result(execution, case))
                    if not E.same_json(_summary_row(execution), rows[index]):
                        failures.append(f"reexecution:{index}")
                    if case["case_id"] in retained and not E.same_json(execution, retained[case["case_id"]]):
                        failures.append(f"reexecution-receipt:{index}")
                    actual_results[case["case_id"]] = execution
                if snapshot.changed_sources():
                    failures.append("inputs-changed-during-verification")
        classifications = ("equal_observed_behavior", "different_behavior", "unsupported_fixture", "infrastructure_failure")
        counts = {name: 0 for name in classifications}
        for row in rows:
            if type(row) is not dict or row.get("classification") not in counts:
                raise ValueError("summary classification")
            counts[row["classification"]] += 1
        if not E.same_json(counts, summary.get("classification_counts")):
            failures.append("classification-counts")
        runtime = len(actual_results) == count
        if runtime:
            executed = [actual_results[c["case_id"]] for c in cases if "original" in actual_results[c["case_id"]]]
            if not executed:
                failures.append("no-executed-case")
            else:
                if not E.same_json(_negative_controls(executed[0]), summary.get("negative_controls")):
                    failures.append("negative-controls")
            expected_runtime = bool(executed) and counts["infrastructure_failure"] == 0 and bool(executed and _negative_controls(executed[0])["all_detected"])
            if not E.same_json(summary["runtime_verified"], expected_runtime):
                failures.append("producer-runtime-summary")
            aggregates = {
                "executed_case_count": len(executed),
                "transaction_count_per_image": sum(len(v["original"]["receipts"]) for v in executed),
                "original_successful_case_count": sum(all(r["error"] is None for r in v["original"]["receipts"]) for v in executed),
            }
            for name, actual in aggregates.items():
                if not E.same_json(actual, summary[name]):
                    failures.append(name)
        # A reduction is admitted only as a case-bound retained final witness.
        # Offline attempt summaries cannot establish executed one-minimality.
        manifests = sorted(name for name in initial_inventory if name.startswith("counterexamples/") and name.endswith("/manifest.json"))
        if len(manifests) != summary["reduced_counterexample_count"]:
            failures.append("reduced-counterexample-count")
        reduced_original_ids = set()
        for name in manifests:
            manifest = _document(report_dir, name, initial_inventory)
            prefix = name.rsplit("/", 1)[0]
            expected_artifacts.update((name, prefix + "/case.json", prefix + "/reduction.json.gz"))
            if manifest.get("original_case_id") in reduced_original_ids:
                failures.append("duplicate-reduction-original-case")
            reduced_original_ids.add(manifest.get("original_case_id"))
            reduced = _document(report_dir, prefix + "/case.json", initial_inventory)
            reduction = _document(report_dir, prefix + "/reduction.json.gz", initial_inventory, compressed=True)
            C.validate_case(reduced)
            if (manifest.get("schema") != "pump-admin-cto-counterexample-manifest-v1"
                    or manifest.get("reduced_case_id") != reduced["case_id"]
                    or prefix != "counterexamples/" + reduced["case_id"]
                    or not E.same_json(manifest.get("program_sha256"), summary["program_sha256"])
                    or manifest.get("original_seed") != summary["seed"]
                    or manifest.get("original_case_id") not in {r["case_id"] for r in rows if r["classification"] == "different_behavior"}
                    or not E.same_json(reduction.get("case"), reduced)
                    or reduction.get("original_case_id") != manifest["original_case_id"]
                    or reduction.get("reduced_case_id") != reduced["case_id"]):
                failures.append("reduction-manifest:" + prefix)
            failures.extend("reduction-witness:" + item for item in E.validate_result(reduction["result"], reduced))
            if reduction["result"]["classification"] != "different_behavior":
                failures.append("reduction-not-different:" + prefix)
            if not E.same_json(manifest.get("minimality"), reduction.get("minimality")):
                failures.append("reduction-minimality-binding:" + prefix)
            original_case = next((c for c in cases if c["case_id"] == manifest["original_case_id"]), None)
            if original_case is None:
                raise ValueError("reduction original case is outside corpus")
            original_result = actual_results.get(original_case["case_id"])
            if original_result is None:
                failures.append("reduction-original-receipt-required:" + prefix)
            else:
                evaluate = None
                if reexecute:
                    with P.InputSnapshot(paths, declared) as reduction_snapshot:
                        reduction_images = {name: reduction_snapshot.paths["dependency_" + name]
                                            for name in E.L.CAPTURED if name != "pump_original"}
                        def evaluate(value):
                            return E.execute_case(value, reduction_snapshot.paths["pump_original"],
                                                  reduction_snapshot.paths["pump_candidate"], reduction_images)
                        failures.extend("reduction:" + item for item in R.validate_reduction(
                            reduction, original_case, original_result, evaluate=evaluate))
                        if reduction_snapshot.changed_sources():
                            failures.append("reduction-inputs-changed")
                else:
                    failures.extend("reduction:" + item for item in R.validate_reduction(
                        reduction, original_case, original_result))
        if set(artifact_manifest["files"]) != expected_artifacts:
            failures.append("artifact-membership-for-plan")
        if manifests:
            warnings.append("reduction final witnesses checked; one-minimality requires independent reduction replay")
        final_inputs = {name: hashlib.sha256(_read(path)).hexdigest() for name, path in paths.items()}
        if not E.same_json(initial_inputs, final_inputs):
            failures.append("inputs-changed-during-verification")
        for path, digest in RUNTIME_SOURCE_HASHES.items():
            if hashlib.sha256(_read(path)).hexdigest() != digest:
                failures.append("loaded-source-changed:" + path)
        if not E.same_json(initial_inventory, _inventory(report_dir)):
            failures.append("report-changed-during-verification")
        result["runtime_verified"] = runtime and not failures
        result["verification_scope"] = ("receipts-and-reexecution" if reexecute else "receipts-and-provenance") if runtime else "provenance-only"
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, OverflowError, EOFError) as error:
        failures.append("report-admission:" + type(error).__name__ + ":" + str(error))
    result.update(valid=not failures, failures=sorted(set(failures)),
                  verified_receipt_count=len(retained), reexecuted_case_count=reexecuted)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reexecute", action="store_true")
    parser.add_argument("--provenance-only", action="store_true",
                        help="admit compact integrity only; never grants runtime verification")
    args = parser.parse_args()
    result = verify_campaign(args.report, args.original, args.candidate,
                             reexecute=args.reexecute, provenance_only=args.provenance_only)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
