#!/usr/bin/env python3
"""Adversarial mutations for the independent multi-donor receipt verifier."""
from __future__ import annotations

import argparse
import base64
import copy
import json
import hashlib
import types
import sys
from pathlib import Path
from typing import Any, Callable

_SELF_SOURCE_SHA256 = globals().get("__source_sha256__")
if _SELF_SOURCE_SHA256 is None:
    _SELF_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if "_ADMISSION" in globals():
    A = _ADMISSION
else:
    _path = HERE / "admission.py"
    if _path.is_symlink():
        raise ValueError("admission source must be regular")
    _raw = _path.read_bytes()
    A = types.ModuleType("_relay_multidonor_admission")
    A.__file__ = str(_path)
    A.__source_sha256__ = hashlib.sha256(_raw).hexdigest()
    exec(compile(_raw, str(_path), "exec", dont_inherit=True), A.__dict__)
verify = A.source_module("verify", HERE / "verify.py", bindings={"_ADMISSION": A})
_output = A.source_module("output", ROOT / "scripts/pump_differential_output.py")
PumpReport = _output.PumpReport
A.LOADED[str(Path(__file__).resolve())] = _SELF_SOURCE_SHA256


def replace_account_data(row: dict[str, Any], raw: bytes) -> None:
    row["data_base64"] = base64.b64encode(raw).decode()
    row["data_len"] = len(raw)
    row["data_sha256"] = verify.sha(raw)


def first_step(report: dict[str, Any]) -> dict[str, Any]:
    return report["cases"][0]["steps"][0]


def corrupt_signature(report: dict[str, Any]) -> None:
    step = first_step(report)
    raw = bytearray(base64.b64decode(step["transaction_base64"]))
    raw[1] ^= 1
    step["transaction_base64"] = base64.b64encode(raw).decode()
    step["transaction_sha256"] = verify.sha(raw)


def corrupt_token_balance(report: dict[str, Any]) -> None:
    case = report["cases"][0]
    step = case["steps"][0]
    source = case["fixture"]["sources"]["A"]["mint_x"]
    for side in ("original", "candidate"):
        row = step[side]["after"][source]
        raw = bytearray(base64.b64decode(row["data_base64"]))
        raw[64:72] = (int.from_bytes(raw[64:72], "little") + 1).to_bytes(8, "little")
        replace_account_data(row, bytes(raw))


def corrupt_debouncer(report: dict[str, Any]) -> None:
    case = report["cases"][0]
    step = case["steps"][-1]
    address = case["fixture"]["domains"]["config_a_mint_x"]["debouncer"]
    for side in ("original", "candidate"):
        row = step[side]["after"][address]
        raw = bytearray(base64.b64decode(row["data_base64"]))
        raw[74:82] = (int.from_bytes(raw[74:82], "little") + 1).to_bytes(8, "little")
        replace_account_data(row, bytes(raw))


def corrupt_event(report: dict[str, Any]) -> None:
    step = first_step(report)
    for side in ("original", "candidate"):
        step[side]["events"].append("Program data: Y29ycnVwdGVk")


def corrupt_outcome(report: dict[str, Any]) -> None:
    step = first_step(report)
    for side in ("original", "candidate"):
        step[side]["error"] = "forged-success-outcome"


def corrupt_owner(report: dict[str, Any]) -> None:
    case = report["cases"][0]
    source = case["fixture"]["sources"]["A"]["mint_x"]
    for side in ("original", "candidate"):
        case["steps"][0][side]["before"][source]["owner"] = str(verify.RELAY)


def corrupt_case_count(report: dict[str, Any]) -> None:
    report["case_count"] += 1


def corrupt_signature_flag_types(report):
    for case in report["cases"]:
        for step in case["steps"]:
            step["signature_verification"] = [1] * len(step["signature_verification"])


def corrupt_program_snapshot_membership(report):
    for case in report["cases"]:
        for step in case["steps"]:
            for side in ("original", "candidate"):
                for stage in ("before", "after"):
                    step[side][stage].pop(str(verify.RELAY))


def corrupt_canonical_budget_with_valid_signatures(report):
    from solders.transaction import Transaction
    from solders.hash import Hash
    from solders.compute_budget import set_compute_unit_limit
    case = report["cases"][0]
    value = verify.F.Fixture.create(case["name"], verify.D.CASES[case["name"]].get("balances"))
    instructions, signers, _records = verify.D.build_step(value, verify.D.CASES[case["name"]]["steps"][0])
    step = case["steps"][0]
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1), *instructions], value.fee.pubkey(),
        verify.F.unique_keypairs([value.fee, *signers]), Hash.from_string(step["recent_blockhash"]))
    step.update(transaction_base64=base64.b64encode(bytes(tx)).decode(),
                transaction_sha256=verify.sha(bytes(tx)), message_base64=base64.b64encode(bytes(tx.message)).decode(),
                message_sha256=verify.sha(bytes(tx.message)), signatures=[str(s) for s in tx.signatures],
                signature_verification=list(tx.verify_with_results()),
                required_signer_pubkeys=[str(k) for k in tx.message.account_keys[:tx.message.header.num_required_signatures]])


