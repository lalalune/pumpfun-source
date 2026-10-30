#!/usr/bin/env python3
"""Compare a persistent signed create/deposit/crank sequence in offline LiteSVM.

Uses synthetic accounts and test-owned keys. Captured dependency ELFs are loaded
locally; no RPC, live writes, or privileged-signature substitution is used.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path

import fees_donation_create_differential as create
import fees_donation_crank_probe as crank
import fees_admin_differential as admin
from pump_amm_reusable_harness import pin_program
from probe_report import write_json_report
from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = create.ROOT
START = 1_700_000_000
RENT = Pubkey.from_string("SysvarRent111111111111111111111111111111111")
RETAINED_SHA256 = {
    "original": "4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e",
    "donation_relay": "367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563",
    "spl_token": "8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697",
    "associated_token": "6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d",
}
ADDRESSES = {
    "transaction_payer": create.PAYER.pubkey(), "payer": create.AUTH.pubkey(),
    "other": create.OTHER.pubkey(), "fee_program_global": create.GLOBAL,
    "donation_fee_pda": create.DONATION, "base_mint": create.MINT,
    "config_id": create.CONFIG, "bonding_curve": create.CURVE,
    "pool": create.POOL, "sharing_config": create.SHARING,
    "event_authority": create.EVENT, "program": create.PROGRAM,
    "system_program": Pubkey.default(), "token_program": crank.TOKEN,
    "associated_token_program": crank.ATA, "rent": RENT,
    "quote_mint": create.QUOTE, "donation_fee_pda_ata": crank.D_ATA,
    "donation_relay_program": crank.RELAY,
    "donation_relay_event_authority": crank.RELAY_EVENT,
    "mint_whitelist": crank.WHITELIST, "epoch_tracker": crank.EPOCH,
    "debouncer": crank.DEBOUNCER, "debouncer_ata": crank.B_ATA,
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(vm, tx):
    # Include every explicitly tracked account and every message account, even
    # if it is read-only. Executable bytes differ by design for the candidate.
    keys = set(ADDRESSES.values()) | set(tx.message.account_keys)
    result = {}
    for key in sorted(keys, key=str):
        account = vm.get_account(key)
        if account is None:
            result[str(key)] = None
            continue
        row = {"lamports": account.lamports, "owner": str(account.owner),
               "executable": account.executable, "rent_epoch": account.rent_epoch,
               "data_base64": None if account.executable else base64.b64encode(account.data).decode(),
               "data_length": len(account.data),
               "data_sha256": hashlib.sha256(account.data).hexdigest()}
        result[str(key)] = row
    return result


class Recorder:
    def __init__(self, vm):
        self.vm = vm
        self.rows = []
        self.label = "create"
        self.timestamp = START

    def __getattr__(self, name):
        return getattr(self.vm, name)

    def send_transaction(self, tx):
        if not all(tx.verify_with_results()):
            raise AssertionError("Transaction signatures did not verify")
        before = snapshot(self.vm, tx)
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        metadata = json.loads(meta.to_json())
        self.rows.append({
            "step": self.label, "timestamp": self.timestamp,
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "signature_verification": True,
            "error": str(result.err()) if failed else None,
            "before": before, "after": snapshot(self.vm, tx),
            "events": [line for line in meta.logs() if line.startswith("Program data:")],
            "inner_instructions": metadata["inner_instructions"],
            "return_data": metadata["return_data"], "logs": meta.logs(),
        })
        return result


class FrozenFixture(create.Fixture):
    """Keep the existing setup while loading the already-bound program bytes."""
    def __init__(self, image):
        self.vm = create.LiteSVM().with_transaction_history(0)
        self.vm.add_program(create.PROGRAM, image)


def execute(binary, *, programs=None, mint_capture=None):
    image = binary if isinstance(binary, bytes) else pin_program(binary).read_bytes()
    fixture = FrozenFixture(image)
    if programs is None:
        programs = {name: pin_program(ROOT / f"evidence/dependencies/{name}/deployed.so").read_bytes()
                    for name in ("donation_relay", "spl_token", "associated_token")}
    for name, key in [("donation_relay", crank.RELAY), ("spl_token", crank.TOKEN),
                      ("associated_token", crank.ATA)]:
        fixture.vm.add_program(key, programs[name])
    recorder = Recorder(fixture.vm)
    fixture.vm = recorder
    recorder.set_clock(Clock(1000, 0, 0, 0, START))
    created = fixture.run({"name": "create-sequence"})
    if created["error"] is not None:
        raise AssertionError(f"Creation failed for {binary}: {created['error']}")

    # Immutable mint capture plus synthetic empty relay whitelist. Subsequent
    # donation and relay state is changed only by normal signed transactions.
    capture = mint_capture if mint_capture is not None else json.loads(
        (ROOT / "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json").read_bytes())
    mint = capture["accounts"]["quote_mint"]
    recorder.set_account(create.QUOTE, Account(mint["lamports"], base64.b64decode(mint["data_base64"]), crank.TOKEN))
    whitelist = hashlib.sha256(b"account:MintWhitelistV1").digest()[:8] + bytes([crank.WB]) + bytes(4)
    recorder.set_account(crank.WHITELIST, Account(10**9, whitelist, crank.RELAY))
    for key in [crank.RELAY_EVENT, crank.EPOCH, crank.DEBOUNCER, crank.D_ATA, crank.B_ATA]:
        recorder.set_account(key, Account(0, b"", Pubkey.default()))
    metas = [AccountMeta(ADDRESSES[entry["name"]], entry.get("signer", False), entry.get("writable", False))
             for entry in crank.IX["accounts"]]
    crank_ix = Instruction(create.PROGRAM, bytes(crank.IX["discriminator"]), metas)

    def send(label, instructions, signers, timestamp):
        recorder.label = label
        recorder.timestamp = timestamp
        recorder.set_clock(Clock(1000, 0, 0, 0, timestamp))
        # New ordinary blockhashes avoid relying on duplicate signatures.
        recorder.expire_blockhash()
        tx = Transaction.new_signed_with_payer(instructions, create.PAYER.pubkey(), signers, recorder.latest_blockhash())
        recorder.send_transaction(tx)

    for label, amount, timestamp in [("initial", 1_000_000, START),
                                      ("same-time", 12_345, START),
                                      ("plus-one-second", 12_345, START + 1),
                                      ("plus-one-day", 12_345, START + 86_400)]:
        send(label + "-deposit", [transfer(TransferParams(from_pubkey=create.AUTH.pubkey(),
             to_pubkey=create.DONATION, lamports=amount))], [create.PAYER, create.AUTH], timestamp)
        send(label + "-crank", [set_compute_unit_limit(1_400_000), crank_ix],
             [create.PAYER, create.AUTH], timestamp)
    send("empty-repeat-crank", [set_compute_unit_limit(1_400_000), crank_ix],
         [create.PAYER, create.AUTH], START + 86_400)
    return recorder.rows


def comparable(row):
    result = {key: row[key] for key in ["step", "timestamp", "error", "events", "inner_instructions", "return_data"]}
    for stage in ["before", "after"]:
        state = {key: dict(value) if value else None for key, value in row[stage].items()}
        # Preserve account bytes or executable length/hash in both snapshots. Only executable bytes of
        # the intentionally different Fees candidate are outside state parity.
        program = state.get(str(create.PROGRAM))
        if program:
            program.pop("data_base64", None)
            program.pop("data_sha256", None)
            program.pop("data_length", None)
            program["lamports"] -= row["before"][str(create.PROGRAM)]["lamports"]
        result[stage] = state
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=ROOT / "localnet/recovery/fees-donation/pump_fees_candidate.so")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original = ROOT / "evidence/original/pump_fees/deployed.so"
    paths = {"original": original, **{name: ROOT / f"evidence/dependencies/{name}/deployed.so"
                                      for name in ("donation_relay", "spl_token", "associated_token")}}
    fixture_path = ROOT / "research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json"
    idl_path = ROOT / "evidence/upstream/pump_fees.json"
    source_paths = {"fees_donation_sequence.py": Path(__file__).resolve(),
                    "fees_donation_create_differential.py": Path(create.__file__).resolve(),
                    "fees_donation_crank_probe.py": Path(crank.__file__).resolve(),
                    "fees_admin_differential.py": Path(admin.__file__).resolve(),
                    "pump_amm_reusable_harness.py": Path(pin_program.__code__.co_filename).resolve(),
                    "probe_report.py": Path(write_json_report.__code__.co_filename).resolve()}
    for path in [args.candidate, *paths.values(), fixture_path, idl_path, *source_paths.values()]:
        if (args.output.resolve() == path.resolve() or
                (args.output.exists() and path.exists() and os.path.samefile(args.output, path))):
            raise ValueError("sequence output aliases an input")
    candidate = pin_program(args.candidate).read_bytes()
    programs = {name: pin_program(path).read_bytes() for name, path in paths.items()}
    for name, raw in programs.items():
        if hashlib.sha256(raw).hexdigest() != RETAINED_SHA256[name]:
            raise ValueError(f"retained {name} image hash mismatch")
    fixture_bytes = fixture_path.read_bytes()
    mint_capture = json.loads(fixture_bytes)
    idl_bytes = idl_path.read_bytes()
    if json.loads(idl_bytes) != create.IDL:
        raise ValueError("Fees IDL changed since fixture import")
    source_hashes = {name: digest(path) for name, path in source_paths.items()}
    left = execute(programs["original"], programs=programs, mint_capture=mint_capture)
    right = execute(candidate, programs=programs, mint_capture=mint_capture)
    if not left or not right:
        raise ValueError("Sequence must contain signed transactions")
    if len(left) != len(right):
        raise AssertionError("Sequence length differs")
    steps = [{"step": x["step"], "match": comparable(x) == comparable(y), "original": x, "candidate": y}
             for x, y in zip(left, right)]
    mismatches = [row["step"] for row in steps if not row["match"]]
    errors = [f"{side}:{row['step']}" for side, rows in [("original", left), ("candidate", right)]
              for row in rows if row["error"] is not None]
    if any(digest(path) != source_hashes[name] for name, path in source_paths.items()):
        raise ValueError("Sequence source changed during execution")
    report = {
        "scope": "Persistent offline synthetic creation, System deposits and repeated crank transactions; normally verified test-owned signatures. Not full program identity.",
        "snapshot_scope": "All tracked accounts and all transaction message accounts; Executable accounts use length/hash instead of repeated binary bytes. Fees executable length/hash and binary-size-dependent initial rent retained but excluded from behavioral comparison; program lamport changes are compared.",
        "original_sha256": hashlib.sha256(programs["original"]).hexdigest(),
        "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
        "script_sha256": source_hashes["fees_donation_sequence.py"],
        "dependency_hashes": {name: hashlib.sha256(programs[name]).hexdigest()
                              for name in ["donation_relay", "spl_token", "associated_token"]},
        "fixture_script_hashes": {name: digest for name, digest in source_hashes.items()
                                  if name != "fees_donation_sequence.py"},
        "fixture_input_hashes": {str(path.relative_to(ROOT)): hashlib.sha256(raw).hexdigest()
                                 for path, raw in [(fixture_path, fixture_bytes), (idl_path, idl_bytes)]},
        "addresses": {name: str(key) for name, key in ADDRESSES.items()},
        "steps": steps, "mismatches": mismatches, "unexpected_errors": errors,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json_report(args.output, report)
    print(json.dumps({"steps": len(steps), "signed_transactions": len(left) + len(right),
                      "mismatches": mismatches, "unexpected_errors": errors}))
    if mismatches or errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
