"""Signed offline Pump admin incentive scheduler target/candidate comparison.

The Global account is a finalized public capture with its stored authority
substituted locally by a disposable signer. The accumulator, mint and token
account are synthetic but canonically derived. No transaction is broadcast.
"""

if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")

import argparse
import base64
import gzip
import hashlib
import json
import re
import struct
from pathlib import Path

from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction


ROOT = Path(__file__).resolve().parents[1]
DEPENDENCIES = {name: ROOT / "evidence/dependencies" / name / "deployed.so"
                for name in ("spl_token", "spl_token_2022", "associated_token")}
TARGET = ROOT / "evidence/original/pump/deployed.so"
CANDIDATE = ROOT / "repro/pump/admin-incentives-fortynine/candidate.so"
BUILD = ROOT / "repro/pump/admin-incentives-fortynine/build-comparison.json"
IDL = ROOT / "evidence/upstream/pump.json"
SNAPSHOT = ROOT / "research/imported-lab/analysis/pump_fun/config-snapshot.json"
OUTPUT = ROOT / "repro/pump/admin-token-incentives-candidate-differential.json.gz"
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSTEM = Pubkey.default()
AUTH = Keypair.from_seed(bytes([223]) * 32)
OUTSIDER = Keypair.from_seed(bytes([224]) * 32)
FEE_PAYER = Keypair.from_seed(bytes([225]) * 32)
MINT = Pubkey.from_bytes(bytes([226]) * 32)
BAD = Pubkey.from_bytes(bytes([228]) * 32)
GLOBAL = Pubkey.find_program_address([b"global"], PUMP)[0]
VOLUME = Pubkey.find_program_address([b"global_volume_accumulator"], PUMP)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], PUMP)[0]
ERROR = re.compile(r"InstructionErrorCustom\((\d+)\)")


def sha(path_or_bytes):
    raw = path_or_bytes.read_bytes() if isinstance(path_or_bytes, Path) else path_or_bytes
    return hashlib.sha256(raw).hexdigest()


