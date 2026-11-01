#!/usr/bin/env python3
"""Independently verify Mayhem stateful lifecycle receipts and economics."""
from __future__ import annotations

import argparse
import base64
import copy
import hashlib
import json
import struct
from pathlib import Path

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

HERE = Path(__file__).resolve().parent
_path = HERE / "admission.py"
_raw = _path.read_bytes()
_admission = {"__file__": str(_path), "__name__": "mayhem_admission"}
exec(compile(_raw, str(_path), "exec", dont_inherit=True), _admission)
producer = _admission["source_module"]("mayhem_stateful_producer", HERE / "producer.py")
lifecycle = producer.lifecycle
MAYHEM, PAYER, ROOT = lifecycle.MAYHEM, lifecycle.PAYER, lifecycle.ROOT
lifecycle_plan, sha256_bytes = lifecycle.lifecycle_plan, lifecycle.sha256_bytes
same_json, recheck_inputs = lifecycle.same_json, lifecycle.recheck_inputs
CANDIDATE_SHA256, ORIGINAL_SHA256 = producer.CANDIDATE_SHA256, producer.ORIGINAL_SHA256
source_tree_sha256 = producer.source_tree_sha256
if sha256_bytes(_raw) != lifecycle.LOADED_INPUT_SHA256[_path.relative_to(ROOT).as_posix()]:
    raise ValueError("admission source changed during import")
if "_ADMITTED_SOURCE_BYTES" in globals() and sha256_bytes(_ADMITTED_SOURCE_BYTES) != lifecycle.LOADED_INPUT_SHA256[Path(__file__).relative_to(ROOT).as_posix()]:
    raise ValueError("verifier source changed during import")
