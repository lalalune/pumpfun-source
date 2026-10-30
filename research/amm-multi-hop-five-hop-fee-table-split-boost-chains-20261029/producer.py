#!/usr/bin/env python3
"""Build research/amm-multi-hop-five-hop-fee-table-split-boost-chains-20261029 receipts.

Multi-hop fee-table split x boost chains, 5 hops: the split route
(main -> POOL2 -> P3 -> P4 -> P5, hop 1 = fee-tier cap selection,
tail = exotic flat fees, from 3rd #37/#61) meets boost_buy_and_burn
(from 3rd #34).
The quote mint carries a 0-bps transfer-fee config, so the split
legs route the buyback through the TOKEN22 ATA and the main-pool
sweeps/collects use the TOKEN22 pipes; the boost authority is the
payer and boost is enabled in the global config.

3rd run packet #62: split x boost, at depth 5. Findings pinned
(measured on the original image; control and candidate agree on
every receipt):

- The boost window is still the vq + accrued sum. On the as-is
  fixture the sum is exactly 0, and 5-hop split trades and sweeps
  preserve it exactly, so no 5-hop trade/sweep chain opens the
  window: fresh-boost, buy-boost, buy-sweep-boost,
  buy-sweep-collect-boost, sell-boost, buy-buy-boost,
  buy-sell-boost and sell-buy-boost all fail 6065
  PoolCannotBoost at boost.rs:245 with full rollback. The
  middle-pool (P3) boost and the true tail-pool (P5) boost fail
  6065 the same way (bare boost5, buy-boost5), and a failed
  middle-pool boost leaves the next 5-hop buy byte-identical to
  the uninterrupted second buy.
- On a main pool patched to vq = 10^9 the boost succeeds with
  depth-independent numbers: 10^9 quote in burns exactly
  5,391,870,655,895 base, vaultquote +10^9, pool fields
  untouched, two events (BuyEvent 512 + BoostBuyAndBurnEvent
  208). Min gates are exact: min == burned succeeds, min ==
  burned + 1 fails 6004 at boost.rs:274; amount 1 fails 6001 at
  boost.rs:273, amount 2 burns 5,435. A second boost burns
  5,306,249,181,882, as at depth 4.
- A boost reprices the following 5-hop split trade off the
  boosted real vaults while the pool fields stay fixed:
  boost-then-buy moves vaultbase1 by -5,257,740,431,110 (the
  depth-4 anchor value) and ends at tail output 5,136,667,160,892
  vs the no-boost 5-hop anchor 5,217,822,094,650; boost-then-sell
  pays 184,757 vs the anchor 181,812. The fresh 5-hop buy ends
  at tail output 5,259,040,470,738.
- Liquidity drifts the window proportionally, unchanged from
  depth 4: dep-1e9 moves vq 10^9 -> 1,000,238,445 and the next
  boost burns 5,391,880,941,907; wd-1e9 moves vq to 999,761,554
  and the next boost burns 5,391,860,365,016; dep -> wd leaves
  vq at 999,999,999 and the next boost burns the baseline
  5,391,870,655,895 again.
- Boost shifts the hop-1 fee-tier selection cap exactly as at
  depth 4: at threshold 185e9 the no-boost buys cross A -> B
  across two buys (buyback 5,489,071 then 10,858,932) while the
  boosted first buy already selects B; at threshold 188e9 the
  boosted buys cross A -> B across two buys.

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
OUT = ROOT / "research/amm-multi-hop-five-hop-fee-table-split-boost-chains-20261029"
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
         PROTO22, CREAT22, DEST22, BB22, BOOST, BATA, BP3, BA3, BP5, BA5]
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
            "boostata": BATA, "boostata3": BA3, "boostata5": BA5}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "protoata2", "creatorata2", "dest2",
               "bb22", "proto22", "creat22", "dest22",
               "boostata", "boostata3", "boostata5"]
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
    transferfee(quote, 0, 2**64 - 1)(h, [])
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
    # P5 is the fifth hop: same pool shape as P4, quote = BASE4.
    h.vm.set_account(BASE5, h.vm.get_account(base))
    d5 = bytearray(poolraw)
    d5[8] = B5
    d5[9:11] = bytes(2)
    d5[11:43] = bytes(C5)
    d5[43:75] = bytes(BASE5)
    d5[75:107] = bytes(BASE4)
    d5[139:171] = bytes(VB5)
    d5[171:203] = bytes(VQ5)
    h.vm.set_account(P5, Account(10**9, bytes(d5), PROGRAM))
    for k, mi, ow in [(VB5, BASE5, P5), (VQ5, BASE4, P5), (U5, BASE5, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    g5 = [AccountMeta(BASE5, False, False), AccountMeta(BASE4, False, False),
          AccountMeta(P5, False, True), AccountMeta(VB5, False, True),
          AccountMeta(VQ5, False, True)]
    if sell:
        metas[16:16] = g4
        metas[16:16] = g5
        metas[1] = AccountMeta(U5, False, True)
    else:
        metas.extend(g4)
        metas.extend(g5)
        metas[2] = AccountMeta(U5, False, True)
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
    elif kind in ("boost", "boost3", "boost5"):
        if kind == "boost":
            keys = [pool, PAYER_KEY, CONFIG_KEY, base, quote, vaultbase, vaultquote,
                    BOOST, BATA, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BATA
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


CASES = [
    {'label': 'c-fresh-boost', 'steps': [('boost', (1000000000, 0))], 'expect': [E(-5000, {}, {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-boost', 'steps': [('mhbuy5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-swc22-boost', 'steps': [('mhbuy5', (1000000000, 1)), ('swc22', None), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'vq1': -123394, 'creat22': 123394}, {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, events=1), E(-5000, {}, {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-swc22-col22-boost', 'steps': [('mhbuy5', (1000000000, 1)), ('swc22', None), ('col22', None), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'vq1': -123394, 'creat22': 123394}, {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, events=1), E(-5000, {'creat22': -123394, 'dest22': 123394}, {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, events=1), E(-5000, {}, {'main': [-4609642, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-sell-boost', 'steps': [('mhsell5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'bb22': 846}, {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5), E(-5000, {}, {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-buy-boost', 'steps': [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5300268622007, 'vq1': 995392847, 'vb2': -5216136464071, 'vq2': 5300268622007, 'vb3': -5134060987112, 'vq3': 5216136464071, 'vb4': -5053973644811, 'vq4': 5134060987112, 'vb5': -4963540456839, 'vq5': 5053973644811, 'u5': 4963540456839, 'bb22': 4607153}, {'main': [-9340190, 9216796, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5164233091, 2488, 5164230603, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-9340190, 9216796, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5164233091, 2488, 5164230603, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-boost3', 'steps': [('mhbuy5', (1000000000, 1)), ('boost3', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-boost3-buy', 'steps': [('mhbuy5', (1000000000, 1)), ('boost3', (1000000000, 0)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True), E(-5000, {'userquote': -1000000000, 'vb1': -5300268622007, 'vq1': 995392847, 'vb2': -5216136464071, 'vq2': 5300268622007, 'vb3': -5134060987112, 'vq3': 5216136464071, 'vb4': -5053973644811, 'vq4': 5134060987112, 'vb5': -4963540456839, 'vq5': 5053973644811, 'u5': 4963540456839, 'bb22': 4607153}, {'main': [-9340190, 9216796, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5164233091, 2488, 5164230603, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-buy-sell-boost', 'steps': [('mhbuy5', (1000000000, 1)), ('mhsell5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': 191240, 'vb1': 1040920104, 'vq1': -192138, 'vb2': 1029798947, 'vq2': -1040920104, 'vb3': 1018855069, 'vq3': -1029798947, 'vb4': 1008084723, 'vq4': -1018855069, 'vb5': 1000000000, 'vq5': -1008084723, 'u5': -1000000000, 'bb22': 898}, {'main': [-4733934, 4610540, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2644053287, 2488, 2644050799, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5), E(-5000, {}, {'main': [-4733934, 4610540, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2644053287, 2488, 2644050799, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-sell-buy-boost', 'steps': [('mhsell5', (1000000000, 1)), ('mhbuy5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': 180345, 'vb1': 997496013, 'vq1': -181191, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'bb22': 846}, {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5385710729466, 'vq1': 995392847, 'vb2': -5356870888804, 'vq2': 5385710729466, 'vb3': -5328338327471, 'vq3': 5356870888804, 'vb4': -5300108160545, 'vq4': 5328338327471, 'vb5': -5259097196054, 'vq5': 5300108160545, 'u5': 5259097196054, 'bb22': 4607153}, {'main': [-4733883, 4610489, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2644071349, 2488, 2644068861, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-4733883, 4610489, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2644071349, 2488, 2644068861, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
    {'label': 'c-vq1e9-boost', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-boost-min-exact', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 5391870655895))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-boost-min-plus1', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 5391870655896))], 'expect': [E(-5000, {}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, events=0, error='6004', rollback=True)]},
    {'label': 'c-vq1e9-boost-amt1', 'vq_patch': 1000000000, 'steps': [('boost', (1, 0))], 'expect': [E(-5000, {}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, events=0, error='6001', rollback=True)]},
    {'label': 'c-vq1e9-boost-amt2', 'vq_patch': 1000000000, 'steps': [('boost', (2, 0))], 'expect': [E(-5000, {'vb1': -5435, 'vq1': 2, 'boostata': -2}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 2, 'used': 2, 'burned': 5435, 'vq': 1000000000, 'quote_after': 122946690722, 'base_after': 673696395907310, 'remaining': 999999999998}, events=2)]},
    {'label': 'c-vq1e9-buy', 'vq_patch': 1000000000, 'steps': [('mhbuy5', (1000000000, 1))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5342582297894, 'vq1': 995392847, 'vb2': -5314190796882, 'vq2': 5342582297894, 'vb3': -5286099456463, 'vq3': 5314190796882, 'vb4': -5258303541630, 'vq4': 5286099456463, 'vb5': -5217822094650, 'vq5': 5258303541630, 'u5': 5217822094650, 'bb22': 4607153}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-boost-buy', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': -1000000000, 'vb1': -5257740431110, 'vq1': 995392847, 'vb2': -5230241181244, 'vq2': 5257740431110, 'vb3': -5203028090113, 'vq3': 5230241181244, 'vb4': -5176096714162, 'vq4': 5203028090113, 'vb5': -5136667160892, 'vq5': 5176096714162, 'u5': 5136667160892, 'bb22': 4607153}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2581720254, 2488, 2581717766, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-sell', 'vq_patch': 1000000000, 'steps': [('mhsell5', (1000000000, 1))], 'expect': [E(-1849400, {'userquote': 181812, 'vb1': 997496013, 'vq1': -182665, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'bb22': 853}, {'main': [999999146, 3342, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5)]},
    {'label': 'c-vq1e9-boost-sell', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0)), ('mhsell5', (1000000000, 1))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': 184757, 'vb1': 997496013, 'vq1': -185624, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'bb22': 867}, {'main': [999999132, 3356, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5)]},
    {'label': 'c-vq1e9-boost-buy-buy', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': -1000000000, 'vb1': -5257740431110, 'vq1': 995392847, 'vb2': -5230241181244, 'vq2': 5257740431110, 'vb3': -5203028090113, 'vq3': 5230241181244, 'vb4': -5176096714162, 'vq4': 5203028090113, 'vb5': -5136667160892, 'vq5': 5176096714162, 'u5': 5136667160892, 'bb22': 4607153}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2581720254, 2488, 2581717766, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5175657939667, 'vq1': 995392847, 'vb2': -5095425397965, 'vq2': 5175657939667, 'vb3': -5017108764821, 'vq3': 5095425397965, 'vb4': -4940645650549, 'vq4': 5017108764821, 'vb5': -4853975590133, 'vq5': 4940645650549, 'u5': 4853975590133, 'bb22': 4607153}, {'main': [990785692, 9216796, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5045882674, 2488, 5045880186, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-boost-swc22-col22', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0)), ('swc22', None), ('col22', None)], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-5000, {'vq1': -123394, 'creat22': 123394}, {'main': [1000123394, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, events=1), E(-5000, {'creat22': -123394, 'dest22': 123394}, {'main': [1000123394, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, events=1)]},
    {'label': 'c-vq1e9-buy-boost', 'vq_patch': 1000000000, 'steps': [('mhbuy5', (1000000000, 1)), ('boost', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5342582297894, 'vq1': 995392847, 'vb2': -5314190796882, 'vq2': 5342582297894, 'vb3': -5286099456463, 'vq3': 5314190796882, 'vb4': -5258303541630, 'vq4': 5286099456463, 'vb5': -5217822094650, 'vq5': 5258303541630, 'u5': 5217822094650, 'bb22': 4607153}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'vb1': -5307028789111, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5307028789111, 'vq': 995392846, 'quote_after': 124942083567, 'base_after': 663046784825740, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-buy-swc22-col22-boost-buy', 'vq_patch': 1000000000, 'steps': [('mhbuy5', (1000000000, 1)), ('swc22', None), ('col22', None), ('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5342582297894, 'vq1': 995392847, 'vb2': -5314190796882, 'vq2': 5342582297894, 'vb3': -5286099456463, 'vq3': 5314190796882, 'vb4': -5258303541630, 'vq4': 5286099456463, 'vb5': -5217822094650, 'vq5': 5258303541630, 'u5': 5217822094650, 'bb22': 4607153}, {'main': [995392846, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'vq1': -123394, 'creat22': 123394}, {'main': [995516240, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, events=1), E(-5000, {'creat22': -123394, 'dest22': 123394}, {'main': [995516240, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, events=1), E(-5000, {'vb1': -5307028789111, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [995516240, 4609642, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2622721165, 2488, 2622718677, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5307028789111, 'vq': 995516240, 'quote_after': 124941960173, 'base_after': 663046784825740, 'remaining': 999000000000}, events=2), E(-5000, {'userquote': -1000000000, 'vb1': -5175657939667, 'vq1': 995392847, 'vb2': -5094567620378, 'vq2': 5175657939667, 'vb3': -5015432801490, 'vq3': 5094567620378, 'vb4': -4938189218517, 'vq4': 5015432801490, 'vb5': -4850783672746, 'vq5': 4938189218517, 'u5': 4850783672746, 'bb22': 4607153}, {'main': [990909086, 9216796, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5085658432, 2488, 5085655944, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-dep-boost', 'vq_patch': 1000000000, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('boost', (1000000000, 0))], 'expect': [E(-5000, {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, {'main': [1000238445, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, events=1), E(-5000, {'vb1': -5391880941907, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000238445, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391880941907, 'vq': 1000238445, 'quote_after': 123976003130, 'base_after': 668465134866062, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-wd-boost', 'vq_patch': 1000000000, 'steps': [('wd', (1000000000, 0, 0)), ('boost', (1000000000, 0))], 'expect': [E(-5000, {'userbase': 160619895223, 'userquote': 29312409, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, {'main': [999761554, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, events=1), E(-5000, {'vb1': -5391860365016, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [999761554, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391860365016, 'vq': 999761554, 'quote_after': 123917378311, 'base_after': 668143915652506, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-depwd-boost', 'vq_patch': 1000000000, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('wd', (1000000000, 0, 0)), ('boost', (1000000000, 0))], 'expect': [E(-5000, {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, {'main': [1000238445, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, events=1), E(-5000, {'userbase': 160619895223, 'userquote': 29312409, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, {'main': [999999999, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, events=1), E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [999999999, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 999999999, 'quote_after': 123946690721, 'base_after': 668304525256851, 'remaining': 999000000000}, events=2)]},
    {'label': 'c-vq1e9-dep-boost-buy', 'vq_patch': 1000000000, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-5000, {'userbase': -160619895224, 'userquote': -29312410, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, {'main': [1000238445, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, events=1), E(-5000, {'vb1': -5391880941907, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000238445, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391880941907, 'vq': 1000238445, 'quote_after': 123976003130, 'base_after': 668465134866062, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': -1000000000, 'vb1': -5257770272075, 'vq1': 995392847, 'vb2': -5230270710873, 'vq2': 5257770272075, 'vb3': -5203057313254, 'vq3': 5230270710873, 'vb4': -5176125635562, 'vq4': 5203057313254, 'vb5': -5136695714551, 'vq5': 5176125635562, 'u5': 5136695714551, 'bb22': 4607153}, {'main': [995631291, 4609642, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2581734678, 2488, 2581732190, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-wd-boost-sell', 'vq_patch': 1000000000, 'steps': [('wd', (1000000000, 0, 0)), ('boost', (1000000000, 0)), ('mhsell5', (1000000000, 1))], 'expect': [E(-5000, {'userbase': 160619895223, 'userquote': 29312409, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, {'main': [999761554, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, event={'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, events=1), E(-5000, {'vb1': -5391860365016, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [999761554, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391860365016, 'vq': 999761554, 'quote_after': 123917378311, 'base_after': 668143915652506, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': 184757, 'vb1': 997496013, 'vq1': -185624, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'bb22': 867}, {'main': [999760686, 3356, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-625882, 2488, 623394, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '3e2f370aa503dc2a', 'len': 449}, events=5)]},
    {'label': 'c-vq1e9-boost-boost', 'vq_patch': 1000000000, 'steps': [('boost', (1000000000, 0)), ('boost', (1000000000, 0))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-5000, {'vb1': -5306249181882, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5306249181882, 'vq': 1000000000, 'quote_after': 124946690720, 'base_after': 662998276074968, 'remaining': 998000000000}, events=2)]},
    {'label': 'c-vq1e9-cross', 'vq_patch': 1000000000, 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (185000000000, (20, 222, 444))]}, 'steps': [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5333146512938, 'vq1': 994510929, 'vb2': -5304854944953, 'vq2': 5333146512938, 'vb3': -5276861958362, 'vq3': 5304854944953, 'vb4': -5249162851258, 'vq4': 5276861958362, 'vb5': -5208799020047, 'vq5': 5249162851258, 'u5': 5208799020047, 'bb22': 5489071}, {'main': [994510928, 5491560, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2618162217, 2488, 2618159729, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5192812983766, 'vq1': 989141068, 'vb2': -5111462814221, 'vq2': 5192812983766, 'vb3': -5032074642711, 'vq3': 5111462814221, 'vb4': -4954583972002, 'vq4': 5032074642711, 'vb5': -4866897611133, 'vq5': 4954583972002, 'u5': 4866897611133, 'bb22': 10858932}, {'main': [983651996, 16350492, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5089276418, 2488, 5089273930, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-cross-boost-shift', 'vq_patch': 1000000000, 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (185000000000, (20, 222, 444))]}, 'steps': [('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': -1000000000, 'vb1': -5191904059818, 'vq1': 989141068, 'vb2': -5165087422111, 'vq2': 5191904059818, 'vb3': -5138546381473, 'vq3': 5165087422111, 'vb4': -5112276711120, 'vq4': 5138546381473, 'vb5': -5073654648636, 'vq5': 5112276711120, 'u5': 5073654648636, 'bb22': 10858932}, {'main': [989141068, 10861420, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2549889828, 2488, 2549887340, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5111856515075, 'vq1': 989141068, 'vb2': -5033588439801, 'vq2': 5111856515075, 'vb3': -4957166577641, 'vq3': 5033588439801, 'vb4': -4882531534124, 'vq4': 4957166577641, 'vb5': -4797763071344, 'vq5': 4882531534124, 'u5': 4797763071344, 'bb22': 10858932}, {'main': [978282136, 21720352, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-4985067651, 2488, 4985065163, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-vq1e9-boost-cross', 'vq_patch': 1000000000, 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (188000000000, (20, 222, 444))]}, 'steps': [('boost', (1000000000, 0)), ('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))], 'expect': [E(-5000, {'vb1': -5391870655895, 'vq1': 1000000000, 'boostata': -1000000000}, {'main': [1000000000, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, boost_event={'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5391870655895, 'vq': 1000000000, 'quote_after': 123946690720, 'base_after': 668304525256850, 'remaining': 999000000000}, events=2), E(-1849400, {'userquote': -1000000000, 'vb1': -5248453900984, 'vq1': 994510929, 'vb2': -5221051453770, 'vq2': 5248453900984, 'vb3': -5193933659538, 'vq3': 5221051453770, 'vb4': -5167096105801, 'vq4': 5193933659538, 'vb5': -5127780917343, 'vq5': 5167096105801, 'u5': 5127780917343, 'bb22': 5489071}, {'main': [994510928, 5491560, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2577231172, 2488, 2577228684, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {'userquote': -1000000000, 'vb1': -5110988040229, 'vq1': 989141068, 'vb2': -5032172807288, 'vq2': 5110988040229, 'vb3': -4955228962370, 'vq3': 5032172807288, 'vb4': -4880095931489, 'vq4': 4955228962370, 'vb5': -4794860285497, 'vq5': 4880095931489, 'u5': 4794860285497, 'bb22': 10858932}, {'main': [983651996, 16350492, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-5011194231, 2488, 5011191743, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5)]},
    {'label': 'c-boost5', 'steps': [('boost5', (1000000000, 0))], 'expect': [E(-5000, {}, {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, None, events=0, error='6065', rollback=True)]},
    {'label': 'c-buy-boost5', 'steps': [('mhbuy5', (1000000000, 1)), ('boost5', (1000000000, 0))], 'expect': [E(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'bb22': 4607153}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, event={'disc': '67f4521f2cf57777', 'len': 508}, events=5), E(-5000, {}, {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-2643547981, 2488, 2643545493, 4194352106721]}, {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, events=0, error='6065', rollback=True)]},
]


MEASURE = bool(os.environ.get("MEASURE"))
STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "mhbuy4": "mhbuy4", "mhsell4": "mhsell4", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1", "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd", "swp22": "swp", "swc22": "swc", "col22": "col", "boost": "boost", "boost3": "boost", "boost5": "boost"}


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
                      ("BOOST", BOOST), ("BATA", BATA), ("BP3", BP3), ("BA3", BA3)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
