"""Canonical captured-original behavior fingerprints and corpus selection.

The fingerprints in this module partition finite transaction observations.
They are deliberately not called code coverage and do not imply bytecode paths.
"""
from __future__ import annotations

import base64
import collections
import copy
import hashlib
import json
from pathlib import Path

import case_model as C
import executor as E


FINGERPRINT_SCHEMA = "pump-admin-cto-behavior-fingerprint-v1"
OBSERVATION_SCHEMA = "pump-admin-cto-original-observation-v1"
SELECTION_SCHEMA = "pump-admin-cto-guided-selection-v1"
MAX_POOL_CASES = 512
MAX_CORPUS_CASES = 128


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _direction(before: int, after: int) -> str:
    return "decrease" if after < before else "increase" if after > before else "equal"


def _owner_class(owner: str | None) -> str:
    known = {
        str(E.L.SYSTEM): "system",
        str(E.L.PUMP): "pump",
        str(E.L.AMM): "pump_amm",
        str(E.L.FEES): "pump_fees",
        str(E.L.TOKEN): "spl_token",
        str(E.L.TOKEN22): "spl_token_2022",
        str(E.L.ATA): "associated_token",
    }
    return "absent" if owner is None else known.get(owner, "other")


def _data(account: dict | None) -> bytes:
    return b"" if account is None else base64.b64decode(account["data_base64"], validate=True)


def _token_amount(account: dict | None) -> int | None:
    if account is None or _owner_class(account["owner"]) not in ("spl_token", "spl_token_2022"):
        return None
    raw = _data(account)
    return int.from_bytes(raw[64:72], "little") if len(raw) >= 72 else None


def _static_roles(case: dict) -> dict[str, set[str]]:
    """Name stable fixture accounts without depending on saved producer labels."""
    fixture = E.fixture_plan(case)
    mint = fixture.mints[0]
    result: dict[str, set[str]] = collections.defaultdict(set)
    fixed = {
        "global": E.L.GLOBAL,
        "mint": mint.mint,
        "quote_mint": mint.quote,
        "bonding_curve": mint.curve,
        "pool_authority": mint.pool_authority,
        "pool": mint.pool,
        "sharing_config": mint.sharing,
        "holder_rewards": mint.holder,
        "payer": E.L.PAYER.pubkey(),
        "admin_set_creator_authority": E.L.ADMIN.pubkey(),
    }
    for name, key in fixed.items():
        result[str(key)].add(name)
    for index, pair in enumerate(E.L.CREATORS):
        result[str(pair.pubkey())].add(f"creator_{index}")
    return result


def _receipt_roles(receipt: dict, static: dict[str, set[str]]) -> dict[str, set[str]]:
    roles = {key: set(values) for key, values in static.items()}
    names = [row["name"] for row in E.L.ADMIN_CTO["accounts"]]
    for index, meta in enumerate(receipt["instruction_accounts"]):
        roles.setdefault(meta["pubkey"], set()).add(
            names[index] if index < len(names) else f"trailing_account_{index}")
    return roles


def _changed_state(receipt: dict, static: dict[str, set[str]]) -> list[dict]:
    roles = _receipt_roles(receipt, static)
    changes = []
    for key in sorted(receipt["before"]):
        before, after = receipt["before"][key], receipt["after"][key]
        if E.same_json(before, after):
            continue
        before_data, after_data = _data(before), _data(after)
        before_amount, after_amount = _token_amount(before), _token_amount(after)
        row = {
            "account_classes": sorted(roles.get(key) or {
                "unreferenced_" + _owner_class((after or before)["owner"])
            }),
            "presence": ("created" if before is None else
                         "deleted" if after is None else "updated"),
            "owner": [_owner_class(None if before is None else before["owner"]),
                      _owner_class(None if after is None else after["owner"])],
            "lamports": _direction(0 if before is None else before["lamports"],
                                   0 if after is None else after["lamports"]),
            "data_length": _direction(len(before_data), len(after_data)),
            "data_changed": before_data != after_data,
            "token_amount": (None if before_amount is None or after_amount is None
                             else _direction(before_amount, after_amount)),
        }
        changes.append(row)
    counts = collections.Counter(canonical(row).decode("utf-8") for row in changes)
    return [{"transition": json.loads(row), "count": count}
            for row, count in sorted(counts.items())]


