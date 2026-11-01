#!/usr/bin/env python3
"""Pump Main security findings replayed against retained bytes in Surfpool 1.6.1.

Only this file and results/main* are owned by this lane. Every executed target
transaction has genuine test-owned signatures. Account fixtures are synthetic;
no production authority or live deployment claim is made.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib
import importlib.util
import json
import struct
import sys
import time
import traceback
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "scripts"))
from surfpool_rpc import (RecordingVM, Surfpool, dependency, install_fixture,
                          original, resign, sha256)

OUT = HERE / "results/main-cases"
PUMP = Pubkey.from_string("6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P")
AMM = Pubkey.from_string("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA")
FEES = Pubkey.from_string("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ")
TOKEN = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
TOKEN22 = Pubkey.from_string("TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb")
ATA = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
META = Pubkey.from_string("metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s")
MAYHEM = Pubkey.from_string("MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e")
PROGRAMS = [
    (PUMP, original("pump")), (AMM, original("pump_amm")),
    (FEES, original("pump_fees")), (MAYHEM, original("mayhem")),
    (TOKEN, dependency("spl_token")), (TOKEN22, dependency("spl_token_2022")),
    (ATA, dependency("associated_token")), (META, dependency("token_metadata")),
]
EXPECTED_PUMP_SHA = "7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d"


class FixtureVM(RecordingVM):
    def __init__(self):
        super().__init__()
        self.clock = None

    def set_clock(self, clock):
        self.clock = clock
        return self.vm.set_clock(clock)


def module(name):
    return importlib.import_module(name)


def capture(patch_targets, invoke):
    made = []
    def factory():
        vm = FixtureVM()
        made.append(vm)
        return vm
    old = [(obj, obj.LiteSVM) for obj in patch_targets]
    try:
        for obj, _ in old:
            obj.LiteSVM = factory
        lite_result = invoke()
    finally:
        for obj, value in old:
            obj.LiteSVM = value
    if len(made) != 1:
        raise RuntimeError(f"expected one recorded VM, got {len(made)}")
    return made[0], lite_result


def snapshot(pool, keys):
    return {str(key): pool.get_account(key) for key in sorted(set(map(str, keys)))}


def replay(vm, payer, signers, timestamp=None):
    OUT.mkdir(parents=True, exist_ok=True)
    with Surfpool(OUT, binary=HERE / "tools/surfpool") as pool:
        for address, path in PROGRAMS:
            pool.load_program(address, path)
        install_fixture(pool, vm)
        if timestamp is not None and timestamp > int(time.time()):
            pool.rpc("surfnet_timeTravel", [{"absoluteTimestamp": timestamp * 1000}])
        keys = set(vm.accounts) | {str(k) for k in vm.transaction.message.account_keys}
        before = snapshot(pool, keys)
        required = list(vm.transaction.message.account_keys)[:vm.transaction.message.header.num_required_signatures]
        by_key = {signer.pubkey(): signer for signer in signers}
        selected = [by_key[key] for key in required]
        tx = resign(vm.transaction, payer, selected, pool.latest_blockhash())
        result = pool.send(tx)
        after = snapshot(pool, keys)
        deltas = {key: {"before": before[key], "after": after[key]}
                  for key in before if before[key] != after[key]}
        result.update(loaded_programs=pool.loaded_programs,
                      account_deltas=deltas,
                      transaction_base64=base64.b64encode(bytes(tx)).decode(),
                      fixture_clock_unix_timestamp=timestamp)
        return result


def write_case(fid, case, result):
    path = OUT / f"{fid.lower()}.json"
    path.write_text(json.dumps({"finding": fid, "case": case, "surfpool": result}, indent=2) + "\n")
    return str(path.relative_to(ROOT))


def run_fixture(fid, case, patch_targets, invoke, payer, signers, timestamp=None):
    vm, lite = capture(patch_targets, invoke)
    result = replay(vm, payer, signers, timestamp)
    result["litesvm_error"] = lite.get("error") if isinstance(lite, dict) else None
    return write_case(fid, case, result)


def test_h04():
    f = module("pump_global_init_differential")
    return run_fixture("H-04", {"initializer": "unrelated test-owned signer"},
        [f], lambda: f.run({"name": "base"}), f.PAYER.pubkey(), [f.PAYER, f.USER])


def test_l01():
    f = module("pump_creator_migration_differential")
    case = {"name": "paused", "op": "migrate_bonding_curve_creator", "status": 0,
            "curve_patches": [(49, bytes(f.AUTH.pubkey()).hex())]}
    return run_fixture("L-01", case, [f.fixtures.f],
        lambda: f.run(case), f.PAYER.pubkey(), [f.PAYER, f.AUTH])


def test_m14():
    f = module("pump_creator_distribution_differential")
    case = {"name": "native-overflow", "op": "distribute_creator_fees",
            "pump_sol": 10**18}
    return run_fixture("M-14", case, [f.fixtures.f], lambda: f.run(case),
                       f.PAYER.pubkey(), [f.PAYER, f.AUTH])


def test_m06():
    f = module("pump_incentives_admin_differential")
    now = int(time.time())
    case = {"name": "fresh", "existing": False, "ata_existing": False,
            "now": now, "start": now + 10, "end": now + 39}
    return run_fixture("M-06", case, [f], lambda: f.run(case),
                       f.PAYER.pubkey(), [f.PAYER, f.AUTH, f.OTHER])


def test_m17():
    f = module("pump_incentives_admin_differential")
    now = int(time.time())
    # Actual Token-2022 PermanentDelegate(type 12), with retained nonzero
    # delegate authority. The scheduler receives a normally signed instruction.
    mint = bytearray(82); mint[44] = 6; mint[45] = 1
    mint = bytes(mint) + bytes(83) + bytes([1]) + struct.pack("<HH", 12, 32) + bytes([7]) * 32
    case = {"name": "permanent-delegate-reward-mint", "token22": True,
            "now": now, "start": now + 10, "end": now + 39,
            "mutations": {"mint": {"patches": [(0, mint.hex())]}}}
    return run_fixture("M-17", case, [f], lambda: f.run(case),
                       f.PAYER.pubkey(), [f.PAYER, f.AUTH, f.OTHER])


def test_h08():
    f = module("pump_create_quote_differential")
    case = {"case": "quote-permanent-delegate", "instruction": "create_v2",
            "quote": True, "quote_token22": True,
            "quote_extensions": [(12, bytes(32).hex())]}
    return run_fixture("H-08", case, [f], lambda: f.run(case),
                       f.USER.pubkey(), [f.USER, f.MINT, f.OTHER], 1_700_000_000)


def test_m16():
    f = module("pump_create_quote_differential")
    # Controlled nonnative global: virtual quote reserves zero.
    case = {"case": "zero-virtual-quote", "instruction": "create_v2",
            "quote": True, "quote_token22": True,
            "global_patches": [(1005, struct.pack("<Q", 0).hex())]}
    return run_fixture("M-16", case, [f], lambda: f.run(case),
                       f.USER.pubkey(), [f.USER, f.MINT, f.OTHER], 1_700_000_000)


def test_h03():
    f = module("pump_migrate_v2_probe")
    # Actual Token-2022 transfer-fee extension: 1% on both epochs.
    mint = bytearray(base64.b64decode(f.SAVED["mint"]["data_base64"])[:82])
    conf = bytes(72) + struct.pack("<QQH", 0, 2**64 - 1, 100) * 2
    mint = bytes(mint) + bytes(83) + bytes([1]) + struct.pack("<HH", 1, len(conf)) + conf
    acct = bytearray(base64.b64decode(f.SAVED["curve_base"]["data_base64"])[:165])
    acct[:32] = bytes([217]) * 32
    acct[32:64] = bytes(f.pda([b"bonding-curve", bytes(f.MINT)], f.P))
    acct[64:72] = struct.pack("<Q", 85_005_359_063)
    acct = bytes(acct) + bytes([2]) + struct.pack("<HHQ", 2, 8, 0)
    case = {"boost": True, "stable": True, "quote22": True,
            "writable": ["quote_mint"],
            "mutations": {"quote_mint": {"patches": [(0, mint.hex())]},
                          "associated_quote_bonding_curve": {"patches": [(0, acct.hex())]}}}
    return run_fixture("H-03", case, [f], lambda: f.run(case),
                       f.PAYER.pubkey(), [f.PAYER, f.USER], 1_234_567_890)


def test_l16():
    f = module("pump_migrate_v2_probe")
    case = {"boost": True,
            "mutations": {"associated_base_bonding_curve": {
                "patches": [(64, struct.pack("<Q", 2**64 - 1).hex())]}}}
    return run_fixture("L-16", case, [f], lambda: f.run(case),
                       f.PAYER.pubkey(), [f.PAYER, f.USER], 1_234_567_890)


def test_m02():
    f = module("pump_buy_v2_differential")
    case = {"name": "normal-buy-volume", "kind": "buy_v2", "amount": 500_000_000}
    return run_fixture("M-02", case, [f.f], lambda: f.run(case),
                       f.USER.pubkey(), [f.USER])


def load_corpus():
    spec = importlib.util.spec_from_file_location(
        "main_multihop_corpus", ROOT / "research/pump-multi-hop-corpus/harness.py")
    corpus = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(corpus)
    return corpus


def test_m01():
    corpus = load_corpus()
    h = corpus.h
    admin = module("pump_amm_admin_differential")
    def small_curve(vm, metas):
        raw = bytearray(vm.vm.get_account(h.CURVE).data)
        raw[8:48] = struct.pack("<QQQQQ", 1000, 100, 100, 0, 1000)
        vm.vm.set_account(h.CURVE, h.Account(10**12, bytes(raw), h.PUMP))
        # Zero ordinary protocol fee for the arithmetic boundary fixture.
        glob = bytearray(vm.vm.get_account(h.PUMP_GLOBAL).data)
        for off in (73, 81, 115):
            glob[off:off + 8] = bytes(8)
        vm.vm.set_account(h.PUMP_GLOBAL, h.Account(10**9, bytes(glob), h.PUMP))
    case = {"route": "AMM signed CPI -> native Main curve", "budget": 14,
            "reserves": [1000, 100, 100, 0, 1000],
            "note": "Retained Fees dependency applies its captured default fee."}
    return run_fixture("M-01", case, [admin],
        lambda: corpus.invoke(False, 14, mutation=small_curve, limit=1),
        h.PAYER.pubkey(), [h.PAYER], 1_234_567_890)


def test_h01(single_hop=False):
    corpus = load_corpus()
    h = corpus.h
    admin = module("pump_amm_admin_differential")
    # Build the report's corrected all-buy AMM(WSOL base) -> native Main route.
    # This is an isolated synthetic pool, not a claim about a live pool.
    def invoke():
        # corpus.invoke is intentionally curve-only; reproduce its harness with
        # the existing AMM-then-curve route and WSOL pool-base mutation.
        vm = admin.Harness(ROOT / "evidence/original/pump_amm/deployed.so")
        vm.vm.set_clock(h.Clock(100, 1234567890, 0, 0, 1234567890))
        for pid, path in [(h.TOKEN, dependency("spl_token")),
                          (h.TOKEN22, dependency("spl_token_2022")),
                          (h.FEES, original("pump_fees")),
                          (h.ATA, dependency("associated_token")),
                          (h.PUMP, original("pump"))]:
            vm.vm.add_program_from_file(pid, path)
        for row in h.f["accounts"].values():
            vm.vm.set_account(h.Pubkey.from_string(row["address"]), h.Account(
                row["lamports"], h.base64.b64decode(row["data_base64"]),
                h.Pubkey.from_string(row["owner"])))
        # Preserve the canonical pool PDA: pool = ["pool", index, creator,
        # base_mint, quote_mint]. Changing the base mint requires a new PDA.
        original_pool = bytearray(vm.vm.get_account(h.pool).data)
        pool_index = original_pool[8:16]
        pool_creator = original_pool[107:139]
        canonical_pool = h.Pubkey.find_program_address([
            b"pool", pool_index, pool_creator,
            bytes(h.Pubkey.from_string("So11111111111111111111111111111111111111112")),
            bytes(h.base)], h.PROGRAM)[0]
        vm.vm.set_account(canonical_pool, vm.vm.get_account(h.pool))
        raw = bytearray(h.RAW); raw[56] = 0
        vm.vm.set_account(h.CONFIG_KEY, h.Account(h.CONFIG["lamports"], bytes(raw), h.PROGRAM))
        for key, mint, native in [(h.userbase, h.base, False), (h.userquote, h.quote, True)]:
            vm.vm.set_account(key, h.Account(10**15 + 2039280 if native else 10**9,
                h.token(mint, h.PAYER.pubkey(), 10**15, native), h.TOKEN))
        vm.vm.set_account(h.volume, h.Account(0, b"", h.Pubkey.default()))
        for key in [h.PUMP_GLOBAL, h.PUMP_FEES, h.PUMP_EVENT]:
            vm.vm.set_account(key, h.Account(10**9, b"", h.Pubkey.default()))
        ix = next(i for i in h.IDL["instructions"] if i["name"] == "multi_hop_swap")
        keys = [h.PAYER.pubkey(), h.userbase, h.userbase, h.CONFIG_KEY,
                h.feeconfig, h.volume, h.buyback, h.TOKEN, h.TOKEN22,
                h.Pubkey.default(), h.EVENT, h.PROGRAM, h.PUMP,
                h.PUMP_GLOBAL, h.PUMP_FEES, h.PUMP_EVENT]
        metas = [h.AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        metas += [h.AccountMeta(k, False, True) for k in
                  (h.base, h.quote, h.pool, h.vaultbase, h.vaultquote)]
        metas[16] = h.AccountMeta(h.base, False, False)
        metas[17] = h.AccountMeta(h.quote, False, False)
        h.amm_then_curve(False)(vm, metas)
        wsol = h.Pubkey.from_string("So11111111111111111111111111111111111111112")
        # First pool is base=WSOL and quote=A; the user supplies A.
        pool = canonical_pool
        d = bytearray(vm.vm.get_account(pool).data)
        d[43:75] = bytes(wsol); d[75:107] = bytes(h.base)
        vb = h.Pubkey.find_program_address([bytes(pool), bytes(h.TOKEN), bytes(wsol)], h.ATA)[0]
        d[139:171] = bytes(vb); d[171:203] = bytes(h.vaultquote)
        vm.vm.set_account(pool, h.Account(10**9, bytes(d), h.PROGRAM))
        native_mint = vm.vm.get_account(h.quote)
        vm.vm.set_account(wsol, native_mint)
        vm.vm.set_account(vb, h.Account(10**12, h.token(wsol, pool, 10**15, True), h.TOKEN))
        metas[16] = h.AccountMeta(wsol, False, False)
        metas[17] = h.AccountMeta(h.base, False, False)
        metas[18] = h.AccountMeta(pool, False, True)
        metas[19] = h.AccountMeta(vb, False, True)
        metas[20] = h.AccountMeta(h.vaultquote, False, True)
        # The second hop is a native Main curve, so both its declared quote and
        # quote vault must also be WSOL rather than the first pool's quote A.
        metas[21] = h.AccountMeta(wsol, False, False)
        curve_data = bytearray(vm.vm.get_account(h.CURVE).data)
        curve_data[83:115] = bytes(wsol)
        vm.vm.set_account(h.CURVE, h.Account(10**12, bytes(curve_data), h.PUMP))
        curve_quote = h.Pubkey.find_program_address(
            [bytes(h.CURVE), bytes(h.TOKEN), bytes(wsol)], h.ATA)[0]
        vm.vm.set_account(curve_quote, h.Account(
            10**12, h.token(wsol, h.CURVE, 10**15, True), h.TOKEN))
        metas[24] = h.AccountMeta(curve_quote, False, True)
        # Align the final output token account with the curve base mint.
        final_out = bytearray(vm.vm.get_account(metas[2].pubkey).data)
        final_out[:32] = bytes(h.CM)
        vm.vm.set_account(metas[2].pubkey, h.Account(
            10**9, bytes(final_out), h.TOKEN22))
        # metas[2] remains the final curve-output account; intermediate WSOL
        # stays in the first pool vault for the next hop.
        if single_hop:
            user_wsol = h.Pubkey.find_program_address(
                [bytes(h.PAYER.pubkey()), bytes(h.TOKEN), bytes(wsol)], h.ATA)[0]
            vm.vm.set_account(user_wsol, h.Account(
                10**12, h.token(wsol, h.PAYER.pubkey(), 0, True), h.TOKEN))
            metas = metas[:21]
            metas[2] = h.AccountMeta(user_wsol, False, True)
        data = bytes(ix["discriminator"]) + h.struct.pack("<QQ", 1_000_000, 1)
        tx = h.Transaction.new_signed_with_payer([h.Instruction(h.PROGRAM, data, metas)],
                                                h.PAYER.pubkey(), [h.PAYER], vm.vm.latest_blockhash())
        result = vm.vm.send_transaction(tx)
        failed = isinstance(result, h.FailedTransactionMetadata)
        return {"error": str(result.err()) if failed else None}
    if single_hop:
        return run_fixture("H-01-single-wsol-output", {
            "route": "A -> WSOL (single AMM buy, user WSOL output)",
            "input": 1_000_000}, [admin], invoke,
            h.PAYER.pubkey(), [h.PAYER], 1_234_567_890)
    return run_fixture("H-01", {"route": "A -> WSOL (AMM buy) -> B (native Main buy)",
                                "input": 1_000_000}, [admin], invoke,
                       h.PAYER.pubkey(), [h.PAYER], 1_234_567_890)


def test_h01_control():
    """Second-pass control: repository's unmodified two-buy AMM->curve route."""
    corpus = load_corpus(); h = corpus.h
    admin = module("pump_amm_admin_differential")
    def invoke():
        vm = admin.Harness(ROOT / "evidence/original/pump_amm/deployed.so")
        vm.vm.set_clock(h.Clock(100, 1234567890, 0, 0, 1234567890))
        for pid, path in [(h.TOKEN, dependency("spl_token")),
                          (h.TOKEN22, dependency("spl_token_2022")),
                          (h.FEES, original("pump_fees")),
                          (h.ATA, dependency("associated_token")),
                          (h.PUMP, original("pump"))]:
            vm.vm.add_program_from_file(pid, path)
        for row in h.f["accounts"].values():
            vm.vm.set_account(h.Pubkey.from_string(row["address"]), h.Account(
                row["lamports"], h.base64.b64decode(row["data_base64"]),
                h.Pubkey.from_string(row["owner"])))
        raw = bytearray(h.RAW); raw[56] = 0
        vm.vm.set_account(h.CONFIG_KEY, h.Account(h.CONFIG["lamports"], bytes(raw), h.PROGRAM))
        for key, mint, native in [(h.userbase, h.base, False), (h.userquote, h.quote, True)]:
            vm.vm.set_account(key, h.Account(10**15 + 2039280 if native else 10**9,
                h.token(mint, h.PAYER.pubkey(), 10**15, native), h.TOKEN))
        vm.vm.set_account(h.volume, h.Account(0, b"", h.Pubkey.default()))
        for key in [h.PUMP_GLOBAL, h.PUMP_FEES, h.PUMP_EVENT]:
            vm.vm.set_account(key, h.Account(10**9, b"", h.Pubkey.default()))
        ix = next(i for i in h.IDL["instructions"] if i["name"] == "multi_hop_swap")
        keys = [h.PAYER.pubkey(), h.userquote, h.userbase, h.CONFIG_KEY,
                h.feeconfig, h.volume, h.buyback, h.TOKEN, h.TOKEN22,
                h.Pubkey.default(), h.EVENT, h.PROGRAM, h.PUMP,
                h.PUMP_GLOBAL, h.PUMP_FEES, h.PUMP_EVENT]
        metas = [h.AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        metas += [h.AccountMeta(h.base, False, False),
                  h.AccountMeta(h.quote, False, False),
                  h.AccountMeta(h.pool, False, True),
                  h.AccountMeta(h.vaultbase, False, True),
                  h.AccountMeta(h.vaultquote, False, True)]
        h.amm_then_curve(False)(vm, metas)
        data = bytes(ix["discriminator"]) + h.struct.pack("<QQ", 1_000_000, 1)
        tx = h.Transaction.new_signed_with_payer([h.Instruction(h.PROGRAM, data, metas)],
                                                h.PAYER.pubkey(), [h.PAYER], vm.vm.latest_blockhash())
        result = vm.vm.send_transaction(tx)
        failed = isinstance(result, h.FailedTransactionMetadata)
        return {"error": str(result.err()) if failed else None}
    return run_fixture("H-01-control-two-buy", {
        "route": "unmodified repository AMM buy -> Main curve buy control",
        "input": 1_000_000}, [admin], invoke, h.PAYER.pubkey(), [h.PAYER], 1_234_567_890)


def cashback_case(fid, item, instruction="claim_cashback_v2"):
    f = importlib.import_module("tests.test_claim_cashback_v2_captured") if False else None
    # tests is not a package; load the retained fixture by path.
    spec = importlib.util.spec_from_file_location("main_cashback_fixture", ROOT / "tests/test_claim_cashback_v2_captured.py")
    f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    made = []
    original_type = f.LiteSVM
    def factory():
        vm = FixtureVM(); made.append(vm); return vm
    f.LiteSVM = factory
    try:
        lite = f.run_captured(item)
    finally:
        f.LiteSVM = original_type
    vm = made[0]
    result = replay(vm, f.PAYER.pubkey(), [f.PAYER], f.TIMESTAMP)
    result["litesvm_error"] = lite["error"]
    result["litesvm_tokens"] = lite.get("tokens")
    return write_case(fid, item, result)


def test_m15():
    fspec = importlib.util.spec_from_file_location("main_cashback_constants", ROOT / "tests/test_claim_cashback_v2_captured.py")
    f = importlib.util.module_from_spec(fspec); fspec.loader.exec_module(f)
    saturate = f.case(stable_claimed=42, uva_ata=f.U64 - 42, quote_user_balance=0)
    path1 = cashback_case("M-15-saturate", saturate)
    positive = f.case(stable_claimed=f.U64, uva_ata=1, quote_user_balance=0)
    path2 = cashback_case("M-15-positive-after-saturation", positive)
    native = f.case(native=True, stable_claimed=f.U64, extra=1)
    path3 = cashback_case("M-15-native-after-saturation", native)
    return {"artifacts": [path1, path2, path3]}


def test_l06():
    # Reuse the exact cashback account construction, then replace the target
    # instruction with a normally signed user close. No sigVerify bypass.
    spec = importlib.util.spec_from_file_location("main_close_fixture", ROOT / "tests/test_claim_cashback_v2_captured.py")
    f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    item = f.case(extra=1_000_000, unclaimed=0) if False else f.case(extra=1_000_000)
    made = []
    original_type = f.LiteSVM
    original_ix = f.IX
    close_ix = next(i for i in f.IDL["instructions"] if i["name"] == "close_user_volume_accumulator")
    class CloseVM(FixtureVM):
        pass
    def factory():
        vm = CloseVM(); made.append(vm); return vm
    f.LiteSVM = factory
    f.IX = close_ix
    # Patch only the final account-meta construction by wrapping Instruction.
    original_instruction = f.Instruction
    def close_instruction(program, data, metas):
        user_volume = f.UVA
        metas = [AccountMeta(f.PAYER.pubkey(), True, True),
                 AccountMeta(f.USER, True, True),
                 AccountMeta(user_volume, False, True),
                 AccountMeta(f.Pubkey.default(), False, False),
                 AccountMeta(f.EVENT_AUTHORITY, False, False),
                 AccountMeta(f.PUMP, False, False)]
        return original_instruction(program, data, metas)
    f.Instruction = close_instruction
    try:
        # Transaction must be signed by USER as well as the payer.
        original_transaction = f.Transaction
        class CloseTransaction:
            @staticmethod
            def new_signed_with_payer(ixs, payer, signers, blockhash):
                return original_transaction.new_signed_with_payer(ixs, payer, [f.PAYER, CloseTransaction.user], blockhash)
        CloseTransaction.user = None
        # USER is only a Pubkey in the fixture; use a matching disposable key
        # cannot be substituted after PDA derivation. Therefore use the actual
        # claim fixture's user as nonsigner is impossible for close: build a
        # test-owned user fixture instead in the next function.
        raise RuntimeError("close fixture replaced by test-owned user builder")
    finally:
        f.LiteSVM = original_type; f.IX = original_ix; f.Instruction = original_instruction


def test_l06_owned():
    from solders.keypair import Keypair
    spec = importlib.util.spec_from_file_location("main_close_owned", ROOT / "tests/test_claim_cashback_v2_captured.py")
    f = importlib.util.module_from_spec(spec); spec.loader.exec_module(f)
    user = Keypair.from_seed(bytes([29]) * 32)
    payer = f.PAYER
    uva = Pubkey.find_program_address([b"user_volume_accumulator", bytes(user.pubkey())], f.PUMP)[0]
    mint = f.QUOTE_MINT
    uva_ata = f.ata(uva, mint)
    user_ata = f.ata(user.pubkey(), mint)
    vm = FixtureVM()
    vm.add_program_from_file(f.PUMP, f.PUMP_ELF)
    vm.add_program_from_file(f.TOKEN, f.TOKEN_ELF)
    vm.add_program_from_file(f.ATA, f.ATA_ELF)
    vm.set_clock(Clock(100, f.TIMESTAMP, 0, 0, f.TIMESTAMP))
    vm.set_account(payer.pubkey(), Account(10**12, b"", f.SYSTEM))
    vm.set_account(user.pubkey(), Account(10**9, b"", f.SYSTEM))
    data = bytearray(f.uva_data(f.case(extra=1_000_000)))
    data[8:40] = bytes(user.pubkey())
    struct.pack_into("<Q", data, 41, 123)  # pending unclaimed incentive rights
    vm.set_account(uva, Account(f.rent(f.UVA_LEN) + 1_000_000, bytes(data), f.PUMP))
    vm.set_account(mint, Account(10**9, f.mint_data(), f.TOKEN))
    vm.set_account(uva_ata, Account(f.TOKEN_RENT, f.token_data(mint, uva, 500_000), f.TOKEN))
    vm.set_account(user_ata, Account(f.TOKEN_RENT, f.token_data(mint, user.pubkey(), 3), f.TOKEN))
    close_ix = next(i for i in f.IDL["instructions"] if i["name"] == "close_user_volume_accumulator")
    names = {"payer": payer.pubkey(), "user": user.pubkey(),
             "user_volume_accumulator": uva, "system_program": f.SYSTEM,
             "event_authority": f.EVENT_AUTHORITY, "program": f.PUMP}
    metas = [AccountMeta(names[a["name"]], bool(a.get("signer")), bool(a.get("writable")))
             for a in close_ix["accounts"]]
    tx = Transaction.new_signed_with_payer([Instruction(f.PUMP, bytes(close_ix["discriminator"]), metas)],
                                           payer.pubkey(), [payer, user], vm.latest_blockhash())
    vm.send_transaction(tx)
    result = replay(vm, payer.pubkey(), [payer, user], f.TIMESTAMP)
    result["pending_unclaimed_before"] = 123
    result["token_cashback_ata"] = str(uva_ata)
    return write_case("L-06", {"user_signed_close": True, "pending_unclaimed": 123,
                               "native_excess": 1_000_000, "token_cashback": 500_000}, result)


def execute(fid):
    if fid == "L-06": return test_l06_owned()
    return {
        "L-01": test_l01, "L-16": test_l16, "M-01": test_m01,
        "M-02": test_m02, "M-06": test_m06, "M-14": test_m14,
        "M-15": test_m15, "M-16": test_m16, "M-17": test_m17,
        "H-01": test_h01, "H-03": test_h03, "H-04": test_h04,
        "H-08": test_h08,
    }[fid]()


IDS = ["L-01", "L-06", "L-16", "M-01", "M-02", "M-06", "M-14",
       "M-15", "M-16", "M-17", "H-01", "H-03", "H-04", "H-08"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ids", nargs="*", choices=IDS)
    args = parser.parse_args()
    assert sha256(original("pump")) == EXPECTED_PUMP_SHA
    for fid in args.ids or IDS:
        try:
            result = execute(fid)
            print(json.dumps({"id": fid, "ok": True, "result": result}))
        except BaseException as exc:
            path = OUT / f"{fid.lower()}-setup-error.json"
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"finding": fid, "setup_error": str(exc),
                                        "traceback": traceback.format_exc()}, indent=2) + "\n")
            print(json.dumps({"id": fid, "ok": False, "error": str(exc), "artifact": str(path)}))


if __name__ == "__main__":
    main()
