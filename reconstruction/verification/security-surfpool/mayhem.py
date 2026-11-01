#!/usr/bin/env python3
"""Signed Surfpool tests for the assigned original-Mayhem security findings."""
from __future__ import annotations

import base64
import hashlib
import importlib
import json
import struct
import sys
from pathlib import Path

from solders.account import Account
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.message import MessageV0
from solders.pubkey import Pubkey
from solders.transaction import Transaction, VersionedTransaction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "results/mayhem"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
from surfpool_rpc import Surfpool, RecordingVM, original, dependency, install_fixture, resign, sha256

MAY = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
FEES = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
META = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
GLOBAL = Pubkey.find_program_address([b"global-params"], MAY)[0]
EVENT = Pubkey.find_program_address([b"__event_authority"], MAY)[0]
SYS = Pubkey.default()
ADMIN = Keypair.from_seed(bytes([1]) * 32)
OTHER = Keypair.from_seed(bytes([3]) * 32)
LEGACY_BUY_PAYER = Keypair.from_seed(hashlib.sha256(b"mayhem-buy-sbf-owned-payer-v1").digest())
LEGACY_SELL_PAYER = Keypair.from_seed(hashlib.sha256(b"mayhem-sell-sbf-owned-payer-v1").digest())


def disc(name: str) -> bytes:
    return hashlib.sha256(("global:" + name).encode()).digest()[:8]


def snapshot(pool: Surfpool, addresses):
    result = {}
    for address in dict.fromkeys(map(str, addresses)):
        value = pool.get_account(address)
        if value is not None:
            value = dict(value)
            value["data"] = value["data"] if len(value["data"]) <= 640 else value["data"][:640]
        result[address] = value
    return result


def deltas(before, after):
    rows = {}
    for key in sorted(set(before) | set(after)):
        b, a = before.get(key), after.get(key)
        if b == a:
            continue
        rows[key] = {
            "before_lamports": b and b["lamports"],
            "after_lamports": a and a["lamports"],
            "lamports_delta": (a["lamports"] if a else 0) - (b["lamports"] if b else 0),
            "before_data_sha256": b and b["data_sha256"],
            "after_data_sha256": a and a["data_sha256"],
            "before_owner": b and b["owner"],
            "after_owner": a and a["owner"],
        }
    return rows


def signers_for(tx: Transaction, candidates):
    mapping = {str(k.pubkey()): k for k in candidates}
    required = tx.message.account_keys[:tx.message.header.num_required_signatures]
    missing = [str(k) for k in required if str(k) not in mapping]
    if missing:
        raise ValueError(f"missing genuine signer keys: {missing}")
    return [mapping[str(k)] for k in required]


