#!/usr/bin/env python3
"""Build research/amm-multi-hop-four-hop-fee-table-split-boost-tf-chains-20261029 receipts.

Multi-hop fee-table split x boost chains under transfer fee, 4 hops:
the split route (main -> POOL2 -> P3 -> P4, three_amm + g4,
final output U4, hop 1 = fee-tier cap selection, tail = exotic flat
fees) meets boost_buy_and_burn with the quote mint carrying a 100-bps
transfer fee (5000-bps and 10000-bps anchors). 3rd #64 covered the same
combination at TRUE depth 3 and 3rd #65 at TRUE depth 5; this packet
is the even-hop check at depth 4: the net-based burn, the fee-shifted
dust ladder, the net min gate, window neutrality of trades/sweeps,
proportional liquidity drift, the tf pipes composing with the boost,
and the hop-1 tier-cap shift.

3rd run packet #66: split x boost x tf, at depth 4. Findings pinned
(measured fresh on the 4-hop route; see README.md for the numbers).

The builder asserts every expected value below per image before
writing. The packet's producer.py is this file.
"""
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
    base, f, lp, pool, poolraw, quote, supply, token, transferfee,
    userbase, userlp, userquote, vaultbase, vaultquote,
)
from pump_amm_trade_v2_differential import FEES, buyback, feeconfig, volume
from pump_amm_multi_hop_differential import (
    BASE2, BASE3, P3, POOL2, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT,
    U3, VB2, VB3, VQ2, VQ3, three_amm,
)

ROOT = Path.home() / "workspace/pumpfun-sparse"
OUT = ROOT / "research/amm-multi-hop-four-hop-fee-table-split-boost-tf-chains-20261029"
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
DEST5 = Pubkey.from_bytes(bytes([99]) * 32)
CREATOR_ATA_P4, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
PROTOCOL_ATA_P4, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
CREATOR_ATA_P5, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
PROTOCOL_ATA_P5, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
PROTO22, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN22), bytes(quote)], ATA_PROG)
CREAT22, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN22), bytes(quote)], ATA_PROG)
DEST22 = Pubkey.from_bytes(bytes([98]) * 32)
_BB_OWNER = None
for _row in f["accounts"].values():
    if _row["address"] == str(buyback):
        _BB_OWNER = Pubkey.from_bytes(base64.b64decode(_row["data_base64"])[32:64])
