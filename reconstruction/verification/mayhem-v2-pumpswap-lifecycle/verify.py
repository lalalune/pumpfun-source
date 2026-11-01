#!/usr/bin/env python3
"""Independently verify Mayhem V2/PumpSwap receipts, signatures, and economics."""
from __future__ import annotations

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import argparse
import base64
import copy
import hashlib
import json
import struct
from pathlib import Path

HERE = Path(__file__).resolve().parent
producer_namespace = {"__file__": str(HERE / "producer.py"), "__name__": "mayhem_v2_pumpswap_producer"}
exec(compile((HERE / "producer.py").read_bytes(), str(HERE / "producer.py"), "exec", dont_inherit=True), producer_namespace)
runtime = producer_namespace["namespace"]
ROOT = producer_namespace["ROOT"]
ORIGINAL = producer_namespace["ORIGINAL"]
ORIGINAL_SHA256 = producer_namespace["ORIGINAL_SHA256"]
CANDIDATE_SHA256 = producer_namespace["CANDIDATE_SHA256"]
MAYHEM = runtime["MAYHEM"]
PAYER = runtime["PAYER"]
TRADER = runtime["TRADER"]
V2VM = runtime["V2VM"]
PumpSwapVM = runtime["PumpSwapVM"]
plan = runtime["plan"]
sha256_bytes = runtime["sha256_bytes"]