def replay_case(name: str, module_name: str, case: dict, programs, patch_target=None):
    """Record a fixture's last signed transaction, then commit it on Surfpool."""
    module = importlib.import_module(module_name)
    target = patch_target or module
    original_type = target.LiteSVM
    recorded = []

    def factory():
        vm = RecordingVM()
        recorded.append(vm)
        return vm

    target.LiteSVM = factory
    try:
        lite = module.run(case)
    finally:
        target.LiteSVM = original_type
    if not recorded or recorded[-1].transaction is None:
        raise AssertionError(f"no transaction recorded for {name}")
    vm = recorded[-1]
    work = OUT / name
    work.mkdir(parents=True, exist_ok=True)
    with Surfpool(work, binary=HERE / "tools/surfpool") as pool:
        for address, path in programs:
            pool.load_program(address, path)
        install_fixture(pool, vm)
        tx0 = vm.transaction
        keys = list(tx0.message.account_keys) + list(vm.accounts)
        before = snapshot(pool, keys)
        candidates = [ADMIN, OTHER, LEGACY_BUY_PAYER, LEGACY_SELL_PAYER]
        for obj in (module, getattr(module, "f", None)):
            if obj is not None:
                candidates += [v for v in vars(obj).values() if isinstance(v, Keypair)]
        tx = resign(tx0, tx0.message.account_keys[0], signers_for(tx0, candidates), pool.latest_blockhash())
        result = pool.send(tx)
        after = snapshot(pool, keys)
        receipt = {
            "case": case,
            "litesvm_error": lite.get("error"),
            "signature": result["signature"],
            "signature_verification": result["signature_verification"],
            "error": result["error"],
            "logs": result["logs"],
            "return_data": result["return_data"],
            "loaded_programs": pool.loaded_programs,
            "state_deltas": deltas(before, after),
            "before": before,
            "after": after,
        }
        if str(GLOBAL) in after and after[str(GLOBAL)]:
            raw = bytes.fromhex(after[str(GLOBAL)]["data"])
            if len(raw) >= 113:
                receipt["global_admin"] = str(Pubkey(raw[49:81]))
                receipt["global_trader"] = str(Pubkey(raw[81:113]))
        (work / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(name, "error=", result["error"], flush=True)
        return receipt


def record_case(module_name, case, patch_target=None):
    module = importlib.import_module(module_name)
    target = patch_target or module
    original_type = target.LiteSVM
    recorded = []
    def factory():
        vm = RecordingVM()
        recorded.append(vm)
        return vm
    target.LiteSVM = factory
    try:
        lite = module.run(case)
    finally:
        target.LiteSVM = original_type
    return module, recorded[-1], lite


def ata(owner, mint, token_program):
    return Pubkey.find_program_address([bytes(owner), bytes(token_program), bytes(mint)], ATA)[0]


def transform_amm_fixture(module, vm, new_quote=None, canonical=False):
    """Rebind a valid captured pool to a new quote and/or canonical Pump creator.

    This only constructs states accepted by AMM create_pool: ordinary pools retain
    zero coin creator; canonical pools use the Pump pool-authority and may carry a
    creator fee. All target signer and adapter checks remain enabled.
    """
    base = Pubkey.from_string(module.F["keys"]["base_mint"])
    native = Pubkey.from_string("So11111111111111111111111111111111111111112")
    usdc = Pubkey.from_string("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
    sample_quote = Pubkey.from_string(module.F["keys"]["quote_mint"])
    old_pool = Pubkey.from_string(module.F["pool"])
    pool_account = vm.accounts[str(old_pool)]
    pd = bytearray.fromhex(pool_account["data"])
    old_creator = Pubkey(pd[11:43])
    creator = Pubkey.find_program_address([b"pool-authority", bytes(base)], PUMP)[0] if canonical else old_creator
    quote = new_quote or sample_quote
    token_program = Pubkey.from_string(pool_account["owner"]) if False else TOKEN
    new_pool = Pubkey.find_program_address([b"pool", bytes(pd[9:11]), bytes(creator), bytes(base), bytes(quote)], AMM)[0]
    old_vb, old_vq = Pubkey(pd[139:171]), Pubkey(pd[171:203])
    new_vb = ata(new_pool, base, TOKEN22)
    new_vq = ata(new_pool, quote, TOKEN if quote != native else TOKEN)
    mapping = {old_pool: new_pool, old_vb: new_vb, old_vq: new_vq}
    if quote != sample_quote:
        mapping[sample_quote] = quote
    if canonical:
        old_coin = Pubkey(pd[211:243])
        new_coin = OTHER.pubkey()
        old_cv = Pubkey.find_program_address([b"creator_vault", bytes(old_coin)], AMM)[0]
        new_cv = Pubkey.find_program_address([b"creator_vault", bytes(new_coin)], AMM)[0]
        mapping[old_cv] = new_cv
        mapping[ata(old_cv, sample_quote, TOKEN)] = ata(new_cv, quote, TOKEN)
    # Rebind every quote ATA, including Mayhem, protocol and buyback accounts.
    for address, value in list(vm.accounts.items()):
        raw = bytes.fromhex(value["data"])
        if len(raw) >= 165 and raw[:32] == bytes(sample_quote):
            owner = Pubkey(raw[32:64])
            owner = mapping.get(owner, owner)
            old = Pubkey.from_string(address)
            if old == ata(Pubkey(raw[32:64]), sample_quote, TOKEN):
                mapping[old] = ata(owner, quote, TOKEN)
    transformed = {}
    for address, value in vm.accounts.items():
        old = Pubkey.from_string(address)
        new = mapping.get(old, old)
        raw = bytes.fromhex(value["data"])
        for source, target in mapping.items():
            raw = raw.replace(bytes(source), bytes(target))
        item = dict(value)
        item["data"] = raw.hex()
        transformed[str(new)] = item
    new_pd = bytearray.fromhex(transformed[str(new_pool)]["data"])
    if canonical:
        new_pd[11:43] = bytes(creator)
        new_pd[211:243] = bytes(OTHER.pubkey())
        new_pd[243] = 1  # is_mayhem_mode, permitted only for this canonical creator
        new_pd[244] = 0  # noncashback route
    transformed[str(new_pool)]["data"] = bytes(new_pd).hex()
    vm.accounts = transformed
    tx0 = vm.transaction
    msg = tx0.message
    header, keys = msg.header, msg.account_keys
    def writable(index):
        if index < header.num_required_signatures:
            return index < header.num_required_signatures - header.num_readonly_signed_accounts
        return index < len(keys) - header.num_readonly_unsigned_accounts
    ixs = []
    for ix in msg.instructions:
        metas = [AccountMeta(mapping.get(keys[n], keys[n]), n < header.num_required_signatures,
                             writable(n)) for n in ix.accounts]
        ixs.append(Instruction(keys[ix.program_id_index], bytes(ix.data), metas))
    candidates = [ADMIN, OTHER, LEGACY_BUY_PAYER, LEGACY_SELL_PAYER] + [v for v in vars(module).values() if isinstance(v, Keypair)]
    vm.transaction = Transaction.new_signed_with_payer(ixs, msg.account_keys[0], signers_for(tx0, candidates), msg.recent_blockhash)
    return {"old_pool": str(old_pool), "new_pool": str(new_pool), "old_quote": str(sample_quote),
            "new_quote": str(quote), "canonical_creator": str(creator) if canonical else None,
            "coin_creator": str(OTHER.pubkey()) if canonical else None}


def replay_transformed(name, case, new_quote=None, canonical=False):
    module, vm, lite = record_case("mayhem_pump_swap_fixture", case)
    transform = transform_amm_fixture(module, vm, new_quote=new_quote, canonical=canonical)
    if canonical:
        config = vm.accounts[module.CONFIG["address"]]
        raw = bytearray.fromhex(config["data"])
        recipient = bytes(raw[57:89])
        for i in range(8):
            raw[57 + 32*i:89 + 32*i] = recipient
        raw[353:385] = bytes(32)  # remove SOL-vault fee exemption
        raw[385:417] = recipient
        for i in range(7):
            raw[418 + 32*i:450 + 32*i] = recipient
        config["data"] = bytes(raw).hex()
        transform["protocol_fee_recipients"] = "ordinary and Mayhem reserved slots set to the existing valid recipient"
        if "one-unit" in name:
            raw[899:907] = bytes(8)  # isolate creator fee from buyback deduction
            config["data"] = bytes(raw).hex()
            fee = vm.accounts[module.F["keys"]["fee_config"]]
            fr = bytearray.fromhex(fee["data"])
            fr[41:49] = bytes(8)  # flat LP bps = 0; preserve creator bps
            fr[49:57] = bytes(8)  # flat protocol bps = 0
            fr[85:93] = bytes(8)  # first retained tier LP bps = 0
            fr[93:101] = bytes(8)  # first retained tier protocol bps = 0
            fee["data"] = bytes(fr).hex()
            transform["lp_fee"] = "LP/protocol zero in flat and first retained tier; positive creator rate preserved"
    work = OUT / name
    work.mkdir(parents=True, exist_ok=True)
    with Surfpool(work, binary=HERE / "tools/surfpool") as pool:
        for address, path in trade_programs():
            pool.load_program(address, path)
        install_fixture(pool, vm)
        tx0 = vm.transaction
        keys = list(tx0.message.account_keys) + list(vm.accounts)
        before = snapshot(pool, keys)
        candidates = [ADMIN, OTHER] + [v for v in vars(module).values() if isinstance(v, Keypair)]
        tx = resign(tx0, tx0.message.account_keys[0], signers_for(tx0, candidates), pool.latest_blockhash())
        result = pool.send(tx)
        after = snapshot(pool, keys)
        receipt = {"case": case, "transform": transform, "litesvm_error_before_transform": lite.get("error"),
                   "signature": result["signature"], "signature_verification": True,
                   "error": result["error"], "logs": result["logs"], "return_data": result["return_data"],
                   "loaded_programs": pool.loaded_programs, "state_deltas": deltas(before, after),
                   "before": before, "after": after}
        (work / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print(name, "error=", result["error"], flush=True)
        return receipt


def legacy_instructions(tx):
    msg = tx.message
    header, keys = msg.header, msg.account_keys
    def writable(index):
        if index < header.num_required_signatures:
            return index < header.num_required_signatures - header.num_readonly_signed_accounts
        return index < len(keys) - header.num_readonly_unsigned_accounts
    return [Instruction(keys[ix.program_id_index], bytes(ix.data),
            [AccountMeta(keys[n], n < header.num_required_signatures, writable(n)) for n in ix.accounts])
            for ix in msg.instructions]


def send_with_alt(pool, tx0, module):
    """Use a genuine signed ALT create/extend to fit the full Mayhem buy ABI."""
    program = Pubkey.from_string("AddressLookupTab1e1111111111111111111111111")
    slot = pool.rpc("getSlot")
    table, bump = Pubkey.find_program_address([bytes(ADMIN.pubkey()), struct.pack("<Q", slot)], program)
    create = Instruction(program, struct.pack("<IQB", 0, slot, bump), [
        AccountMeta(table, False, True), AccountMeta(ADMIN.pubkey(), True, False),
        AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(SYS, False, False)])
    tx = Transaction.new_signed_with_payer([create], ADMIN.pubkey(), [ADMIN], pool.latest_blockhash())
    created = pool.send(tx)
    compute_budget = Pubkey.from_string("ComputeBudget111111111111111111111111111111")
    addresses = [k for k in tx0.message.account_keys if k not in (tx0.message.account_keys[0], compute_budget, SYS)]
    extend = Instruction(program, struct.pack("<IQ", 2, len(addresses)) + b"".join(map(bytes, addresses)), [
        AccountMeta(table, False, True), AccountMeta(ADMIN.pubkey(), True, False),
        AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(SYS, False, False)])
    tx = Transaction.new_signed_with_payer([extend], ADMIN.pubkey(), [ADMIN], pool.latest_blockhash())
    extended = pool.send(tx)
    if created["error"] is not None or extended["error"] is not None:
        raise AssertionError({"alt_create": created["error"], "alt_create_logs": created["logs"],
                              "alt_extend": extended["error"], "alt_extend_logs": extended["logs"]})
    lookup = AddressLookupTableAccount(table, addresses)
    msg = MessageV0.try_compile(tx0.message.account_keys[0], legacy_instructions(tx0), [lookup], pool.latest_blockhash())
    candidates = [ADMIN, OTHER] + [v for v in vars(module).values() if isinstance(v, Keypair)]
    signed = VersionedTransaction(msg, signers_for(tx0, candidates))
    result = pool.send(signed)
    result["lookup_table"] = str(table)
    result["lookup_create"] = {"signature": created["signature"], "error": created["error"], "logs": created["logs"]}
    result["lookup_extend"] = {"signature": extended["signature"], "error": extended["error"], "logs": extended["logs"]}
    return result


def h06_cross_mint():
    case_sell = {"instruction": "sell_pump_swap", "token_quote": True, "quote_tokens": 10**12,
                 "stable_global_risk": 100, "stable_coin_risk": 100, "deadline": 10**12}
    case_buy = {"instruction": "buy_pump_swap", "token_quote": True, "quote_tokens": 10**12,
                "stable_global_risk": 100, "stable_coin_risk": 100, "deadline": 10**12}
    sell_module, sell_vm, _ = record_case("mayhem_pump_swap_fixture", case_sell)
    buy_module, buy_vm, _ = record_case("mayhem_pump_swap_fixture", case_buy)
    quote2 = Keypair.from_seed(hashlib.sha256(b"mayhem-h06-second-quote-mint-v1").digest()).pubkey()
    transform = transform_amm_fixture(buy_module, buy_vm, new_quote=quote2)
    work = OUT / "h06-second-cross-mint"
    work.mkdir(parents=True, exist_ok=True)
    with Surfpool(work, binary=HERE / "tools/surfpool") as pool:
        for address, path in trade_programs():
            pool.load_program(address, path)
        pool.set_account(ADMIN.pubkey(), Account(10**10, b"", SYS))
        install_fixture(pool, sell_vm)
        sell0 = sell_vm.transaction
        keys1 = list(sell0.message.account_keys) + list(sell_vm.accounts)
        before_sell = snapshot(pool, keys1)
        candidates = [ADMIN, OTHER] + [v for v in vars(sell_module).values() if isinstance(v, Keypair)]
        sell_tx = resign(sell0, sell0.message.account_keys[0], signers_for(sell0, candidates), pool.latest_blockhash())
        sell = pool.send(sell_tx)
        after_sell = snapshot(pool, keys1)
        if sell["error"] is not None:
            raise AssertionError({"negative_exposure_prerequisite_failed": sell["error"]})
        # Preserve value and exposure produced by the sell. Install only the new
        # ordinary pool/mint/ATA fixture and unrelated program configuration.
        base = Pubkey.from_string(sell_module.F["keys"]["base_mint"])
        mayhem_base_vault = ata(Pubkey.find_program_address([b"sol-vault"], MAY)[0], base, TOKEN22)
        preserve = {str(GLOBAL), str(Pubkey.find_program_address([b"mayhem-state", bytes(base)], MAY)[0]),
                    str(Pubkey.find_program_address([b"sol-vault"], MAY)[0]), str(mayhem_base_vault),
                    str(sell_module.TRADER.pubkey()), str(sell_module.PAYER.pubkey())}
        for address, value in buy_vm.accounts.items():
            if address not in preserve:
                pool.set_account(address, value)
        buy0 = buy_vm.transaction
        keys2 = list(buy0.message.account_keys) + list(buy_vm.accounts)
        before_buy = snapshot(pool, keys2)
        buy = send_with_alt(pool, buy0, buy_module)
        after_buy = snapshot(pool, keys2)
        receipt = {"sell_case": case_sell, "buy_case": case_buy, "transform": transform,
                   "sell": {k: sell[k] for k in ["signature", "error", "logs"]},
                   "buy": {k: buy.get(k) for k in ["signature", "error", "logs", "lookup_table", "lookup_create", "lookup_extend"]},
                   "signature_verification": True, "loaded_programs": pool.loaded_programs,
                   "sell_state_deltas": deltas(before_sell, after_sell),
                   "buy_state_deltas": deltas(before_buy, after_buy),
                   "before_sell": before_sell, "after_sell": after_sell,
                   "before_buy": before_buy, "after_buy": after_buy}
        raw = after_buy.get(str(GLOBAL), {}).get("data") if after_buy.get(str(GLOBAL)) else None
        if raw:
            data = bytes.fromhex(raw)
            receipt["final_stable_deployed"] = int.from_bytes(data[206:222], "little", signed=True)
            receipt["configured_stable_global_limit"] = int.from_bytes(data[190:198], "little")
        (work / "result.json").write_text(json.dumps(receipt, indent=2) + "\n")
        print("h06-second-cross-mint sell=", sell["error"], "buy=", buy["error"],
              "final_stable=", receipt.get("final_stable_deployed"), flush=True)
        return receipt


def trade_programs():
    return [(MAY, original("mayhem")), (AMM, original("pump_amm")),
            (FEES, original("pump_fees")), (TOKEN, dependency("spl_token")),
            (TOKEN22, dependency("spl_token_2022")), (ATA, dependency("associated_token"))]


def legacy_programs():
    return [(MAY, original("mayhem")), (PUMP, original("pump")),
            (FEES, original("pump_fees")), (TOKEN, dependency("spl_token")),
            (TOKEN22, dependency("spl_token_2022")), (ATA, dependency("associated_token"))]


def create_programs():
    return legacy_programs() + [(META, dependency("token_metadata"))]


def admin_tests():
    work = OUT / "admin"
    work.mkdir(parents=True, exist_ok=True)
    receipts = {}
    with Surfpool(work, binary=HERE / "tools/surfpool") as pool:
        pool.load_program(MAY, original("mayhem"))
        for kp in (ADMIN, OTHER):
            pool.set_account(kp.pubkey(), Account(10**10, b"", SYS))
        pool.set_account(EVENT, Account(10**8, b"", SYS))

        def send(name, instruction, signers, keys):
            tx = Transaction.new_signed_with_payer([instruction], signers[0].pubkey(), signers,
                                                    pool.latest_blockhash())
            before = snapshot(pool, keys)
            result = pool.send(tx)
            after = snapshot(pool, keys)
            row = {"signature": result["signature"], "signature_verification": True,
                   "error": result["error"], "logs": result["logs"],
                   "state_deltas": deltas(before, after), "before": before, "after": after,
                   "loaded_programs": pool.loaded_programs}
            receipts[name] = row
            print(name, "error=", row["error"], flush=True)
            return row

        metas = [AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(GLOBAL, False, True),
                 AccountMeta(SYS, False, False)]
        send("initialize", Instruction(MAY, disc("initialize_global_params"), metas), [ADMIN],
             [ADMIN.pubkey(), GLOBAL])
        raw = bytes.fromhex(pool.get_account(GLOBAL)["data"])
        receipts["initialize"]["stored_admin"] = str(Pubkey(raw[49:81]))
        send("initialize_again", Instruction(MAY, disc("initialize_global_params"), metas), [ADMIN],
             [ADMIN.pubkey(), GLOBAL])
        admin_metas = [AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(GLOBAL, False, True),
                       AccountMeta(SYS, False, False), AccountMeta(EVENT, False, False),
                       AccountMeta(MAY, False, False)]
        send("update_trader", Instruction(MAY, disc("update_trader") + bytes(OTHER.pubkey()), admin_metas),
             [ADMIN], [GLOBAL])
        raw = bytes.fromhex(pool.get_account(GLOBAL)["data"])
        receipts["update_trader"]["stored_trader"] = str(Pubkey(raw[81:113]))
        send("update_admin_nonsigner", Instruction(MAY, disc("update_admin") + bytes(OTHER.pubkey()), admin_metas),
             [ADMIN], [GLOBAL])
        raw = bytes.fromhex(pool.get_account(GLOBAL)["data"])
        receipts["update_admin_nonsigner"]["stored_admin"] = str(Pubkey(raw[49:81]))
        send("old_admin_after_rotation", Instruction(MAY, disc("update_admin") + bytes(ADMIN.pubkey()), admin_metas),
             [ADMIN], [GLOBAL])
    (work / "result.json").write_text(json.dumps(receipts, indent=2) + "\n")
    return receipts


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tests = {}
    tests["admin"] = admin_tests()
    tests["l09_amm_sell_retained_10001"] = replay_case(
        "l09-amm-sell-retained-10001", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "retained": 10001, "deadline": 10**12}, trade_programs())
    tests["l09_legacy_buy_retained_10001"] = replay_case(
        "l09-legacy-buy-retained-10001", "mayhem_buy_fixture",
        {"retained": 10001, "deadline": 10**12}, legacy_programs(), patch_target=importlib.import_module("pump_trade_fixture"))
    tests["m08_native_sell_new_ata"] = replay_case(
        "m08-native-sell-new-ata", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "missing_quote_vault": True, "deadline": 10**12}, trade_programs())
    tests["m10_legacy_buy_wrong_v2"] = replay_case(
        "m10-legacy-buy-wrong-v2", "mayhem_buy_fixture", {"deadline": 10**12},
        legacy_programs(), patch_target=importlib.import_module("pump_trade_fixture"))
    tests["m10_legacy_buy_canonical_v2"] = replay_case(
        "m10-legacy-buy-canonical-v2", "mayhem_buy_fixture", {"deadline": 10**12, "wrong_v2_program": True},
        legacy_programs(), patch_target=importlib.import_module("pump_trade_fixture"))
    tests["m10_legacy_sell_wrong_v2"] = replay_case(
        "m10-legacy-sell-wrong-v2", "mayhem_sell_fixture", {"deadline": 10**12},
        legacy_programs(), patch_target=importlib.import_module("pump_trade_fixture"))
    tests["m11_amm_native_sell"] = replay_case(
        "m11-amm-native-sell", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "deadline": 10**12}, trade_programs())
    tests["m18_create_duration_zero"] = replay_case(
        "m18-create-duration-zero", "pump_create_mayhem_differential", {"duration_hours": 0}, create_programs())
    tests["m18_create_traderless"] = replay_case(
        "m18-create-traderless", "pump_create_mayhem_differential", {"duration_hours": 1}, create_programs())
    tests["h05_ordinary_native_pool"] = replay_case(
        "h05-ordinary-native-pool", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "deadline": 10**12}, trade_programs())
    tests["h05_ordinary_external_quote_pool"] = replay_case(
        "h05-ordinary-external-quote-pool", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "token_quote": True, "deadline": 10**12}, trade_programs())
    tests["h06_negative_netting_sell"] = replay_case(
        "h06-negative-netting-sell", "mayhem_pump_swap_fixture",
        {"instruction": "sell_pump_swap", "token_quote": True, "quote_tokens": 10**12,
         "stable_global_risk": 100, "stable_coin_risk": 100, "deadline": 10**12}, trade_programs())
    tests["h06_cross_mint_buy_not_reached"] = {
        "error": None, "blocked": True,
        "reason": "The retained fixture exposes one external quote mint; a second genuinely canonical ordinary pool with a different quote mint was not constructed. Negative exposure alone does not prove cross-mint bypass."
    }
    (OUT / "tests.json").write_text(json.dumps(tests, indent=2) + "\n")


if __name__ == "__main__":
    main()