assert _BB_OWNER is not None, "buyback fixture row not found"
BB22, _ = Pubkey.find_program_address([bytes(_BB_OWNER), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BOOST, _ = Pubkey.find_program_address([b'boost_vault', bytes(pool)], PROGRAM)
BATA, _ = Pubkey.find_program_address([bytes(BOOST), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BP3, _ = Pubkey.find_program_address([b'boost_vault', bytes(P3)], PROGRAM)
BA3, _ = Pubkey.find_program_address([bytes(BP3), bytes(TOKEN22), bytes(BASE2)], ATA_PROG)
BP4, _ = Pubkey.find_program_address([b'boost_vault', bytes(P4)], PROGRAM)
BA4, _ = Pubkey.find_program_address([bytes(BP4), bytes(TOKEN22), bytes(BASE3)], ATA_PROG)
BP5, _ = Pubkey.find_program_address([b'boost_vault', bytes(P5)], PROGRAM)
BA5, _ = Pubkey.find_program_address([bytes(BP5), bytes(TOKEN22), bytes(BASE4)], ATA_PROG)


def t22acct(owner, amount, withheld=0):
    data = bytearray(165)
    data[0:32] = bytes(quote)
    data[32:64] = bytes(owner)
    struct.pack_into("<Q", data, 64, amount)
    data[108] = 1
    return bytes(data) + bytes([2]) + struct.pack("<HH", 7, 0) + struct.pack("<HHQ", 2, 8, withheld)
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
         PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5,
         PROTO22, CREAT22, DEST22, BB22, BOOST, BATA, BP3, BA3, BP4, BA4, BP5, BA5]
ROLE_KEY = {"userbase": userbase, "userquote": userquote, "userlp": userlp,
            "vaultbase": vaultbase, "vaultquote": vaultquote, "buyback": buyback,
            "vb1": vaultbase, "vq1": vaultquote, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22,
            "boostata": BATA, "boostata3": BA3, "boostata4": BA4, "boostata5": BA5}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "protoata2", "creatorata2", "dest2",
               "bb22", "proto22", "creat22", "dest22",
               "boostata", "boostata3", "boostata4", "boostata5"]
SWP_DISC = "82a42461e48287a5"
COL_DISC = "e8f5c2eeeada3a59"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def setup_vm(binary, bps=100):
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
    # boost authority = payer, boost enabled (else 6005 InvalidAdmin).
    glob[907:939] = bytes(PAYER_KEY)
    glob[939] = 1
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
    # 0-bps transfer-fee config on quote: the boost instruction requires
    # TOKEN22 quote accounts, and the split legs route the buyback
    # through BB22. Set the TOKEN22 ATAs before the override (as in #34).
    h.vm.set_account(BB22, Account(2157600, t22acct(_BB_OWNER, 0), TOKEN22))
    h.vm.set_account(PROTO22, Account(2157600, t22acct(PROTOCOL, 0), TOKEN22))
    h.vm.set_account(CREAT22, Account(2157600, t22acct(CREATOR_VAULT, 0), TOKEN22))
    h.vm.set_account(DEST22, Account(2157600, t22acct(CREATOR, 0), TOKEN22))
    transferfee(quote, bps, 2**64 - 1)(h, [])
    # Main-pool boost accounts (mirror #34).
    h.vm.set_account(BOOST, Account(10**9, b"", Pubkey.default()))
    ex = h.vm.get_account(BATA)
    if ex is None:
        raw = token(quote, BOOST, 10**12, True)
        d = bytes(raw[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    else:
        d = bytes(ex.data[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BATA, Account(10**12 + 10**9, d, TOKEN22))
    # Tail-pool boost accounts (P3 boost is only ever attempted, never
    # expected to succeed: its window sum is 0 on every fixture here).
    h.vm.set_account(BP3, Account(10**9, b"", Pubkey.default()))
    raw3 = token(BASE2, BP3, 10**12, False)
    d3 = bytes(raw3[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BA3, Account(10**12 + 10**9, d3, TOKEN22))
    # True-tail-pool (P4) boost accounts, same shape as the P3 pair.
    h.vm.set_account(BP4, Account(10**9, b"", Pubkey.default()))
    raw4 = token(BASE3, BP4, 10**12, False)
    d4 = bytes(raw4[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BA4, Account(10**12 + 10**9, d4, TOKEN22))
    # Tail-pool (P5) boost accounts, same shape as the P3 pair.
    h.vm.set_account(BP5, Account(10**9, b"", Pubkey.default()))
    raw5 = token(BASE4, BP5, 10**12, False)
    d5 = bytes(raw5[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BA5, Account(10**12 + 10**9, d5, TOKEN22))
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
    # NOTE: no g5 hop group is appended here: this is the 4-hop route
    # (three_amm + g4), final output U4. P5 stays fixture-only (outside
    # the route) but must exist for snapshots.
    h.vm.set_account(BASE5, h.vm.get_account(base))
    h.vm.set_account(P5, Account(10**9, bytes(poolraw), PROGRAM))
    for k, mi, ow in [(VB5, BASE5, P5), (VQ5, BASE4, P5), (U5, BASE5, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    # 4-hop route: three_amm + g4, final output U4.
    if sell:
        metas[16:16] = g4
        metas[1] = AccountMeta(U4, False, True)
    else:
        metas.extend(g4)
        metas[2] = AccountMeta(U4, False, True)
    # 0-bps fee config on quote: the program requires the TOKEN22 buyback.
    m6 = metas[6]
    metas[6] = AccountMeta(BB22, m6.is_signer, m6.is_writable)
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


def wh_of(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) == 178:
        return struct.unpack_from("<Q", raw, 170)[0]
    if len(raw) == 182:
        return struct.unpack_from("<Q", raw, 174)[0]
    return None


def wh_delta(rec, key):
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
    return (wh_of(a) or 0) - (wh_of(b) or 0)


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
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
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
    if kind == "boost":
        if raw[:8].hex() != BST_DISC:
            return {"disc": raw[:8].hex(), "len": len(raw)}
        return {"disc": raw[:8].hex(), "len": len(raw),
                "requested": u64(raw, 144), "used": u64(raw, 152),
                "burned": u64(raw, 160),
                "vq": int.from_bytes(raw[168:184], "little", signed=True),
                "quote_after": u64(raw, 184), "base_after": u64(raw, 192),
                "remaining": u64(raw, 200)}
    return None


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def disc(name):
    return bytes(next(x for x in IDL["instructions"] if x["name"] == name)["discriminator"])


def do_step(h, kind, args, routes):
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell3": "sell", "mhbuy3": "buy",
                        "mhsell5": "sell", "mhbuy5": "buy",
                        "mhsell4": "sell", "mhbuy4": "buy",
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
    elif kind in ("swp22", "swc22"):
        name = "sweep_protocol_fee" if kind == "swp22" else "sweep_creator_fee"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [PAYER_KEY, CONFIG_KEY, pool, quote, TOKEN22, vaultquote,
                PROTOCOL if kind == "swp22" else CREATOR_VAULT,
                PROTO22 if kind == "swp22" else CREAT22,
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name)
    elif kind == "col22":
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [quote, TOKEN22, CREATOR, CREATOR_VAULT, CREAT22, DEST22, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
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
    elif kind in ("boost", "boost3", "boost4", "boost5"):
        if kind == "boost":
            keys = [pool, PAYER_KEY, CONFIG_KEY, base, quote, vaultbase, vaultquote,
                    BOOST, BATA, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BATA
        elif kind == "boost4":
            keys = [P4, PAYER_KEY, CONFIG_KEY, BASE4, BASE3, VB4, VQ4,
                    BP4, BA4, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BA4
        elif kind == "boost5":
            keys = [P5, PAYER_KEY, CONFIG_KEY, BASE5, BASE4, VB5, VQ5,
                    BP5, BA5, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BA5
        else:
            keys = [P3, PAYER_KEY, CONFIG_KEY, BASE3, BASE2, VB3, VQ3,
                    BP3, BA3, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BA3
        ix = next(x for x in IDL["instructions"] if x["name"] == "boost_buy_and_burn")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        metas[8] = AccountMeta(bata, False, True)
        metas[10] = AccountMeta(TOKEN22, False, False)
        data = disc("boost_buy_and_burn") + struct.pack("<QQ", *args)
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


BST_DISC = "3f451c16305cc2b9"
MHBUY_DISC = "67f4521f2cf57777"


def E(dPAYER, deltas, pools, volume, event=None, events=1, error=None,
      rollback=False, withheld=None, boost_event=None):
    return {"dPAYER": dPAYER, "deltas": deltas, "pools": pools,
            "volume": volume, "event": event, "events": events, "error": error,
            "rollback": rollback, "withheld": withheld or {},
            "boost_event": boost_event}


def BST_EV(used, burned, vq, quote_after, base_after, remaining, requested=None):
    return {"disc": BST_DISC, "len": 208,
            "requested": used if requested is None else requested, "used": used,
            "burned": burned, "vq": vq, "quote_after": quote_after,
            "base_after": base_after, "remaining": remaining}


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


def POOLS3(main, pool2, p3):
    return {"main": main, "pool2": pool2, "p3": p3}


def MH(dPAYER, deltas, pools, event, withheld=None):
    return E(dPAYER, deltas, pools, VOL, event=event, events=4, withheld=withheld)


def SWC(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "creatorata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 1, CREATOR_VAULT), withheld=withheld)


def SWP(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "protoata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 0, PROTOCOL), withheld=withheld)


def COL(pool_tag, amount, pools, volume=VOL, withheld=None):
    suffix = {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3, "p4": CREATOR_ATA_P4, "p5": CREATOR_ATA_P5}[pool_tag]
    dest = {"main": DEST, "p2": DEST2, "p3": DEST3, "p4": DEST4, "p5": DEST5}[pool_tag]
    return E(-5000, {"creatorata" + suffix: -amount, "dest" + suffix: amount},
             pools, volume, event=COL_EV(amount, vault_ata, dest), withheld=withheld)


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


CASES = [{'label': 't-fresh-boost',
  'steps': [['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-125882, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-boost',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-sell-boost',
  'steps': [['mhsell4', [1000000000, 1]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': 178541,
                         'vb1': 997497009,
                         'vq1': -181191,
                         'vb2': 997498005,
                         'vq2': -997497009,
                         'vb3': 997499001,
                         'vq3': -997498005,
                         'vb4': 1000000000,
                         'vq4': -997499001,
                         'u4': -1000000000,
                         'bb22': 837},
              'pools': {'main': [-126729, 3335, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-625882, 2488, 623394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'userquote': 1804, 'bb22': 9},
              'error': None,
              'rollback': False,
              'event': {'disc': '3e2f370aa503dc2a', 'len': 449},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-126729, 3335, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-625882, 2488, 623394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-buy-boost',
  'steps': [['mhbuy4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5248517951916,
                         'vq1': 985438918,
                         'vb2': -5166019382620,
                         'vq2': 5248517951916,
                         'vb3': -5085518093451,
                         'vq3': 5166019382620,
                         'vb4': -4994603067981,
                         'vq4': 5085518093451,
                         'u4': 4994603067981,
                         'bb22': 4515471},
              'pools': {'main': [-9248046, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5167964403, 2488, 5167961915, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-9248046, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5167964403, 2488, 5167961915, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-sell-boost',
  'steps': [['mhbuy4', [1000000000, 1]], ['mhsell4', [1000000000, 1]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': 187248,
                         'vb1': 1029649551,
                         'vq1': -190028,
                         'vb2': 1018757076,
                         'vq2': -1029649551,
                         'vb3': 1008036536,
                         'vq3': -1018757076,
                         'vb4': 1000000000,
                         'vq4': -1008036536,
                         'u4': -1000000000,
                         'bb22': 879},
              'pools': {'main': [-4687852, 4564458, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2632051683, 2488, 2632049195, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'userquote': 1892, 'bb22': 9},
              'error': None,
              'rollback': False,
              'event': {'disc': '3e2f370aa503dc2a', 'len': 449},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4687852, 4564458, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2632051683, 2488, 2632049195, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-sell-buy-boost',
  'steps': [['mhsell4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': 178541,
                         'vb1': 997497009,
                         'vq1': -181191,
                         'vb2': 997498005,
                         'vq2': -997497009,
                         'vb3': 997499001,
                         'vq3': -997498005,
                         'vb4': 1000000000,
                         'vq4': -997499001,
                         'u4': -1000000000,
                         'bb22': 837},
              'pools': {'main': [-126729, 3335, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-625882, 2488, 623394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'userquote': 1804, 'bb22': 9},
              'error': None,
              'rollback': False,
              'event': {'disc': '3e2f370aa503dc2a', 'len': 449},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332279897957,
                         'vq1': 985438918,
                         'vb2': -5304008052775,
                         'vq2': 5332279897957,
                         'vb3': -5276034477658,
                         'vq3': 5304008052775,
                         'vb4': -5235334847992,
                         'vq4': 5276034477658,
                         'u4': 5235334847992,
                         'bb22': 4515471},
              'pools': {'main': [-4687811, 4564417, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2632064525, 2488, 2632062037, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4687811, 4564417, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2632064525, 2488, 2632062037, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-swc22-boost',
  'steps': [['mhbuy4', [1000000000, 1]], ['swc22', None], ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vq1': -123394, 'creat22': 122160},
              'pools': {'main': [-4563570, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 1,
              'withheld': {'creat22': 1234},
              'error': None,
              'rollback': False,
              'event': {'disc': '82a42461e48287a5',
                        'len': 185,
                        'timestamp': 1234567890,
                        'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd',
                        'amount': 123394,
                        'bucket': 1},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4563570, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-swc22-col22-boost',
  'steps': [['mhbuy4', [1000000000, 1]],
            ['swc22', None],
            ['col22', None],
            ['boost', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vq1': -123394, 'creat22': 122160},
              'pools': {'main': [-4563570, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 1,
              'withheld': {'creat22': 1234},
              'error': None,
              'rollback': False,
              'event': {'disc': '82a42461e48287a5',
                        'len': 185,
                        'timestamp': 1234567890,
                        'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd',
                        'amount': 123394,
                        'bucket': 1},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'creat22': -122160, 'dest22': 120938},
              'pools': {'main': [-4563570, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 1,
              'withheld': {'dest22': 1222},
              'error': None,
              'rollback': False,
              'event': {'disc': 'e8f5c2eeeada3a59',
                        'len': 120,
                        'timestamp': 1234567890,
                        'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae',
                        'fee': 122160,
                        'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a',
                        'dest': '6262626262626262626262626262626262626262626262626262626262626262'},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4563570, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-boost4',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost4', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-boost4-buy',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost4', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5248517951916,
                         'vq1': 985438918,
                         'vb2': -5166019382620,
                         'vq2': 5248517951916,
                         'vb3': -5085518093451,
                         'vq3': 5166019382620,
                         'vb4': -4994603067981,
                         'vq4': 5085518093451,
                         'u4': 4994603067981,
                         'bb22': 4515471},
              'pools': {'main': [-9248046, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5167964403, 2488, 5167961915, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-boost4',
  'steps': [['boost4', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-125882, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-boost3',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost3', [1000000000, 0]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-buy-boost3-buy',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost3', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5235288546505,
                         'vq4': 5275998139846,
                         'u4': 5235288546505,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2631546401, 2488, 2631543913, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 0,
              'withheld': {},
              'error': '6065',
              'rollback': True,
              'event': None,
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5248517951916,
                         'vq1': 985438918,
                         'vb2': -5166019382620,
                         'vq2': 5248517951916,
                         'vb3': -5085518093451,
                         'vq3': 5166019382620,
                         'vb4': -4994603067981,
                         'vq4': 5085518093451,
                         'u4': 4994603067981,
                         'bb22': 4515471},
              'pools': {'main': [-9248046, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5167964403, 2488, 5167961915, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-boost',
  'steps': [['boost', [1000000000, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}}]},
 {'label': 't-vq-boost-min-exact',
  'steps': [['boost', [1000000000, 5338379201831]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}}]},
 {'label': 't-vq-boost-min-plus1',
  'steps': [['boost', [1000000000, 5338379201832]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6004',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-vq-boost-amt1',
  'steps': [['boost', [1, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6002',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-vq-boost-amt2',
  'steps': [['boost', [2, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6001',
              'rollback': True,
              'event': None,
              'boost_event': None}]},
 {'label': 't-vq-boost-amt3',
  'steps': [['boost', [3, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5435, 'vq1': 2, 'boostata': -3},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 1},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 3,
                              'used': 3,
                              'burned': 5435,
                              'vq': 1000000000,
                              'quote_after': 122946690722,
                              'base_after': 673696395907310,
                              'remaining': 999999999997}}]},
 {'label': 't-vq-boost-buy',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5206402664533,
                         'vq1': 985438918,
                         'vb2': -5179436433535,
                         'vq2': 5206402664533,
                         'vb3': -5152748102925,
                         'vq3': 5179436433535,
                         'vb4': -5113614896866,
                         'vq4': 5152748102925,
                         'u4': 5113614896866,
                         'bb22': 4515471},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2570075061, 2488, 2570072573, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-boost-sell',
  'steps': [['boost', [1000000000, 0]], ['mhsell4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': 182879,
                         'vb1': 997497009,
                         'vq1': -185594,
                         'vb2': 997498005,
                         'vq2': -997497009,
                         'vb3': 997499001,
                         'vq3': -997498005,
                         'vb4': 1000000000,
                         'vq4': -997499001,
                         'u4': -1000000000,
                         'bb22': 858},
              'pools': {'main': [999999132, 3356, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-625882, 2488, 623394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'userquote': 1848, 'bb22': 9},
              'error': None,
              'rollback': False,
              'event': {'disc': '3e2f370aa503dc2a', 'len': 449},
              'boost_event': None}]},
 {'label': 't-vq-boost-buy-buy',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5206402664533,
                         'vq1': 985438918,
                         'vb2': -5179436433535,
                         'vq2': 5206402664533,
                         'vb3': -5152748102925,
                         'vq3': 5179436433535,
                         'vb4': -5113614896866,
                         'vq4': 5152748102925,
                         'u4': 5113614896866,
                         'bb22': 4515471},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2570075061, 2488, 2570072573, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5125915548708,
                         'vq1': 985438918,
                         'vb2': -5047216746082,
                         'vq2': 5125915548708,
                         'vb3': -4970379364263,
                         'vq3': 5047216746082,
                         'vb4': -4883270291053,
                         'vq4': 4970379364263,
                         'u4': 4883270291053,
                         'bb22': 4515471},
              'pools': {'main': [990877836, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5049067263, 2488, 5049064775, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-buy-boost-buy',
  'steps': [['mhbuy4', [1000000000, 1]], ['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5289575951198,
                         'vq1': 985438918,
                         'vb2': -5261743559664,
                         'vq2': 5289575951198,
                         'vb3': -5234202528875,
                         'vq3': 5261743559664,
                         'vb4': -5194030843046,
                         'vq4': 5234202528875,
                         'u4': 5194030843046,
                         'bb22': 4515471},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5255205915165, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5255205915165,
                              'vq': 995438918,
                              'quote_after': 124922129638,
                              'base_after': 663151614046382,
                              'remaining': 999000000000}},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5125915548708,
                         'vq1': 985438918,
                         'vb2': -5046383729377,
                         'vq2': 5125915548708,
                         'vb3': -4968751413485,
                         'vq3': 5046383729377,
                         'vb4': -4880890740588,
                         'vq4': 4968751413485,
                         'u4': 4880890740588,
                         'bb22': 4515471},
              'pools': {'main': [990877836, 9124652, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5088880967, 2488, 5088878479, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-boost-swc22-col22',
  'steps': [['boost', [1000000000, 0]], ['swc22', None], ['col22', None]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -5000,
              'deltas': {'vq1': -123394, 'creat22': 122160},
              'pools': {'main': [1000123394, 2488, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'creat22': 1234},
              'error': None,
              'rollback': False,
              'event': {'disc': '82a42461e48287a5',
                        'len': 185,
                        'timestamp': 1234567890,
                        'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd',
                        'amount': 123394,
                        'bucket': 1},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'creat22': -122160, 'dest22': 120938},
              'pools': {'main': [1000123394, 2488, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'dest22': 1222},
              'error': None,
              'rollback': False,
              'event': {'disc': 'e8f5c2eeeada3a59',
                        'len': 120,
                        'timestamp': 1234567890,
                        'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae',
                        'fee': 122160,
                        'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a',
                        'dest': '6262626262626262626262626262626262626262626262626262626262626262'},
              'boost_event': None}]},
 {'label': 't-vq-boost-boost',
  'steps': [['boost', [1000000000, 0]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5254441549265, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5254441549265,
                              'vq': 1000000000,
                              'quote_after': 124926690720,
                              'base_after': 663103575161649,
                              'remaining': 998000000000}}]},
 {'label': 't-vq-buy-swc22-col22-boost-buy',
  'steps': [['mhbuy4', [1000000000, 1]],
            ['swc22', None],
            ['col22', None],
            ['boost', [1000000000, 0]],
            ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5289575951198,
                         'vq1': 985438918,
                         'vb2': -5261743559664,
                         'vq2': 5289575951198,
                         'vb3': -5234202528875,
                         'vq3': 5261743559664,
                         'vb4': -5194030843046,
                         'vq4': 5234202528875,
                         'u4': 5194030843046,
                         'bb22': 4515471},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vq1': -123394, 'creat22': 122160},
              'pools': {'main': [995562312, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 1,
              'withheld': {'creat22': 1234},
              'error': None,
              'rollback': False,
              'event': {'disc': '82a42461e48287a5',
                        'len': 185,
                        'timestamp': 1234567890,
                        'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd',
                        'amount': 123394,
                        'bucket': 1},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'creat22': -122160, 'dest22': 120938},
              'pools': {'main': [995562312, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 1,
              'withheld': {'dest22': 1222},
              'error': None,
              'rollback': False,
              'event': {'disc': 'e8f5c2eeeada3a59',
                        'len': 120,
                        'timestamp': 1234567890,
                        'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae',
                        'fee': 122160,
                        'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a',
                        'dest': '6262626262626262626262626262626262626262626262626262626262626262'},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5255205915165, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [995562312, 4563570, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2610700710, 2488, 2610698222, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5255205915165,
                              'vq': 995562312,
                              'quote_after': 124922006244,
                              'base_after': 663151614046382,
                              'remaining': 999000000000}},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5125915548708,
                         'vq1': 985438918,
                         'vb2': -5046383729377,
                         'vq2': 5125915548708,
                         'vb3': -4968751413485,
                         'vq3': 5046383729377,
                         'vb4': -4880890740588,
                         'vq4': 4968751413485,
                         'u4': 4880890740588,
                         'bb22': 4515471},
              'pools': {'main': [991001230, 9124652, 0, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5088880967, 2488, 5088878479, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-dep-boost',
  'steps': [['dep', [1000000000, 18446744073709551615, 18446744073709551615]],
            ['boost', [1000000000, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'userbase': -160619895224,
                         'userquote': -29608495,
                         'userlp': 1000000000,
                         'vb1': 160619895224,
                         'vq1': 29312410},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'vq1': 296085},
              'error': None,
              'rollback': False,
              'event': {'disc': '78f83d531f8e6b90',
                        'len': 264,
                        'base': 160619895224,
                        'quote': 29312410},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5338389284765, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338389284765,
                              'vq': 1000238445,
                              'quote_after': 123966003130,
                              'base_after': 668518626523204,
                              'remaining': 999000000000}}]},
 {'label': 't-vq-wd-boost',
  'steps': [['wd', [1000000000, 0, 0]], ['boost', [1000000000, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'userbase': 160619895223,
                         'userquote': 29019284,
                         'userlp': -1000000000,
                         'vb1': -160619895223,
                         'vq1': -29312409},
              'pools': {'main': [999761554, 2488, 123394, 4193352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'userquote': 293125},
              'error': None,
              'rollback': False,
              'event': {'disc': '1609851aa02c47c0',
                        'len': 264,
                        'base': 160619895223,
                        'quote': 29312409},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5338369114126, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [999761554, 2488, 123394, 4193352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338369114126,
                              'vq': 999761554,
                              'quote_after': 123907378311,
                              'base_after': 668197406903396,
                              'remaining': 999000000000}}]},
 {'label': 't-vq-depwd-boost',
  'steps': [['dep', [1000000000, 18446744073709551615, 18446744073709551615]],
            ['wd', [1000000000, 0, 0]],
            ['boost', [1000000000, 0]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'userbase': -160619895224,
                         'userquote': -29608495,
                         'userlp': 1000000000,
                         'vb1': 160619895224,
                         'vq1': 29312410},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'vq1': 296085},
              'error': None,
              'rollback': False,
              'event': {'disc': '78f83d531f8e6b90',
                        'len': 264,
                        'base': 160619895224,
                        'quote': 29312410},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userbase': 160619895223,
                         'userquote': 29019284,
                         'userlp': -1000000000,
                         'vb1': -160619895223,
                         'vq1': -29312409},
              'pools': {'main': [999999999, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'userquote': 293125},
              'error': None,
              'rollback': False,
              'event': {'disc': '1609851aa02c47c0',
                        'len': 264,
                        'base': 160619895223,
                        'quote': 29312409},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [999999999, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 999999999,
                              'quote_after': 123936690721,
                              'base_after': 668358016710915,
                              'remaining': 999000000000}}]},
 {'label': 't-vq-dep-boost-buy',
  'steps': [['dep', [1000000000, 18446744073709551615, 18446744073709551615]],
            ['boost', [1000000000, 0]],
            ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'userbase': -160619895224,
                         'userquote': -29608495,
                         'userlp': 1000000000,
                         'vb1': 160619895224,
                         'vq1': 29312410},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'vq1': 296085},
              'error': None,
              'rollback': False,
              'event': {'disc': '78f83d531f8e6b90',
                        'len': 264,
                        'base': 160619895224,
                        'quote': 29312410},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5338389284765, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338389284765,
                              'vq': 1000238445,
                              'quote_after': 123966003130,
                              'base_after': 668518626523204,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5206431922484,
                         'vq1': 985438918,
                         'vb2': -5179465389191,
                         'vq2': 5206431922484,
                         'vb3': -5152776760947,
                         'vq3': 5179465389191,
                         'vb4': -5113643191808,
                         'vq4': 5152776760947,
                         'u4': 5113643191808,
                         'bb22': 4515471},
              'pools': {'main': [995677363, 4563570, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2570089354, 2488, 2570086866, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-wd-boost-sell',
  'steps': [['wd', [1000000000, 0, 0]], ['boost', [1000000000, 0]], ['mhsell4', [1000000000, 1]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'userbase': 160619895223,
                         'userquote': 29019284,
                         'userlp': -1000000000,
                         'vb1': -160619895223,
                         'vq1': -29312409},
              'pools': {'main': [999761554, 2488, 123394, 4193352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'userquote': 293125},
              'error': None,
              'rollback': False,
              'event': {'disc': '1609851aa02c47c0',
                        'len': 264,
                        'base': 160619895223,
                        'quote': 29312409},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5338369114126, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [999761554, 2488, 123394, 4193352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338369114126,
                              'vq': 999761554,
                              'quote_after': 123907378311,
                              'base_after': 668197406903396,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': 182880,
                         'vb1': 997497009,
                         'vq1': -185595,
                         'vb2': 997498005,
                         'vq2': -997497009,
                         'vb3': 997499001,
                         'vq3': -997498005,
                         'vb4': 1000000000,
                         'vq4': -997499001,
                         'u4': -1000000000,
                         'bb22': 858},
              'pools': {'main': [999760686, 3356, 123394, 4193352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-625882, 2488, 623394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'userquote': 1848, 'bb22': 9},
              'error': None,
              'rollback': False,
              'event': {'disc': '3e2f370aa503dc2a', 'len': 449},
              'boost_event': None}]},
 {'label': 't-vq-boost-dep',
  'steps': [['boost', [1000000000, 0]],
            ['dep', [1000000000, 18446744073709551615, 18446744073709551615]]],
  'bps': 100,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -5000,
              'deltas': {'userbase': -159347141038,
                         'userquote': -29846911,
                         'userlp': 1000000000,
                         'vb1': 159347141038,
                         'vq1': 29548441},
              'pools': {'main': [1000238445, 2488, 123394, 4195352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 1,
              'withheld': {'vq1': 298470},
              'error': None,
              'rollback': False,
              'event': {'disc': '78f83d531f8e6b90',
                        'len': 264,
                        'base': 159347141038,
                        'quote': 29548441},
              'boost_event': None}]},
 {'label': 't-vq-cross-185',
  'steps': [['mhbuy4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'fee_patch': {'tiers_inplace': [[100, [10, 111, 333]], [185000000000, [20, 222, 444]]]},
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5280233041700,
                         'vq1': 984565819,
                         'vb2': -5252498625566,
                         'vq2': 5280233041700,
                         'vb3': -5225054037074,
                         'vq3': 5252498625566,
                         'vb4': -5184999635360,
                         'vq4': 5225054037074,
                         'u4': 5184999635360,
                         'bb22': 5379839},
              'pools': {'main': [994565819, 5436669, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2606137871, 2488, 2606135383, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 54342},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5142095263785,
                         'vq1': 979249658,
                         'vb2': -5062325200882,
                         'vq2': 5142095263785,
                         'vb3': -4984460447395,
                         'vq3': 5062325200882,
                         'vb4': -4896334816905,
                         'vq4': 4984460447395,
                         'u4': 4896334816905,
                         'bb22': 10642838},
              'pools': {'main': [983815476, 16187012, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5092153057, 2488, 5092150569, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 107504},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-cross-boost-shift-185',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'fee_patch': {'tiers_inplace': [[100, [10, 111, 333]], [185000000000, [20, 222, 444]]]},
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5141204111729,
                         'vq1': 979249658,
                         'vb2': -5114907329776,
                         'vq2': 5141204111729,
                         'vb3': -5088878190060,
                         'vq3': 5114907329776,
                         'vb4': -5050550180582,
                         'vq4': 5088878190060,
                         'u4': 5050550180582,
                         'bb22': 10642838},
              'pools': {'main': [989249657, 10752831, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2538219743, 2488, 2538217255, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 107504},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5062712618600,
                         'vq1': 979249658,
                         'vb2': -4985941184674,
                         'vq2': 5062712618600,
                         'vb3': -4910963440170,
                         'vq3': 4985941184674,
                         'vb4': -4825789651392,
                         'vq4': 4910963440170,
                         'u4': 4825789651392,
                         'bb22': 10642838},
              'pools': {'main': [978499314, 21503174, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-4987578068, 2488, 4987575580, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 107504},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-vq-boost-cross-188',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'fee_patch': {'tiers_inplace': [[100, [10, 111, 333]], [188000000000, [20, 222, 444]]]},
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5197206091771,
                         'vq1': 984565819,
                         'vb2': -5170334796917,
                         'vq2': 5197206091771,
                         'vb3': -5143739939965,
                         'vq3': 5170334796917,
                         'vb4': -5104720782479,
                         'vq4': 5143739939965,
                         'u4': 5104720782479,
                         'bb22': 5379839},
              'pools': {'main': [994565819, 5436669, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-2565582212, 2488, 2565579724, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 54342},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5061860927283,
                         'vq1': 979249658,
                         'vb2': -4984552553513,
                         'vq2': 5061860927283,
                         'vb3': -4909062337048,
                         'vq3': 4984552553513,
                         'vb4': -4823406061831,
                         'vq4': 4909062337048,
                         'u4': 4823406061831,
                         'bb22': 10642838},
              'pools': {'main': [983815476, 16187012, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-5013992356, 2488, 5013989868, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 107504},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't5-vq-boost',
  'steps': [['boost', [1000000000, 0]]],
  'bps': 5000,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -2706767012738, 'vq1': 500000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 500000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 2706767012738,
                              'vq': 1000000000,
                              'quote_after': 123446690720,
                              'base_after': 670989628900007,
                              'remaining': 999000000000}}]},
 {'label': 't5-boost-buy',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 5000,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -2706767012738, 'vq1': 500000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 500000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 2706767012738,
                              'vq': 1000000000,
                              'quote_after': 123446690720,
                              'base_after': 670989628900007,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -2660460364848,
                         'vq1': 497696423,
                         'vb2': -2653401096731,
                         'vq2': 2660460364848,
                         'vb3': -2646379191613,
                         'vq3': 2653401096731,
                         'vb4': -2632829652205,
                         'vq4': 2646379191613,
                         'u4': 2632829652205,
                         'bb22': 1151788},
              'pools': {'main': [997696423, 2306065, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-1320015754, 2488, 1320013266, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 500000000, 'bb22': 1151789},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't5-dust-ladder',
  'steps': [['boost', [1, 0]], ['boost', [2, 0]], ['boost', [3, 0]], ['boost', [4, 0]]],
  'bps': 5000,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6002',
              'rollback': True,
              'event': None,
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6001',
              'rollback': True,
              'event': None,
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6001',
              'rollback': True,
              'event': None,
              'boost_event': None},
             {'dPAYER': -5000,
              'deltas': {'vb1': -5435, 'vq1': 2, 'boostata': -4},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 2},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 4,
                              'used': 4,
                              'burned': 5435,
                              'vq': 1000000000,
                              'quote_after': 122946690722,
                              'base_after': 673696395907310,
                              'remaining': 999999999996}}]},
 {'label': 't-exotic-buy',
  'steps': [['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'fee_patch': {'exotic': [25, 5, 333]},
  'expect': [{'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5332264170203,
                         'vq1': 985438918,
                         'vb2': -5303981938022,
                         'vq2': 5332264170203,
                         'vb3': -5275998139846,
                         'vq3': 5303981938022,
                         'vb4': -5067831887327,
                         'vq4': 5275998139846,
                         'u4': 5067831887327,
                         'bb22': 4515471},
              'pools': {'main': [-4686964, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-169618525242, 2488, 169618522754, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't-boost-exotic-buy',
  'steps': [['boost', [1000000000, 0]], ['mhbuy4', [1000000000, 1]]],
  'bps': 100,
  'fee_patch': {'exotic': [25, 5, 333]},
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {'vb1': -5338379201831, 'vq1': 990000000, 'boostata': -1000000000},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 2,
              'withheld': {'vq1': 10000000},
              'error': None,
              'rollback': False,
              'event': None,
              'boost_event': {'disc': '3f451c16305cc2b9',
                              'len': 208,
                              'requested': 1000000000,
                              'used': 1000000000,
                              'burned': 5338379201831,
                              'vq': 1000000000,
                              'quote_after': 123936690720,
                              'base_after': 668358016710914,
                              'remaining': 999000000000}},
             {'dPAYER': -1849400,
              'deltas': {'userquote': -1000000000,
                         'vb1': -5206402664533,
                         'vq1': 985438918,
                         'vb2': -5179436433535,
                         'vq2': 5206402664533,
                         'vb3': -5152748102925,
                         'vq3': 5179436433535,
                         'vb4': -4950030741509,
                         'vq4': 5152748102925,
                         'u4': 4950030741509,
                         'bb22': 4515471},
              'pools': {'main': [995438918, 4563570, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-165656151976, 2488, 165656149488, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': {'lamports': 1844400,
                         'len': 137,
                         'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'},
              'events': 4,
              'withheld': {'vq1': 10000000, 'bb22': 45611},
              'error': None,
              'rollback': False,
              'event': {'disc': '67f4521f2cf57777', 'len': 508},
              'boost_event': None}]},
 {'label': 't10000-vq-boost',
  'steps': [['boost', [1000000000, 0]]],
  'bps': 10000,
  'vq_patch': 1000000000,
  'expect': [{'dPAYER': -5000,
              'deltas': {},
              'pools': {'main': [1000000000, 2488, 123394, 4194352106721],
                        'pool2': [-125882, 2488, 123394, 4194352106721],
                        'p3': [-125882, 2488, 123394, 4194352106721],
                        'p4': [-125882, 2488, 123394, 4194352106721],
                        'p5': [-125882, 2488, 123394, 4194352106721]},
              'volume': None,
              'events': 0,
              'withheld': {},
              'error': '6002',
              'rollback': True,
              'event': None,
              'boost_event': None}]}]

MEASURE = bool(os.environ.get("MEASURE"))
STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "mhbuy4": "mhbuy4", "mhsell4": "mhsell4", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1", "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd", "swp22": "swp", "swc22": "swc", "col22": "col", "boost": "boost", "boost3": "boost", "boost4": "boost", "boost5": "boost"}


def case_expect(case, image_name):
    exp = case["expect"]
    if isinstance(exp, dict):
        return exp["original" if image_name == "original" else "rebuilt"]
    return exp


def run_case(case, image_name, binary):
    h = setup_vm(binary, case.get("bps", 100))
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
        if MEASURE:
            meas = {"label": case["label"], "image": image_name, "step": kind,
                    "dPAYER": lam_delta(rec, PAYER_KEY),
                    "deltas": {role: tok_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if tok_delta(rec, ROLE_KEY[role]) != 0},
                    "pools": {name: pool_state(rec["after"][str(key)]) for name, key in (("main", pool), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5))},
                    "volume": vol_state(rec["after"][str(volume)]),
                    "events": len(rec["events"]),
                    "decoded": [decode_event(STEP_KIND[kind], raw) for raw in ev_list(rec["logs"])],
                    "withheld": {role: wh_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if wh_delta(rec, ROLE_KEY[role]) != 0},
                    "error": rec["error"]}
            print("MEAS " + json.dumps(meas))
            rec["case"] = case["label"]
            rec["image"] = image_name
            rec["step"] = kind
            out.append(rec)
            continue
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
        for role, want in exp.get("withheld", {}).items():
            got_w = wh_delta(rec, ROLE_KEY[role])
            check(got_w == want, f"{tag}: withheld {role} {got_w} != {want}")
        for role in TOKEN_ROLES:
            if role in exp.get("withheld", {}):
                continue
            got_w = wh_delta(rec, ROLE_KEY[role])
            check(got_w == 0, f"{tag}: unexpected withheld {role} {got_w}")
        for pool_name, pool_key in (("main", pool), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5)):
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
        if exp.get("boost_event") is not None:
            raws = ev_list(rec["logs"])
            check(len(raws) == 2, f"{tag}: boost events {len(raws)} != 2")
            first = decode_event("boost", raws[0])
            check(first == {"disc": MHBUY_DISC, "len": 512},
                  f"{tag}: boost first event {first}")
            got = decode_event("boost", raws[1])
            check(got is not None, f"{tag}: boost event decode failed")
            for fkey, want in exp["boost_event"].items():
                check(got.get(fkey) == want,
                      f"{tag}: boost event {fkey} {got.get(fkey)} != {want}")
        elif exp.get("event") is not None:
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
    if MEASURE:
        for case in CASES:
            for image_name, binary in IMAGES.items():
                run_case(case, image_name, binary)
        return
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
                      ("DEST5", DEST5),
                      ("BOOST", BOOST), ("BATA", BATA), ("BP3", BP3), ("BA3", BA3), ("BP4", BP4), ("BA4", BA4),
                      ("BP5", BP5), ("BA5", BA5)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
