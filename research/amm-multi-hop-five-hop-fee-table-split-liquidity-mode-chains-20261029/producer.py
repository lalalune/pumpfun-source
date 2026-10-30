"""Build research/amm-multi-hop-five-hop-fee-table-split-liquidity-mode-chains-20261029 receipts.

Multi-hop fee-table split x liquidity x mode chains, 5 hops:
the split x liquidity chains of #50 under a mode gate (cashback /
mayhem) on one pool, i.e. the 5-hop generalisation of 3rd #55.
The original image prices mode-blind legs exactly as in #50; its
cashback gate fires only at the last-listed pool (p5), so
main/pool2/p3/p4-cashback buys and sells succeed on the original
while the rebuilt images fail 6079 at the gated hop in execution
order (buys head-first: main 0, pool2 1, p3 2, p4 3 ghosts; sells
tail-first: p5 0, p4 1, p3 2, pool2 3, main 4 ghosts), and
main/pool2/p3/p4-cashback sells succeed on the original and fail
6079 on the rebuilt images. Mayhem gates every hop on all images
(6080); on both-flag pools the original reports mayhem (6080)
and the rebuilt images report cashback (6079). Liquidity
(deposit/withdraw) is mode-blind on all images, and the post-trade
limit gates are the same numbers as in #55 (dep quote 29,548,629,
wd quote 29,548,628), because the hop-1 leg is depth-invariant.

The builder asserts every expected value below per image before
writing. The packet's producer.py is this file.
"""
#!/usr/bin/env python3

import base64
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import os
sys.path.insert(0, str(Path.home() / "workspace/pumpfun-sparse/scripts"))
os.chdir(Path.home() / "workspace/pumpfun-sparse")
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

from pump_amm_admin_differential import Harness
from pump_amm_liquidity_differential import (
    CONFIG, CONFIG_KEY, EVENT, IDL, PAYER, PROGRAM, RAW, TOKEN, TOKEN22,
    base, f, lp, pool, poolraw, quote, supply, token,
    userbase, userlp, userquote, vaultbase, vaultquote,
)
from pump_amm_trade_v2_differential import FEES, buyback, feeconfig, volume
from pump_amm_multi_hop_differential import (
    BASE2, BASE3, P3, POOL2, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT,
    U3, VB2, VB3, VQ2, VQ3, three_amm,
)

ROOT = Path.home() / "workspace/pumpfun-sparse"
OUT = ROOT / "research/amm-multi-hop-five-hop-fee-table-split-liquidity-mode-chains-20261029"
WS = Path.home() / "workspace/slop-verify"
IMAGES = {
    "original": ROOT / "evidence/original/pump_amm/deployed.so",
    "control": WS / "control.so",
    "candidate": WS / "candidate.so",
}
IMAGE_SHA = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in IMAGES.items()}

ATA_PROG = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
PAYER_KEY = PAYER.pubkey()
PAYER_HEX = bytes(PAYER_KEY).hex()
CREATOR = Pubkey.from_bytes(bytes(poolraw[211:243]))
CREATOR_VAULT, _ = Pubkey.find_program_address([b'creator_vault', bytes(CREATOR)], PROGRAM)
CREATOR_ATA, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(quote)], ATA_PROG)
PROTOCOL = Pubkey.from_bytes(bytes(RAW[57:89]))
PROTOCOL_ATA, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(quote)], ATA_PROG)
CREATOR_ATA_P3, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE2)], ATA_PROG)
PROTOCOL_ATA_P3, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE2)], ATA_PROG)
CREATOR_ATA_P2, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(base)], ATA_PROG)
PROTOCOL_ATA_P2, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(base)], ATA_PROG)
DEST = Pubkey.from_bytes(bytes([94]) * 32)
DEST3 = Pubkey.from_bytes(bytes([95]) * 32)
DEST2 = Pubkey.from_bytes(bytes([96]) * 32)

BASE4 = Pubkey.from_bytes(bytes([88]) * 32)
C4 = Pubkey.find_program_address([b'pool-authority', bytes(BASE4)], PUMP)[0]
P4, B4 = Pubkey.find_program_address([b'pool', bytes(2), bytes(C4), bytes(BASE4), bytes(BASE3)], PROGRAM)
VB4 = Pubkey.find_program_address([bytes(P4), bytes(TOKEN), bytes(BASE4)], ATA_PROG)[0]
VQ4 = Pubkey.find_program_address([bytes(P4), bytes(TOKEN), bytes(BASE3)], ATA_PROG)[0]
U4 = Pubkey.from_bytes(bytes([89]) * 32)
BASE5 = Pubkey.from_bytes(bytes([90]) * 32)
C5 = Pubkey.find_program_address([b'pool-authority', bytes(BASE5)], PUMP)[0]
P5, B5 = Pubkey.find_program_address([b'pool', bytes(2), bytes(C5), bytes(BASE5), bytes(BASE4)], PROGRAM)
VB5 = Pubkey.find_program_address([bytes(P5), bytes(TOKEN), bytes(BASE5)], ATA_PROG)[0]
VQ5 = Pubkey.find_program_address([bytes(P5), bytes(TOKEN), bytes(BASE4)], ATA_PROG)[0]
U5 = Pubkey.from_bytes(bytes([91]) * 32)
DEST4 = Pubkey.from_bytes(bytes([97]) * 32)
DEST5 = Pubkey.from_bytes(bytes([98]) * 32)
CREATOR_ATA_P4, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
PROTOCOL_ATA_P4, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
CREATOR_ATA_P5, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
PROTOCOL_ATA_P5, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
S_ASIS = 4194352106721