from solders.account import Account  # noqa: E402
from solders.compute_budget import set_compute_unit_limit  # noqa: E402
from solders.hash import Hash  # noqa: E402
from solders.message import Message  # noqa: E402
from solders.pubkey import Pubkey  # noqa: E402
from solders.transaction import Transaction  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def strict_loads(raw: str) -> object:
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def constant(value):
        raise ValueError(f"nonfinite JSON number: {value}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def same(left: object, right: object) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(right, sort_keys=True, separators=(",", ":"))


def raw_account(receipt: dict, phase: str, role: str) -> bytes:
    saved = receipt[phase][receipt["account_roles"][role]]
    require(saved is not None and type(saved["data_base64"]) is str, f"{phase} {role} account data")
    return base64.b64decode(saved["data_base64"], validate=True)


def amount(receipt: dict, phase: str, role: str) -> int:
    return struct.unpack_from("<Q", raw_account(receipt, phase, role), 64)[0]


def i128(receipt: dict, phase: str, role: str, offset: int) -> int:
    raw = raw_account(receipt, phase, role)
    return int.from_bytes(raw[offset : offset + 16], "little", signed=True)


def lamports(receipt: dict, phase: str, role: str) -> int:
    saved = receipt[phase][receipt["account_roles"][role]]
    return 0 if saved is None else saved["lamports"]


def validate_snapshot(state: dict, canonical: dict) -> None:
    require(type(state) is dict and state.keys() == canonical.keys(), "watched snapshot membership")
    fields = {"lamports", "owner", "executable", "rent_epoch", "data_bytes", "data_sha256", "data_base64"}
    for address, saved in state.items():
        Pubkey.from_string(address)
        if saved is None:
            continue
        require(type(saved) is dict and saved.keys() == fields, "account snapshot fields")
        Pubkey.from_string(saved["owner"])
        for field in ("lamports", "rent_epoch", "data_bytes"):
            require(type(saved[field]) is int and saved[field] >= 0, f"snapshot {field}")
        require(type(saved["executable"]) is bool, "snapshot executable type")
        if saved["executable"]:
            require(saved["data_base64"] is None, "executable snapshot embeds data")
        else:
            require(type(saved["data_base64"]) is str, "snapshot data type")
            raw = base64.b64decode(saved["data_base64"], validate=True)
            require(base64.b64encode(raw).decode() == saved["data_base64"], "noncanonical base64")
            require(len(raw) == saved["data_bytes"] and sha256_bytes(raw) == saved["data_sha256"], "snapshot data metadata")


class SnapshotVM:
    def __init__(self, receipt: dict):
        self.receipt = receipt

    def get_account(self, key: Pubkey) -> Account:
        saved = self.receipt["before"][str(key)]
        require(saved is not None and not saved["executable"], f"planned message missing {key}")
        return Account(
            saved["lamports"],
            base64.b64decode(saved["data_base64"], validate=True),
            Pubkey.from_string(saved["owner"]),
            saved["executable"],
            saved["rent_epoch"],
        )


def planned_message(fixture, receipt: dict, step: dict) -> Message:
    cls = V2VM if receipt["venue"] == "v2" else PumpSwapVM
    planned = object.__new__(cls)
    planned.keys = fixture.keys
    planned.base_program = fixture.base_program
    planned.quote_program = fixture.quote_program
    planned.vm = SnapshotVM(receipt)
    instructions = [set_compute_unit_limit(1_400_000)]
    instructions.extend(planned.build_instruction(name) for name in step["instructions"])
    return Message.new_with_blockhash(instructions, PAYER.pubkey(), Hash.from_string(receipt["recent_blockhash"]))


def validate_receipt(receipt: dict, fixture, initial: dict, lifecycle: dict, step: dict, index: int) -> None:
    require(receipt["venue"] == lifecycle["venue"], "receipt venue")
    require(receipt["lifecycle"] == lifecycle["name"] and receipt["step"] == step["name"], "receipt case identity")
    require(same(receipt["instructions"], step["instructions"]) and receipt["expected"] == step["expect"], "receipt plan")
    require(type(receipt["transaction_index"]) is int and receipt["transaction_index"] == index, "transaction index")
    require(same(receipt["account_roles"], fixture.roles()), "canonical account roles")
    validate_snapshot(receipt["before"], initial)
    validate_snapshot(receipt["after"], initial)
    raw = base64.b64decode(receipt["transaction_base64"], validate=True)
    tx = Transaction.from_bytes(raw)
    verified = list(tx.verify_with_results())
    required = tx.message.header.num_required_signatures
    require(bytes(tx) == raw and required == 2 and len(tx.signatures) == 2, "signed transaction shape")
    require(verified == [True, True] and receipt["signature_verification"] == [True, True], "transaction signatures")
    require(receipt["signatures"] == [str(item) for item in tx.signatures], "signature vector binding")
    require(receipt["transaction_sha256"] == sha256_bytes(raw), "transaction hash binding")
    require(str(tx.message.recent_blockhash) == receipt["recent_blockhash"], "blockhash binding")
    require(set(tx.message.account_keys[:required]) == {PAYER.pubkey(), TRADER.pubkey()}, "required signer membership")
    require(bytes(tx.message) == bytes(planned_message(fixture, receipt, step)), "signed instruction plan")
    require(type(receipt["logs"]) is list and all(type(line) is str for line in receipt["logs"]), "logs type")
    require(receipt["events"] == [line for line in receipt["logs"] if line.startswith("Program data: ")], "event/log binding")
    require(type(receipt["compute_units_consumed"]) is int and receipt["compute_units_consumed"] > 0, "compute units")
    require(receipt["error"] is None or type(receipt["error"]) is str, "error type")


def verify_failed_rollback(receipt: dict) -> None:
    payer = receipt["account_roles"]["payer"]
    for address, before in receipt["before"].items():
        after = receipt["after"][address]
        if address != payer:
            require(same(before, after), f"failed transaction mutated {address}")
        else:
            expected = dict(before)
            expected["lamports"] -= 10_000
            require(same(expected, after), "failed transaction fee delta")


def verify_success_economics(receipt: dict) -> None:
    venue = receipt["venue"]
    base_role = "base_vault"
    counterparty = "curve_base_vault" if venue == "v2" else "pool_base_vault"
    base_delta = amount(receipt, "after", base_role) - amount(receipt, "before", base_role)
    counterparty_delta = amount(receipt, "after", counterparty) - amount(receipt, "before", counterparty)
    require(base_delta != 0 and base_delta + counterparty_delta == 0, "base token movement/conservation")
    state_token_delta = i128(receipt, "after", "mayhem_state", 72) - i128(receipt, "before", "mayhem_state", 72)
    state_quote_delta = i128(receipt, "after", "mayhem_state", 56) - i128(receipt, "before", "mayhem_state", 56)
    global_quote_delta = i128(receipt, "after", "global_params", 113) - i128(receipt, "before", "global_params", 113)
    require(state_token_delta == -base_delta, "Mayhem per-token base accounting")
    require(state_quote_delta == global_quote_delta and state_quote_delta != 0, "Mayhem global/per-token quote accounting")
    mint_role = "mint" if venue == "v2" else "base_mint"
    require(struct.unpack_from("<Q", raw_account(receipt, "before", mint_role), 36)[0] == struct.unpack_from("<Q", raw_account(receipt, "after", mint_role), 36)[0], "base mint supply changed")
    total_before = sum(saved["lamports"] for saved in receipt["before"].values() if saved is not None)
    total_after = sum(saved["lamports"] for saved in receipt["after"].values() if saved is not None)
    require(total_before - total_after == 10_000, "watched lamport conservation/transaction fee")
    require(lamports(receipt, "after", "sol_vault") - lamports(receipt, "before", "sol_vault") == -state_quote_delta, "SOL vault/accounting delta")
    if venue == "v2":
        curve_before = struct.unpack_from("<QQQQ", raw_account(receipt, "before", "bonding_curve"), 8)
        curve_after = struct.unpack_from("<QQQQ", raw_account(receipt, "after", "bonding_curve"), 8)
        require(curve_after[0] - curve_before[0] == -base_delta, "V2 virtual base reserve")
        require(curve_after[2] - curve_before[2] == -base_delta, "V2 real base reserve")
        require(curve_after[1] - curve_before[1] == state_quote_delta, "V2 virtual quote reserve")
        require(curve_after[3] - curve_before[3] == state_quote_delta, "V2 real quote reserve")
    else:
        pool_quote_delta = amount(receipt, "after", "pool_quote_vault") - amount(receipt, "before", "pool_quote_vault")
        instruction_count = len(receipt["instructions"])
        require(pool_quote_delta - state_quote_delta == 2_039_280 * instruction_count, "PumpSwap wrapped-SOL rent/accounting boundary")
        for role in ("protocol_quote_vault", "creator_quote_vault", "buyback_quote_vault"):
            require(amount(receipt, "after", role) == amount(receipt, "before", role), f"unexpected {role} accrual")


def without_program(snapshot: dict) -> dict:
    return {key: value for key, value in snapshot.items() if key != str(MAYHEM)}


def verify_semantics(report: dict, rows: list[dict]) -> dict:
    expected = [(lifecycle, step) for lifecycle in plan() for step in lifecycle["steps"]]
    require(len(rows) == len(expected), "receipt count differs from plan")
    require(report["observed_case_count"] == len(rows), "declared case count")
    require(report["observed_signed_transactions"] == len(rows) * 2, "declared signed transaction count")
    fixtures = {}
    initial = {}
    prior = {}
    seen_transactions = {}
    seen_blockhashes = {}
    classifications = []
    successful = failed = 0
    for row, (lifecycle, step) in zip(rows, expected, strict=True):
        case_id = f"{lifecycle['name']}/{step['name']}"
        require(row["case_id"] == case_id, "case order")
        for side, image in (("original", ORIGINAL), ("candidate", Path(report["candidate"]["path"]))):
            fixture_key = (side, lifecycle["name"])
            if fixture_key not in fixtures:
                fixtures[fixture_key] = V2VM(image) if lifecycle["venue"] == "v2" else PumpSwapVM(image)
                initial[fixture_key] = fixtures[fixture_key].snapshot()
            receipt = row[side]
            index = len(seen_transactions.setdefault(fixture_key, set()))
            validate_receipt(receipt, fixtures[fixture_key], initial[fixture_key], lifecycle, step, index)
            require(same(receipt["before"], prior.get(fixture_key, initial[fixture_key])), f"{case_id} {side} state continuity")
            prior[fixture_key] = receipt["after"]
            require(receipt["transaction_sha256"] not in seen_transactions[fixture_key], "duplicate signed transaction")
            require(receipt["recent_blockhash"] not in seen_blockhashes.setdefault(fixture_key, set()), "stale blockhash")
            seen_transactions[fixture_key].add(receipt["transaction_sha256"])
            seen_blockhashes[fixture_key].add(receipt["recent_blockhash"])
            success = receipt["error"] is None
            require(success == (step["expect"] == "success"), f"{case_id} expected outcome")
            if "error_contains" in step:
                require(receipt["error"] == f"TransactionErrorInstructionError((1, Tagged({step['error_contains']})))", f"{case_id} exact error")
            if success:
                verify_success_economics(receipt)
            else:
                verify_failed_rollback(receipt)
        original, candidate = row["original"], row["candidate"]
        if original["error"] is None:
            successful += 1
        else:
            failed += 1
        differences = []
        for field in ("transaction_base64", "signatures", "recent_blockhash", "error", "events", "inner_instructions", "return_data", "logs", "compute_units_consumed"):
            if not same(original[field], candidate[field]):
                differences.append(field)
        for phase in ("before", "after"):
            if not same(without_program(original[phase]), without_program(candidate[phase])):
                differences.append(phase)
        classifications.append({"case_id": case_id, "classification": "equal_observed_behavior" if not differences else "different_behavior", "different_fields": differences})
    mismatches = [item for item in classifications if item["classification"] == "different_behavior"]
    return {
        "case_count": len(rows),
        "signed_transaction_count": len(rows) * 2,
        "successful_original_transitions": successful,
        "failed_original_transitions": failed,
        "equal_observed_behavior": len(rows) - len(mismatches),
        "different_behavior": len(mismatches),
        "unsupported_fixture": 0,
        "infrastructure_failure": 0,
        "classifications": classifications,
    }


def mutate_data(saved: dict, offset: int, value: int, size: int = 8) -> None:
    raw = bytearray(base64.b64decode(saved["data_base64"], validate=True))
    raw[offset : offset + size] = value.to_bytes(size, "little", signed=False)
    saved["data_base64"] = base64.b64encode(raw).decode()
    saved["data_bytes"] = len(raw)
    saved["data_sha256"] = sha256_bytes(raw)


def negative_controls(report: dict, rows: list[dict]) -> list[dict]:
    controls = []

    def rejected(name: str, changed_report: dict, changed_rows: list[dict]) -> None:
        try:
            verify_semantics(changed_report, changed_rows)
        except (ValueError, Exception) as error:
            controls.append({"name": name, "detected": True, "reason": str(error)})
        else:
            controls.append({"name": name, "detected": False})

    changed = copy.deepcopy(rows)
    raw = bytearray(base64.b64decode(changed[0]["candidate"]["transaction_base64"]))
    raw[-1] ^= 1
    changed[0]["candidate"]["transaction_base64"] = base64.b64encode(raw).decode()
    rejected("altered_transaction_signature", report, changed)

    changed = copy.deepcopy(rows)
    receipt = changed[0]["candidate"]
    mutate_data(receipt["after"][receipt["account_roles"]["base_vault"]], 64, amount(receipt, "after", "base_vault") + 1)
    rejected("altered_vault_balance", report, changed)

    changed = copy.deepcopy(rows)
    receipt = next(row["candidate"] for row in changed if row["candidate"]["venue"] == "pumpswap" and row["candidate"]["error"] is None)
    mutate_data(receipt["after"][receipt["account_roles"]["pool_base_vault"]], 64, amount(receipt, "after", "pool_base_vault") + 1)
    rejected("altered_pool_reserve", report, changed)

    changed = copy.deepcopy(rows)
    receipt = changed[0]["candidate"]
    state = receipt["after"][receipt["account_roles"]["mayhem_state"]]
    mutate_data(state, 56, int.from_bytes(base64.b64decode(state["data_base64"])[56:72], "little") + 1, 16)
    rejected("altered_mayhem_accounting", report, changed)

    changed = copy.deepcopy(rows)
    changed[0]["candidate"]["events"].append("Program data: altered")
    rejected("altered_event", report, changed)

    changed = copy.deepcopy(rows)
    failure = next(row["candidate"] for row in changed if row["candidate"]["error"] is not None)
    failure["error"] = None
    rejected("altered_failure_result", report, changed)

    changed = copy.deepcopy(rows)
    receipt = changed[0]["candidate"]
    receipt["after"][receipt["account_roles"]["base_vault"]]["owner"] = str(Pubkey.default())
    rejected("altered_token_owner", report, changed)

    changed = copy.deepcopy(rows)
    changed[0], changed[1] = changed[1], changed[0]
    rejected("altered_transaction_sequence", report, changed)

    changed_report = copy.deepcopy(report)
    changed_report["candidate"]["sha256"] = "0" * 64
    try:
        validate_report(changed_report, Path(report["candidate"]["path"]), rows, check_receipt=False)
    except ValueError as error:
        controls.append({"name": "altered_executable_digest", "detected": True, "reason": str(error)})
    else:
        controls.append({"name": "altered_executable_digest", "detected": False})

    changed_report = copy.deepcopy(report)
    changed_report["observed_case_count"] += 1
    rejected("forged_passing_case_count", changed_report, rows)
    require(all(item["detected"] for item in controls), "negative control escaped verification")
    return controls


def validate_report(report: dict, candidate: Path, rows: list[dict] | None = None, check_receipt: bool = True) -> None:
    require(report["schema"] == "mayhem-v2-pumpswap-lifecycle-report-v1", "report schema")
    require(report["mode"] in ("original_vs_original", "original_vs_candidate"), "report mode")
    require(report["fixture_classification"] == "synthetic_preinitialized", "fixture classification")
    require(same(report["plan"], plan()), "report plan")
    require(sha256_file(ORIGINAL) == ORIGINAL_SHA256, "captured original hash")
    require(candidate.is_file() and Path(report["candidate"]["path"]).resolve() == candidate, "candidate path")
    require(report["candidate"]["bytes"] == candidate.stat().st_size and report["candidate"]["sha256"] == sha256_file(candidate), "candidate identity")
    expected = ORIGINAL_SHA256 if report["mode"] == "original_vs_original" else CANDIDATE_SHA256
    require(report["candidate"]["sha256"] == expected, "candidate admission")
    require(same(report["original"], {"path": str(ORIGINAL.relative_to(ROOT)), "bytes": ORIGINAL.stat().st_size, "sha256": ORIGINAL_SHA256}), "original identity")
    current_inventory = producer_namespace["inventory"]()
    require(same(report["input_sha256"], current_inventory), "declared input inventory")
    mayhem_sources = [ROOT / path for path in report["input_sha256"] if path.startswith("programs/mayhem/")]
    require(report["mayhem_source_files"] == len(mayhem_sources), "Mayhem source file count")
    require(report["mayhem_source_tree_sha256"] == producer_namespace["source_tree_sha256"](mayhem_sources), "Mayhem source tree hash")
    if rows is not None:
        require(report["observed_case_count"] == len(rows) and report["observed_signed_transactions"] == len(rows) * 2, "report counts")


def verify(report_path: Path, candidate: Path) -> dict:
    report_path = report_path.resolve()
    candidate = candidate.resolve()
    report = strict_loads(report_path.read_text())
    require(type(report) is dict, "report object")
    require(report["receipt_file"] == "receipts.jsonl", "receipt filename")
    receipt_path = report_path.parent / report["receipt_file"]
    require(receipt_path.is_file() and sha256_file(receipt_path) == report["receipt_sha256"], "receipt hash")
    rows = [strict_loads(line) for line in receipt_path.read_text().splitlines() if line]
    require(all(type(row) is dict for row in rows), "receipt rows")
    validate_report(report, candidate, rows)
    result = verify_semantics(report, rows)
    controls = negative_controls(report, rows)
    result.update(
        {
            "schema": "mayhem-v2-pumpswap-lifecycle-verification-v1",
            "status": "PASS" if result["different_behavior"] == 0 else "FAIL",
            "report_sha256": sha256_file(report_path),
            "receipt_sha256": sha256_file(receipt_path),
            "candidate_sha256": sha256_file(candidate),
            "negative_controls": controls,
            "producer_summary_fields_trusted": False,
        }
    )
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
        producer_namespace["require_outside_repository"](args.output)
        require(not args.output.exists(), "verification output already exists")
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    raise SystemExit(result["status"] != "PASS")


if __name__ == "__main__":
    main()