from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.hash import Hash
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def strict_loads(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON key: " + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError("nonfinite JSON number: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def data(receipt: dict, phase: str, role: str) -> bytes:
    key = receipt["account_roles"][role]
    encoded = receipt[phase][key]["data_base64"]
    require(encoded is not None, f"{receipt['step']} {phase} {role} has no account data")
    return base64.b64decode(encoded, validate=True)


def lamports(receipt: dict, phase: str, role: str) -> int:
    return receipt[phase][receipt["account_roles"][role]]["lamports"]


def u64(raw: bytes, offset: int) -> int:
    return struct.unpack_from("<Q", raw, offset)[0]


def i128(raw: bytes, offset: int) -> int:
    return int.from_bytes(raw[offset : offset + 16], "little", signed=True)


def compare_snapshots(left: dict, right: dict, subject: str) -> bool:
    return same_json({key: value for key, value in left.items() if key != subject},
                     {key: value for key, value in right.items() if key != subject})


def validate_snapshot(state, canonical):
    require(type(state) is dict and state.keys() == canonical.keys(), "watched snapshot membership")
    fields = {"lamports", "owner", "executable", "rent_epoch", "data_bytes", "data_sha256", "data_base64"}
    for key, saved in state.items():
        Pubkey.from_string(key)
        if canonical[key] is not None and canonical[key]["executable"]:
            require(same_json(saved, canonical[key]), "executable snapshot metadata")
            continue
        if saved is None:
            continue
        require(type(saved) is dict and saved.keys() == fields, "account snapshot fields")
        Pubkey.from_string(saved["owner"])
        for field in ("lamports", "rent_epoch", "data_bytes"):
            require(type(saved[field]) is int and saved[field] >= 0, "account snapshot integer " + field)
        require(type(saved["executable"]) is bool, "account snapshot executable type")
        if saved["executable"]:
            require(same_json(saved, canonical[key]), "executable snapshot metadata")
        else:
            require(type(saved["data_base64"]) is str, "account snapshot data")
            raw = base64.b64decode(saved["data_base64"], validate=True)
            require(base64.b64encode(raw).decode() == saved["data_base64"], "noncanonical snapshot base64")
            require(len(raw) == saved["data_bytes"] and sha256_bytes(raw) == saved["data_sha256"], "account snapshot data metadata")


def planned_message(fixture, receipt, step, blockhash):
    class Snapshot:
        def get_account(self, key):
            saved = receipt["before"][str(key)]
            require(saved is not None and not saved["executable"], "planned instruction missing account")
            return Account(saved["lamports"], base64.b64decode(saved["data_base64"], validate=True),
                           Pubkey.from_string(saved["owner"]), saved["executable"], saved["rent_epoch"])
    planned = object.__new__(lifecycle.LifecycleVM)
    planned.keys, planned.spec, planned.vm = fixture.keys, fixture.spec, Snapshot()
    instructions = [set_compute_unit_limit(1_400_000)]
    signers = {PAYER.pubkey()}
    for name in step["instructions"]:
        instruction, signer = planned.named_instruction(name)
        instructions.append(instruction)
        signers.add(signer.pubkey())
    return Message.new_with_blockhash(instructions, PAYER.pubkey(), blockhash), signers


def validate_receipt(receipt, fixture, initial, lifecycle_name, step, index):
    require(receipt["lifecycle"] == lifecycle_name and receipt["step"] == step["name"], "receipt lifecycle/step")
    require(same_json(receipt["instructions"], step["instructions"]) and receipt["expected"] == step["expect"], "receipt instruction plan")
    require(type(receipt["transaction_index"]) is int and receipt["transaction_index"] == index, "transaction index")
    require(same_json(receipt["account_roles"], fixture.account_roles()), "canonical account roles")
    for phase in ("before", "after"):
        validate_snapshot(receipt[phase], initial)
    raw = base64.b64decode(receipt["transaction_base64"], validate=True)
    tx = Transaction.from_bytes(raw)
    required = tx.message.header.num_required_signatures
    checked = list(tx.verify_with_results())
    require(bytes(tx) == raw and required > 0 and len(tx.signatures) == required
            and checked == [True] * required, "signature verification")
    require(same_json(receipt["signature_verification"], checked), "producer signature field")
    require(same_json(receipt["signatures"], [str(value) for value in tx.signatures]), "signature vector binding")
    require(sha256_bytes(raw) == receipt["transaction_sha256"], "transaction hash")
    require(str(tx.message.recent_blockhash) == receipt["recent_blockhash"], "blockhash binding")
    expected, signers = planned_message(fixture, receipt, step, Hash.from_string(receipt["recent_blockhash"]))
    require(set(tx.message.account_keys[:required]) == signers and bytes(tx.message) == bytes(expected), "signed instruction plan")
    require(type(receipt["logs"]) is list and all(type(line) is str for line in receipt["logs"]), "logs type")
    require(same_json(receipt["events"], [line for line in receipt["logs"] if line.startswith("Program data: ")]), "events/log binding")
    require(type(receipt["compute_units_consumed"]) is int and receipt["compute_units_consumed"] >= 0, "compute units type")
    require(receipt["error"] is None or type(receipt["error"]) is str, "error type")


def verify_failed_rollback(receipt: dict) -> None:
    before = receipt["before"]
    after = receipt["after"]
    payer = receipt["account_roles"]["payer"]
    for key, expected in before.items():
        actual = after[key]
        if key != payer:
            require(same_json(actual, expected), f"{receipt['step']} failed transaction mutated {key}")
            continue
        expected_copy = dict(expected)
        expected_copy["lamports"] -= 10_000
        require(same_json(actual, expected_copy), f"{receipt['step']} failed transaction payer delta is not two signatures")


def verify_trade_economics(receipt: dict) -> None:
    global_before = data(receipt, "before", "global_params")
    global_after = data(receipt, "after", "global_params")
    state_before = data(receipt, "before", "mayhem_state")
    state_after = data(receipt, "after", "mayhem_state")
    vault_before = data(receipt, "before", "mayhem_token_vault")
    vault_after = data(receipt, "after", "mayhem_token_vault")
    curve_ata_before = data(receipt, "before", "associated_bonding_curve")
    curve_ata_after = data(receipt, "after", "associated_bonding_curve")
    curve_before = data(receipt, "before", "bonding_curve")
    curve_after = data(receipt, "after", "bonding_curve")
    mint_before = data(receipt, "before", "mint")
    mint_after = data(receipt, "after", "mint")

    token_delta = u64(vault_after, 64) - u64(vault_before, 64)
    deployed_delta = lamports(receipt, "before", "sol_vault") - lamports(receipt, "after", "sol_vault")
    require(token_delta != 0, f"{receipt['step']} observed no token movement")
    require(deployed_delta != 0, f"{receipt['step']} observed no SOL movement")
    require(i128(global_after, 113) - i128(global_before, 113) == deployed_delta, f"{receipt['step']} global SOL accounting")
    require(i128(state_after, 56) - i128(state_before, 56) == deployed_delta, f"{receipt['step']} state SOL accounting")
    require(i128(state_after, 72) - i128(state_before, 72) == -token_delta, f"{receipt['step']} state token accounting")

    before_curve = struct.unpack_from("<QQQQ", curve_before, 8)
    after_curve = struct.unpack_from("<QQQQ", curve_after, 8)
    require(after_curve[0] - before_curve[0] == -token_delta, f"{receipt['step']} virtual token reserve")
    require(after_curve[1] - before_curve[1] == deployed_delta, f"{receipt['step']} virtual SOL reserve")
    require(after_curve[2] - before_curve[2] == -token_delta, f"{receipt['step']} real token reserve")
    require(after_curve[3] - before_curve[3] == deployed_delta, f"{receipt['step']} real SOL reserve")
    require(
        u64(vault_before, 64) + u64(curve_ata_before, 64)
        == u64(vault_after, 64) + u64(curve_ata_after, 64),
        f"{receipt['step']} token conservation",
    )
    require(u64(mint_before, 36) == u64(mint_after, 36), f"{receipt['step']} mint supply changed")
    economic_roles = ("sol_vault", "bonding_curve", "fee_recipient", "creator_vault")
    require(
        sum(lamports(receipt, "before", role) for role in economic_roles)
        == sum(lamports(receipt, "after", role) for role in economic_roles),
        f"{receipt['step']} SOL conservation",
    )


def verify_admin_transition(receipt: dict) -> None:
    before = data(receipt, "before", "global_params")
    after = data(receipt, "after", "global_params")
    expected = 1 if receipt["instructions"] == ["stop_trading"] else 0
    require(before[48] == 1 - expected and after[48] == expected, f"{receipt['step']} pause transition")
    require(before[:48] + before[49:] == after[:48] + after[49:], f"{receipt['step']} changed non-pause global bytes")


def verify_semantics(report: dict, rows: list[dict]) -> dict:
    recheck_inputs()
    planned = [(lifecycle["name"], step) for lifecycle in lifecycle_plan() for step in lifecycle["steps"]]
    require(len(rows) == len(planned), "receipt count differs from fixture plan")
    subject = str(MAYHEM)
    classifications = []
    successful_original = 0
    failed_original = 0
    original_transaction_hashes: dict[str, set[str]] = {}
    original_blockhashes: dict[str, set[str]] = {}
    fixtures = {"original": lifecycle.LifecycleVM(producer.ORIGINAL),
                "candidate": lifecycle.LifecycleVM(Path(report["candidate"]["path"]))}
    initial = {side: fixture.snapshot() for side, fixture in fixtures.items()}
    previous = {}
    indices = {}

    for row, (lifecycle_name, step) in zip(rows, planned, strict=True):
        expected_case = f"{lifecycle_name}/{step['name']}"
        require(row["case_id"] == expected_case, f"unexpected case order at {expected_case}")
        original = row["original"]
        candidate = row["candidate"]
        for side, receipt in (("original", original), ("candidate", candidate)):
            key = (side, lifecycle_name)
            index = indices.get(key, 0)
            validate_receipt(receipt, fixtures[side], initial[side], lifecycle_name, step, index)
            require(same_json(receipt["before"], previous.get(key, initial[side])), f"{expected_case} {side} state continuity/constructor prestate")
            previous[key] = receipt["after"]
            indices[key] = index + 1
            success = receipt["error"] is None
            require(success == (step["expect"] == "success"), f"{expected_case} {side} outcome")
            if "error_contains" in step:
                expected_error = f"TransactionErrorInstructionError(({step['error_instruction_index']}, Tagged({step['error_contains']})))"
                require(receipt["error"] == expected_error, f"{expected_case} {side} exact error code/instruction index")
            if not success:
                verify_failed_rollback(receipt)
            elif any(name in ("buy", "sell") for name in step["instructions"]):
                verify_trade_economics(receipt)
            elif step["instructions"] in (["stop_trading"], ["resume_trading"]):
                verify_admin_transition(receipt)

        if original["error"] is None:
            successful_original += 1
        else:
            failed_original += 1
        original_transaction_hashes.setdefault(lifecycle_name, set())
        original_blockhashes.setdefault(lifecycle_name, set())
        require(original["transaction_sha256"] not in original_transaction_hashes[lifecycle_name], f"{expected_case} duplicate transaction")
        require(original["recent_blockhash"] not in original_blockhashes[lifecycle_name], f"{expected_case} stale blockhash")
        original_transaction_hashes[lifecycle_name].add(original["transaction_sha256"])
        original_blockhashes[lifecycle_name].add(original["recent_blockhash"])

        fields = []
        if original["transaction_base64"] != candidate["transaction_base64"]:
            fields.append("signed_transaction")
        for name in ("error", "events", "inner_instructions", "return_data", "logs", "compute_units_consumed"):
            if not same_json(original[name], candidate[name]):
                fields.append(name)
        for phase in ("before", "after"):
            if not compare_snapshots(original[phase], candidate[phase], subject):
                fields.append(phase)
        classifications.append(
            {"case_id": expected_case, "classification": "equal_observed_behavior" if not fields else "different_behavior", "different_fields": fields}
        )

    first_by_lifecycle = {}
    for row in rows:
        name = row["original"]["lifecycle"]
        first_by_lifecycle.setdefault(name, row["original"]["before"])
    starts = list(first_by_lifecycle.values())
    require(len(starts) == 2 and same_json(starts[0], starts[1]), "independent lifecycle initial states differ")
    recheck_inputs()
    mismatches = [row for row in classifications if row["classification"] != "equal_observed_behavior"]
    return {
        "case_count": len(rows),
        "signed_transaction_count": len(rows) * 2,
        "successful_original_transitions": successful_original,
        "failed_original_transitions": failed_original,
        "equal_observed_behavior": len(rows) - len(mismatches),
        "different_behavior": len(mismatches),
        "unsupported_fixture": 0,
        "infrastructure_failure": 0,
        "classifications": classifications,
    }


def negative_controls(report: dict, rows: list[dict]) -> list[dict]:
    controls = []
    changed_error = copy.deepcopy(rows)
    changed_error[0]["candidate"]["error"] = "deliberately altered error"
    try:
        verify_semantics(report, changed_error)
    except ValueError as exc:
        controls.append({"name": "altered_outcome", "detected": True, "reason": str(exc)})
    else:
        controls.append({"name": "altered_outcome", "detected": False})

    changed_state = copy.deepcopy(rows)
    candidate = changed_state[0]["candidate"]
    key = candidate["account_roles"]["fee_recipient"]
    candidate["after"][key]["lamports"] += 1
    try:
        result = verify_semantics(report, changed_state)
        require(result["different_behavior"] == 0, "deliberately altered state was accepted")
    except ValueError as exc:
        controls.append({"name": "altered_account_state", "detected": True, "reason": str(exc)})
    else:
        controls.append({"name": "altered_account_state", "detected": False})
    return controls


def verify(report_path: Path, candidate: Path) -> dict:
    recheck_inputs()
    require(sha256_file(producer.ORIGINAL) == ORIGINAL_SHA256, "captured Mayhem original hash mismatch")
    report_path = report_path.resolve()
    report = strict_loads(report_path.read_text())
    require(report["schema"] == "mayhem-stateful-lifecycle-report-v1", "report schema")
    require(report["mode"] in ("original_vs_original", "original_vs_candidate"), "report mode")
    require(report["fixture_classification"] == "synthetic_preinitialized", "fixture classification")
    require(same_json(report["plan"], lifecycle_plan()), "report plan")
    candidate = candidate.resolve()
    require(candidate.is_file(), "candidate is not a regular file")
    require(sha256_file(candidate) == report["candidate"]["sha256"], "candidate hash binding")
    require(Path(report["candidate"]["path"]).resolve() == candidate, "candidate path binding")
    require(type(report["candidate"]["bytes"]) is int and report["candidate"]["bytes"] == candidate.stat().st_size, "candidate size binding")
    require(same_json(report["original"], {"path": str(producer.ORIGINAL.relative_to(ROOT)), "sha256": ORIGINAL_SHA256, "bytes": producer.ORIGINAL.stat().st_size}), "original image binding")
    expected_candidate = ORIGINAL_SHA256 if report["mode"] == "original_vs_original" else CANDIDATE_SHA256
    require(report["candidate"]["sha256"] == expected_candidate, "candidate is not admitted for report mode")
    require(same_json(report["input_sha256"], lifecycle.LOADED_INPUT_SHA256), "complete current input inventory binding")
    mayhem_sources = [ROOT / relative for relative in report["input_sha256"] if relative.startswith("programs/mayhem/")]
    require(type(report["mayhem_source_files"]) is int and len(mayhem_sources) == report["mayhem_source_files"], "Mayhem source file count binding")
    require(source_tree_sha256(mayhem_sources) == report["mayhem_source_tree_sha256"], "Mayhem source tree binding")
    require(report["receipt_file"] == "receipts.jsonl", "receipt path binding")
    receipt_path = report_path.parent / report["receipt_file"]
    require(sha256_file(receipt_path) == report["receipt_sha256"], "receipt file hash binding")
    rows = [strict_loads(line) for line in receipt_path.read_text().splitlines() if line]
    result = verify_semantics(report, rows)
    controls = negative_controls(report, rows)
    require(all(control["detected"] for control in controls), "negative control was not detected")
    result.update(
        {
            "schema": "mayhem-stateful-lifecycle-verification-v1",
            "status": "PASS" if result["different_behavior"] == 0 else "FAIL",
            "report_sha256": sha256_file(report_path),
            "receipt_sha256": sha256_file(receipt_path),
            "candidate_sha256": sha256_file(candidate),
            "negative_controls": controls,
            "producer_summary_fields_trusted": False,
        }
    )
    recheck_inputs()
    require(sha256_file(candidate) == report["candidate"]["sha256"], "candidate changed during verification")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.report, args.candidate)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        _admission["outside_repository"](args.output)
        require(args.output.resolve() not in {args.report.resolve(), args.candidate.resolve(), args.report.resolve().parent / "receipts.jsonl"}, "verification output overlaps an input")
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    raise SystemExit(result["status"] != "PASS")


if __name__ == "__main__":
    main()