MH_KEYS_BUY = [PAYER_KEY, userquote, userbase, CONFIG_KEY, feeconfig, volume, buyback,
               TOKEN, TOKEN22, Pubkey.default(), EVENT, PROGRAM, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]
MH_KEYS_SELL = [PAYER_KEY, userbase, userquote, CONFIG_KEY, feeconfig, volume, buyback,
                TOKEN, TOKEN22, Pubkey.default(), EVENT, PROGRAM, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]
MH_TAIL = [AccountMeta(base, False, False), AccountMeta(quote, False, False),
           AccountMeta(pool, False, True), AccountMeta(vaultbase, False, True),
           AccountMeta(vaultquote, False, True)]
DEP_KEYS = [pool, CONFIG_KEY, PAYER_KEY, base, quote, lp, userbase, userquote,
            userlp, vaultbase, vaultquote, TOKEN, TOKEN22, EVENT, PROGRAM]
DEP_DISC = "78f83d531f8e6b90"
WD_DISC = "1609851aa02c47c0"
MX = 2**64 - 1
# pool tag -> (pool, quote mint, quote vault, protocol ATA, creator ATA, dest)
POOLS = {
    "main": (pool, quote, vaultquote, PROTOCOL_ATA, CREATOR_ATA, DEST),
    "p2": (POOL2, base, VQ2, PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2),
    "p3": (P3, BASE2, VQ3, PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3),
    "p4": (P4, BASE3, VQ4, PROTOCOL_ATA_P4, CREATOR_ATA_P4, DEST4),
    "p5": (P5, BASE4, VQ5, PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5),
}
WATCH = [PAYER_KEY, pool, POOL2, P3, P4, P5, base, quote, BASE2, BASE3, BASE4, BASE5, lp, userbase,
         userquote, userlp, vaultbase, vaultquote, VB2, VQ2, VB3, VQ3, VB4, VQ4, VB5, VQ5, U3, U4, U5,
         buyback, volume, feeconfig, CONFIG_KEY,
         PROTOCOL_ATA, CREATOR_ATA, DEST,
         PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3,
         PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2,
         PROTOCOL_ATA_P4, CREATOR_ATA_P4, DEST4,
         PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5]
ROLE_KEY = {"userbase": userbase, "userquote": userquote, "userlp": userlp,
            "vaultbase": vaultbase, "vaultquote": vaultquote, "buyback": buyback,
            "vb1": vaultbase, "vq1": vaultquote, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata2", "creatorata2", "dest2",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5"]
