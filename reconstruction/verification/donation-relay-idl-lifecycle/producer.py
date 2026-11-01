#!/usr/bin/env python3
"""Signed, stateful differential for Donation Relay's reserved Anchor IDL path."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.rent import Rent
from solders.system_program import CreateAccountParams, create_account
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata


P = Pubkey.from_string
RELAY = P("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu")
SYSTEM = Pubkey.default()
IDL_SELECTOR = bytes([64, 244, 188, 120, 167, 233, 105, 10])
IDL_DISCRIMINATOR = bytes([24, 70, 98, 191, 58, 144, 123, 158])
ORIGINAL_SHA256 = "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563"
COMPUTE_RE = re.compile(r"Program \S+ consumed \d+ of \d+ compute units")
HEADER_LEN = 44


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def owned_key(case: str, label: str) -> Keypair:
    seed = hashlib.sha256(f"donation-relay-idl-lifecycle/{case}/{label}".encode()).digest()
    return Keypair.from_seed(seed)


def data_key(case: str, label: str) -> Pubkey:
    return Pubkey.from_bytes(hashlib.sha256(f"donation-relay-idl-data/{case}/{label}".encode()).digest())


def idl_address() -> tuple[Pubkey, Pubkey]:
    base = Pubkey.find_program_address([], RELAY)[0]
    return Pubkey.create_with_seed(base, "anchor:idl", RELAY), base


def idl_data(authority: Pubkey, capacity: int, content: bytes = b"", *, discriminator: bytes = IDL_DISCRIMINATOR) -> bytes:
    if capacity < len(content):
        raise ValueError("IDL capacity is smaller than content")
    return discriminator + bytes(authority) + len(content).to_bytes(4, "little") + content + bytes(capacity - len(content))


def decode_idl(data: bytes) -> dict[str, Any] | None:
    if len(data) < HEADER_LEN:
        return None
    length = int.from_bytes(data[40:44], "little")
    return {
        "discriminator": data[:8].hex(),
        "authority": str(Pubkey.from_bytes(data[8:40])),
        "data_len": length,
        "content_base64": base64.b64encode(data[44:44 + min(length, max(0, len(data) - 44))]).decode(),
    }


def snapshot(vm: LiteSVM, addresses: Iterable[Pubkey]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for address in sorted(set(addresses), key=str):
        value = vm.get_account(address)
        if value is None:
            result[str(address)] = None
            continue
        row: dict[str, Any] = {
            "lamports": value.lamports,
            "owner": str(value.owner),
            "executable": value.executable,
            "data_len": len(value.data),
            "data_sha256": sha(bytes(value.data)),
        }
        if value.executable:
            row["data_omitted"] = True
        else:
            row["data_base64"] = base64.b64encode(bytes(value.data)).decode()
            decoded = decode_idl(bytes(value.data))
            if decoded is not None:
                row["idl"] = decoded
        result[str(address)] = row
    return result


def account(lamports: int, data: bytes = b"", owner: Pubkey = SYSTEM) -> Account:
    return Account(lamports, data, owner)


def idl_ix(tag: int, payload: bytes, metas: list[AccountMeta]) -> Instruction:
    return Instruction(RELAY, IDL_SELECTOR + bytes([tag]) + payload, metas)


def create_ix(size: int, authority: Pubkey, target: Pubkey, base: Pubkey) -> Instruction:
    return idl_ix(0, size.to_bytes(8, "little"), [
        AccountMeta(authority, True, True),
        AccountMeta(target, False, True),
        AccountMeta(base, False, False),
        AccountMeta(SYSTEM, False, False),
        AccountMeta(RELAY, False, False),
    ])


def create_buffer_ix(buffer: Pubkey, authority: Pubkey) -> Instruction:
    return idl_ix(1, b"", [AccountMeta(buffer, False, True), AccountMeta(authority, True, False)])


def write_ix(target: Pubkey, authority: Pubkey, content: bytes, *, writable: bool = True) -> Instruction:
    payload = len(content).to_bytes(4, "little") + content
    return idl_ix(2, payload, [AccountMeta(target, False, writable), AccountMeta(authority, True, False)])


def set_buffer_ix(buffer: Pubkey, target: Pubkey, authority: Pubkey) -> Instruction:
    return idl_ix(3, b"", [
        AccountMeta(buffer, False, True), AccountMeta(target, False, True), AccountMeta(authority, True, False),
    ])


def set_authority_ix(target: Pubkey, authority: Pubkey, new_authority: Pubkey) -> Instruction:
    return idl_ix(4, bytes(new_authority), [AccountMeta(target, False, True), AccountMeta(authority, True, False)])


def close_ix(target: Pubkey, authority: Pubkey, destination: Pubkey) -> Instruction:
    return idl_ix(5, b"", [
        AccountMeta(target, False, True), AccountMeta(authority, True, False), AccountMeta(destination, False, True),
    ])


def resize_ix(target: Pubkey, authority: Pubkey, requested_total: int) -> Instruction:
    return idl_ix(6, requested_total.to_bytes(8, "little"), [
        AccountMeta(target, False, True), AccountMeta(authority, True, True), AccountMeta(SYSTEM, False, False),
    ])


@dataclass
class Fixture:
    case: str
    fee: Keypair
    old: Keypair
    new: Keypair
    outsider: Keypair
    buffer: Keypair
    destination: Pubkey
    canonical: Pubkey
    base: Pubkey
    accounts: dict[Pubkey, Account]

    @classmethod
    def create(cls, case: str) -> "Fixture":
        fee = owned_key(case, "fee")
        old = owned_key(case, "old-authority")
        new = owned_key(case, "new-authority")
        outsider = owned_key(case, "outsider")
        buffer = owned_key(case, "buffer")
        destination = data_key(case, "close-destination")
        canonical, base = idl_address()
        accounts = {
            fee.pubkey(): account(50_000_000_000),
            old.pubkey(): account(50_000_000_000),
            new.pubkey(): account(50_000_000_000),
            outsider.pubkey(): account(50_000_000_000),
            destination: account(7_000_000),
        }
        return cls(case, fee, old, new, outsider, buffer, destination, canonical, base, accounts)

    def watched(self) -> set[Pubkey]:
        return set(self.accounts) | {self.canonical, self.base, self.buffer.pubkey(), self.destination, RELAY, SYSTEM}


class Pair:
    def __init__(self, original: Path, candidate: Path, fixture: Fixture):
        self.fixture = fixture
        self.vms: dict[str, LiteSVM] = {}
        for side, image in (("original", original), ("candidate", candidate)):
            vm = (LiteSVM().with_sigverify(True).with_blockhash_check(True)
                  .with_transaction_history(256).with_log_bytes_limit(None))
            vm.add_program_from_file(RELAY, image)
            for address, value in fixture.accounts.items():
                vm.set_account(address, value)
            self.vms[side] = vm

    def add_account(self, address: Pubkey, value: Account) -> None:
        self.fixture.accounts[address] = value
        for vm in self.vms.values():
            vm.set_account(address, value)

    def transact(self, name: str, instructions: list[Instruction], signers: list[Keypair], watch: set[Pubkey] | None = None) -> dict[str, Any]:
        original, candidate = self.vms.values()
        original.expire_blockhash()
        candidate.expire_blockhash()
        blockhash = original.latest_blockhash()
        if blockhash != candidate.latest_blockhash():
            raise RuntimeError("independent LiteSVM blockhashes diverged")
        all_signers = [self.fixture.fee, *signers]
        unique_signers = list({str(s.pubkey()): s for s in all_signers}.values())
        tx = Transaction.new_signed_with_payer(instructions, self.fixture.fee.pubkey(), unique_signers, blockhash)
        # solders verifies no signature when the vector is empty, and all([]) is true.
        verified = bool(tx.signatures) and all(tx.verify_with_results())
        if not verified:
            raise RuntimeError("locally signed transaction failed signature verification")
        addresses = self.fixture.watched() | set(watch or ()) | set(tx.message.account_keys)
        rows = {side: self._run(vm, tx, addresses) for side, vm in self.vms.items()}
        mismatches = self.comparison_mismatches(rows["original"], rows["candidate"])
        return {
            "name": name,
            "signature": str(tx.signatures[0]),
            "all_signatures": [str(signature) for signature in tx.signatures],
            "signature_verified": verified,
            "mismatches": mismatches,
            "original": rows["original"],
            "candidate": rows["candidate"],
        }

    @staticmethod
    def _run(vm: LiteSVM, tx: Transaction, addresses: set[Pubkey]) -> dict[str, Any]:
        before = snapshot(vm, addresses)
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = json.loads(meta.to_json())
        after = snapshot(vm, addresses)
        rollback_changes: list[str] = []
        if failed:
            fee = str(tx.message.account_keys[0])
            rollback_changes = [key for key in before if key != fee and before[key] != after[key]]
            if rollback_changes:
                raise AssertionError(f"failed transaction changed non-fee state: {rollback_changes}")
        logs = list(meta.logs())
        return {
            "error": str(result.err()) if failed else None,
            "compute_units": meta.compute_units_consumed(),
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
        """One comparison path for real receipts and their mutation controls."""
        left, right = cls._comparable(original), cls._comparable(candidate)
        return sorted(key for key in left if left[key] != right[key])

    @staticmethod
    def _comparable(row: dict[str, Any]) -> dict[str, Any]:
        def state(stage: str) -> dict[str, Any]:
            value = json.loads(json.dumps(row[stage]))
            value.pop(str(RELAY), None)
            return value

        return {
            "error": row["error"],
            "relevant_logs": [line for line in row["logs"] if not COMPUTE_RE.fullmatch(line)],
            "events": row["events"],
            "inner_instructions": row["inner_instructions"],
            "return_data": row["return_data"],
            "before": state("before"),
            "after": state("after"),
        }


def error_contains(step: dict[str, Any], code: int) -> bool:
    return f"Custom({code})" in (step["original"]["error"] or "").replace(" ", "")


def successful(step: dict[str, Any]) -> bool:
    return step["original"]["error"] is None and step["candidate"]["error"] is None


def stateful_lifecycle(original: Path, candidate: Path) -> dict[str, Any]:
    f = Fixture.create("stateful-lifecycle")
    pair = Pair(original, candidate, f)
    steps: list[dict[str, Any]] = []

    def submit(name: str, ixs: list[Instruction], signers: list[Keypair], watch: set[Pubkey] | None = None) -> dict[str, Any]:
        step = pair.transact(name, ixs, signers, watch)
        steps.append(step)
        return step

    submit("create", [create_ix(128, f.old.pubkey(), f.canonical, f.base)], [f.old])
    submit("resize_empty", [resize_ix(f.canonical, f.old.pubkey(), 300)], [f.old])
    buffer_space = 300
    buffer_create = create_account(CreateAccountParams(
        from_pubkey=f.fee.pubkey(), to_pubkey=f.buffer.pubkey(),
        lamports=Rent.default().minimum_balance(buffer_space), space=buffer_space, owner=RELAY,
    ))
    submit("create_buffer", [buffer_create, create_buffer_ix(f.buffer.pubkey(), f.old.pubkey())], [f.buffer, f.old])
    first_bytes = b'{"name":"relay-idl-lifecycle","version":1}'
    submit("write_buffer", [write_ix(f.buffer.pubkey(), f.old.pubkey(), first_bytes)], [f.old])
    submit("set_buffer", [set_buffer_ix(f.buffer.pubkey(), f.canonical, f.old.pubkey())], [f.old])
    submit("resize_nonempty_rejected", [resize_ix(f.canonical, f.old.pubkey(), 512)], [f.old])
    submit("set_authority", [set_authority_ix(f.canonical, f.old.pubkey(), f.new.pubkey())], [f.old])
    submit("old_authority_write_rejected", [write_ix(f.canonical, f.old.pubkey(), b"old")], [f.old])
    submit("new_authority_write", [write_ix(f.canonical, f.new.pubkey(), b"\nnew-authority")], [f.new])
    destination_before = pair.vms["original"].get_account(f.destination).lamports
    canonical_before_close = pair.vms["original"].get_account(f.canonical).lamports
    submit("close", [close_ix(f.canonical, f.new.pubkey(), f.destination)], [f.new])
    submit("repeated_close_rejected", [close_ix(f.canonical, f.new.pubkey(), f.destination)], [f.new])

    problems: list[str] = []
    problems.extend(f"{step['name']}:{field}" for step in steps for field in step["mismatches"])
    for name in ("create", "resize_empty", "create_buffer", "write_buffer", "set_buffer", "set_authority", "new_authority_write", "close"):
        step = next(row for row in steps if row["name"] == name)
        if not successful(step):
            problems.append(name + ":expected_success")
    expected_errors = {"resize_nonempty_rejected": 1002, "old_authority_write_rejected": 2001, "repeated_close_rejected": 3012}
    for name, code in expected_errors.items():
        if not error_contains(next(row for row in steps if row["name"] == name), code):
            problems.append(f"{name}:expected_{code}")
    canonical_after_set = next(row for row in steps if row["name"] == "set_buffer")["original"]["after"][str(f.canonical)]
    if canonical_after_set["idl"]["content_base64"] != base64.b64encode(first_bytes).decode():
        problems.append("set_buffer:content")
    after_resize = next(row for row in steps if row["name"] == "resize_empty")["original"]["after"][str(f.canonical)]
    if after_resize["data_len"] != 300:
        problems.append("resize_empty:length")
    after_close = next(row for row in steps if row["name"] == "close")["original"]["after"]
    closed = after_close[str(f.canonical)]
    if closed is not None and not (closed["lamports"] == 0 and closed["data_len"] == 0 and closed["owner"] == str(SYSTEM)):
        problems.append("close:account_not_closed")
    if after_close[str(f.destination)]["lamports"] != destination_before + canonical_before_close:
        problems.append("close:rent_not_transferred")
    return {
        "name": "stateful_lifecycle",
        "classification": "equal_observed_behavior" if not problems else "different_behavior",
        "problems": problems,
        "operation_order": [step["name"] for step in steps],
        "steps": steps,
    }


def admission_matrix(original: Path, candidate: Path) -> dict[str, Any]:
    f = Fixture.create("admission-matrix")
    pair = Pair(original, candidate, f)
    short = data_key(f.case, "short")
    wrong_owner = data_key(f.case, "wrong-owner")
    bad_header = data_key(f.case, "bad-header")
    poor_buffer = data_key(f.case, "poor-buffer")
    alias = data_key(f.case, "noncanonical-valid-idl")
    too_small = data_key(f.case, "capacity-error")
    pair.add_account(short, account(Rent.default().minimum_balance(7), bytes(7), RELAY))
    pair.add_account(wrong_owner, account(10_000_000, idl_data(f.old.pubkey(), 16), SYSTEM))
    pair.add_account(bad_header, account(10_000_000, idl_data(f.old.pubkey(), 16, discriminator=b"BAD-DISC"), RELAY))
    pair.add_account(poor_buffer, account(1, bytes(100), RELAY))
    pair.add_account(alias, account(Rent.default().minimum_balance(80), idl_data(f.old.pubkey(), 36), RELAY))
    pair.add_account(too_small, account(Rent.default().minimum_balance(44), idl_data(f.old.pubkey(), 0), RELAY))

    cases: list[tuple[str, list[Instruction], list[Keypair], int | None]] = [
        ("write_before_initialization", [write_ix(f.canonical, f.old.pubkey(), b"x")], [f.old], 3012),
        ("resize_before_initialization", [resize_ix(f.canonical, f.old.pubkey(), 80)], [f.old], 3012),
        ("incorrect_owner", [write_ix(wrong_owner, f.old.pubkey(), b"x")], [f.old], 3007),
        ("short_account_header", [write_ix(short, f.old.pubkey(), b"x")], [f.old], 3001),
        ("incorrect_discriminator", [write_ix(bad_header, f.old.pubkey(), b"x")], [f.old], 3002),
        ("insufficient_rent_buffer", [create_buffer_ix(poor_buffer, f.old.pubkey())], [f.old], 2005),
        ("unauthorized_signer", [write_ix(alias, f.outsider.pubkey(), b"x")], [f.outsider], 2001),
        ("readonly_idl", [write_ix(alias, f.old.pubkey(), b"x", writable=False)], [f.old], 2000),
        ("write_capacity_error", [write_ix(too_small, f.old.pubkey(), b"x")], [f.old], None),
        ("noncanonical_valid_idl", [write_ix(alias, f.old.pubkey(), b"alias")], [f.old], None),
        ("truncated_write_payload", [idl_ix(2, b"\x04\x00", [])], [], 102),
        ("invalid_operation_tag", [idl_ix(255, b"", [])], [], 102),
        ("missing_create_accounts", [idl_ix(0, (80).to_bytes(8, "little"), [])], [], 3005),
    ]
    steps: list[dict[str, Any]] = []
    problems: list[str] = []
    for name, ixs, signers, expected in cases:
        step = pair.transact(name, ixs, signers)
        steps.append(step)
        problems.extend(f"{name}:{field}" for field in step["mismatches"])
        if name == "noncanonical_valid_idl":
            if not successful(step):
                problems.append(name + ":expected_success")
        elif name == "write_capacity_error":
            if step["original"]["error"] is None:
                problems.append(name + ":expected_failure")
        elif expected is not None and not error_contains(step, expected):
            problems.append(f"{name}:expected_{expected}")

    # An oversized request is admitted but grows by at most 10,000 bytes.
    fresh = Fixture.create("oversized-resize")
    resize_pair = Pair(original, candidate, fresh)
    create_step = resize_pair.transact("oversized_setup_create", [create_ix(0, fresh.old.pubkey(), fresh.canonical, fresh.base)], [fresh.old])
    resize_step = resize_pair.transact("oversized_resize_capped", [resize_ix(fresh.canonical, fresh.old.pubkey(), 1_000_000)], [fresh.old])
    steps.extend([create_step, resize_step])
    problems.extend(f"{step['name']}:{field}" for step in (create_step, resize_step) for field in step["mismatches"])
    if not successful(create_step) or not successful(resize_step):
        problems.append("oversized_resize:expected_success")
    resized = resize_step["original"]["after"][str(fresh.canonical)]
    if resized["data_len"] != HEADER_LEN + 10_000:
        problems.append("oversized_resize:cap")

    # Create must target the canonical address selected by the system CPI.
    wrong = Fixture.create("wrong-canonical-create")
    wrong_pair = Pair(original, candidate, wrong)
    wrong_target = data_key(wrong.case, "wrong-target")
    wrong_step = wrong_pair.transact("wrong_canonical_create", [create_ix(80, wrong.old.pubkey(), wrong_target, wrong.base)], [wrong.old], {wrong_target})
    steps.append(wrong_step)
    problems.extend(f"wrong_canonical_create:{field}" for field in wrong_step["mismatches"])
    if wrong_step["original"]["error"] is None:
        problems.append("wrong_canonical_create:expected_failure")

    return {
        "name": "admission_matrix",
        "classification": "equal_observed_behavior" if not problems else "different_behavior",
        "problems": problems,
        "steps": steps,
    }


def comparator_controls(step: dict[str, Any]) -> dict[str, Any]:
    """Replay mutated copies of a recorded step through the case comparison.

    The comparison in Pair.transact is the witness behind every
    equal_observed_behavior classification, so these controls must prove that
    this comparison still notices an altered compared field. Comparing two
    hand-built literals stays true even if the comparison itself stops
    reporting differences, so each control mutates a deep copy of a real
    recorded candidate row and requires the compared field it alters to be
    reported.
    """
    controls: dict[str, bool] = {}
    for label, field, mutate in (
        ("account_state", "after",
         lambda row: row["after"].update({"negative-control-account": {"lamports": 2}})),
        ("error", "error",
         lambda row: row.update(error="Custom(1)")),
        ("event_payload", "events",
         lambda row: row["events"].append("Program data: altered")),
    ):
        changed = json.loads(json.dumps(step["candidate"]))
        mutate(changed)
        mismatches = Pair.comparison_mismatches(step["original"], changed)
        controls[label] = field in mismatches
    return {"kind": "comparator mutation controls replayed through the case comparison", "detected": controls, "all_detected": all(controls.values())}


def source_manifest(root: Path) -> tuple[dict[str, str], str]:
    base = root / "programs/donation-relay"
    rows = {path.relative_to(root).as_posix(): file_sha(path) for path in sorted(base.rglob("*")) if path.is_file()}
    encoded = json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()
    return rows, sha(encoded)


def package_manifest(root: Path) -> dict[str, str]:
    base = Path(__file__).resolve().parent
    return {path.relative_to(root).as_posix(): file_sha(path) for path in sorted(base.iterdir()) if path.is_file() and path.name != "__pycache__"}


def transaction_identity(cases: list[dict[str, Any]]) -> dict[str, Any]:
    steps = [step for case in cases for step in case["steps"]]
    signatures = [step["signature"] for step in steps]
    return {
        "transaction_count": len(signatures),
        "unique_transaction_count": len(set(signatures)),
        "all_transactions_signature_verified": all(step["signature_verified"] for step in steps),
    }


def execute(root: Path, candidate: Path, output: Path) -> bool:
    if output.exists():
        raise SystemExit(f"refusing to overwrite existing receipt: {output}")
    original = root / "evidence/dependencies/donation_relay/deployed.so"
    if not original.is_file() or file_sha(original) != ORIGINAL_SHA256:
        raise SystemExit(f"captured Relay is missing or fails SHA-256 binding: {original}")
    if not candidate.is_file():
        raise SystemExit(f"candidate does not exist: {candidate}")
    sources, source_digest = source_manifest(root)
    cases = [stateful_lifecycle(original, candidate), admission_matrix(original, candidate)]
    identities = transaction_identity(cases)
    controls = comparator_controls(cases[0]["steps"][0])
    report = {
        "schema": "donation-relay-idl-lifecycle-v1",
        "program": str(RELAY),
        "selector_hex": IDL_SELECTOR.hex(),
        "inputs": {
            "upstream_commit": "2bb05a51af71a8b8e3ba834f16c8db720f57ce2b",
            "captured_elf": {"path": original.relative_to(root).as_posix(), "bytes": original.stat().st_size, "sha256": file_sha(original)},
            "candidate_elf": {"bytes": candidate.stat().st_size, "sha256": file_sha(candidate)},
            "source_manifest_sha256": source_digest,
            "source_files": sources,
            "test_package_files": package_manifest(root),
        },
        "runtime": {
            "engine": "LiteSVM through solders 0.27.1",
            "signature_verification": True,
            "blockhash_verification": True,
            "privileged_signer_injection": False,
            "public_rpc": False,
            "comparison": "same signed transaction in independent persistent VMs; exact errors, non-CU logs, events, inner instructions, return data, and complete watched account state",
        },
        "supported_operations": ["Create", "CreateBuffer", "Write", "SetBuffer", "SetAuthority", "Close", "Resize"],
        "case_count": len(cases),
        "matching_cases": sum(case["classification"] == "equal_observed_behavior" for case in cases),
        "different_cases": [case["name"] for case in cases if case["classification"] == "different_behavior"],
        "transaction_identity": identities,
        "negative_controls": controls,
        "cases": cases,
        "limitations": [
            "runtime equality does not establish historical source completeness or byte identity",
            "IDL instructions emit no Anchor events, so event comparison is retained but successful event coverage is not applicable",
            "account-borrow conflicts requiring an already-held loader borrow are not forgeable by ordinary top-level signed transactions",
            "the candidate is the ordinary pinned macOS SBF build, not PR #2305's separately qualified exact Linux linker layout",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    ok = (
        report["matching_cases"] == report["case_count"]
        and not report["different_cases"]
        and controls["all_detected"]
        and identities["transaction_count"] == identities["unique_transaction_count"]
        and identities["all_transactions_signature_verified"]
    )
    print(json.dumps({
        "case_count": report["case_count"],
        "matching_cases": report["matching_cases"],
        "different_cases": report["different_cases"],
        **identities,
        "negative_controls_detected": controls["all_detected"],
    }, indent=2, sort_keys=True))
    return ok


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if execute(args.root.resolve(), args.candidate.resolve(), args.output.resolve()) else 1)


if __name__ == "__main__":
    main()