def _transaction_keys(receipt: dict) -> list[str]:
    raw = base64.b64decode(receipt["transaction_base64"], validate=True)
    tx = E.Transaction.from_bytes(raw)
    return [str(key) for key in tx.message.account_keys]


def _inner_sequence(receipt: dict) -> tuple[list[dict], list[str]]:
    keys = _transaction_keys(receipt)
    sequence, token_path = [], []
    for group in receipt.get("inner_instructions") or []:
        if not isinstance(group, dict):
            continue
        for instruction in group.get("instructions") or []:
            if not isinstance(instruction, dict):
                continue
            index = instruction.get("program_id_index")
            program = keys[index] if type(index) is int and 0 <= index < len(keys) else None
            program_class = _owner_class(program)
            data = instruction.get("data")
            entry = {
                "program": program_class,
                "account_indices": instruction.get("accounts"),
                "data_sha256": hashlib.sha256(str(data).encode("utf-8")).hexdigest(),
                "stack_height": instruction.get("stack_height"),
            }
            sequence.append(entry)
            if program_class in ("spl_token", "spl_token_2022", "associated_token"):
                token_path.append(program_class)
    return sequence, token_path


def _event_sequence(receipt: dict) -> list[dict]:
    result = []
    for value in receipt["events"]:
        try:
            raw = base64.b64decode(value, validate=True)
        except (ValueError, TypeError):
            raw = str(value).encode("utf-8")
        result.append({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    return result


def _return_data(receipt: dict) -> dict | None:
    value = receipt.get("return_data")
    return None if value is None else {"sha256": digest(value)}


def behavior_fingerprint(case: dict, original_run: dict) -> dict:
    """Return the canonical v1 fingerprint and its SHA-256 identity."""
    C.validate_case(case)
    failures = E.validate_run(original_run, case)
    if failures:
        raise ValueError("cannot fingerprint an invalid original run: " + repr(failures))
    static = _static_roles(case)
    steps = []
    for receipt in original_run["receipts"]:
        inner, token_path = _inner_sequence(receipt)
        authority_roles = []
        names = [row["name"] for row in E.L.ADMIN_CTO["accounts"]]
        for index, meta in enumerate(receipt["instruction_accounts"]):
            if meta["signer"]:
                authority_roles.append(names[index] if index < len(names) else f"trailing_account_{index}")
        stage = ("success" if receipt["error"] is None else
                 "failed_after_cpi" if inner else "failed_before_cpi")
        steps.append({
            "outcome": receipt["outcome"],
            "stage": stage,
            "failure_class": receipt["failure_class"],
            "authority_signer_roles": authority_roles,
            "events": _event_sequence(receipt),
            "inner_cpi_sequence": inner,
            "token_program_path": token_path,
            "state_transitions": _changed_state(receipt, static),
            "return_data": _return_data(receipt),
        })
    payload = {"schema": FINGERPRINT_SCHEMA, "steps": steps}
    return {"schema": FINGERPRINT_SCHEMA, "sha256": digest(payload), "payload": payload}


def is_boundary_case(case: dict) -> bool:
    boundaries = set(C.BOUNDARIES)
    def walk(value):
        if type(value) is int:
            return value in boundaries
        if isinstance(value, dict):
            return any(walk(item) for item in value.values())
        if isinstance(value, list):
            return any(walk(item) for item in value)
        return False
    return walk(case["config"]) or walk(case["initial_mutations"]) or walk(case["steps"])


def observe_case(case: dict, original: Path, images=None) -> dict:
    C.validate_case(case)
    base = {"schema": OBSERVATION_SCHEMA, "case_id": case["case_id"],
            "case": copy.deepcopy(case), "boundary_case": is_boundary_case(case)}
    try:
        E.fixture_plan(case)
        if E.sha(E.P.regular_bytes(original)) != E.CANONICAL_ORIGINAL_SHA256:
            raise ValueError("original image is not the captured Pump Main")
        run = E.run_image(original, case, images)
        failures = E.validate_run(run, case)
        if failures:
            base.update(classification="infrastructure_failure",
                        reason="invalid original receipt: " + repr(failures))
            return base
        fingerprint = behavior_fingerprint(case, run)
        base.update(classification="observed_behavior", reason=None, original=run,
                    fingerprint=fingerprint,
                    successful_sequence=all(row["error"] is None for row in run["receipts"]))
        return base
    except E.UnsupportedFixture as error:
        base.update(classification="unsupported_fixture", reason=str(error))
        return base
    except BaseException as error:
        if isinstance(error, (KeyboardInterrupt, SystemExit, GeneratorExit)):
            raise
        base.update(classification="infrastructure_failure",
                    reason=f"{type(error).__name__}: {error}")
        return base


def validate_observation(observation: dict, case: dict) -> list[str]:
    failures = []
    try:
        C.validate_case(case)
        common = {"schema", "case_id", "case", "boundary_case", "classification", "reason"}
        if (type(observation) is not dict or observation.get("schema") != OBSERVATION_SCHEMA
                or observation.get("case_id") != case["case_id"]
                or not E.same_json(observation.get("case"), case)
                or observation.get("boundary_case") is not is_boundary_case(case)):
            return ["observation-case"]
        classification = observation.get("classification")
        if classification == "observed_behavior":
            if set(observation) != common | {"original", "fingerprint", "successful_sequence"}:
                failures.append("observation-fields")
            run_failures = E.validate_run(observation.get("original"), case)
            failures.extend("original:" + item for item in run_failures)
            if not run_failures:
                expected = behavior_fingerprint(case, observation["original"])
                if not E.same_json(expected, observation.get("fingerprint")):
                    failures.append("fingerprint")
                successful = all(row["error"] is None for row in observation["original"]["receipts"])
                if observation.get("successful_sequence") is not successful:
                    failures.append("successful-sequence")
            if observation.get("reason") is not None:
                failures.append("observed-reason")
        elif classification == "unsupported_fixture":
            if set(observation) != common:
                failures.append("unsupported-fields")
            try:
                E.fixture_plan(case)
            except E.UnsupportedFixture as error:
                if observation.get("reason") != str(error):
                    failures.append("unsupported-reason")
            else:
                failures.append("unsupported-not-reproduced")
        elif classification == "infrastructure_failure":
            if set(observation) != common or type(observation.get("reason")) is not str:
                failures.append("infrastructure-fields")
        else:
            failures.append("observation-classification")
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        failures.append("malformed-observation:" + type(error).__name__)
    return failures


def _row(case: dict, observation: dict) -> dict:
    row = {"case_id": case["case_id"], "case_index": case["case_index"],
           "classification": observation["classification"],
           "boundary_case": observation["boundary_case"]}
    if observation["classification"] == "observed_behavior":
        row.update(fingerprint_sha256=observation["fingerprint"]["sha256"],
                   successful_sequence=observation["successful_sequence"])
    return row


def select_corpus(cases: list[dict], observations: list[dict], limit: int) -> dict:
    """Select a bounded deterministic corpus and an equal-size unguided control."""
    if type(cases) is not list or not 1 <= len(cases) <= MAX_POOL_CASES:
        raise ValueError(f"pool size must be between 1 and {MAX_POOL_CASES}")
    if type(observations) is not list or len(observations) != len(cases):
        raise ValueError("observation count differs from pool")
    if type(limit) is not int or not 1 <= limit <= min(MAX_CORPUS_CASES, len(cases)):
        raise ValueError(f"corpus limit must be between 1 and {min(MAX_CORPUS_CASES, len(cases))}")
    rows, seen = [], set()
    for case, observation in zip(cases, observations):
        C.validate_case(case)
        rejected = validate_observation(observation, case)
        if rejected:
            raise ValueError("invalid observation: " + repr(rejected))
        if case["case_id"] in seen:
            continue
        seen.add(case["case_id"])
        rows.append(_row(case, observation))
    eligible = [row for row in rows if row["classification"] == "observed_behavior"]
    frequencies = collections.Counter(row["fingerprint_sha256"] for row in eligible)
    groups: dict[str, list[dict]] = collections.defaultdict(list)
    for row in eligible:
        row["class_frequency"] = frequencies[row["fingerprint_sha256"]]
        groups[row["fingerprint_sha256"]].append(row)
    representative = {}
    for fingerprint, members in groups.items():
        representative[fingerprint] = min(
            members, key=lambda row: (not row["boundary_case"], row["case_index"], row["case_id"]))

    def class_key(row):
        return (not row["successful_sequence"], row["class_frequency"],
                not row["boundary_case"], row["fingerprint_sha256"],
                row["case_index"], row["case_id"])

    reps = sorted(representative.values(), key=class_key)
    ordered, reasons = [], {}
    anchors = (
        ("underrepresented-success", [row for row in reps if row["successful_sequence"]]),
        ("known-failure", [row for row in reps if not row["successful_sequence"]]),
        ("boundary", [row for row in reps if row["boundary_case"]]),
    )
    for reason, candidates in anchors:
        if candidates:
            row = min(candidates, key=class_key)
            if row["case_id"] not in reasons:
                ordered.append(row)
                reasons[row["case_id"]] = reason
    for row in reps:
        if row["case_id"] not in reasons:
            ordered.append(row)
            reasons[row["case_id"]] = "novel-behavior-representative"
    remainder = sorted((row for row in eligible if row["case_id"] not in reasons), key=class_key)
    for row in remainder:
        ordered.append(row)
        reasons[row["case_id"]] = "bounded-class-member"
    retained_count = min(limit, len(eligible))
    selected_rows = ordered[:retained_count]
    unguided_rows = eligible[:retained_count]

    def ranked(values, *, guided):
        return [{"rank": rank, "case_id": row["case_id"],
                 "case_index": row["case_index"],
                 "fingerprint_sha256": row["fingerprint_sha256"],
                 **({"selection_reason": reasons[row["case_id"]]} if guided else {})}
                for rank, row in enumerate(values, 1)]

    selected_classes = {row["fingerprint_sha256"] for row in selected_rows}
    unguided_classes = {row["fingerprint_sha256"] for row in unguided_rows}
    document = {
        "schema": SELECTION_SCHEMA,
        "fingerprint_schema": FINGERPRINT_SCHEMA,
        "pool_count": len(cases),
        "deduplicated_pool_count": len(rows),
        "eligible_count": len(eligible),
        "unsupported_count": sum(row["classification"] == "unsupported_fixture" for row in rows),
        "infrastructure_failure_count": sum(row["classification"] == "infrastructure_failure" for row in rows),
        "corpus_limit": limit,
        "retained_count": retained_count,
        "rows": rows,
        "selected": ranked(selected_rows, guided=True),
        "unguided_baseline": ranked(unguided_rows, guided=False),
        "selected_behavior_class_count": len(selected_classes),
        "unguided_behavior_class_count": len(unguided_classes),
        "selected_success_count": sum(row["successful_sequence"] for row in selected_rows),
        "unguided_success_count": sum(row["successful_sequence"] for row in unguided_rows),
    }
    document["selection_sha256"] = digest(document)
    return document


def selected_cases(cases: list[dict], selection: dict) -> list[dict]:
    by_id = {case["case_id"]: case for case in cases}
    return [copy.deepcopy(by_id[row["case_id"]]) for row in selection["selected"]]


def validate_selection(selection: dict, cases: list[dict], observations: list[dict], limit: int) -> list[str]:
    try:
        expected = select_corpus(cases, observations, limit)
        return [] if E.same_json(selection, expected) else ["selection-recomputation"]
    except (KeyError, TypeError, ValueError, IndexError, AttributeError, OverflowError) as error:
        return ["malformed-selection:" + type(error).__name__]
