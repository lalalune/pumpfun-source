#!/usr/bin/env python3
"""Persistent original/candidate Donation Relay multi-donor differential."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import tempfile
import types
from pathlib import Path
from typing import Any

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

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
fixture = globals().get("_FIXTURE") or A.source_module("fixture", HERE / "fixture.py")
_output = A.source_module("output", ROOT / "scripts/pump_differential_output.py")
PumpReport = _output.PumpReport
A.LOADED[str(Path(__file__).resolve())] = _SELF_SOURCE_SHA256


COMPUTE_RE = re.compile(r"Program \S+ consumed \d+ of \d+ compute units")
FIXED_CLOCK = Clock(1_000, 0, 0, 0, 1_700_000_000)


def donation(donor: str, amount: int, *, domain: str = "config_a_mint_x",
             message: str = "multi-donor donation", source_donor: str | None = None) -> dict[str, Any]:
    return {"donor": donor, "amount": amount, "domain": domain,
            "message": message, "source_donor": source_donor}


CASES: dict[str, dict[str, Any]] = {
    "same_epoch_a_then_b": {
        "steps": [
            {"donations": [donation("A", 1_000_000)], "error": None},
            {"donations": [donation("B", 2_000_000)], "error": None},
        ],
    },
    "interleaved_a_b_a": {
        "steps": [
            {"donations": [donation("A", 100)], "error": None},
            {"donations": [donation("B", 200)], "error": None},
            {"donations": [donation("A", 300)], "error": None},
        ],
    },
    "three_donors_one_transaction": {
        "steps": [{"donations": [donation("A", 1_000), donation("B", 2_000),
                                    donation("C", 3_000)], "error": None}],
    },
    "a_success_b_fail_c_success": {
        "steps": [
            {"donations": [donation("A", 1_000)], "error": None},
            {"donations": [donation("B", 1, message="m" * 256)], "error": "Custom(6009)"},
            {"donations": [donation("C", 3_000)], "error": None},
        ],
    },
    "atomic_rollback_invalid_third": {
        "steps": [{"donations": [donation("A", 100), donation("B", 200),
                                    donation("C", 1, message="m" * 256)],
                   "error": "Custom(6009)"}],
    },
    "different_balance_boundaries": {
        "balances": {"A:mint_x": 5, "B:mint_x": 10, "C:mint_x": 0},
        "steps": [
            {"donations": [donation("A", 5)], "error": None},
            {"donations": [donation("B", 11)], "error": "Custom(1)"},
            {"donations": [donation("C", 0)], "error": None},
        ],
    },
    "authority_substitution": {
        "steps": [
            {"donations": [donation("B", 7, source_donor="A")], "error": "Custom(2015)"},
            {"donations": [donation("B", 17)], "error": None},
        ],
    },
    "separate_configurations": {
        "steps": [
            {"donations": [donation("A", 111, domain="config_a_mint_x")], "error": None},
            {"donations": [donation("B", 222, domain="config_b_mint_x")], "error": None},
        ],
    },
    "separate_mints": {
        "steps": [
            {"donations": [donation("A", 333, domain="config_a_mint_x")], "error": None},
            {"donations": [donation("B", 444, domain="config_a_mint_y")], "error": None},
        ],
    },
    "zero_and_u64_boundary": {
        "steps": [
            {"donations": [donation("A", 0)], "error": None},
            {"donations": [donation("B", (1 << 64) - 1)], "error": "Custom(1)"},
            {"donations": [donation("C", 1)], "error": None},
        ],
    },
    "rejected_close_between_donors": {
        "steps": [
            {"donations": [donation("A", 777)], "error": None},
            {"close_wrong_signer": "config_a_mint_x", "error": "Custom(2012)"},
            {"donations": [donation("B", 223)], "error": None},
        ],
    },
    "failed_donor_retry": {
        "balances": {"B:mint_x": 100},
        "steps": [
            {"donations": [donation("A", 10)], "error": None},
            {"donations": [donation("B", 101)], "error": "Custom(1)"},
            {"donations": [donation("B", 100, message="fresh retry")], "error": None},
        ],
    },
}
CASE_NAMES = list(CASES)


def file_sha(path: Path) -> str:
    return fixture.sha(path.read_bytes())


def source_manifest(root: Path) -> tuple[dict[str, str], str]:
    base = root / "programs/donation-relay"
    rows = {path.relative_to(root).as_posix(): file_sha(path)
            for path in sorted(base.rglob("*")) if path.is_file()}
    digest = fixture.sha(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())
    return rows, digest


def package_manifest(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): file_sha(path)
            for path in sorted(HERE.iterdir()) if path.is_file()}


def snapshot(vm: LiteSVM, addresses: set[Pubkey]) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for address in sorted(addresses, key=str):
        value = vm.get_account(address)
        if value is None:
            rows[str(address)] = None
            continue
        row = {"lamports": value.lamports, "owner": str(value.owner),
               "executable": value.executable, "rent_epoch": value.rent_epoch, "data_len": len(value.data),
               "data_sha256": fixture.sha(bytes(value.data))}
        if value.executable:
            row["data_omitted"] = True
        else:
            row["data_base64"] = base64.b64encode(bytes(value.data)).decode()
        rows[str(address)] = row
    return rows


def row_token_amount(row: dict[str, Any] | None) -> int:
    return fixture.token_amount(row) or 0


class Pair:
    def __init__(self, original: Path, candidate: Path, value: fixture.Fixture,
                 token: Path, associated: Path):
        self.fixture = value
        self.vms: dict[str, LiteSVM] = {}
        self.blockhashes: list[str] = []
        for side, image in (("original", original), ("candidate", candidate)):
            vm = (LiteSVM().with_sigverify(True).with_blockhash_check(True)
                  .with_transaction_history(256).with_log_bytes_limit(None))
            vm.set_clock(FIXED_CLOCK)
            vm.add_program_from_file(fixture.RELAY, image)
            vm.add_program_from_file(fixture.TOKEN, token)
            vm.add_program_from_file(fixture.ATA, associated)
            for address, value_account in value.accounts.items():
                vm.set_account(address, value_account)
            # Each persistent case receives a disjoint deterministic blockhash
            # range. This preserves replay determinism while proving that no
            # transaction identity is reused across independently seeded cases.
            for _ in range(CASE_NAMES.index(value.case) * 100):
                vm.expire_blockhash()
            self.vms[side] = vm

    def add_fixture_accounts(self, addresses: set[Pubkey]) -> None:
        for address in addresses:
            value = self.fixture.accounts[address]
            for vm in self.vms.values():
                vm.set_account(address, value)

    def transact(self, instructions: list[Instruction], signers: list[Keypair],
                 donation_records: list[dict[str, Any]]) -> dict[str, Any]:
        original, candidate = self.vms.values()
        original.expire_blockhash()
        candidate.expire_blockhash()
        blockhash = original.latest_blockhash()
        if blockhash != candidate.latest_blockhash():
            raise RuntimeError("independent LiteSVM blockhashes diverged")
        blockhash_text = str(blockhash)
        if blockhash_text in self.blockhashes:
            raise RuntimeError("fresh transaction reused a prior blockhash")
        self.blockhashes.append(blockhash_text)
        all_signers = fixture.unique_keypairs([self.fixture.fee, *signers])
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), *instructions],
            self.fixture.fee.pubkey(), all_signers, blockhash,
        )
        verified = list(tx.verify_with_results())
        if not verified or not all(verified):
            raise RuntimeError("locally signed transaction failed verification")
        addresses = self.fixture.watch() | set(tx.message.account_keys)
        rows = {side: self._run(vm, tx, addresses) for side, vm in self.vms.items()}
        return {
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "transaction_sha256": fixture.sha(bytes(tx)),
            "message_base64": base64.b64encode(bytes(tx.message)).decode(),
            "message_sha256": fixture.sha(bytes(tx.message)),
            "recent_blockhash": blockhash_text,
            "signatures": [str(value) for value in tx.signatures],
            "signature_verification": verified,
            "required_signer_pubkeys": [str(value) for value in
                                        tx.message.account_keys[:tx.message.header.num_required_signatures]],
            "donor_signers": sorted({row["donor"] for row in donation_records}),
            "donations": donation_records,
            "mismatches": self.comparison_mismatches(rows["original"], rows["candidate"]),
            "original": rows["original"],
            "candidate": rows["candidate"],
        }

    def _run(self, vm: LiteSVM, tx: Transaction, addresses: set[Pubkey]) -> dict[str, Any]:
        before = snapshot(vm, addresses)
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        metadata = result.meta() if failed else result
        raw = json.loads(metadata.to_json())
        after = snapshot(vm, addresses)
        fee_key = str(self.fixture.fee.pubkey())
        fee_lamports = before[fee_key]["lamports"] - after[fee_key]["lamports"]
        rollback_changes = []
        if failed:
            rollback_changes = [address for address in before
                                if address != fee_key and before[address] != after[address]]
            if rollback_changes:
                raise AssertionError("failed transaction changed non-fee state: " + ", ".join(rollback_changes))
        logs = list(metadata.logs())
        return {
            "error": str(result.err()) if failed else None,
            "compute_units": metadata.compute_units_consumed(),
            "transaction_fee_lamports": fee_lamports,
            "logs": logs,
            "events": [line for line in logs if line.startswith("Program data: ")],
            "inner_instructions": raw["inner_instructions"],
            "return_data": raw["return_data"],
            "rollback_non_fee_changes": rollback_changes,
            "before": before,
            "after": after,
        }

    @classmethod
    def comparison_mismatches(cls, original: dict[str, Any], candidate: dict[str, Any]) -> list[str]:
        left, right = cls.comparable(original), cls.comparable(candidate)
        return sorted(field for field in left if left[field] != right[field])

    @staticmethod
    def comparable(row: dict[str, Any]) -> dict[str, Any]:
        def state(stage: str) -> dict[str, Any]:
            value = json.loads(json.dumps(row[stage]))
            value.pop(str(fixture.RELAY), None)
            return value
        return {
            "error": row["error"],
            "transaction_fee_lamports": row["transaction_fee_lamports"],
            "logs": [line for line in row["logs"] if not COMPUTE_RE.fullmatch(line)],
            "events": row["events"],
            "inner_instructions": row["inner_instructions"],
            "return_data": row["return_data"],
            "before": state("before"),
            "after": state("after"),
        }


def error_matches(error: str | None, expected: str | None, instruction_index: int = 1) -> bool:
    if expected is None:
        return error is None
    match = re.fullmatch(r"Custom\((\d+)\)", expected)
    return bool(match) and error == f"TransactionErrorInstructionError(({instruction_index}, Tagged(InstructionErrorCustom({match.group(1)}))))"


def token_total(value: fixture.Fixture, state: dict[str, Any], mint_name: str) -> int:
    donors = sum(row_token_amount(state.get(str(donor.sources[mint_name])))
                 for donor in value.donors.values())
    destinations = sum(row_token_amount(state.get(str(domain.destination)))
                       for domain in value.domains.values() if domain.mint_name == mint_name)
    return donors + destinations


def check_invariants(value: fixture.Fixture, step: dict[str, Any]) -> list[str]:
    """Independently derive conservation and isolation from the executed step."""
    problems: list[str] = []
    row = step["original"]
    before, after = row["before"], row["after"]
    if row["transaction_fee_lamports"] <= 0:
        problems.append("payer_fee_not_charged")
    for mint_name in value.mints:
        if token_total(value, before, mint_name) != token_total(value, after, mint_name):
            problems.append("token_conservation:" + mint_name)
    if row["error"] is not None:
        if row["rollback_non_fee_changes"]:
            problems.append("failed_transaction_not_rolled_back")
        return problems

    source_deltas: dict[tuple[str, str], int] = {}
    destination_deltas: dict[str, int] = {}
    touched_domains = set()
    for item in step["donations"]:
        domain = value.domains[item["domain"]]
        source_name = item.get("source_donor") or item["donor"]
        source_deltas[(source_name, domain.mint_name)] = source_deltas.get((source_name, domain.mint_name), 0) + item["amount"]
        destination_deltas[domain.name] = destination_deltas.get(domain.name, 0) + item["amount"]
        touched_domains.add(domain.name)
    for donor_name, donor in value.donors.items():
        for mint_name, source in donor.sources.items():
            actual = row_token_amount(before[str(source)]) - row_token_amount(after[str(source)])
            expected = source_deltas.get((donor_name, mint_name), 0)
            if actual != expected:
                problems.append(f"source_delta:{donor_name}:{mint_name}")
    for name, domain in value.domains.items():
        before_destination = row_token_amount(before[str(domain.destination)])
        after_destination = row_token_amount(after[str(domain.destination)])
        expected = destination_deltas.get(name, 0)
        if after_destination - before_destination != expected:
            problems.append("destination_delta:" + name)
        before_debouncer = fixture.account_data(before[str(domain.debouncer)])
        after_debouncer = fixture.account_data(after[str(domain.debouncer)])
        before_total = 0 if len(before_debouncer) < 82 else int.from_bytes(before_debouncer[74:82], "little")
        after_total = 0 if len(after_debouncer) < 82 else int.from_bytes(after_debouncer[74:82], "little")
        if after_total - before_total != expected:
            problems.append("debouncer_delta:" + name)
        if name not in touched_domains:
            for address in (domain.epoch, domain.debouncer, domain.destination):
                if before[str(address)] != after[str(address)]:
                    problems.append("domain_isolation:" + name)

    donor_lamport_loss = sum(before[str(d.keypair.pubkey())]["lamports"]
                             - after[str(d.keypair.pubkey())]["lamports"]
                             for d in value.donors.values())
    def lamports(row: dict[str, Any] | None) -> int:
        return 0 if row is None else row["lamports"]
    state_rent_gain = sum(lamports(after[str(address)]) - lamports(before[str(address)])
                          for domain in value.domains.values()
                          for address in (domain.epoch, domain.debouncer, domain.destination))
    if donor_lamport_loss != state_rent_gain:
        problems.append("rent_conservation")
    return problems


def build_step(value: fixture.Fixture, spec: dict[str, Any]) -> tuple[list[Instruction], list[Keypair], list[dict[str, Any]]]:
    if "close_wrong_signer" in spec:
        instruction, added = value.close_wrong_signer(spec["close_wrong_signer"])
        return [instruction], [value.outsider], []
    records = [dict(row) for row in spec["donations"]]
    instructions = [value.donation(
        row["donor"], row["amount"], domain_name=row["domain"],
        message=row["message"].encode(), source_donor=row.get("source_donor"),
    ) for row in records]
    signers = [value.donors[name].keypair for name in sorted({row["donor"] for row in records})]
    return instructions, signers, records


def run_case(name: str, original: Path, candidate: Path, token: Path, associated: Path) -> dict[str, Any]:
    spec = CASES[name]
    value = fixture.Fixture.create(name, spec.get("balances"))
    pair = Pair(original, candidate, value, token, associated)
    # Relayer rejection accounts must be visible from the first continuity snapshot.
    if any("close_wrong_signer" in step for step in spec["steps"]):
        _instruction, added = value.close_wrong_signer()
        pair.add_fixture_accounts(added)
    steps = []
    previous: dict[str, dict[str, Any]] | None = None
    problems: list[str] = []
    for index, step_spec in enumerate(spec["steps"]):
        instructions, signers, records = build_step(value, step_spec)
        step = pair.transact(instructions, signers, records)
        step["index"] = index
        step["expected_error"] = step_spec["error"]
        step["original_state"] = value.decode(step["original"]["after"])
        step["candidate_state"] = value.decode(step["candidate"]["after"])
        step["invariant_problems"] = check_invariants(value, step)
        if previous is not None:
            for side in ("original", "candidate"):
                if previous[side] != step[side]["before"]:
                    problems.append(f"step_{index}:sequence_continuity:{side}")
        previous = {side: step[side]["after"] for side in ("original", "candidate")}
        problems.extend(f"step_{index}:differential:{field}" for field in step["mismatches"])
        problems.extend(f"step_{index}:invariant:{field}" for field in step["invariant_problems"])
        if not error_matches(step["original"]["error"], step_spec["error"],
                             3 if name == "atomic_rollback_invalid_third" else 1):
            problems.append(f"step_{index}:original_expected_error")
        steps.append(step)
    return {
        "name": name,
        "classification": "equal_observed_behavior" if not problems else "different_behavior",
        "problems": problems,
        "fixture": {
            "donors": {name: str(donor.keypair.pubkey()) for name, donor in value.donors.items()},
            "fee_payer": str(value.fee.pubkey()),
            "outsider": str(value.outsider.pubkey()),
            "production_relayer": str(fixture.RELAYER),
            "domains": {name: {"config_hex": domain.config.hex(), "mint": str(domain.mint),
                                "epoch": str(domain.epoch), "debouncer": str(domain.debouncer),
                                "destination": str(domain.destination)}
                        for name, domain in value.domains.items()},
            "sources": {name: {mint: str(address) for mint, address in donor.sources.items()}
                        for name, donor in value.donors.items()},
        },
        "initial_balances": spec.get("balances", {}),
        "plan": spec["steps"],
        "expected_errors": [step["error"] for step in spec["steps"]],
        "final_state": steps[-1]["original_state"],
        "steps": steps,
    }


def execute(root: Path, candidate: Path, output: Path,
            build_receipt: Path | None = None) -> bool:
    if root.resolve() != ROOT:
        raise ValueError("root must be this admitted source checkout")
    if build_receipt is not None:
        raise ValueError("source-build receipts are not authenticated by this runtime suite")
    A.outside_repository(output)
    admitted = A.snapshot_inputs()
    original = root / "evidence/dependencies/donation_relay/deployed.so"
    token = root / "evidence/dependencies/spl_token/deployed.so"
    associated = root / "evidence/dependencies/associated_token/deployed.so"
    pins = {"original": (original, fixture.ORIGINAL_SHA256),
            "spl_token": (token, fixture.TOKEN_SHA256),
            "associated_token": (associated, fixture.ATA_SHA256)}
    for label, (path, expected) in pins.items():
        if not path.is_file() or file_sha(path) != expected:
            raise SystemExit(f"{label} input missing or hash mismatch: {path}")
    if not candidate.is_file():
        raise SystemExit("candidate does not exist: " + str(candidate))
    sources, source_digest = source_manifest(root)
    publisher = PumpReport(
        output, root, candidate, __file__, overwrite=False,
        extra_inputs=[HERE / "fixture.py", *[path for path, _ in pins.values()],
                      *[root / name for name in sources],
                      *([build_receipt] if build_receipt is not None else [])],
    )
    images = {label: A.regular_bytes(path, root=ROOT) for label, (path, _expected) in pins.items()}
    images["candidate"] = A.regular_bytes(candidate)
    for label, (_path, digest) in pins.items():
        if fixture.sha(images[label]) != digest:
            raise ValueError("captured input changed before snapshot: " + label)
    with tempfile.TemporaryDirectory(prefix="relay-multidonor-inputs-") as directory:
        private = {label: Path(directory) / f"{label}.so" for label in images}
        for label, content in images.items():
            private[label].write_bytes(content)
        cases = [run_case(name, private["original"], private["candidate"],
                          private["spl_token"], private["associated_token"])
                 for name in CASE_NAMES]
    transactions = [step for case in cases for step in case["steps"]]
    transaction_hashes = [step["transaction_sha256"] for step in transactions]
    blockhashes = [step["recent_blockhash"] for step in transactions]
    signatures = [signature for step in transactions for signature in step["signatures"]]
    source_files = sources
    fixture_evidence = [{key: case[key] for key in
                         ("name", "fixture", "initial_balances", "plan", "expected_errors")}
                        for case in cases]
    report = {
        "schema": "donation-relay-multidonor-v2",
        "program": str(fixture.RELAY),
        "authority_boundary": {"production_relayer": str(fixture.RELAYER),
                               "private_key_retained": False,
                               "privileged_signer_injection": False},
        "inputs": {
            **{label: {"path": path.relative_to(root).as_posix(), "sha256": fixture.sha(images[label])}
               for label, (path, _expected) in pins.items()},
            "candidate": {"sha256": fixture.sha(images["candidate"]), "bytes": len(images["candidate"])},
            "candidate_provenance": {"mode": "supplied_binary_only", "source_build_verified_by_this_suite": False},
            "source_snapshot_context_only": True,
            "admitted_input_sha256": admitted,
            "source_manifest_sha256": source_digest,
            "source_files": source_files,
            "package_files": package_manifest(root),
        },
        "runtime": {"engine": "LiteSVM through solders 0.27.1", "clock": {
            "slot": FIXED_CLOCK.slot, "epoch_start_timestamp": FIXED_CLOCK.epoch_start_timestamp,
            "epoch": FIXED_CLOCK.epoch, "leader_schedule_epoch": FIXED_CLOCK.leader_schedule_epoch,
            "unix_timestamp": FIXED_CLOCK.unix_timestamp,
        }, "signature_verification": True, "blockhash_verification": True,
            "public_rpc": False},
        "case_count": len(cases),
        "fixture_identity_sha256": fixture.sha(json.dumps(
            fixture_evidence, sort_keys=True, separators=(",", ":")).encode()),
        "transaction_count": len(transactions),
        "individual_signature_count": len(signatures),
        "transaction_identity": {
            "unique_transaction_count": len(set(transaction_hashes)),
            "unique_blockhash_count": len(set(blockhashes)),
            "all_signatures_verified": all(all(step["signature_verification"]) for step in transactions),
        },
        "classification_counts": {
            name: sum(case["classification"] == name for case in cases)
            for name in ("equal_observed_behavior", "different_behavior",
                         "unsupported_fixture", "infrastructure_failure")
        },
        "original_positive_cases": sum(any(step["original"]["error"] is None for step in case["steps"])
                                       for case in cases),
        "strict_mismatches": [case["name"] for case in cases if case["classification"] == "different_behavior"],
        "unsupported": [
            {"family": "production-relayer epoch closure and distribution",
             "classification": "unsupported_fixture",
             "reason": "production relayer private key is not retained"},
            {"family": "Jupiter swap settlement",
             "classification": "unsupported_fixture",
             "reason": "cannot legitimately cross the same relayer gate"},
        ],
        "cases": cases,
    }
    A.recheck_inputs(admitted)
    if A.regular_bytes(candidate) != images["candidate"]:
        raise ValueError("candidate changed during execution")
    publisher.write((json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())
    A.recheck_inputs(admitted)
    if A.regular_bytes(candidate) != images["candidate"]:
        raise ValueError("candidate changed during publication")
    print(json.dumps({key: report[key] for key in
                      ("case_count", "transaction_count", "individual_signature_count",
                       "classification_counts", "original_positive_cases", "strict_mismatches")},
                     indent=2, sort_keys=True))
    return (
        report["classification_counts"]["equal_observed_behavior"] == report["case_count"]
        and report["transaction_identity"]["unique_transaction_count"] == report["transaction_count"]
        and report["transaction_identity"]["unique_blockhash_count"] == report["transaction_count"]
        and report["transaction_identity"]["all_signatures_verified"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--build-receipt", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    ok = execute(args.root.resolve(), args.candidate.resolve(), args.output.resolve(),
                 args.build_receipt.resolve() if args.build_receipt else None)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