def corrupt_fee_scalar(report):
    for side in ("original", "candidate"):
        report["cases"][0]["steps"][0][side]["transaction_fee_lamports"] += 123


def corrupt_constructor_prestate(report):
    case = report["cases"][0]
    outsider = case["fixture"]["outsider"]
    for step in case["steps"]:
        for side in ("original", "candidate"):
            for stage in ("before", "after"):
                step[side][stage][outsider]["lamports"] += 1


def corrupt_exact_error(report):
    for side in ("original", "candidate"):
        report["cases"][5]["steps"][1][side]["error"] = "invented noncanonical error Custom(1) suffix"


def fabricate_build_claim(report):
    executable = Path(sys.executable).resolve()
    build = {"schema": "donation-relay-candidate-build-v1",
             "builder": {"path": "reconstruction/verification/donation-relay-multidonor/producer.py",
                         "sha256": verify.file_sha(HERE / "producer.py")},
             "command": [str(executable), "rustc", "--release", "--target", "sbpf-solana-solana", "--locked", "--offline", "--manifest-path", "fixture", "--lib", "--"],
             "offline": True, "locked": True, "source_files": report["inputs"]["source_files"],
             "source_manifest_sha256": report["inputs"]["source_manifest_sha256"],
             "toolchain": {"rust/bin/cargo": {"path": str(executable), "sha256": verify.file_sha(executable)}},
             "unstripped": {"sha256": "1" * 64, "bytes": 1}, "candidate": report["inputs"]["candidate"]}
    report["inputs"]["candidate_build"] = build
    report["inputs"]["candidate_build_receipt_sha256"] = verify.sha(verify.canonical(build))


MUTATIONS: dict[str, Callable[[dict[str, Any]], None]] = {
    "donor_signature": corrupt_signature,
    "token_balance": corrupt_token_balance,
    "debouncer_aggregate": corrupt_debouncer,
    "event": corrupt_event,
    "transaction_outcome": corrupt_outcome,
    "account_owner": corrupt_owner,
    "case_count": corrupt_case_count,
    "typed_signature_flags": corrupt_signature_flag_types,
    "canonical_program_snapshot_membership": corrupt_program_snapshot_membership,
    "canonical_budget_with_valid_signatures": corrupt_canonical_budget_with_valid_signatures,
    "payer_fee_scalar": corrupt_fee_scalar,
    "constructor_prestate": corrupt_constructor_prestate,
    "exact_error_structure": corrupt_exact_error,
    "fabricated_source_build_claim": fabricate_build_claim,
}


def run(report: dict[str, Any], root: Path, candidate: Path) -> dict[str, Any]:
    baseline = verify.validate(report, root, candidate)
    if baseline:
        raise ValueError("baseline report is invalid: " + ", ".join(baseline))
    results = {}
    for name, mutate in MUTATIONS.items():
        changed = copy.deepcopy(report)
        mutate(changed)
        problems = verify.validate(changed, root, candidate)
        results[name] = {"detected": bool(problems), "problems": problems[:8]}
    return {
        "schema": "donation-relay-multidonor-negative-controls-v1",
        "control_count": len(results),
        "detected_count": sum(row["detected"] for row in results.values()),
        "all_detected": all(row["detected"] for row in results.values()),
        "controls": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, candidate, report_path = args.root.resolve(), args.candidate.resolve(), args.report.resolve()
    A.outside_repository(args.output)
    admitted = A.snapshot_inputs()
    raw = A.regular_bytes(report_path)
    report = A.json_bytes(raw)
    result = run(report, root, candidate)
    result["report_sha256"] = verify.sha(raw)
    publisher = PumpReport(args.output.resolve(), root, candidate, __file__, overwrite=False,
                           extra_inputs=[report_path, HERE / "verify.py"])
    A.recheck_inputs(admitted)
    if A.regular_bytes(report_path) != raw:
        raise ValueError("report changed during controls")
    publisher.write(verify.canonical(result))
    print(json.dumps(result, indent=2, sort_keys=True))
    raise SystemExit(0 if result["all_detected"] else 1)


if __name__ == "__main__":
    main()