SWP_DISC = "82a42461e48287a5"
COL_DISC = "e8f5c2eeeada3a59"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def setup_vm(binary):
    h = Harness(binary)
    vm = h.vm
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    for pid, p in [(TOKEN, "evidence/dependencies/spl_token/deployed.so"),
                   (TOKEN22, "evidence/dependencies/spl_token_2022/deployed.so"),
                   (FEES, "evidence/original/pump_fees/deployed.so"),
                   (ATA_PROG, "evidence/dependencies/associated_token/deployed.so"),
                   (PUMP, "evidence/original/pump/deployed.so")]:
        vm.add_program_from_file(pid, ROOT / p)
    glob = bytearray(RAW)
    glob[56] = 0
    vm.set_account(CONFIG_KEY, Account(CONFIG["lamports"], bytes(glob), PROGRAM))
    for n, row in f["accounts"].items():
        vm.set_account(Pubkey.from_string(row["address"]),
                       Account(row["lamports"], base64.b64decode(row["data_base64"]),
                               Pubkey.from_string(row["owner"])))
    vm.set_account(pool, Account(f["accounts"]["pool"]["lamports"], bytes(poolraw), PROGRAM))
    mint = struct.pack("<I", 1) + bytes(pool) + struct.pack("<Q", supply) + bytes([9, 1]) + bytes(36)
    vm.set_account(lp, Account(10**9, mint, TOKEN22))
    vm.set_account(userbase, Account(10**9, token(base, PAYER_KEY, 10**15, False), TOKEN))
    vm.set_account(userquote, Account(10**15 + 2039280, token(quote, PAYER_KEY, 10**15, True), TOKEN))
    vm.set_account(userlp, Account(10**9, token(lp, PAYER_KEY, supply // 2, False), TOKEN22))
    vm.set_account(volume, Account(0, b"", Pubkey.default()))
    vm.set_account(DEST, Account(2039280, token(quote, CREATOR, 0, True), TOKEN))
    vm.set_account(CREATOR_ATA, Account(2039280, token(quote, CREATOR_VAULT, 0, True), TOKEN))
    vm.set_account(PROTOCOL_ATA, Account(2039280, token(quote, PROTOCOL, 0, True), TOKEN))
    # BASE2/base are SPL mints, NOT the native SOL mint: non-native layout.
    vm.set_account(DEST3, Account(2039280, token(BASE2, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P3, Account(2039280, token(BASE2, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P3, Account(2039280, token(BASE2, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST2, Account(2039280, token(base, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P2, Account(2039280, token(base, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P2, Account(2039280, token(base, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST4, Account(2039280, token(BASE3, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P4, Account(2039280, token(BASE3, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P4, Account(2039280, token(BASE3, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST5, Account(2039280, token(BASE4, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P5, Account(2039280, token(BASE4, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P5, Account(2039280, token(BASE4, PROTOCOL, 0, False), TOKEN))
    for k in [PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]:
        vm.set_account(k, Account(10**9, b"", Pubkey.default()))
    return h


def build_route(h, sell):
    keys = MH_KEYS_SELL if sell else MH_KEYS_BUY
    ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
    metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
             for k, a in zip(keys, ix["accounts"])] + list(MH_TAIL)
    three_amm(sell)(SimpleNamespace(vm=h.vm), metas)
    h.vm.set_account(BASE4, h.vm.get_account(base))
    d = bytearray(poolraw)
    d[8] = B4
    d[9:11] = bytes(2)
    d[11:43] = bytes(C4)
    d[43:75] = bytes(BASE4)
    d[75:107] = bytes(BASE3)
    d[139:171] = bytes(VB4)
    d[171:203] = bytes(VQ4)
    h.vm.set_account(P4, Account(10**9, bytes(d), PROGRAM))
    for k, mi, ow in [(VB4, BASE4, P4), (VQ4, BASE3, P4), (U4, BASE4, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    g4 = [AccountMeta(BASE4, False, False), AccountMeta(BASE3, False, False),
          AccountMeta(P4, False, True), AccountMeta(VB4, False, True),
          AccountMeta(VQ4, False, True)]
    h.vm.set_account(BASE5, h.vm.get_account(base))
    d = bytearray(poolraw)
    d[8] = B5
    d[9:11] = bytes(2)
    d[11:43] = bytes(C5)
    d[43:75] = bytes(BASE5)
    d[75:107] = bytes(BASE4)
    d[139:171] = bytes(VB5)
    d[171:203] = bytes(VQ5)
    h.vm.set_account(P5, Account(10**9, bytes(d), PROGRAM))
    for k, mi, ow in [(VB5, BASE5, P5), (VQ5, BASE4, P5), (U5, BASE5, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    g5 = [AccountMeta(BASE5, False, False), AccountMeta(BASE4, False, False),
          AccountMeta(P5, False, True), AccountMeta(VB5, False, True),
          AccountMeta(VQ5, False, True)]
    if sell:
        metas[16:16] = g4
        metas[1] = AccountMeta(U4, False, True)
        metas[16:16] = g5
        metas[1] = AccountMeta(U5, False, True)
    else:
        metas.extend(g4)
        metas[2] = AccountMeta(U4, False, True)
        metas.extend(g5)
        metas[2] = AccountMeta(U5, False, True)
    return metas


def flag_pool(h, poolkey, mode):
    a = h.vm.get_account(poolkey)
    d = bytearray(a.data)
    if mode in ("cb", "both"):
        d[244] = 1
    if mode in ("mayhem", "both"):
        d[243] = 1
    h.vm.set_account(poolkey, Account(a.lamports, bytes(d), a.owner))


def apply_fee_patch(h, patch):
    if not patch:
        return
    a = h.vm.get_account(feeconfig)
    raw = bytearray(a.data)
    if "tiers_inplace" in patch:
        for i, (t, fs) in enumerate(patch["tiers_inplace"]):
            off = 69 + i * 40
            raw[off:off + 16] = t.to_bytes(16, "little")
            struct.pack_into("<QQQ", raw, off + 16, *fs)
    if "tiers_rebuild" in patch:
        tiers = patch["tiers_rebuild"]
        new = bytes(raw[:41]) + struct.pack("<QQQ", 25, 5, 0) + struct.pack("<I", len(tiers))
        for t, fs in tiers:
            new += t.to_bytes(16, "little") + struct.pack("<QQQ", *fs)
        new += struct.pack("<I", 0) + bytes(24)
        raw = bytearray(new.ljust(4097, b"\0"))
    if "stable_inplace" in patch:
        for i, (t, fs) in enumerate(patch["stable_inplace"]):
            off = 1073 + i * 40
            raw[off:off + 16] = t.to_bytes(16, "little")
            struct.pack_into("<QQQ", raw, off + 16, *fs)
    if "stable_count" in patch:
        struct.pack_into("<I", raw, 1069, patch["stable_count"])
    if "exotic" in patch:
        struct.pack_into("<QQQ", raw, 2073, *patch["exotic"])
    h.vm.set_account(feeconfig, Account(a.lamports, bytes(raw), a.owner))


POOLKEYS = {"main": pool, "p2": POOL2, "p3": P3, "p4": P4, "p5": P5}


def build_route_1hop(h, sell):
    keys = MH_KEYS_SELL if sell else MH_KEYS_BUY
    ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
    metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
             for k, a in zip(keys, ix["accounts"])] + list(MH_TAIL)
    # Unused hop pools sit at the INIT state so snapshots stay complete.
    for pk in (POOL2, P3, P4, P5):
        h.vm.set_account(pk, Account(10**9, bytes(poolraw), PROGRAM))
    return metas


def snap(vm):
    out = {}
    for k in WATCH:
        a = vm.get_account(k)
        out[str(k)] = None if a is None else {
            "lamports": a.lamports, "owner": str(a.owner),
            "data_hex": bytes(a.data).hex()}
    return out


def tok_amount(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return struct.unpack_from("<Q", raw, 64)[0] if len(raw) >= 72 else None


def tok_delta(rec, key):
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
    return (tok_amount(a) or 0) - (tok_amount(b) or 0)


def lam_delta(rec, key):
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
    return (a["lamports"] if a else 0) - (b["lamports"] if b else 0)


def pool_state(entry):
    d = bytes.fromhex(entry["data_hex"])
    return [int.from_bytes(d[245:261], "little", signed=True),
            struct.unpack_from("<Q", d, 271)[0],
            struct.unpack_from("<Q", d, 279)[0],
            struct.unpack_from("<Q", d, 203)[0]]


def vol_state(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return {"lamports": entry["lamports"], "len": len(raw),
            "user": raw[8:40].hex()}


def ev_list(logs):
    out = []
    for l in logs:
        if l.startswith("Program data: "):
            raw = base64.b64decode(l.split("Program data: ", 1)[1].strip())
            out.append(raw)
    return out


def u64(raw, off):
    return struct.unpack_from("<Q", raw, off)[0]


def decode_event(kind, raw):
    if kind in ("mhbuy5", "mhsell5", "mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind in ("swp", "swc"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "recipient": raw[112:144].hex(),
                "amount": u64(raw, 176), "bucket": raw[184]}
    if kind in ("dep", "wd"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 72), "quote": u64(raw, 80)}
    if kind == "col":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "creator": raw[16:48].hex(), "fee": u64(raw, 48),
                "vault_ata": raw[56:88].hex(), "dest": raw[88:120].hex()}
    return None


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def disc(name):
    return bytes(next(x for x in IDL["instructions"] if x["name"] == name)["discriminator"])


def do_step(h, kind, args, routes):
    if kind in ("mhbuy5", "mhsell5", "mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell5": "sell", "mhbuy5": "buy",
                        "mhsell3": "sell", "mhbuy3": "buy",
                        "mhsell1": "sell1", "mhbuy1": "buy1"}[kind]]
        data = bytes(ix["discriminator"]) + struct.pack("<QQ", args[0], args[1])
    elif kind in ("swp", "swc"):
        pool_k, mint_k, vq_k, proto_ata, creat_ata, _dest = POOLS[args]
        name = "sweep_protocol_fee" if kind == "swp" else "sweep_creator_fee"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [PAYER_KEY, CONFIG_KEY, pool_k, mint_k, TOKEN, vq_k,
                PROTOCOL if kind == "swp" else CREATOR_VAULT,
                proto_ata if kind == "swp" else creat_ata,
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name)
    elif kind == "col":
        _pool_k, mint_k, _vq_k, _proto_ata, creat_ata, dest = POOLS[args]
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [mint_k, TOKEN, CREATOR, CREATOR_VAULT, creat_ata, dest, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
    elif kind in ("dep", "wd"):
        name = "deposit" if kind == "dep" else "withdraw"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(DEP_KEYS, ix["accounts"])]
        data = bytes(ix["discriminator"]) + struct.pack("<QQQ", *args)
    else:
        raise ValueError(kind)
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, data, metas)], PAYER_KEY, [PAYER], h.vm.latest_blockhash())
    assert tx.verify_with_results() and all(tx.verify_with_results())
    before = snap(h.vm)
    r = h.vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    logs = meta.logs()
    return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "error": str(r.err()) if failed else None, "logs": logs,
            "events": [l for l in logs if l.startswith("Program data: ")],
            "before": before, "after": snap(h.vm),
            "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}


def E(dPAYER, deltas, pools, volume, event=None, events=1, error=None,
      rollback=False):
    return {"dPAYER": dPAYER, "deltas": deltas, "pools": pools,
            "volume": volume, "event": event, "events": events, "error": error,
            "rollback": rollback}


def P(vq, pf, cf, sup=S_ASIS):
    return [vq, pf, cf, sup]


INIT = P(-125882, 2488, 123394)
ZERO = P(0, 0, 0)
VOL = {"lamports": 1844400, "len": 137, "user": PAYER_HEX}


def SWP_EV(amount, bucket, recipient):
    return {"disc": SWP_DISC, "len": 185, "timestamp": 1234567890,
            "recipient": bytes(recipient).hex(), "amount": amount, "bucket": bucket}


def COL_EV(amount, vault_ata, dest):
    return {"disc": COL_DISC, "len": 120, "timestamp": 1234567890,
            "creator": bytes(CREATOR).hex(), "fee": amount,
            "vault_ata": bytes(vault_ata).hex(), "dest": bytes(dest).hex()}


MHBUY_EV = {"disc": "67f4521f2cf57777", "len": 508}
MHSELL_EV = {"disc": "3e2f370aa503dc2a", "len": 449}

D_BUY3_1E9 = {"userquote": -10**9, "vb1": -5385694844757, "vq1": 995392847,
              "vb2": -5356844515538, "vq2": 5385694844757,
              "vb3": -5315084721958, "vq3": 5356844515538,
              "u3": 5315084721958, "buyback": 4607153}
D_SELL3_1E9 = {"userquote": 180345, "vb1": 997498005, "vq1": -181191,
               "vb2": 997499001, "vq2": -997498005,
               "vb3": 10**9, "vq3": -997499001, "u3": -10**9, "buyback": 846}
D_BUY3_1E6 = {"userquote": -10**6, "vb1": -5429043355, "vq1": 995393,
              "vb2": -5429013880, "vq2": 5429043355,
              "vb3": -5415445863, "vq3": 5429013880,
              "u3": 5415445863, "buyback": 4607}
D_SELL3_1E6 = {"userquote": 180, "vb1": 997498, "vq1": -181,
               "vb2": 997499, "vq2": -997498,
               "vb3": 10**6, "vq3": -997499, "u3": -10**6, "buyback": 1}
D_BUY3_2ND = {"userquote": -10**9, "vb1": -5300268622007, "vq1": 995392847,
              "vb2": -5216136464071, "vq2": 5300268622007,
              "vb3": -5121405353567, "vq3": 5216136464071,
              "u3": 5121405353567, "buyback": 4607153}
D_SELL3_2ND = {"userquote": 180344, "vb1": 997494021, "vq1": -181190,
               "vb2": 997497007, "vq2": -997494021,
               "vb3": 10**9, "vq3": -997497007, "u3": -10**9, "buyback": 846}
D_CROSS_SELL = {"userquote": 187229, "vb1": 1019086346, "vq1": -188108,
                "vb2": 1008198438, "vq2": -1019086346,
                "vb3": 10**9, "vq3": -1008198438, "u3": -10**9, "buyback": 879}


def POOLS5(main, pool2, p3, p4, p5):
    return {"main": main, "pool2": pool2, "p3": p3, "p4": p4, "p5": p5}


def MH(dPAYER, deltas, pools, event):
    return E(dPAYER, deltas, pools, VOL, event=event, events=5)


def SWC(pool_tag, amount, pools, volume=VOL):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "creatorata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 1, CREATOR_VAULT))


def SWP(pool_tag, amount, pools, volume=VOL):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "protoata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 0, PROTOCOL))


def COL(pool_tag, amount, pools, volume=VOL):
    suffix = {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3, "p4": CREATOR_ATA_P4, "p5": CREATOR_ATA_P5}[pool_tag]
    dest = {"main": DEST, "p2": DEST2, "p3": DEST3, "p4": DEST4, "p5": DEST5}[pool_tag]
    return E(-5000, {"creatorata" + suffix: -amount, "dest" + suffix: amount},
             pools, volume, event=COL_EV(amount, vault_ata, dest))


def NOOP(pools, volume=VOL):
    return E(-5000, {}, pools, volume, events=0)


def FAIL(code, events, pools, event, volume=None):
    return E(-5000, {}, pools, volume, event=event, events=events,
             error=code, rollback=True)


def MH1(dPAYER, deltas, pools, event):
    return E(dPAYER, deltas, pools, VOL, event=event, events=1)


# --- case expectations ---
CAP0 = 182350153971
CAP_BUY1 = 185295721063
CAP_SELL1 = 182349613986
A = (10, 111, 333)
B = (20, 222, 444)
C = (30, 333, 555)
T_BUY = CAP0 + 10**9
T_SELL_MID = (CAP0 + CAP_SELL1) // 2


def TIERS_AB(t):
    return {"tiers_inplace": [(100, A), (t, B)]}


CASES = [
    {"label": 'a-cb-dep-buy5', "flags": {'main': 'cb'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385705107182, 'vq1': 995392847, 'vb2': -5356854668309, 'vq2': 5385705107182, 'vb3': -5328311677693, 'vq3': 5356854668309, 'vb4': -5300071246842, 'vq4': 5328311677693, 'vb5': -5259050280623, 'vq5': 5300071246842, 'u5': 5259050280623, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643552938, 2488, 2643550450, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-cb-dep-sell5', "flags": {'main': 'cb'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhsell5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 846}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-cb-dep-buy-cross5', "flags": {'main': 'cb'}, "fee_patch": {'tiers_inplace': [[100, [10, 111, 333]], [183350153971, [20, 222, 444]]]}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5376193755410, 'vq1': 994510929, 'vb2': -5347444856437, 'vq2': 5376193755410, 'vb3': -5319001788351, 'vq3': 5347444856437, 'vb4': -5290859696826, 'vq4': 5319001788351, 'vb5': -5249958011207, 'vq5': 5290859696826, 'u5': 5249958011207, 'buyback': 5489071}, 'pools': {'main': [-5614954, 5491560, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2638958649, 2488, 2638956161, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5234081918787, 'vq1': 989141068, 'vb2': -5151434811531, 'vq2': 5234081918787, 'vb3': -5070796637475, 'vq3': 5151434811531, 'vb4': -4992100843061, 'vq4': 5070796637475, 'vb5': -4903163691967, 'vq5': 4992100843061, 'u5': 4903163691967, 'buyback': 10858932}, 'pools': {'main': [-16473886, 16350492, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5128784506, 2488, 5128782018, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-cb-dep1e12-buy5', "flags": {'main': 'cb'}, "steps": [('dep', [1000000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895223680, 'userquote': -29312409095, 'userlp': 1000000000000, 'vb1': 160619895223680, 'vq1': 29312409095}, 'pools': {'main': [-125882, 2488, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895223680, 'quote': 29312409095}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5393996348726, 'vq1': 995392847, 'vb2': -5365057250182, 'vq2': 5393996348726, 'vb3': -5336427014409, 'vq3': 5365057250182, 'vb4': -5308100722982, 'vq4': 5336427014409, 'vb5': -5266975647284, 'vq5': 5308100722982, 'u5': 5266975647284, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2647557665, 2488, 2647555177, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895223680, 'userquote': -29312409095, 'userlp': 1000000000000, 'vb1': 160619895223680, 'vq1': 29312409095}, 'pools': {'main': [-125882, 2488, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895223680, 'quote': 29312409095}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-mayhem-dep-buy5', "flags": {'main': 'mayhem'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}]},
    {"label": 'a-both-dep-buy5', "flags": {'main': 'both'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-p2-cb-dep-buy5', "flags": {'p2': 'cb'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385705107182, 'vq1': 995392847, 'vb2': -5356854668309, 'vq2': 5385705107182, 'vb3': -5328311677693, 'vq3': 5356854668309, 'vb4': -5300071246842, 'vq4': 5328311677693, 'vb5': -5259050280623, 'vq5': 5300071246842, 'u5': 5259050280623, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643552938, 2488, 2643550450, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 1, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-p4-cb-dep-buy5', "flags": {'p4': 'cb'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385705107182, 'vq1': 995392847, 'vb2': -5356854668309, 'vq2': 5385705107182, 'vb3': -5328311677693, 'vq3': 5356854668309, 'vb4': -5300071246842, 'vq4': 5328311677693, 'vb5': -5259050280623, 'vq5': 5300071246842, 'u5': 5259050280623, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643552938, 2488, 2643550450, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-p5-cb-dep-buy5', "flags": {'p5': 'cb'}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': '6079', 'rollback': True}]},
    {"label": 'a-cb-dep-exotic5', "flags": {'main': 'cb'}, "fee_patch": {'exotic': [25, 5, 333]}, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1]), ('swc', 'p5'), ('col', 'p5')], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385705107182, 'vq1': 995392847, 'vb2': -5356854668309, 'vq2': 5385705107182, 'vb3': -5328311677693, 'vq3': 5356854668309, 'vb4': -5300071246842, 'vq4': 5328311677693, 'vb5': -5090837464986, 'vq5': 5300071246842, 'u5': 5090837464986, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-170392453088, 2488, 170392450600, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'vq5': -170392450600, 'creatorata5': 170392450600}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 170392450600, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'creatorata5': -170392450600, 'dest5': 170392450600}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 170392450600, 'vault_ata': '572b2374b081b839a27bf4df267942ad32e4ee657d81318902bb6c13cb1b53d7', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, 'events': 1, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'vq5': -123394, 'creatorata5': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'creatorata5': -123394, 'dest5': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': '572b2374b081b839a27bf4df267942ad32e4ee657d81318902bb6c13cb1b53d7', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, 'events': 1, 'error': None, 'rollback': False}]}},
    {"label": 'a-cb-wd-buy5', "flags": {'main': 'cb'}, "steps": [('wd', [1000000000, 0, 0]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29312409, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385684577433, 'vq1': 995392847, 'vb2': -5356834357921, 'vq2': 5385684577433, 'vb3': -5328291583169, 'vq3': 5356834357921, 'vb4': -5300051364757, 'vq4': 5328291583169, 'vb5': -5259030656171, 'vq5': 5300051364757, 'u5': 5259030656171, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643543022, 2488, 2643540534, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29312409, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'a-cb-vq0-dep-buy5', "flags": {'main': 'cb'}, "vq_patch": 0, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [30, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385699636968, 'vq1': 995392847, 'vb2': -5356849256545, 'vq2': 5385699636968, 'vb3': -5328306323447, 'vq3': 5356849256545, 'vb4': -5300065949201, 'vq4': 5328306323447, 'vb5': -5259045051629, 'vq5': 5300065949201, 'u5': 5259045051629, 'buyback': 4607153}, 'pools': {'main': [-4607124, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643550296, 2488, 2643547808, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [30, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [30, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'b-cb-buy-dep-buy5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userbase': -159335860239, 'userquote': -29548629, 'userlp': 1000000000, 'vb1': 159335860239, 'vq1': 29548629}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159335860239, 'quote': 29548629}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5300278641554, 'vq1': 995392847, 'vb2': -5216146272865, 'vq2': 5300278641554, 'vb3': -5134070591734, 'vq3': 5216146272865, 'vb4': -5053983051570, 'vq4': 5134070591734, 'vb5': -4963549649179, 'vq5': 5053983051570, 'u5': 4963549649179, 'buyback': 4607153}, 'pools': {'main': [-9340190, 9216796, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5164237783, 2488, 5164235295, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'b-cb-buy-dep-sell5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhsell5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userbase': -159335860239, 'userquote': -29548629, 'userlp': 1000000000, 'vb1': 159335860239, 'vq1': 29548629}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159335860239, 'quote': 29548629}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userquote': 191240, 'vb1': 1040920104, 'vq1': -192138, 'vb2': 1029798947, 'vq2': -1040920104, 'vb3': 1018855069, 'vq3': -1029798947, 'vb4': 1008084723, 'vq4': -1018855069, 'vb5': 1000000000, 'vq5': -1008084723, 'u5': -1000000000, 'buyback': 898}, 'pools': {'main': [-4733934, 4610540, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2644053287, 2488, 2644050799, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}]}},
    {"label": 'b-mayhem-buy-dep-buy5', "flags": {'main': 'mayhem'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}]},
    {"label": 'b-cb-buy-dep-swc-col5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('swc', 'main'), ('col', 'main'), ('swp', 'main')], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userbase': -159335860239, 'userquote': -29548629, 'userlp': 1000000000, 'vb1': 159335860239, 'vq1': 29548629}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159335860239, 'quote': 29548629}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-4609642, 4609642, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'creatorata': -123394, 'dest': 123394}, 'pools': {'main': [-4609642, 4609642, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': '21121023f08971cd5db1e5ec3043d7a23d911a6df02339858f08f6fae8cb227f', 'dest': '5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e'}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'vq1': -4609642, 'protoata': 4609642}, 'pools': {'main': [0, 0, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 4609642, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-2488, 2488, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'creatorata': -123394, 'dest': 123394}, 'pools': {'main': [-2488, 2488, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': '21121023f08971cd5db1e5ec3043d7a23d911a6df02339858f08f6fae8cb227f', 'dest': '5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e'}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'vq1': -2488, 'protoata': 2488}, 'pools': {'main': [0, 0, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 2488, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False}]}},
    {"label": 'b-cb-sell-dep-sell5', "flags": {'main': 'cb'}, "steps": [('mhsell5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhsell5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 846}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userbase': -160620133043, 'userquote': -29312366, 'userlp': 1000000000, 'vb1': 160620133043, 'vq1': 29312366}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160620133043, 'quote': 29312366}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userquote': 180343, 'vb1': 997488049, 'vq1': -181189, 'vb2': 997491035, 'vq2': -997488049, 'vb3': 997494021, 'vq3': -997491035, 'vb4': 997497007, 'vq4': -997494021, 'vb5': 1000000000, 'vq5': -997497007, 'u5': -1000000000, 'buyback': 846}, 'pools': {'main': [-127576, 4182, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-1125881, 2488, 1123393, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}]}},
    {"label": 'c-cb-swc-buy5', "flags": {'main': 'cb'}, "steps": [('swc', 'main'), ('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'c-mayhem-swp-buy5', "flags": {'main': 'mayhem'}, "steps": [('swp', 'main'), ('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6013', 'rollback': True}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}]},
    {"label": 'c-cb-swc-sell5', "flags": {'main': 'cb'}, "steps": [('swc', 'main'), ('mhsell5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 846}, 'pools': {'main': [-3335, 3335, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creatorata': 123394}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}]}},
    {"label": 'd-cb-buy-dep-limit-low5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 29548628])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}]}},
    {"label": 'd-cb-buy-dep-limit-exact5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 29548629])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {'userbase': -159335860239, 'userquote': -29548629, 'userlp': 1000000000, 'vb1': 159335860239, 'vq1': 29548629}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159335860239, 'quote': 29548629}, 'events': 1, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}]}},
    {"label": 'd-cb-buy-wd-limit-high5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1]), ('wd', [1000000000, 0, 29548629])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6004', 'rollback': True}]}},
    {"label": 'd-mayhem-buy-dep-limit5', "flags": {'main': 'mayhem'}, "steps": [('mhbuy5', [1000000000, 1]), ('dep', [1000000000, 18446744073709551615, 29548628])], "expect": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}]},
    {"label": 'e-cb-dep-buy1', "flags": {'main': 'cb'}, "onehop": True, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy1', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]},
    {"label": 'e-cb-dep-sell1', "flags": {'main': 'cb'}, "onehop": True, "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhsell1', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]},
    {"label": 'z-cb-buy5', "flags": {'main': 'cb'}, "steps": [('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'z-cb-sell5', "flags": {'main': 'cb'}, "steps": [('mhsell5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -1849400, 'deltas': {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 846}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 5, 'error': None, 'rollback': False}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': '6079', 'rollback': True}]}},
    {"label": 'z-mayhem-buy5', "flags": {'main': 'mayhem'}, "steps": [('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}]},
    {"label": 'z-both-buy5', "flags": {'main': 'both'}, "steps": [('mhbuy5', [1000000000, 1])], "expect": {"original": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True}], "rebuilt": [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True}]}},
    {"label": 'z-dep-buy5', "steps": [('dep', [1000000000, 18446744073709551615, 18446744073709551615]), ('mhbuy5', [1000000000, 1])], "expect": [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5385705107182, 'vq1': 995392847, 'vb2': -5356854668309, 'vq2': 5385705107182, 'vb3': -5328311677693, 'vq3': 5356854668309, 'vb4': -5300071246842, 'vq4': 5328311677693, 'vb5': -5259050280623, 'vq5': 5300071246842, 'u5': 5259050280623, 'buyback': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643552938, 2488, 2643550450, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 5, 'error': None, 'rollback': False}]},
]

STEP_KIND = {"mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1",
             "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd"}
POOL5 = (("main", pool), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5))


def case_expect(case, image_name):
    exp = case["expect"]
    if isinstance(exp, dict):
        return exp["original" if image_name == "original" else "rebuilt"]
    return exp


def run_case(case, image_name, binary):
    h = setup_vm(binary)
    apply_fee_patch(h, case.get("fee_patch"))
    if case.get("vq_patch") is not None:
        a = h.vm.get_account(pool)
        d = bytearray(a.data)
        d[245:261] = case["vq_patch"].to_bytes(16, "little", signed=True)
        h.vm.set_account(pool, Account(a.lamports, bytes(d), a.owner))
    if case.get("onehop"):
        routes = {"buy1": build_route_1hop(h, False), "sell1": build_route_1hop(h, True)}
    else:
        routes = {"buy": build_route(h, False), "sell": build_route(h, True)}
    for tag, mode in case.get("flags", {}).items():
        flag_pool(h, POOLKEYS[tag], mode)
    out = []
    for step, exp in zip(case["steps"], case_expect(case, image_name)):
        kind = step[0]
        args = step[1] if len(step) > 1 else None
        rec = do_step(h, kind, args, routes)
        tag = f"{case['label']}/{image_name}/{kind}"
        if exp["error"] is None:
            check(rec["error"] is None, f"{tag}: unexpected error {rec['error']}")
        else:
            check(rec["error"] is not None and exp["error"] in rec["error"],
                  f"{tag}: expected error {exp['error']}, got {rec['error']}")
        check(len(rec["events"]) == exp["events"],
              f"{tag}: events {len(rec['events'])} != {exp['events']}")
        d_payer = lam_delta(rec, PAYER_KEY)
        check(d_payer == exp["dPAYER"], f"{tag}: dPAYER {d_payer} != {exp['dPAYER']}")
        for role, want in exp["deltas"].items():
            got_d = tok_delta(rec, ROLE_KEY[role])
            check(got_d == want, f"{tag}: delta {role} {got_d} != {want}")
        for role in TOKEN_ROLES:
            if role in exp["deltas"]:
                continue
            got_d = tok_delta(rec, ROLE_KEY[role])
            check(got_d == 0, f"{tag}: unexpected delta {role} {got_d}")
        for pool_name, pool_key in POOL5:
            got_pool = pool_state(rec["after"][str(pool_key)])
            check(got_pool == exp["pools"][pool_name],
                  f"{tag}: pool {pool_name} {got_pool} != {exp['pools'][pool_name]}")
        got_vol = vol_state(rec["after"][str(volume)])
        check(got_vol == exp["volume"], f"{tag}: volume {got_vol} != {exp['volume']}")
        if exp.get("rollback"):
            for k, b in rec["before"].items():
                if k == str(PAYER_KEY):
                    continue
                check(rec["after"][k] == b, f"{tag}: rollback violated for {k}")
        if exp.get("event") is not None:
            raws = ev_list(rec["logs"])
            check(len(raws) == exp["events"],
                  f"{tag}: decoded events {len(raws)} != {exp['events']}")
            for raw in raws:
                got = decode_event(STEP_KIND[kind], raw)
                check(got is not None, f"{tag}: event decode failed")
                for fkey, want in exp["event"].items():
                    check(got.get(fkey) == want,
                          f"{tag}: event {fkey} {got.get(fkey)} != {want}")
        rec["case"] = case["label"]
        rec["image"] = image_name
        rec["step"] = kind
        out.append(rec)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "runtime").mkdir(exist_ok=True)
    receipts = []
    report_cases = []
    for case in CASES:
        per_image = {}
        for image_name, binary in IMAGES.items():
            per_image[image_name] = run_case(case, image_name, binary)
        for image_name in IMAGES:
            for rec in per_image[image_name]:
                receipts.append(rec)

        def surface(recs):
            out = []
            for rec in recs:
                def strip(snap):
                    d = dict(snap)
                    if d.get(str(PAYER_KEY)) is not None:
                        d[str(PAYER_KEY)] = dict(d[str(PAYER_KEY)])
                        d[str(PAYER_KEY)]["lamports"] = 0
                    return d
                out.append({"step": rec["step"], "error": rec["error"],
                            "events": len(rec["events"]),
                            "before": strip(rec["before"]), "after": strip(rec["after"])})
            return out
        # This packet PINS a divergence on purpose: do not assert surface
        # equality. Record it instead; control must still equal candidate.
        base = surface(per_image["original"])
        divergent = (surface(per_image["control"]) != base
                     or surface(per_image["candidate"]) != base)
        check(surface(per_image["control"]) == surface(per_image["candidate"]),
              f"{case['label']}: control and candidate surfaces differ")
        report_cases.append({"label": case["label"],
                             "flags": case.get("flags", {}),
                             "onehop": bool(case.get("onehop")),
                             "divergent": divergent,
                             "steps": case["expect"],
                             "error_sites": {image_name: [r["site"] for r in per_image[image_name]] for image_name in IMAGES}})
        print(f"OK {case['label']} ({len(case['steps'])} steps x 3 images)")
    parts = []
    for i in range(0, len(receipts), 10):
        chunk = receipts[i:i + 10]
        name = f"raw-transactions-part{i // 10 + 1:02d}.jsonl.gz"
        path = OUT / "runtime" / name
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            for rec in chunk:
                fh.write(json.dumps(rec) + "\n")
        parts.append({"file": f"runtime/{name}", "count": len(chunk),
                      "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size})
    report = {"case_count": len(CASES), "receipt_count": len(receipts),
              "counts": {"cases": len(CASES), "receipts": len(receipts),
                         "parts": len(parts)},
              "mismatches": [],
              "input_sha256": {k: IMAGE_SHA[k] for k in IMAGES},
              "parts": parts, "cases": report_cases,
              "images": {k: IMAGE_SHA[k] for k in IMAGES}}
    with gzip.open(OUT / "runtime" / "report.json.gz", "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(report, indent=2))
    print(f"cases={len(CASES)} receipts={len(receipts)} parts={len(parts)}")
    for p in parts:
        print(f"  {p['file']} {p['count']} receipts {p['bytes']} bytes")
    print("NEXT: write verify.py and README.md, then regenerate MANIFEST.json")
    print("ADDRESSES for verify.py:")
    for name, key in [("POOL", pool), ("POOL2", POOL2), ("P3", P3), ("P4", P4), ("P5", P5),
                      ("BASE2", BASE2), ("BASE3", BASE3), ("BASE4", BASE4), ("BASE5", BASE5),
                      ("VB2", VB2), ("VQ2", VQ2), ("VB3", VB3), ("VQ3", VQ3),
                      ("VB4", VB4), ("VQ4", VQ4), ("VB5", VB5), ("VQ5", VQ5),
                      ("U3", U3), ("U4", U4), ("U5", U5),
                      ("CREATOR", CREATOR), ("CREATOR_VAULT", CREATOR_VAULT),
                      ("PROTOCOL", PROTOCOL),
                      ("PROTOCOL_ATA", PROTOCOL_ATA), ("CREATOR_ATA", CREATOR_ATA),
                      ("DEST", DEST),
                      ("PROTOCOL_ATA_P3", PROTOCOL_ATA_P3), ("CREATOR_ATA_P3", CREATOR_ATA_P3),
                      ("DEST3", DEST3),
                      ("PROTOCOL_ATA_P2", PROTOCOL_ATA_P2), ("CREATOR_ATA_P2", CREATOR_ATA_P2),
                      ("DEST2", DEST2),
                      ("PROTOCOL_ATA_P4", PROTOCOL_ATA_P4), ("CREATOR_ATA_P4", CREATOR_ATA_P4),
                      ("DEST4", DEST4),
                      ("PROTOCOL_ATA_P5", PROTOCOL_ATA_P5), ("CREATOR_ATA_P5", CREATOR_ATA_P5),
                      ("DEST5", DEST5)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