def receipt_path(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def canonical_vault(program=TOKEN, mint=MINT):
    return Pubkey.find_program_address([bytes(VOLUME), bytes(program), bytes(mint)], ATA)[0]


def snapshot(vm, addresses):
    result = {}
    for name, key in addresses.items():
        account = vm.get_account(key)
        result[name] = None if account is None else {
            "pubkey": str(key), "lamports": account.lamports,
            "owner": str(account.owner), "data_base64": base64.b64encode(account.data).decode(),
            "data_sha256": sha(account.data), "executable": account.executable,
            "rent_epoch": account.rent_epoch,
        }
    return result


def initial_accumulator(case):
    data = bytearray(600)
    data[:8] = hashlib.sha256(b"account:GlobalVolumeAccumulator").digest()[:8]
    struct.pack_into("<qqq", data, 8, case.get("old_start", 20),
                     case.get("old_end", 49), case.get("old_period", 1))
    data[32:64] = bytes(Pubkey.from_string(case["old_mint"]) if "old_mint" in case
                        else MINT)
    struct.pack_into("<30Q", data, 64, *case.get("supplies", [1000] * 30))
    struct.pack_into("<30Q", data, 304, *case.get("volumes", [100] * 30))
    if case.get("bad_volume_discriminator"):
        data[0] ^= 1
    if case.get("volume_length") is not None:
        length = case["volume_length"]
        data = data[:length].ljust(length, b"\x00")
    return bytes(data)


def mint_data():
    return struct.pack("<I", 0) + bytes(32) + struct.pack("<Q", 10**12) + bytes([6, 1]) + bytes(36)


def vault_data(amount=10**9, *, mint=MINT, owner=VOLUME):
    data = bytearray(165)
    data[:32] = bytes(mint)
    data[32:64] = bytes(owner)
    struct.pack_into("<Q", data, 64, amount)
    data[108] = 1
    return bytes(data)


def run(binary, item, case, global_fixture):
    vm = LiteSVM().with_sigverify(True).with_blockhash_check(False).with_log_bytes_limit(None)
    vm.set_clock(Clock(100, 0, 0, 0, case.get("now", 10)))
    vm.add_program_from_file(PUMP, str(binary))
    for program, path in ((TOKEN, "spl_token"), (TOKEN22, "spl_token_2022"),
                          (ATA, "associated_token")):
        vm.add_program_from_file(program, str(pin_program(DEPENDENCIES[path])))
    for signer in (AUTH, OUTSIDER, FEE_PAYER):
        vm.airdrop(signer.pubkey(), 10**10)
    raw = bytearray(base64.b64decode(global_fixture["data_base64"]))
    assert len(raw) == global_fixture["data_bytes"] == 1088
    raw[9:41] = bytes(OUTSIDER.pubkey() if case.get("stored_outsider") else AUTH.pubkey())
    if case.get("bad_global_discriminator"):
        raw[0] ^= 1
    if case.get("global_length") is not None:
        length = case["global_length"]
        raw = raw[:length].ljust(length, b"\x00")
    global_key = BAD if case.get("wrong_global_pda") else GLOBAL
    vm.set_account(global_key, Account(global_fixture["lamports"], bytes(raw),
                                       SYSTEM if case.get("wrong_global_owner") else PUMP))
    volume_key = BAD if case.get("wrong_volume_pda") else VOLUME
    if not case.get("missing_volume"):
        vm.set_account(volume_key, Account(10**8, initial_accumulator(case),
                                           SYSTEM if case.get("wrong_volume_owner") else PUMP))
    token_program = TOKEN22 if case.get("token22") or case.get("wrong_token_program") else TOKEN
    if not case.get("missing_mint"):
        raw_mint = mint_data()
        if case.get("mint_length") is not None:
            length = case["mint_length"]
            raw_mint = raw_mint[:length].ljust(length, b"\x00")
        vm.set_account(MINT, Account(10**7, raw_mint,
            SYSTEM if case.get("wrong_mint_owner") else
            TOKEN if case.get("wrong_token_program") else token_program))
    vault_key = canonical_vault(token_program)
    if case.get("wrong_vault_pda"):
        vault_key = BAD
    if not case.get("missing_vault"):
        raw_vault = bytearray(vault_data(case.get("vault_amount", 10**9),
                       mint=BAD if case.get("wrong_vault_mint") else MINT,
                       owner=BAD if case.get("wrong_vault_authority") else VOLUME))
        if case.get("vault_state_bad"):
            raw_vault[108] = 0
        if case.get("vault_length") is not None:
            length = case["vault_length"]
            raw_vault = raw_vault[:length].ljust(length, b"\x00")
        vm.set_account(vault_key, Account(10**7, bytes(raw_vault),
            SYSTEM if case.get("wrong_vault_owner") else token_program))
    authority = OUTSIDER if case.get("wrong_authority") else AUTH
    fee_payer = FEE_PAYER if case.get("unsigned_authority") or case.get("readonly_authority") else AUTH
    associated_program = BAD if case.get("wrong_associated_program") else ATA
    system_program = BAD if case.get("wrong_system_program") else SYSTEM
    event_authority = BAD if case.get("wrong_event_authority") else EVENT
    program_account = BAD if case.get("wrong_program") else PUMP
    if (associated_program == BAD or system_program == BAD or
            event_authority == BAD or program_account == BAD):
        vm.set_account(BAD, Account(10**7, b"", SYSTEM))
    keys = {"authority": authority.pubkey(), "global": global_key,
            "global_volume_accumulator": volume_key, "mint": MINT,
            "global_incentive_token_account": vault_key,
            "associated_token_program": associated_program,
            "system_program": system_program, "token_program": token_program,
            "event_authority": event_authority, "program": program_account}
    watched = {name: key for name, key in keys.items() if name in (
        "authority", "global", "global_volume_accumulator", "mint",
        "global_incentive_token_account")}
    watched["canonical_global"] = GLOBAL
    watched["canonical_volume"] = VOLUME
    watched["canonical_vault"] = canonical_vault(token_program)
    watched["fee_payer"] = fee_payer.pubkey()
    watched["outsider"] = OUTSIDER.pubkey()
    before = snapshot(vm, watched)
    values = (case.get("new_start", 30), case.get("new_end", 59),
              case.get("new_period", 1), case.get("day", 0),
              case.get("supply", 1000))
    data = bytes(item["discriminator"]) + struct.pack("<qqqQQ", *values)
    if case.get("truncated_args") is not None:
        data = data[:8 + case["truncated_args"]]
    if case.get("extra_bytes"):
        data += b"\xa5\x5a"
    metas = [AccountMeta(keys[entry["name"]],
                         bool(entry.get("signer")) and not case.get("unsigned_authority"),
                         bool(entry.get("writable")) and entry["name"] not in case.get("readonly", []))
             for entry in item["accounts"]]
    message = Message.new_with_blockhash([Instruction(PUMP, data, metas)],
                                         fee_payer.pubkey(), vm.latest_blockhash())
    signers = [fee_payer] if fee_payer == authority or case.get("unsigned_authority") else [fee_payer, authority]
    transaction = VersionedTransaction(message, signers)
    assert all(transaction.verify_with_results())
    result = vm.send_transaction(transaction)
    error = str(result.err()) if hasattr(result, "err") else None
    meta = result.meta() if error else result
    match = ERROR.search(error or "")
    after = snapshot(vm, watched)
    inner = [{"program_id_index": item.instruction().program_id_index,
              "account_indices": list(item.instruction().accounts),
              "data_hex": item.instruction().data.hex()}
             for group in meta.inner_instructions() for item in group]
    return {"error": error, "error_code": int(match.group(1)) if match else None,
            "before": before, "after": after,
            "signed_transaction_base64": base64.b64encode(bytes(transaction)).decode(),
            "signature": str(transaction.signatures[0]), "signature_verified": True,
            "events": [line.removeprefix("Program data: ") for line in meta.logs()
                       if line.startswith("Program data: ")],
            "state_debug_logs": [line for line in meta.logs() if
                                 line.startswith("Program log: GlobalVolumeAccumulator=")],
            "inner_instructions": inner,
            "return_data_hex": bytes(meta.return_data().data).hex(),
            "compute_units": meta.compute_units_consumed(),
            "relevant_logs": [line for line in meta.logs() if "Instruction:" in line or
                              "Error" in line or "panicked" in line or "failed" in line],
            "args": list(values), "keys": {name: str(key) for name, key in keys.items()}}


def variants():
    rows = [("baseline", {}), ("same_start", {"new_start":20,"new_end":49}),
            ("supply_zero", {"supply":0}),
            ("day_last", {"day":29}),
            ("supply_all_days", {"day":30,"supply":5}),
            ("time_zero_supply_zero", {"new_start":0,"new_end":0,"supply":0}),
            ("active_range_future", {"now":21,"new_start":20,"new_end":49,"day":1}),
            ("missing_vault", {"missing_vault":True}),
            ("token22", {"token22":True}),
            ("new_start_in_past", {"new_start":9}),
            ("new_end_in_past", {"new_end":9}),
            ("end_before_start", {"new_start":30,"new_end":29}),
            ("time_range_too_large", {"new_start":30,"new_end":60}),
            ("supply_range_finished", {"now":60,"new_start":0,"new_end":0}),
            ("day_after_end", {"new_start":20,"new_end":30,"day":29}),
            ("day_in_active_range", {"now":21,"new_start":20,"new_end":49,"day":0}),
            ("wrong_authority", {"wrong_authority":True}),
            ("unsigned_authority", {"unsigned_authority":True}),
            ("readonly_authority", {"readonly_authority":True,"readonly":["authority"]}),
            ("readonly_volume", {"readonly":["global_volume_accumulator"]}),
            ("wrong_global_pda", {"wrong_global_pda":True}),
            ("wrong_global_owner", {"wrong_global_owner":True}),
            ("bad_global_discriminator", {"bad_global_discriminator":True}),
            ("wrong_volume_pda", {"wrong_volume_pda":True}),
            ("wrong_volume_owner", {"wrong_volume_owner":True}),
            ("bad_volume_discriminator", {"bad_volume_discriminator":True}),
            ("missing_volume", {"missing_volume":True}),
            ("wrong_mint_owner", {"wrong_mint_owner":True}),
            ("wrong_token_program", {"wrong_token_program":True}),
            ("missing_mint", {"missing_mint":True}),
            ("wrong_vault_pda", {"wrong_vault_pda":True}),
            ("wrong_vault_owner", {"wrong_vault_owner":True}),
            ("wrong_vault_mint", {"wrong_vault_mint":True}),
            ("wrong_vault_authority", {"wrong_vault_authority":True}),
            ("vault_state_bad", {"vault_state_bad":True}),
            ("vault_amount_zero", {"vault_amount":0}),
            ("wrong_associated_program", {"wrong_associated_program":True}),
            ("wrong_system_program", {"wrong_system_program":True}),
            ("wrong_event_authority", {"wrong_event_authority":True}),
            ("wrong_program", {"wrong_program":True}),
            ("token22_missing_vault", {"token22":True,"missing_vault":True}),
            ("changed_incentive_mint", {"old_mint":str(BAD)}),
            ("period_zero_without_supply", {"new_start":0,"new_end":0,"new_period":0,"supply":0}),
            ("extra_bytes", {"extra_bytes":True}),
            ("truncated_args", {"truncated_args":8})]
    for day in (0,1,28,29,30,31,(1<<64)-1):
        rows.append((f"day_{day}", {"day":day}))
    for supply in (0,1,(1<<64)-1):
        rows.append((f"supply_{supply}", {"supply":supply}))
    for period in (-1,0,1,2,10):
        rows.append((f"period_{period}", {"new_period":period}))
    for now,start,end,day in ((0,20,49,0),(19,20,49,1),(20,20,49,0),
                              (21,20,49,1),(29,20,49,9),(49,20,49,29),
                              (50,20,49,29),(60,30,59,0),(10,0,0,0),
                              (21,0,0,30),(21,20,21,1),(21,20,30,11)):
        rows.append((f"clock_{now}_{start}_{end}_{day}",
                     {"now":now,"new_start":start,"new_end":end,"day":day}))
    for field, lengths in (("global_length",(0,7,8,939,940,1087,1088,1089)),
                           ("volume_length",(0,7,8,543,544,599,600,601)),
                           ("mint_length",(0,7,81,82,83)),
                           ("vault_length",(0,7,164,165,166))):
        for length in lengths:
            rows.append((f"{field}_{length}",{field:length}))
    return rows


def main(candidate=CANDIDATE, build_path=BUILD, output=OUTPUT,
         second_build_path=None):
    candidate, build_path, output = map(Path, (candidate, build_path, output))
    source_inputs = [ROOT / name for name in (
        "programs/pump/src/incentives.rs", "programs/pump/src/volume_sync.rs",
        "programs/pump/src/lib.rs", "programs/pump/Cargo.toml", "programs/pump/Cargo.lock")]
    extra_inputs = [build_path, TARGET, IDL, SNAPSHOT, *DEPENDENCIES.values(), *source_inputs]
    if second_build_path is not None:
        extra_inputs.append(Path(second_build_path))
    publisher = PumpReport(output, ROOT, candidate, __file__, extra_inputs=extra_inputs)
    candidate = pin_program(candidate)
    target_image = pin_program(TARGET)
    build_bytes = build_path.read_bytes()
    build = json.loads(build_bytes)
    assert sha(target_image) == build["comparison"]["original_sha256"]
    assert sha(candidate) == build["comparison"]["candidate_sha256"]
    clean_rebuild = None
    if second_build_path is not None:
        second_build_path = Path(second_build_path)
        second_bytes = second_build_path.read_bytes()
        second = json.loads(second_bytes)
        assert second["comparison"]["candidate_sha256"] == sha(candidate)
        assert second["source_sha256"] == build["source_sha256"]
        assert second["selected_toolchain"] == build["selected_toolchain"] == "v1.44"
        clean_rebuild = {"comparison_path": receipt_path(second_build_path),
                         "comparison_sha256": sha(second_bytes),
                         "candidate_sha256": second["comparison"]["candidate_sha256"],
                         "source_hashes_equal": True, "toolchain_equal": True}
    idl_bytes = IDL.read_bytes()
    idl = json.loads(idl_bytes)
    item = next(item for item in idl["instructions"]
                if item["name"] == "admin_update_token_incentives")
    assert [entry["name"] for entry in item["accounts"]] == [
        "authority", "global", "global_volume_accumulator", "mint",
        "global_incentive_token_account", "associated_token_program",
        "system_program", "token_program", "event_authority", "program"]
    snapshot_bytes = SNAPSHOT.read_bytes()
    fixture = next(row for row in json.loads(snapshot_bytes)["accounts"]
                   if row["program_name"] == "pump")
    assert sha(base64.b64decode(fixture["data_base64"])) == fixture["data_sha256"]
    assert fixture["address"] == str(GLOBAL) and fixture["owner"] == str(PUMP)
    source_hashes = {str(path.relative_to(ROOT)): sha(path) for path in source_inputs}
    dependency_hashes = {name: sha(pin_program(path)) for name, path in DEPENDENCIES.items()}
    rows = []
    for name, case in variants():
        target = run(target_image, item, case, fixture)
        recovered = run(candidate, item, case, fixture)
        fields = ("error", "error_code", "before", "after",
                  "signed_transaction_base64", "signature", "events",
                  "state_debug_logs", "inner_instructions", "return_data_hex",
                  "args", "keys")
        differences = [field for field in fields if target[field] != recovered[field]]
        rows.append({"case": name, "variant": case, "match": not differences,
                     "differing_fields": differences, "target": target,
                     "candidate": recovered})
    report = {
        "scope": "Pump admin_update_token_incentives only; signed isolated target/candidate VM differential",
        "baseline_commit": "4ffe8bd88761059693e481ae972443c10204f7af",
        "target_sha256": sha(target_image), "candidate_sha256": sha(candidate),
        "candidate_path": receipt_path(candidate),
        "build_comparison_sha256": sha(build_bytes), "idl_sha256": sha(idl_bytes),
        "build_comparison_path": receipt_path(build_path),
        "second_clean_build": clean_rebuild,
        "global_snapshot_sha256": sha(snapshot_bytes),
        "global_snapshot_account_data_sha256": fixture["data_sha256"],
        "source_sha256": source_hashes,
        "programs": {"pump": str(PUMP), "spl_token": str(TOKEN),
                     "spl_token_2022": str(TOKEN22), "associated_token": str(ATA)},
        "dependency_sha256": dependency_hashes,
        "summary": {"cases": len(rows), "matched": sum(row["match"] for row in rows),
                    "target_successes": sum(row["target"]["error"] is None for row in rows),
                    "candidate_successes": sum(row["candidate"]["error"] is None for row in rows)},
        "cases": rows,
        "limits": "The Global account comes from a finalized public capture but its authority is locally replaced by a disposable signer. GlobalVolumeAccumulator, mint and incentive ATA are synthetic canonical states. Cases compare full watched bytes, errors, event logs, inner CPIs and return data; CU and source-log wording are recorded separately. This does not prove live admin key possession, downstream claim scheduling for every clock/mint or full-program byte identity. No broadcast or real funds.",
    }
    encoded = (json.dumps(report, separators=(",", ":")) + "\n").encode()
    publisher.write(gzip.compress(encoded, mtime=0) if output.suffix == ".gz"
                    else encoded)
    print(json.dumps(report["summary"], indent=2))
    print([(row["case"], row["target"]["error_code"],
            row["candidate"]["error_code"], row["differing_fields"])
           for row in rows if not row["match"]])
    if not all(row["match"] for row in rows):
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, default=CANDIDATE)
    parser.add_argument("--build-comparison", type=Path, default=BUILD)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--second-build-comparison", type=Path)
    args = parser.parse_args()
    main(args.candidate, args.build_comparison, args.output,
         args.second_build_comparison)
