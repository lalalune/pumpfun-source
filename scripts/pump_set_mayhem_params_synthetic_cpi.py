#!/usr/bin/env python3
"""Local-only Pump Mayhem-parameter differential through a synthetic Mayhem-ID CPI.

This VM replaces the deployed Mayhem program with a tiny caller that signs its
own `sol-vault` PDA. It proves target-body behavior only under that constructed
caller. It says nothing about whether deployed Mayhem exposes such a route.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

ROOT = Path(__file__).resolve().parents[1]
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
MAYHEM = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
TARGET_SHA256 = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
PAYER = Keypair.from_seed(bytes([212]) * 32)
FIXTURE = ROOT / "repro/pump/mayhem-synthetic/account-snapshot.json.gz"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def state(account):
    if account is None:
        return None
    return {"lamports": account.lamports, "owner": str(account.owner),
            "executable": account.executable, "data_hex": bytes(account.data).hex()}


def mutated_account(index, item, case):
    data = bytearray(base64.b64decode(item["data"][0], validate=True))
    assert len(data) == item["space"]
    if index == 4:
        if "real_quote" in case:
            struct.pack_into("<Q", data, 32, case["real_quote"])
        if "virtual_token" in case:
            struct.pack_into("<Q", data, 8, case["virtual_token"])
        if "token_supply" in case:
            struct.pack_into("<Q", data, 40, case["token_supply"])
        if "complete" in case:
            data[48] = case["complete"]
        if "mayhem_mode" in case:
            data[81] = case["mayhem_mode"]
        if "quote_mint" in case:
            data[83:115] = bytes([case["quote_mint"]]) * 32
        if case.get("bad_curve_discriminator"):
            data[0] ^= 0xFF
    if index == 1 and "token_amount" in case:
        struct.pack_into("<Q", data, 0x40, case["token_amount"])
    if index == 1 and case.get("bad_token_authority"):
        data[32:64] = bytes([17]) * 32
    if index == 1 and case.get("bad_token_mint"):
        data[0:32] = bytes([19]) * 32
    if index == 3 and case.get("bad_global_discriminator"):
        data[0] ^= 0xFF
    owner = Pubkey.default() if case.get("bad_owner_index") == index else Pubkey.from_string(item["owner"])
    return Account(item["lamports"], bytes(data), owner,
                   item["executable"], item["rentEpoch"])


def run(binary, caller, fixture, case):
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(True)
    vm.add_program_from_file(PUMP, str(binary))
    vm.add_program_from_file(MAYHEM, str(caller))
    vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
    vm.airdrop(PAYER.pubkey(), 10**9)
    keys = [Pubkey.from_string(item["address"]) for item in fixture["accounts"]]
    assert keys[-1] == PUMP
    assert keys[0] == Pubkey.find_program_address([b"sol-vault"], MAYHEM)[0]
    for index, (key, item) in enumerate(zip(keys[:-1], fixture["accounts"][:-1])):
        vm.set_account(key, mutated_account(index, item, case))
    before = [state(vm.get_account(key)) for key in keys[:-1]]
    ix = Instruction(MAYHEM, b"", [AccountMeta(key, False, index in (0, 1, 4))
                                    for index, key in enumerate(keys)])
    message = Message.new_with_blockhash([ix], PAYER.pubkey(), vm.latest_blockhash())
    tx = VersionedTransaction(message, [PAYER])
    assert all(tx.verify_with_results())
    result = vm.send_transaction(tx)
    failed = hasattr(result, "err")
    meta = result.meta() if failed else result
    raw = json.loads(meta.to_json())
    logs = meta.logs()
    after = [state(vm.get_account(key)) for key in keys[:-1]]
    return {
        "case": case["name"], "binary_sha256": sha(binary.read_bytes()),
        "signed_transaction_sha256": sha(bytes(tx)), "signatures_valid": True,
        "signed_transaction_base64": base64.b64encode(bytes(tx)).decode(),
        "error": str(result.err()) if failed else None,
        "before": before, "after": after,
        "pump_instruction_reached": any("Instruction: SetMayhemVirtualParams" in line for line in logs),
        "logs": logs, "events": [line for line in logs if line.startswith("Program data:")],
        "inner": raw.get("inner_instructions", []),
        "return_data": raw.get("return_data"),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=Path, default=ROOT / "evidence/original/pump/deployed.so")
    p.add_argument("--candidate", type=Path)
    p.add_argument("--caller", type=Path, default=ROOT / "repro/pump/mayhem-synthetic/synthetic-caller.so")
    p.add_argument("--output", type=Path, default=ROOT / "repro/pump/mayhem-synthetic/differential.json.gz")
    a = p.parse_args()
    assert sha(a.target.read_bytes()) == TARGET_SHA256
    fixture = json.loads(gzip.decompress(FIXTURE.read_bytes()))
    assert len(fixture["accounts"]) == 8
    t = base64.b64decode(fixture["accounts"][1]["data"][0]); g = base64.b64decode(fixture["accounts"][3]["data"][0]); c = base64.b64decode(fixture["accounts"][4]["data"][0])
    initial_d = 2 * struct.unpack_from("<Q", c, 40)[0] - struct.unpack_from("<Q", g, 0x59)[0] - struct.unpack_from("<Q", t, 0x40)[0]
    threshold_token_amount = 2 * struct.unpack_from("<Q", c, 40)[0] - struct.unpack_from("<Q", g, 0x59)[0] - (10**12 - 1)
    exact_token_amount = threshold_token_amount - 1
    cases = [
        {"name": "live_snapshot_noop"},
        {"name": "below_sol_threshold", "real_quote": 9_999_999},
        {"name": "sol_threshold", "real_quote": 10_000_000},
        {"name": "sol_uncapped", "real_quote": 20_000_000},
        {"name": "sol_capped", "real_quote": 1_000_000_000_000},
        {"name": "complete_noop", "complete": 1, "real_quote": 20_000_000},
        {"name": "mayhem_disabled_noop", "mayhem_mode": 0, "real_quote": 20_000_000},
        {"name": "d_below_threshold", "token_amount": threshold_token_amount, "real_quote": 20_000_000},
        {"name": "d_exact_threshold", "token_amount": exact_token_amount, "real_quote": 20_000_000},
        {"name": "supply_double_overflow", "token_supply": 2**64 - 1, "real_quote": 20_000_000},
        {"name": "d_first_sub_underflow", "token_supply": 1_000, "real_quote": 20_000_000},
        {"name": "d_sub_underflow", "token_amount": 2**64 - 1, "real_quote": 20_000_000},
        {"name": "numerator_overflow", "virtual_token": 2**64 - 1, "real_quote": 2**64 - 1},
        {"name": "u64_quotient_overflow", "real_quote": 2**64 - 1},
        {"name": "nonzero_quote_below_threshold", "quote_mint": 7, "real_quote": 999_999},
        {"name": "nonzero_quote_threshold", "quote_mint": 7, "real_quote": 1_000_000},
        {"name": "nonzero_quote_capped", "quote_mint": 7, "real_quote": 1_000_000_000_000},
        {"name": "token_vault_wrong_owner", "bad_owner_index": 1},
        {"name": "mint_wrong_owner", "bad_owner_index": 2},
        {"name": "global_wrong_owner", "bad_owner_index": 3},
        {"name": "curve_wrong_owner", "bad_owner_index": 4},
        {"name": "token_vault_wrong_authority", "bad_token_authority": True},
        {"name": "token_vault_wrong_mint", "bad_token_mint": True},
        {"name": "global_wrong_discriminator", "bad_global_discriminator": True},
        {"name": "curve_wrong_discriminator", "bad_curve_discriminator": True},
    ]
    target = [run(a.target, a.caller, fixture, case) for case in cases]
    assert all(x["pump_instruction_reached"] for x in target)
    report = {"scope": "Synthetic local Mayhem-ID signer caller; no deployed-Mayhem route or live fund claim",
              "target_sha256": TARGET_SHA256,
              "synthetic_caller_sha256": sha(a.caller.read_bytes()),
              "fixture_sha256": sha(FIXTURE.read_bytes()),
              "fixture_slot": fixture["context_slot"], "initial_d": initial_d,
              "cases": target}
    if a.candidate:
        candidate = [run(a.candidate, a.caller, fixture, case) for case in cases]
        keys = ("error", "before", "after", "events", "inner", "return_data")
        matches = [{"case": t["case"], "equal": {key: t[key] == c[key] for key in keys}}
                   for t, c in zip(target, candidate)]
        assert all(all(row["equal"].values()) for row in matches), "candidate diverges from captured target"
        report["candidate_sha256"] = sha(a.candidate.read_bytes())
        report["candidate_cases"] = candidate
        report["comparison"] = matches
    a.output.parent.mkdir(parents=True, exist_ok=True)
    serialized = (json.dumps(report, separators=(",", ":")) + "\n").encode()
    a.output.write_bytes(gzip.compress(serialized, mtime=0) if a.output.suffix == ".gz" else serialized)
    print(json.dumps({"cases": len(cases), "reached": sum(x["pump_instruction_reached"] for x in target),
                      "successes": sum(x["error"] is None for x in target),
                      "errors": [x["error"] for x in target],
                      "matches": report.get("comparison")}, indent=2))


if __name__ == "__main__":
    main()
