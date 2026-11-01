#!/usr/bin/env python3
"""Deterministic execution-backed reduction for Admin CTO counterexamples."""
from __future__ import annotations

import copy
import hashlib
import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_pfile = HERE / "corpus.py"
if _pfile.is_symlink():
    raise ValueError("corpus source must not be a symlink")
_pbytes = _pfile.read_bytes()
P = types.ModuleType("_pump_fuzz_reducer_corpus")
P.__file__ = str(_pfile)
P.__source_path__ = str(_pfile)
P.__source_sha256__ = hashlib.sha256(_pbytes).hexdigest()
exec(compile(_pbytes, str(_pfile), "exec", dont_inherit=True, optimize=0), P.__dict__)
C = P.source_module("reducer_case_model", HERE / "case_model.py")
case_identity, validate_case = C.case_identity, C.validate_case
RUNTIME_SOURCE_HASHES = {module.__source_path__: module.__source_sha256__ for module in (P, C)}

SCHEMA = "pump-admin-cto-counterexample-reduction-v1"
STEP_OPTIONALS = (
    "new", "new_none", "holder", "fee", "wrong", "readonly",
    "replace_accounts", "drop_accounts", "instruction_mutation",
)


def _leaf_count(value) -> int:
    if isinstance(value, dict):
        return sum(_leaf_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(_leaf_count(item) for item in value)
    return 1


def _numeric_score(value) -> int:
    if isinstance(value, dict):
        return sum(_numeric_score(item) for item in value.values())
    if isinstance(value, list):
        return sum(_numeric_score(item) for item in value)
    return value if type(value) is int and value >= 0 else 0


def complexity(case: dict) -> dict:
    optional = sum(sum(key in step for key in STEP_OPTIONALS) for step in case["steps"])
    config = {key: value for key, value in case["config"].items() if key != "mints"}
    step_fields = [{key: value for key, value in step.items() if key not in ("name", "op")}
                   for step in case["steps"]]
    values = [config, case["initial_mutations"], step_fields]
    return {
        "modified_accounts": len({row.get("target") for row in case["initial_mutations"]}),
        "modified_fields": sum(_leaf_count(value) for value in values),
        "instruction_sequence_length": len(case["steps"]),
        "optional_arguments": optional,
        "numeric_score": sum(_numeric_score(value) for value in values),
    }


def complexity_tuple(case: dict) -> tuple[int, ...]:
    value = complexity(case)
    return tuple(value[key] for key in (
        "modified_accounts", "modified_fields", "instruction_sequence_length",
        "optional_arguments", "numeric_score",
    ))


def mismatch_property(result: dict) -> dict | None:
    """Return the exact observable divergence the reducer must retain."""
    if result.get("classification") != "different_behavior":
        return None
    if (not isinstance(result.get("mismatch_fields"), list)
            or not result["mismatch_fields"]
            or any(not isinstance(item, str) or not item for item in result["mismatch_fields"])):
        return None
    pairs = []
    left = {row["step"]: row for row in result["original"]["receipts"]}
    right = {row["step"]: row for row in result["candidate"]["receipts"]}
    for comparison in result.get("comparison", []):
        if comparison["mismatch_fields"]:
            name = comparison["step"]
            pairs.append({
                "step": name,
                "fields": sorted(comparison["mismatch_fields"]),
                "original_outcome": left[name]["outcome"],
                "candidate_outcome": right[name]["outcome"],
            })
    top = sorted(field for field in result.get("mismatch_fields", []) if ":" not in field)
    return {"top_level_fields": top, "steps": pairs} if top or pairs else None


def _with_identity(case: dict) -> dict:
    changed = copy.deepcopy(case)
    changed["case_id"] = case_identity(changed)
    return validate_case(changed)


def _smaller_numbers(value: int):
    if type(value) is not int or value <= 0:
        return []
    return list(dict.fromkeys(item for item in (0, 1, value // 2) if item < value))


def immediate_reductions(case: dict) -> list[dict]:
    """Enumerate the stable, local reduction neighborhood for one case."""
    candidates = []

    def add(changed):
        try:
            value = _with_identity(changed)
        except (KeyError, TypeError, ValueError):
            return
        if complexity_tuple(value) < complexity_tuple(case):
            candidates.append(value)

    for index in range(len(case["initial_mutations"])):
        changed = copy.deepcopy(case)
        del changed["initial_mutations"][index]
        add(changed)
    if len(case["steps"]) > 1:
        for index in range(len(case["steps"])):
            changed = copy.deepcopy(case)
            del changed["steps"][index]
            add(changed)
    for index, step in enumerate(case["steps"]):
        for key in STEP_OPTIONALS:
            if key in step:
                changed = copy.deepcopy(case)
                del changed["steps"][index][key]
                add(changed)
        for key in ("readonly", "replace_accounts"):
            for item in range(len(step.get(key, []))):
                changed = copy.deepcopy(case)
                del changed["steps"][index][key][item]
                if not changed["steps"][index][key]:
                    del changed["steps"][index][key]
                add(changed)
        for key in ("new", "fee", "drop_accounts"):
            for smaller in _smaller_numbers(step.get(key)):
                changed = copy.deepcopy(case)
                changed["steps"][index][key] = smaller
                add(changed)
        mutation = step.get("instruction_mutation")
        if mutation and type(mutation.get("value")) is int:
            for smaller in _smaller_numbers(mutation["value"]):
                changed = copy.deepcopy(case)
                changed["steps"][index]["instruction_mutation"]["value"] = smaller
                add(changed)
    for index, mutation in enumerate(case["initial_mutations"]):
        for key in ("value", "offset"):
            for smaller in _smaller_numbers(mutation.get(key)):
                changed = copy.deepcopy(case)
                changed["initial_mutations"][index][key] = smaller
                add(changed)
    for key, value in case["config"].items():
        if key != "mints":
            changed = copy.deepcopy(case)
            del changed["config"][key]
            add(changed)
        for smaller in _smaller_numbers(value):
            changed = copy.deepcopy(case)
            changed["config"][key] = smaller
            add(changed)
    unique = {row["case_id"]: row for row in candidates}
    return [unique[key] for key in sorted(unique)]


def reduce_case(case: dict, evaluate, *, max_trials: int = 500) -> dict:
    """Greedily reduce a mismatch and audit its final local neighborhood."""
    if type(max_trials) is not int or not 1 <= max_trials <= 10_000:
        raise ValueError("max_trials must be between 1 and 10000")
    original = validate_case(copy.deepcopy(case))
    first = evaluate(original)
    target = mismatch_property(first)
    if target is None:
        raise ValueError("initial case does not demonstrate different behavior")
    cache = {original["case_id"]: first}
    attempts, accepted, current = [], [], original

    def trial(candidate):
        if candidate["case_id"] in cache:
            return cache[candidate["case_id"]], False
        if len(cache) >= max_trials + 1:
            return None, False
        result = evaluate(candidate)
        cache[candidate["case_id"]] = result
        return result, True

    while True:
        changed = False
        for candidate in immediate_reductions(current):
            result, executed = trial(candidate)
            if result is None:
                break
            kept = mismatch_property(result) == target
            attempts.append({"case_id": candidate["case_id"], "executed": executed,
                             "preserved_property": kept,
                             "classification": result.get("classification")})
            if kept:
                accepted.append({"from": current["case_id"], "to": candidate["case_id"],
                                 "complexity": complexity(candidate)})
                current = candidate
                changed = True
                break
        if not changed:
            break

    unchecked, preserving = [], []
    for candidate in immediate_reductions(current):
        result, executed = trial(candidate)
        if result is None or result.get("classification") in ("unsupported_fixture", "infrastructure_failure"):
            unchecked.append(candidate["case_id"])
            continue
        kept = mismatch_property(result) == target
        attempts.append({"case_id": candidate["case_id"], "executed": executed,
                         "preserved_property": kept,
                         "classification": result.get("classification"), "audit": True})
        if kept:
            preserving.append(candidate["case_id"])
    one_minimal = not unchecked and not preserving
    return {
        "schema": SCHEMA,
        "original_case_id": original["case_id"],
        "reduced_case_id": current["case_id"],
        "mismatch_property": target,
        "original_complexity": complexity(original),
        "reduced_complexity": complexity(current),
        "executions": len(cache),
        "max_trials": max_trials,
        "accepted_reductions": accepted,
        "attempts": attempts,
        "minimality": {
            "criterion": "one-minimal over immediate_reductions() neighborhood",
            "demonstrated": one_minimal,
            "unchecked_case_ids": unchecked,
            "preserving_case_ids": preserving,
        },
        "case": current,
        "result": cache[current["case_id"]],
    }


def validate_reduction(reduction: dict, original_case: dict, original_result: dict,
                       *, evaluate=None) -> list[str]:
    """Check a retained witness; prove its local minimum only on explicit replay."""
    failures = []
    try:
        original_case = validate_case(copy.deepcopy(original_case))
        if not isinstance(reduction, dict) or reduction.get("schema") != SCHEMA:
            return ["reduction-schema"]
        case = validate_case(copy.deepcopy(reduction["case"]))
        if reduction["original_case_id"] != original_case["case_id"] or reduction["reduced_case_id"] != case["case_id"]:
            failures.append("reduction-case-identity")
        target = mismatch_property(original_result)
        if target is None or reduction["mismatch_property"] != target or mismatch_property(reduction["result"]) != target:
            failures.append("reduction-mismatch-property")
        for name, expected in (("original_complexity", complexity(original_case)),
                               ("reduced_complexity", complexity(case))):
            observed = reduction[name]
            if (not isinstance(observed, dict) or set(observed) != set(expected)
                    or any(type(value) is not int or value < 0 for value in observed.values())
                    or observed != expected):
                failures.append("reduction-" + name)
        budget, executions = reduction["max_trials"], reduction["executions"]
        if type(budget) is not int or not 1 <= budget <= 10_000 or type(executions) is not int or not 1 <= executions <= budget + 1:
            failures.append("reduction-execution-budget")
        accepted, attempts = reduction["accepted_reductions"], reduction["attempts"]
        if not isinstance(accepted, list) or not isinstance(attempts, list):
            return failures + ["reduction-trials"]
        previous = original_case["case_id"]
        previous_complexity = complexity_tuple(original_case)
        for row in accepted:
            current_complexity = row["complexity"]
            if (row["from"] != previous or not isinstance(row["to"], str)
                    or not isinstance(current_complexity, dict)
                    or set(current_complexity) != set(complexity(case))
                    or any(type(v) is not int or v < 0 for v in current_complexity.values())):
                failures.append("reduction-accepted-chain")
                break
            order = tuple(current_complexity[k] for k in complexity(case))
            if order >= previous_complexity:
                failures.append("reduction-complexity-order")
            previous, previous_complexity = row["to"], order
        if previous != case["case_id"] or previous_complexity != complexity_tuple(case):
            failures.append("reduction-final-chain")
        for row in attempts:
            if (not isinstance(row, dict) or type(row.get("executed")) is not bool
                    or type(row.get("preserved_property")) is not bool
                    or not isinstance(row.get("case_id"), str)
                    or row.get("classification") not in ("equal_observed_behavior", "different_behavior", "unsupported_fixture", "infrastructure_failure")
                    or ("audit" in row and type(row["audit"]) is not bool)):
                failures.append("reduction-attempt-type")
                break
        minimality = reduction["minimality"]
        if (not isinstance(minimality, dict) or set(minimality) != {"criterion", "demonstrated", "unchecked_case_ids", "preserving_case_ids"}
                or minimality["criterion"] != "one-minimal over immediate_reductions() neighborhood"
                or type(minimality["demonstrated"]) is not bool
                or any(not isinstance(minimality[k], list) or any(not isinstance(v, str) for v in minimality[k])
                       for k in ("unchecked_case_ids", "preserving_case_ids"))):
            return failures + ["reduction-minimality-type"]
        if minimality["demonstrated"] and (minimality["unchecked_case_ids"] or minimality["preserving_case_ids"]):
            failures.append("reduction-incomplete-minimality")
        if evaluate is not None:
            replayed = evaluate(case)
            if mismatch_property(replayed) != target:
                failures.append("reduction-witness-reexecution")
            if minimality["demonstrated"]:
                neighbors = immediate_reductions(case)
                if len(neighbors) > 1000:
                    failures.append("reduction-neighborhood-budget")
                else:
                    for neighbor in neighbors:
                        result = evaluate(neighbor)
                        if result.get("classification") in ("unsupported_fixture", "infrastructure_failure"):
                            failures.append("reduction-unchecked-neighbor")
                        elif mismatch_property(result) == target:
                            failures.append("reduction-preserving-neighbor")
    except (KeyError, TypeError, ValueError, IndexError):
        failures.append("reduction-malformed")
    return sorted(set(failures))
