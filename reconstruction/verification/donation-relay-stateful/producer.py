#!/usr/bin/env python3
"""Signed, stateful Donation Relay differential for the reproducible public paths.

The production relayer key is deliberately not forged.  Relayer-only success
families are reported as unsupported unless a caller supplies a genuine key,
which this tool has no interface to accept.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata


P = Pubkey.from_string
RELAY = P("RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu")
RELAYER = P("RLYRf96HAJSbbXCNS6ibQYnkxtb6kbfuFxqEkm9oQUc")
TOKEN = P("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ATA = P("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
ORIGINAL_SHA = "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563"
TOKEN_SHA = "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697"
ATA_SHA = "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d"
COMPUTE_RE = re.compile(r"Program \S+ consumed \d+ of \d+ compute units")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha(path: Path) -> str:
    return sha(path.read_bytes())


def key(label: str) -> Keypair:
    return Keypair.from_seed(hashlib.sha256(("relay-stateful-owned/" + label).encode()).digest())


def pub(label: str) -> Pubkey:
    return Pubkey.from_bytes(hashlib.sha256(("relay-stateful-data/" + label).encode()).digest())


def discriminator(namespace: str, name: str) -> bytes:
    return hashlib.sha256(f"{namespace}:{name}".encode()).digest()[:8]


def pda(*seeds: bytes) -> tuple[Pubkey, int]:
    return Pubkey.find_program_address(list(seeds), RELAY)


def ata(owner: Pubkey, mint: Pubkey) -> Pubkey:
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(decimals: int = 6, supply: int = 10**12) -> bytes:
    data = bytearray(82)
    data[36:44] = supply.to_bytes(8, "little")
    data[44] = decimals
    data[45] = 1
    return bytes(data)


def token_data(mint: Pubkey, authority: Pubkey, amount: int) -> bytes:
    data = bytearray(165)
    data[:32] = bytes(mint)
    data[32:64] = bytes(authority)
    data[64:72] = amount.to_bytes(8, "little")
    data[108] = 1
    return bytes(data)


def account(lamports: int, data: bytes = b"", owner: Pubkey = SYSTEM) -> Account:
    return Account(lamports, data, owner)


def snap(vm: LiteSVM, addresses: set[Pubkey]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for address in sorted(addresses, key=str):
        value = vm.get_account(address)
        if value is None:
            result[str(address)] = None
        elif value.executable:
            # Executed images are hash-bound separately; embedding megabytes of
            # program bytes in every transaction receipt obscures state changes.
            result[str(address)] = {"lamports": value.lamports, "owner": str(value.owner), "executable": True}
        else:
            result[str(address)] = {
                "lamports": value.lamports,
                "owner": str(value.owner),
                "executable": False,
                "data_len": len(value.data),
                "data_sha256": sha(bytes(value.data)),
                "data_base64": base64.b64encode(bytes(value.data)).decode(),
            }
    return result


def decoded_state(snapshot: dict[str, Any], fixture: "Fixture") -> dict[str, Any]:
    def data(address: Pubkey) -> bytes:
        row = snapshot.get(str(address))
        return b"" if row is None else base64.b64decode(row["data_base64"])

    tracker = data(fixture.epoch)
    debouncer = data(fixture.debouncer)
    source = data(fixture.source)
    destination = data(fixture.destination)
    return {
        "epoch": None if len(tracker) < 90 else int.from_bytes(tracker[74:90], "little"),
        "epoch_state": None if len(tracker) < 10 else tracker[9],
        "debouncer_total": None if len(debouncer) < 82 else int.from_bytes(debouncer[74:82], "little"),
        "debouncer_state": None if len(debouncer) < 10 else debouncer[9],
        "source_tokens": None if len(source) < 72 else int.from_bytes(source[64:72], "little"),
        "destination_tokens": None if len(destination) < 72 else int.from_bytes(destination[64:72], "little"),
    }


@dataclass
class Fixture:
    fee: Keypair
    donor: Keypair
    outsider: Keypair
    mint: Pubkey
    config: bytes
    whitelist: Pubkey
    epoch: Pubkey
    debouncer: Pubkey
    source: Pubkey
    destination: Pubkey
    event: Pubkey
    accounts: dict[Pubkey, Account]

    @classmethod
    def create(cls) -> "Fixture":
        fee, donor, outsider = key("fee"), key("donor"), key("outsider")
        mint = pub("mint")
        config = bytes(pub("config"))
        whitelist, whitelist_bump = pda(b"mint_whitelist_v1")
        epoch = pda(b"epoch_tracker_v1", config, bytes(mint))[0]
        debouncer = pda(b"debouncer_v1", config, bytes(mint))[0]
        source = ata(donor.pubkey(), mint)
        destination = ata(debouncer, mint)
        event = pda(b"__event_authority")[0]
        accounts = {
            fee.pubkey(): account(10**11),
            donor.pubkey(): account(10**11),
            outsider.pubkey(): account(10**11),
            mint: account(10**9, mint_data(), TOKEN),
            source: account(3_000_000, token_data(mint, donor.pubkey(), 10_000_000), TOKEN),
            whitelist: account(10**9, discriminator("account", "MintWhitelistV1") + bytes([whitelist_bump])
                               + (0).to_bytes(4, "little") + bytes(1024), RELAY),
            epoch: account(0),
            debouncer: account(0),
            destination: account(0),
            event: account(0),
        }
        return cls(fee, donor, outsider, mint, config, whitelist, epoch, debouncer, source, destination, event, accounts)

    def watch(self) -> set[Pubkey]:
        return set(self.accounts)

    def donation(self, amount: int, *, message: bytes = b"stateful donation", tip: int = 125,
                 source: Pubkey | None = None, epoch: Pubkey | None = None,
                 debouncer: Pubkey | None = None) -> Instruction:
        metas = [
            AccountMeta(epoch or self.epoch, False, True),
            AccountMeta(debouncer or self.debouncer, False, True),
            AccountMeta(self.destination, False, True),
            AccountMeta(self.mint, False, True),
            AccountMeta(source or self.source, False, True),
            AccountMeta(self.donor.pubkey(), True, True),
            AccountMeta(self.whitelist, False, False),
            AccountMeta(ATA, False, False),
            AccountMeta(TOKEN, False, False),
            AccountMeta(SYSTEM, False, False),
            AccountMeta(self.event, False, False),
            AccountMeta(RELAY, False, False),
        ]
        data = (discriminator("global", "donate_v1") + amount.to_bytes(8, "little") + self.config
                + tip.to_bytes(2, "little") + len(message).to_bytes(4, "little") + message
                + bytes(self.outsider.pubkey()))
        return Instruction(RELAY, data, metas)

    def upsert_wrong_signer(self) -> Instruction:
        data = discriminator("global", "upsert_mint_whitelist_v1") + (1).to_bytes(4, "little") + bytes(self.mint)
        return Instruction(RELAY, data, [
            AccountMeta(self.whitelist, False, True),
            AccountMeta(self.outsider.pubkey(), True, True),
            AccountMeta(SYSTEM, False, False),
        ])

    def close_wrong_signer(self) -> tuple[Instruction, set[Pubkey]]:
        distribution = pda(b"distribution_v1", self.config, bytes(self.mint), (0).to_bytes(16, "little"))[0]
        vault = ata(distribution, self.mint)
        for address in (distribution, vault):
            self.accounts.setdefault(address, account(0))
        data = discriminator("global", "close_donation_epoch_v1") + self.config + (0).to_bytes(16, "little")
        metas = [
            AccountMeta(distribution, False, True), AccountMeta(vault, False, True),
            AccountMeta(self.epoch, False, True), AccountMeta(self.debouncer, False, True),
            AccountMeta(self.destination, False, True), AccountMeta(self.mint, False, True),
            AccountMeta(TOKEN, False, False), AccountMeta(self.outsider.pubkey(), True, True),
            AccountMeta(ATA, False, False), AccountMeta(SYSTEM, False, False), AccountMeta(self.event, False, False),
            AccountMeta(RELAY, False, False),
        ]
        return Instruction(RELAY, data, metas), {distribution, vault}


class Pair:
    def __init__(self, original: Path, candidate: Path, token: Path, associated: Path, fixture: Fixture):
        self.fixture = fixture
        self.vms = {}
        for side, image in (("original", original), ("candidate", candidate)):
            vm = LiteSVM().with_sigverify(True).with_blockhash_check(True).with_transaction_history(256).with_log_bytes_limit(None)
            vm.add_program_from_file(RELAY, image)
            vm.add_program_from_file(TOKEN, token)
            vm.add_program_from_file(ATA, associated)
            for address, value in fixture.accounts.items():
                vm.set_account(address, value)
            self.vms[side] = vm

    def add_account(self, address: Pubkey, value: Account) -> None:
        self.fixture.accounts[address] = value
        for vm in self.vms.values():
            vm.set_account(address, value)

    def transact(self, instruction: Instruction, signers: list[Keypair], watch: set[Pubkey]) -> dict[str, Any]:
        left, right = self.vms.values()
        left.expire_blockhash()
        right.expire_blockhash()
        if left.latest_blockhash() != right.latest_blockhash():
            raise RuntimeError("LiteSVM blockhashes diverged")
        tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), instruction], self.fixture.fee.pubkey(),
            [self.fixture.fee, *signers], left.latest_blockhash(),
        )
        if not all(tx.verify_with_results()):
            raise RuntimeError("locally signed transaction did not verify")
        addresses = watch | set(tx.message.account_keys)
        rows = {side: self._run(vm, tx, addresses) for side, vm in self.vms.items()}
        comparable = {side: self._comparable(row) for side, row in rows.items()}
        mismatches = [field for field in comparable["original"] if comparable["original"][field] != comparable["candidate"][field]]
        return {
            "signature": str(tx.signatures[0]),
            "signature_verified": all(tx.verify_with_results()),
            "mismatches": mismatches,
            "original": rows["original"],
            "candidate": rows["candidate"],
        }

    @staticmethod
    def _run(vm: LiteSVM, tx: Transaction, addresses: set[Pubkey]) -> dict[str, Any]:
        before = snap(vm, addresses)
        result = vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        raw = json.loads(meta.to_json())
        after = snap(vm, addresses)
        if failed:
            fee = str(tx.message.account_keys[0])
            changed = [address for address in before if address != fee and before[address] != after[address]]
            if changed:
                raise AssertionError(f"failed transaction changed non-fee state: {changed}")
        logs = list(meta.logs())
        return {
            "error": str(result.err()) if failed else None,
            "compute_units": meta.compute_units_consumed(),
            "logs": logs,
            "events": [line for line in logs if line.startswith("Program data: ")],
            "inner_instructions": raw["inner_instructions"],
            "return_data": raw["return_data"],
            "before": before,
            "after": after,
        }

    @staticmethod
    def _comparable(row: dict[str, Any]) -> dict[str, Any]:
        def state(stage: str) -> dict[str, Any]:
            result = json.loads(json.dumps(row[stage]))
            # The two explicitly hashed program images necessarily have different
            # executable account bytes in a non-byte-identical candidate build.
            # Their invoked identity and executable bit remain compared in logs.
            result.pop(str(RELAY), None)
            return result

        return {
            "error": row["error"],
            "relevant_logs": [line for line in row["logs"] if not COMPUTE_RE.fullmatch(line)],
            "events": row["events"],
            "inner_instructions": row["inner_instructions"],
            "return_data": row["return_data"],
            "before": state("before"),
            "after": state("after"),
        }


def run_case(name: str, original: Path, candidate: Path, token: Path, associated: Path) -> dict[str, Any]:
    fixture = Fixture.create()
    pair = Pair(original, candidate, token, associated, fixture)
    steps: list[dict[str, Any]] = []

    def submit(ix: Instruction, signers: list[Keypair] | None = None) -> dict[str, Any]:
        row = pair.transact(ix, signers or [fixture.donor], fixture.watch())
        row["original_state"] = decoded_state(row["original"]["after"], fixture)
        row["candidate_state"] = decoded_state(row["candidate"]["after"], fixture)
        steps.append(row)
        return row

    expected: dict[str, Any] = {}
    if name == "repeat_same_epoch":
        submit(fixture.donation(1_000_000))
        submit(fixture.donation(2_000_000, message=b"second donation"))
        expected = {"error": None, "epoch": 0, "debouncer_total": 3_000_000,
                    "source_tokens": 7_000_000, "destination_tokens": 3_000_000}
    elif name == "zero_donation":
        submit(fixture.donation(0))
        expected = {"error": None, "epoch": 0, "debouncer_total": 0,
                    "source_tokens": 10_000_000, "destination_tokens": 0}
    elif name == "message_limit":
        submit(fixture.donation(1, message=b"m" * 256))
        expected = {"error_contains": "Custom(6009)", "rollback": True}
    elif name == "tip_limit":
        submit(fixture.donation(1, tip=10001))
        expected = {"error_contains": "Custom(6018)", "rollback": True}
    elif name == "insufficient_balance":
        submit(fixture.donation(10_000_001))
        expected = {"error_contains": "Custom(1)", "rollback": True}
    elif name == "wrong_epoch_pda":
        wrong = pda(b"epoch_tracker_v1", bytes(pub("other-config")), bytes(fixture.mint))[0]
        pair.add_account(wrong, account(0))
        submit(fixture.donation(1, epoch=wrong))
        expected = {"error_contains": "Custom(2006)", "rollback": True}
    elif name == "wrong_source_mint":
        wrong_source = pub("wrong-source")
        pair.add_account(wrong_source, account(3_000_000, token_data(pub("other-mint"), fixture.donor.pubkey(), 10), TOKEN))
        submit(fixture.donation(1, source=wrong_source))
        expected = {"error_contains": "Custom(2009)", "rollback": True}
    elif name == "wrong_debouncer_owner":
        pair.add_account(fixture.debouncer, account(10**9, bytes(82), SYSTEM))
        submit(fixture.donation(1))
        expected = {"error_contains": "Custom(0)", "rollback": True}
    elif name == "second_failure_rolls_back":
        submit(fixture.donation(777))
        baseline = steps[-1]["original"]["after"]
        submit(fixture.donation(1, message=b"m" * 256))
        expected = {"error_contains": "Custom(6009)", "rollback_to_prior_success": baseline}
    elif name == "whitelist_requires_production_relayer":
        submit(fixture.upsert_wrong_signer(), [fixture.outsider])
        expected = {"error_contains": "Custom(2012)", "rollback": True}
    elif name == "close_requires_production_relayer":
        first = submit(fixture.donation(777, message=b"close authority setup"))
        if first["original"]["error"] is not None:
            raise AssertionError("close authority setup donation failed")
        close, new_accounts = fixture.close_wrong_signer()
        for address in new_accounts:
            pair.add_account(address, account(0))
        submit(close, [fixture.outsider])
        expected = {"error_contains": "Custom(2012)", "rollback": True}
    else:
        raise ValueError(name)

    problems: list[str] = []
    for index, step in enumerate(steps):
        problems.extend(f"step_{index}:{field}" for field in step["mismatches"])
    final = steps[-1]
    original_error = final["original"]["error"]
    state = final["original_state"]
    if "error" in expected and original_error != expected["error"]:
        problems.append("original_expected_error")
    if "error_contains" in expected and expected["error_contains"].replace(" ", "") not in (original_error or "").replace(" ", ""):
        problems.append("original_expected_error")
    for field in ("epoch", "debouncer_total", "source_tokens", "destination_tokens"):
        if field in expected and state[field] != expected[field]:
            problems.append("original_expected_" + field)
    if expected.get("rollback_to_prior_success") is not None:
        before = final["original"]["before"]
        after = final["original"]["after"]
        fee = str(fixture.fee.pubkey())
        if any(before[k] != after[k] for k in before if k != fee):
            problems.append("original_failed_step_not_rolled_back")
    return {"name": name, "classification": "equal_observed_behavior" if not problems else "different_behavior",
            "problems": problems, "expected": {k: v for k, v in expected.items() if k != "rollback_to_prior_success"},
            "steps": steps}


CASES = [
    "repeat_same_epoch", "zero_donation", "message_limit", "tip_limit",
    "insufficient_balance", "wrong_epoch_pda", "wrong_source_mint",
    "wrong_debouncer_owner", "second_failure_rolls_back",
    "whitelist_requires_production_relayer", "close_requires_production_relayer",
]


def source_manifest(root: Path) -> tuple[dict[str, str], str]:
    base = root / "programs/donation-relay"
    rows = {str(path.relative_to(root)): file_sha(path) for path in sorted(base.rglob("*")) if path.is_file()}
    return rows, sha(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode())


def transaction_identity(cases: list[dict[str, Any]]) -> dict[str, Any]:
    steps = [step for case in cases for step in case["steps"]]
    signatures = [step["signature"] for step in steps]
    return {
        "count": len(signatures),
        "unique_count": len(set(signatures)),
        "all_signatures_verified": all(step["signature_verified"] for step in steps),
    }


def execute(root: Path, candidate: Path, output: Path) -> bool:
    original = root / "evidence/dependencies/donation_relay/deployed.so"
    token = root / "evidence/dependencies/spl_token/deployed.so"
    associated = root / "evidence/dependencies/associated_token/deployed.so"
    pins = {"original": (original, ORIGINAL_SHA), "spl_token": (token, TOKEN_SHA), "associated_token": (associated, ATA_SHA)}
    for label, (path, expected) in pins.items():
        if not path.is_file() or file_sha(path) != expected:
            raise SystemExit(f"{label} input is missing or fails its retained SHA-256 binding: {path}")
    if not candidate.is_file():
        raise SystemExit(f"candidate does not exist: {candidate}")
    sources, source_digest = source_manifest(root)
    cases = [run_case(name, original, candidate, token, associated) for name in CASES]
    identities = transaction_identity(cases)
    negative_control = json.loads(json.dumps(cases[0]["steps"][-1]["candidate_state"]))
    negative_control["debouncer_total"] += 1
    control_detected = negative_control != cases[0]["steps"][-1]["original_state"]
    unsupported = [
        {"family": "upsert_mint_whitelist_v1 success", "classification": "unsupported_fixture", "reason": "production relayer private key is not retained"},
        {"family": "close_donation_epoch_v1 success and next epoch", "classification": "unsupported_fixture", "reason": "production relayer private key is not retained"},
        {"family": "distribute_non_swap_output_mint_v1 success", "classification": "unsupported_fixture", "reason": "requires the same unavailable production relayer signature"},
        {"family": "Jupiter swap instructions", "classification": "unsupported_fixture", "reason": "non-swap lifecycle cannot legitimately cross its relayer gate"},
    ]
    report = {
        "schema": "donation-relay-stateful-v1",
        "program": str(RELAY),
        "authority_boundary": {"production_relayer": str(RELAYER), "private_key_retained": False, "privileged_signer_injection": False},
        "inputs": {label: {"path": str(path.relative_to(root)), "sha256": file_sha(path)} for label, (path, _) in pins.items()},
        "candidate": {"sha256": file_sha(candidate), "bytes": candidate.stat().st_size,
                      "source_manifest_sha256": source_digest, "source_files": sources},
        "comparison": "same signed transaction in independent LiteSVMs; error, relevant logs, events, inner instructions, return data, and full watched before/after accounts",
        "case_count": len(cases),
        "transaction_count": sum(len(row["steps"]) for row in cases),
        "transaction_identity": identities,
        "matching_cases": sum(row["classification"] == "equal_observed_behavior" for row in cases),
        "different_cases": [row["name"] for row in cases if row["classification"] == "different_behavior"],
        "negative_control": {"kind": "expected state mutation", "detected": control_detected},
        "unsupported": unsupported,
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    summary = {key: report[key] for key in ("case_count", "transaction_count", "matching_cases", "different_cases")}
    summary["negative_control_detected"] = control_detected
    print(json.dumps(summary, indent=2, sort_keys=True))
    return (report["matching_cases"] == report["case_count"] and control_detected
            and identities["count"] == identities["unique_count"]
            and identities["all_signatures_verified"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if execute(args.root.resolve(), args.candidate.resolve(), args.output.resolve()) else 1)


if __name__ == "__main__":
    main()
