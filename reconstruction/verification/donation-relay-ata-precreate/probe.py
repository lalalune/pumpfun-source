#!/usr/bin/env python3
"""Exercise Donation Relay epoch-close behavior with a pre-created distribution ATA.

The outsider donation and ATA-creation transactions are genuinely signed. The
local-only epoch-close transaction disables signature verification because the
production relayer private key is not retained. This reaches post-authorization
account handling; it is not evidence of an authorization bypass.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[3]
STATEFUL = ROOT / "reconstruction/verification/donation-relay-stateful/producer.py"
SPEC = importlib.util.spec_from_file_location("relay_stateful", STATEFUL)
assert SPEC is not None and SPEC.loader is not None
stateful = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = stateful
SPEC.loader.exec_module(stateful)

ORIGINAL = ROOT / "evidence/dependencies/donation_relay/deployed.so"
TOKEN_ELF = ROOT / "evidence/dependencies/spl_token/deployed.so"
ATA_ELF = ROOT / "evidence/dependencies/associated_token/deployed.so"
RELAYER = stateful.RELAYER


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_ata(fixture, distribution: Pubkey) -> Instruction:
    vault = stateful.ata(distribution, fixture.mint)
    return Instruction(stateful.ATA, bytes([0]), [
        AccountMeta(fixture.outsider.pubkey(), True, True),
        AccountMeta(vault, False, True),
        AccountMeta(distribution, False, False),
        AccountMeta(fixture.mint, False, False),
        AccountMeta(stateful.SYSTEM, False, False),
        AccountMeta(stateful.TOKEN, False, False),
    ])


def close_epoch(fixture, distribution: Pubkey, vault: Pubkey) -> Instruction:
    data = (stateful.discriminator("global", "close_donation_epoch_v1") + fixture.config
            + (0).to_bytes(16, "little"))
    return Instruction(stateful.RELAY, data, [
        AccountMeta(distribution, False, True),
        AccountMeta(vault, False, True),
        AccountMeta(fixture.epoch, False, True),
        AccountMeta(fixture.debouncer, False, True),
        AccountMeta(fixture.destination, False, True),
        AccountMeta(fixture.mint, False, True),
        AccountMeta(stateful.TOKEN, False, False),
        AccountMeta(RELAYER, True, True),
        AccountMeta(stateful.ATA, False, False),
        AccountMeta(stateful.SYSTEM, False, False),
        AccountMeta(fixture.event, False, False),
        AccountMeta(stateful.RELAY, False, False),
    ])


def result_row(result) -> dict:
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    raw = json.loads(meta.to_json())
    return {
        "error": str(result.err()) if failed else None,
        "logs": list(meta.logs()),
        "inner_instructions": raw["inner_instructions"],
        "return_data": raw["return_data"],
    }


def decoded(vm: LiteSVM, addresses: dict[str, Pubkey]) -> dict:
    rows = {}
    for address in sorted(addresses.values(), key=str):
        value = vm.get_account(address)
        rows[str(address)] = None if value is None else {
            "lamports": value.lamports,
            "owner": str(value.owner),
            "data_base64": base64.b64encode(bytes(value.data)).decode(),
        }
    tracker = vm.get_account(addresses["epoch"])
    debouncer = vm.get_account(addresses["debouncer"])
    source = vm.get_account(addresses["debouncer_ata"])
    distribution_ata = vm.get_account(addresses["distribution_ata"])
    return {
        "accounts": rows,
        "epoch": None if tracker is None else int.from_bytes(tracker.data[74:90], "little"),
        "debouncer_total": None if debouncer is None else int.from_bytes(debouncer.data[74:82], "little"),
        "debouncer_ata_amount": None if source is None else int.from_bytes(source.data[64:72], "little"),
        "distribution_ata_amount": None if distribution_ata is None else int.from_bytes(distribution_ata.data[64:72], "little"),
    }


def run_case(pre_create: bool) -> dict:
    fixture = stateful.Fixture.create()
    fixture.accounts[RELAYER] = stateful.account(10**11)
    distribution = stateful.pda(b"distribution_v1", fixture.config, bytes(fixture.mint),
                                (0).to_bytes(16, "little"))[0]
    distribution_ata = stateful.ata(distribution, fixture.mint)
    fixture.accounts[distribution] = stateful.account(0)
    if not pre_create:
        fixture.accounts[distribution_ata] = stateful.account(0)

    vm = (LiteSVM().with_sigverify(True).with_blockhash_check(True)
          .with_transaction_history(256).with_log_bytes_limit(None))
    vm.add_program_from_file(stateful.RELAY, ORIGINAL)
    vm.add_program_from_file(stateful.TOKEN, TOKEN_ELF)
    vm.add_program_from_file(stateful.ATA, ATA_ELF)
    for address, value in fixture.accounts.items():
        vm.set_account(address, value)

    addresses = {
        "epoch": fixture.epoch,
        "debouncer": fixture.debouncer,
        "debouncer_ata": fixture.destination,
        "distribution": distribution,
        "distribution_ata": distribution_ata,
    }

    donation_tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), fixture.donation(1_000_000)],
        fixture.fee.pubkey(), [fixture.fee, fixture.donor], vm.latest_blockhash())
    assert all(donation_tx.verify_with_results())
    donation = result_row(vm.send_transaction(donation_tx))
    if donation["error"] is not None:
        raise AssertionError(f"donation setup failed: {donation['error']}")

    creation = None
    if pre_create:
        creation_tx = Transaction.new_signed_with_payer(
            [set_compute_unit_limit(1_400_000), create_ata(fixture, distribution)],
            fixture.outsider.pubkey(), [fixture.outsider], vm.latest_blockhash())
        assert all(creation_tx.verify_with_results())
        creation = result_row(vm.send_transaction(creation_tx))
        if creation["error"] is not None:
            raise AssertionError(f"outsider ATA creation failed: {creation['error']}")

    # Disable verification only after the genuinely signed outsider actions.
    # This reaches the privileged close handler without claiming a signature bypass.
    vm = vm.with_sigverify(False)
    before = decoded(vm, addresses)
    close_tx = Transaction.new_unsigned(Message.new_with_blockhash(
        [set_compute_unit_limit(1_400_000), close_epoch(fixture, distribution, distribution_ata)],
        RELAYER, vm.latest_blockhash()))
    close = result_row(vm.send_transaction(close_tx))
    after = decoded(vm, addresses)
    return {
        "case": "pre_created_distribution_ata" if pre_create else "normal_close_control",
        "outsider_ata_creation": creation,
        "donation": donation,
        "close": close,
        "before_close": before,
        "after_close": after,
        "non_fee_state_rolled_back": before["accounts"] == after["accounts"] if close["error"] else None,
    }


def execute(output: Path) -> bool:
    assert sha(ORIGINAL) == stateful.ORIGINAL_SHA
    assert sha(TOKEN_ELF) == stateful.TOKEN_SHA
    assert sha(ATA_ELF) == stateful.ATA_SHA
    control = run_case(False)
    attack = run_case(True)
    problems = []
    if control["close"]["error"] is not None:
        problems.append("normal_close_control_failed")
    if control["after_close"]["epoch"] != 1 or control["after_close"]["debouncer_total"] != 0:
        problems.append("normal_close_did_not_advance_epoch")
    if control["after_close"]["distribution_ata_amount"] != 1_000_000:
        problems.append("normal_close_did_not_move_donations")
    if attack["close"]["error"] is None:
        problems.append("pre_created_ata_did_not_block_close")
    if not attack["non_fee_state_rolled_back"]:
        problems.append("failed_close_changed_state")
    if attack["after_close"]["epoch"] != 0 or attack["after_close"]["debouncer_total"] != 1_000_000:
        problems.append("attack_did_not_leave_donations_in_current_epoch")
    report = {
        "schema": "donation-relay-ata-precreate-v1",
        "program": str(stateful.RELAY),
        "inputs": {path.relative_to(ROOT).as_posix(): sha(path)
                   for path in (ORIGINAL, TOKEN_ELF, ATA_ELF)},
        "authority_boundary": {
            "donation_and_ata_creation_signatures_verified": True,
            "close_signature_verification": False,
            "reason": "production relayer private key is not retained; local harness reaches post-authorization account logic only",
            "authorization_bypass_claimed": False,
        },
        "control": control,
        "pre_created_ata": attack,
        "problems": problems,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "control_close_error": control["close"]["error"],
        "pre_created_ata_close_error": attack["close"]["error"],
        "donations_left_in_debouncer": attack["after_close"]["debouncer_total"],
        "problems": problems,
    }, indent=2))
    return not problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if execute(args.output.resolve()) else 1)


if __name__ == "__main__":
    main()
