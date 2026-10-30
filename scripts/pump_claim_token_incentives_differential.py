"""Signed offline Pump claim_token_incentives target/candidate differential.

A signed Pump trade receipt supplies a program-created UserVolumeAccumulator,
Token-2022 mint and user ATA. The GlobalVolumeAccumulator schedule and its
funded canonical incentive ATA are explicit synthetic local fixtures.
"""

import argparse
import base64
import hashlib
import json
import re
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata


ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "evidence/original/pump/deployed.so"
IDL = ROOT / "evidence/upstream/pump.json"
FIXTURE = ROOT / "research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json"
OUT = ROOT / "repro/pump/claim-token-incentives/differential.json"
BUILD = ROOT / "repro/pump/claim-token-incentives/build-comparison.json"
PROGRAM = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
TOKEN = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
GLOBAL_VOLUME = Pubkey.find_program_address([b"global_volume_accumulator"], PROGRAM)[0]
EVENT_AUTHORITY = Pubkey.find_program_address([b"__event_authority"], PROGRAM)[0]
PAYER = Keypair.from_seed(bytes([180]) * 32)
OTHER = Keypair.from_seed(bytes([181]) * 32)
DISCRIMINATOR = bytes([16, 4, 71, 28, 204, 1, 40, 27])
GLOBAL_DISCRIMINATOR = bytes([202, 42, 246, 43, 142, 190, 30, 255])
ERROR_CODE = re.compile(r"InstructionErrorCustom\((\d+)\)")
CASES = (
    {"name": "baseline"},
    {"name": "volume_zero", "volume": 0},
    {"name": "volume_one", "volume": 1},
    {"name": "volume_fifty", "volume": 50},
    {"name": "volume_above_day_total", "volume": 101},
    {"name": "fractional_quote_holdout", "volume": 7,
     "supply": 997, "day_volume": 13},
    {"name": "large_quote_holdout", "volume": 123_456,
     "supply": 789_012, "day_volume": 654_321},
    {"name": "small_denominator_holdout", "volume": 100,
     "supply": 1_000, "day_volume": 3},
    {"name": "large_u128_product_holdout", "volume": 2**32,
     "supply": 2**32, "day_volume": 2**32,
     "vault_amount": 2**32 + 10},
    {"name": "large_u128_rounding_holdout", "volume": 2**32,
     "supply": 2**32, "day_volume": 2**32 - 1,
     "vault_amount": 2**32 + 10},
    {"name": "supply_small", "supply": 10},
    {"name": "supply_zero", "supply": 0},
    {"name": "day_volume_zero", "day_volume": 0},
    {"name": "supply_only_day_0", "supply_slot": 0},
    {"name": "supply_only_day_8", "supply_slot": 8},
    {"name": "supply_only_day_9", "supply_slot": 9},
    {"name": "supply_only_day_10", "supply_slot": 10},
    {"name": "supply_only_day_11", "supply_slot": 11},
    {"name": "day_volume_only_0", "volume_slot": 0},
    {"name": "day_volume_only_9", "volume_slot": 9},
    {"name": "day_volume_only_10", "volume_slot": 10},
    {"name": "now_one", "now": 1},
    {"name": "now_two", "now": 2},
    {"name": "now_day_29", "now": 29},
    {"name": "now_day_30", "now": 30},
    {"name": "now_day_31", "now": 31},
    {"name": "before_end_with_long_period", "now": 99,
     "seconds_in_a_day": 10},
    {"name": "at_end_with_long_period", "now": 100,
     "seconds_in_a_day": 10},
    {"name": "after_end_with_long_period", "now": 101,
     "seconds_in_a_day": 10},
    {"name": "start_after_last", "now": 11, "start": 10,
     "end": 39},
    {"name": "first_day_after_start", "now": 11, "start": 10,
     "end": 39, "last": 10},
    {"name": "last_one", "last": 1},
    {"name": "last_five", "last": 5},
    {"name": "last_five_supply_day_zero", "last": 5, "supply_slot": 0},
    {"name": "last_five_supply_day_five", "last": 5, "supply_slot": 5},
    {"name": "last_five_next_second", "last": 5, "now": 6,
     "supply_slot": 5, "volume_slot": 5},
    {"name": "last_five_volume_day_zero", "last": 5, "volume_slot": 0},
    {"name": "last_five_volume_day_five", "last": 5, "volume_slot": 5},
    {"name": "last_nine", "last": 9},
    {"name": "last_ten", "last": 10},
    {"name": "needs_claim_zero", "needs_claim": 0},
    {"name": "prior_claimed", "claimed": 100, "has_claimed": 1},
    {"name": "prior_unclaimed", "unclaimed": 100},
    {"name": "prior_unclaimed_zero_day_volume", "unclaimed": 100,
     "day_volume": 0},
    {"name": "prior_unclaimed_zero_supply", "unclaimed": 100,
     "supply": 0},
    {"name": "prior_unclaimed_fractional", "unclaimed": 17,
     "volume": 7, "supply": 997, "day_volume": 13},
    {"name": "now_before_start", "now": 9, "start": 10, "end": 39},
    {"name": "at_start", "now": 10, "start": 10, "end": 39},
    {"name": "after_end", "now": 40, "start": 10, "end": 39},
    {"name": "last_after_now", "last": 11},
    {"name": "vault_underfunded", "vault_amount": 199},
    {"name": "wrong_global_owner", "wrong_global_owner": True},
    {"name": "wrong_user_owner", "wrong_user_owner": True},
    {"name": "wrong_global_pda", "wrong_global_pda": True},
    {"name": "wrong_user_pda", "wrong_user_pda": True},
    {"name": "wrong_mint", "wrong_mint": True},
    {"name": "wrong_token_program", "wrong_token_program": True},
    {"name": "wrong_event_authority", "wrong_event_authority": True},
    {"name": "wrong_program_account", "wrong_program_account": True},
    {"name": "read_only_user_volume", "read_only_user_volume": True},
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def account_record(vm, key):
    account = vm.get_account(key)
    if account is None:
        return None
    data = bytes(account.data)
    return {"address": str(key), "owner": str(account.owner),
            "lamports": account.lamports,
            "data_base64": base64.b64encode(data).decode(),
            "data_sha256": sha(data), "executable": account.executable,
            "rent_epoch": account.rent_epoch}


def fixture_data():
    source = json.loads(FIXTURE.read_text())
    keys = {name: Pubkey.from_string(value) for name, value in source["accounts"].items()}
    prior = source["steps"][4]["before"]
    user_volume = Pubkey.find_program_address(
        [b"user_volume_accumulator", bytes(keys["user"])], PROGRAM)[0]
    global_ata = Pubkey.find_program_address(
        [bytes(GLOBAL_VOLUME), bytes(TOKEN), bytes(keys["mint"])], ATA)[0]
    assert user_volume == keys["volume"]
    for name in ("user", "mint", "user_base", "curve_base", "volume"):
        assert sha(base64.b64decode(prior[name]["data_base64"])) == \
               prior[name]["data_sha256"]
    return source, keys, prior, user_volume, global_ata


def parse_user(data):
    return struct.unpack_from("<BQQQqBQQQQ", data, 40)


def run_case(binary, case):
    source, keys, prior, user_volume, global_ata = fixture_data()
    now = case.get("now", 10)
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(False)
    vm.set_clock(Clock(460_000_000, 0, 0, 0, now))
    vm.add_program_from_file(PROGRAM, str(binary))
    vm.add_program_from_file(TOKEN, str(ROOT / "evidence/dependencies/spl_token_2022/deployed.so"))
    vm.add_program_from_file(ATA, str(ROOT / "evidence/dependencies/associated_token/deployed.so"))
    vm.airdrop(PAYER.pubkey(), 10_000_000_000)
    vm.airdrop(OTHER.pubkey(), 10_000_000_000)
    for name in ("user", "mint", "user_base"):
        record = prior[name]
        vm.set_account(keys[name], Account(record["lamports"],
            base64.b64decode(record["data_base64"]), Pubkey.from_string(record["owner"])))
    user_data = bytearray(base64.b64decode(prior["volume"]["data_base64"]))
    user_data[40] = case.get("needs_claim", 1)
    struct.pack_into("<QQQq", user_data, 41, case.get("unclaimed", 0),
                     case.get("claimed", 0), case.get("volume", 20),
                     case.get("last", 0))
    user_data[73] = case.get("has_claimed", 0)
    vm.set_account(user_volume, Account(prior["volume"]["lamports"],
        bytes(user_data), Pubkey.default() if case.get("wrong_user_owner") else PROGRAM))
    supply_values = ([case.get("supply", 1000)] * 30 if "supply_slot" not in case
                     else [1000 if index == case["supply_slot"] else 0
                           for index in range(30)])
    volume_values = ([case.get("day_volume", 100)] * 30 if "volume_slot" not in case
                     else [100 if index == case["volume_slot"] else 0
                           for index in range(30)])
    global_data = bytearray(GLOBAL_DISCRIMINATOR + struct.pack(
        "<qqq", case.get("start", 0), case.get("end", 100),
        case.get("seconds_in_a_day", 1)) + bytes(keys["mint"]) +
        b"".join(struct.pack("<Q", value) for value in supply_values) +
        b"".join(struct.pack("<Q", value) for value in volume_values))
    global_data.extend(bytes(600 - len(global_data)))
    vm.set_account(GLOBAL_VOLUME, Account(100_000_000, bytes(global_data),
        Pubkey.default() if case.get("wrong_global_owner") else PROGRAM))
    incentive_data = bytearray(base64.b64decode(prior["curve_base"]["data_base64"]))
    incentive_data[32:64] = bytes(GLOBAL_VOLUME)
    struct.pack_into("<Q", incentive_data, 64, case.get("vault_amount", 1_000_000))
    vm.set_account(global_ata, Account(prior["curve_base"]["lamports"],
                                       bytes(incentive_data), TOKEN))
    global_key, user_key, mint_key = GLOBAL_VOLUME, user_volume, keys["mint"]
    if case.get("wrong_global_pda"):
        global_key = OTHER.pubkey()
        vm.set_account(global_key, Account(100_000_000, bytes(global_data), PROGRAM))
    if case.get("wrong_user_pda"):
        user_key = OTHER.pubkey()
        vm.set_account(user_key, Account(prior["volume"]["lamports"],
                                         bytes(user_data), PROGRAM))
    if case.get("wrong_mint"):
        mint_key = OTHER.pubkey()
    token_program = OTHER.pubkey() if case.get("wrong_token_program") else TOKEN
    event_authority = OTHER.pubkey() if case.get("wrong_event_authority") else EVENT_AUTHORITY
    program_account = Pubkey.default() if case.get("wrong_program_account") else PROGRAM
    ordered = [keys["user"], keys["user_base"], global_key, global_ata, user_key,
               mint_key, token_program, Pubkey.default(), ATA,
               event_authority, program_account, PAYER.pubkey()]
    idl = json.loads(IDL.read_text(encoding='utf-8'))
    item = next(row for row in idl["instructions"] if row["name"] == "claim_token_incentives")
    metas = [AccountMeta(key, bool(info.get("signer")),
                         bool(info.get("writable")))
             for key, info in zip(ordered, item["accounts"], strict=True)]
    if case.get("read_only_user_volume"):
        metas[4] = AccountMeta(user_key, False, False)
    instruction = Instruction(PROGRAM, DISCRIMINATOR, metas)
    watched = {"payer": PAYER.pubkey(), "user": keys["user"],
               "user_ata": keys["user_base"], "global_volume": GLOBAL_VOLUME,
               "global_ata": global_ata, "user_volume": user_volume,
               "mint": keys["mint"], "other": OTHER.pubkey()}
    before = {name: account_record(vm, key) for name, key in watched.items()}
    tx = Transaction.new_signed_with_payer([instruction], PAYER.pubkey(),
                                            [PAYER], vm.latest_blockhash())
    assert all(tx.verify_with_results())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    error = str(result.err()) if failed else None
    code = ERROR_CODE.search(error or "")
    after = {name: account_record(vm, key) for name, key in watched.items()}
    message_keys = tx.message.account_keys
    inner = []
    for group in meta.inner_instructions():
        for item in group:
            ix = item.instruction()
            inner.append({"program": str(message_keys[ix.program_id_index]),
                          "accounts": [str(message_keys[index]) for index in ix.accounts],
                          "data_hex": bytes(ix.data).hex(),
                          "stack_height": item.stack_height()})
    logs = list(meta.logs())
    user_before = parse_user(base64.b64decode(before["user_volume"]["data_base64"]))
    user_after = parse_user(base64.b64decode(after["user_volume"]["data_base64"]))
    return {"logs": logs, "case": case, "error": error,
            "error_code": int(code.group(1)) if code else None,
            "success": error is None,
            "signature": str(tx.signatures[0]),
            "transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "before": before, "after": after,
            "changed": sorted(name for name in before if before[name] != after[name]),
            "user_before": list(user_before), "user_after": list(user_after),
            "event_data_base64": [line.removeprefix("Program data: ") for line in logs
                                  if line.startswith("Program data: ")],
            "inner": inner, "compute_units": meta.compute_units_consumed(),
            "relevant_logs": [line for line in logs if "Instruction:" in line or
                              "AnchorError" in line or "Program data:" in line or
                              "failed" in line]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    assert sha(ORIGINAL.read_bytes()) == \
           "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"
    if args.candidate:
        build = json.loads(BUILD.read_text())
        assert build["comparison"]["candidate_sha256"] == sha(args.candidate.read_bytes())
        assert build["comparison"]["original_sha256"] == sha(ORIGINAL.read_bytes())
    report_rows = []
    for case in CASES:
        target = run_case(ORIGINAL, case)
        candidate = run_case(args.candidate, case) if args.candidate else None
        differences = ([] if candidate is None else [
            name for name in ("error", "before", "after", "event_data_base64", "inner")
            if target[name] != candidate[name]])
        report_rows.append({"case": case, "target": target, "candidate": candidate,
                            "differences": differences})
    receipt = {"scope": "Signed isolated current-Pump claim_token_incentives differential with captured program-created UserVolume/mint/user ATA and explicit synthetic daily schedule/incentive vault; no live transaction or funds.",
               "baseline_commit": "4ffe8bd88761059693e481ae972443c10204f7af",
               "target_sha256": sha(ORIGINAL.read_bytes()),
               "candidate_sha256": sha(args.candidate.read_bytes()) if args.candidate else None,
               "build_receipt_sha256": sha(BUILD.read_bytes()) if args.candidate else None,
               "idl_sha256": sha(IDL.read_bytes()),
               "fixture_sha256": sha(FIXTURE.read_bytes()),
               "dependency_sha256": {name: sha((ROOT / f"evidence/dependencies/{name}/deployed.so").read_bytes())
                                     for name in ("spl_token_2022", "associated_token")},
               "source_sha256": {name: sha((ROOT / name).read_bytes()) for name in (
                   "programs/pump/Cargo.toml", "programs/pump/Cargo.lock",
                   "programs/pump/src/lib.rs", "programs/pump/src/volume_sync.rs",
                   "programs/pump/src/token_incentives/mod.rs",
                   "programs/pump/src/token_incentives/claim_token_incentives.rs",
                   "scripts/pump_claim_token_incentives_differential.py")},
               "script_sha256": sha(Path(__file__).read_bytes()),
               "signed_local": True, "offline_only": True,
               "summary": {"cases": len(report_rows),
                           "matched": sum(not row["differences"] for row in report_rows)
                                      if args.candidate else None,
                           "target_successes": sum(row["target"]["success"] for row in report_rows)},
               "qualification": "GlobalVolumeAccumulator and its incentive ATA are locally constructed; the user volume, mint and user ATA come from a saved signed Pump-created/traded fixture and are modified only as listed per case. Positive synthetic state is not a proven live accrual. Token-2022 CPI executes its pinned dependency. No full handler/source or current fund-risk claim.",
               "cases": report_rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"cases": len(report_rows),
                      "successes": receipt["summary"]["target_successes"],
                      "results": [(row["case"]["name"], row["target"]["error_code"],
                                   row["target"]["user_after"][:6]) for row in report_rows],
                      "mismatches": [(row["case"]["name"], row["differences"])
                                     for row in report_rows if row["differences"]]}, indent=2))
    if any(row["differences"] for row in report_rows):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
