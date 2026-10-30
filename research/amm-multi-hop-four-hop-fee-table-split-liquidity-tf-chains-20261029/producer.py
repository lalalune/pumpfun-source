#!/usr/bin/env python3
"""Build research/amm-multi-hop-four-hop-fee-table-split-liquidity-tf-chains-20261029 receipts.

3rd run packet #54: multi-hop fee-table split x liquidity x transfer fee at depth 4.
The split route (main -> POOL2 -> P3 -> P4, hop 1 = fee-tier cap selection,
tail = exotic flat fees, from 3rd #37) meets main-pool deposit/withdraw
UNDER transfer fee on the quote mint (tf100, plus tf5000 anchors):

- Every quote-mint leg grosses up: the dep quote leg, the buy vault
  and buyback legs, the sell user leg, and the sweep/collect pipes.
  Events report gross for sweeps/collects and net for deposits/
  withdraws; withheld stays isolated per hop account.
- The liquidity findings from 3rd #49 are re-pinned under tf: buys
  stay liquidity-sensitive, sells stay liquidity-blind, proportional
  deposits still cannot flip hop 1's tier (cap invariant), and the
  post-trade limit gates sit on the tf basis (dep cap gross-side,
  wd floor net-side).
- The tf100 split anchors from 3rd #40 are reproduced, then
  interleaved with dep/wd exactly as in 3rd #49.

Case list mirrors 3rd #52 (split x liquidity x tf, 3 hops) and 3rd #53
(split x liquidity x tf, 5 hops) step for step, with the route at 4 hops
(P5 kept at fixture state, tail token U4), the quote mint under tf,
and the main-pool sweep/collect steps
routed through the TOKEN22 pipes (swc22/swp22/col22, BB22 buyback):

- A main-pool deposit/withdraw before a split trade moves the hop-1
  cap (supply * effective_quote / vault_base) and the vault balances,
  so it moves the tail legs; but a proportional deposit leaves the
  cap exactly invariant, so even a 10^12 deposit does NOT flip the
  first buy's tier.
- A deposit/withdraw between two split trades reprices the second
  trade off post-trade vaults; the dep/wd legs themselves price off
  post-trade available reserves, and the tf post-trade basis differs
  from the no-fee one because the tf buy leaves different vault
  state. Limit gates pin the tf basis (dep cap gross-side, wd floor
  net-side).
- Sweeps stay leg-neutral for the split route too: sweeping the
  main buckets through the TOKEN22 pipes converts accrued to vq 1:1
  (gross in, net out, withheld isolated), so the next split trade
  has byte-identical token legs (only the pool relabel differs).
- The vq + accrued sum is invariant (0) across split trades and
  sweeps on this fixture, so dep/wd never hit the can_boost drift
  branch here; patching main vq to 0 makes dep drift vq (+30 floor),
  and vq itself still prices the split buy (vq0 buy differs from
  the as-is buy), while the dep move on top is the same ~+9.8M
  tail-out shift as on the as-is fixture.

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

import atexit
import os
import shutil
import tempfile
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
os.chdir(REPO)
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

ROOT = REPO
OUT = ROOT / "research/amm-multi-hop-four-hop-fee-table-split-liquidity-tf-chains-20261029"
WS = REPO / "research/amm-multi-hop-images"
IMAGES = {
    "original": ROOT / "evidence/original/pump_amm/deployed.so",
    "control": WS / "control.so.gz",
    "candidate": WS / "candidate.so.gz",
}
PROGRAM_FILES = {}


def image_bytes(path):
    raw = Path(path).read_bytes()
    return gzip.decompress(raw) if Path(path).suffix == ".gz" else raw


def program_file(path):
    path = Path(path)
    if path.suffix != ".gz":
        return path
    if path not in PROGRAM_FILES:
        scratch = Path(tempfile.mkdtemp(prefix="amm-multi-hop-image-"))
        atexit.register(shutil.rmtree, scratch, True)
        PROGRAM_FILES[path] = scratch / path.stem
        PROGRAM_FILES[path].write_bytes(image_bytes(path))
    return PROGRAM_FILES[path]


IMAGE_SHA = {k: hashlib.sha256(image_bytes(v)).hexdigest() for k, v in IMAGES.items()}

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
PROTO22, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN22), bytes(quote)], ATA_PROG)
CREAT22, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN22), bytes(quote)], ATA_PROG)
DEST22 = Pubkey.from_bytes(bytes([98]) * 32)
_BB_OWNER = None
for _row in f["accounts"].values():
    if _row["address"] == str(buyback):
        _BB_OWNER = Pubkey.from_bytes(base64.b64decode(_row["data_base64"])[32:64])
assert _BB_OWNER is not None, "buyback fixture row not found"
BB22, _ = Pubkey.find_program_address([bytes(_BB_OWNER), bytes(TOKEN22), bytes(quote)], ATA_PROG)

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
         PROTO22, CREAT22, DEST22, BB22]
ROLE_KEY = {"userbase": userbase, "userquote": userquote, "userlp": userlp,
            "vaultbase": vaultbase, "vaultquote": vaultquote, "buyback": buyback,
            "vb1": vaultbase, "vq1": vaultquote, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata2", "creatorata2", "dest2",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "bb22", "proto22", "creat22", "dest22"]
SWP_DISC = "82a42461e48287a5"
COL_DISC = "e8f5c2eeeada3a59"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def setup_vm(binary, bps=0):
    h = Harness(program_file(binary))
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
    vm.set_account(DEST4, Account(2039280, token(BASE3, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P4, Account(2039280, token(BASE3, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P4, Account(2039280, token(BASE3, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST5, Account(2039280, token(BASE4, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P5, Account(2039280, token(BASE4, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P5, Account(2039280, token(BASE4, PROTOCOL, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P2, Account(2039280, token(base, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P2, Account(2039280, token(base, PROTOCOL, 0, False), TOKEN))
    for k in [PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]:
        vm.set_account(k, Account(10**9, b"", Pubkey.default()))
    if bps:
        transferfee(quote, bps, 2**64 - 1)(h, [])
        h.vm.set_account(BB22, Account(2157600, t22acct(_BB_OWNER, 0), TOKEN22))
        h.vm.set_account(PROTO22, Account(2157600, t22acct(PROTOCOL, 0), TOKEN22))
        h.vm.set_account(CREAT22, Account(2157600, t22acct(CREATOR_VAULT, 0), TOKEN22))
        h.vm.set_account(DEST22, Account(2157600, t22acct(CREATOR, 0), TOKEN22))
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
    # P5 is NOT part of the 4-hop route; keep it at fixture state so pool
    # snapshots stay complete (pool_state(P5) must equal INIT).
    h.vm.set_account(P5, Account(10**9, bytes(poolraw), PROGRAM))
    for k, mi, ow in [(VB5, BASE5, P5), (VQ5, BASE4, P5), (U5, BASE5, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    if sell:
        metas[16:16] = g4
        metas[1] = AccountMeta(U4, False, True)
    else:
        metas.extend(g4)
        metas[2] = AccountMeta(U4, False, True)
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
    for pk in (POOL2, P3):
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
    if kind in ("mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
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
    if kind in ("mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell5": "sell", "mhbuy5": "buy",
                        "mhsell4": "sell", "mhbuy4": "buy",
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
      rollback=False, withheld=None):
    return {"dPAYER": dPAYER, "deltas": deltas, "pools": pools,
            "volume": volume, "event": event, "events": events, "error": error,
            "rollback": rollback, "withheld": withheld or {}}


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


def MH(dPAYER, deltas, pools, event):
    return E(dPAYER, deltas, pools, VOL, event=event, events=3)


def SWC(pool_tag, amount, pools, volume=VOL):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3"}[pool_tag]: -amount,
                     "creatorata" + {"main": "", "p2": "2", "p3": "3"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 1, CREATOR_VAULT))


def SWP(pool_tag, amount, pools, volume=VOL):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3"}[pool_tag]: -amount,
                     "protoata" + {"main": "", "p2": "2", "p3": "3"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 0, PROTOCOL))


def COL(pool_tag, amount, pools, volume=VOL):
    suffix = {"main": "", "p2": "2", "p3": "3"}[pool_tag]
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3}[pool_tag]
    dest = {"main": DEST, "p2": DEST2, "p3": DEST3}[pool_tag]
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


CASES = [{'label': 'a-dep-buy', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5276007988474, 'vq3': 5303991891401, 'vb4': -5235298267979, 'vq4': 5276007988474, 'u4': 5235298267979, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631551313, 2488, 2631548825, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'a-dep-buy-cross', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322856485808, 'vq1': 984565819, 'vb2': -5294673698238, 'vq2': 5322856485808, 'vb3': -5266787776187, 'vq3': 5294673698238, 'vb4': -5226197013761, 'vq4': 5266787776187, 'u4': 5226197013761, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626952704, 2488, 2626950216, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182970635538, 'vq1': 979249658, 'vb2': -5101928518871, 'vq2': 5182970635538, 'vb3': -5022837303300, 'vq3': 5101928518871, 'vb4': -4933438175247, 'vq4': 5022837303300, 'u4': 4933438175247, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5132108467, 2488, 5132105979, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'a-dep12-buy-cross', 'steps': [('dep', (1000000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895223680, 'userquote': -29608494036, 'userlp': 1000000000000, 'vb1': 160619895223680, 'vq1': 29312409095}, 'pools': {'main': [-125882, 2488, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895223680, 'quote': 29312409095}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296084941}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5330955201237, 'vq1': 984565819, 'vb2': -5302686816041, 'vq2': 5330955201237, 'vb3': -5274716646285, 'vq3': 5302686816041, 'vb4': -5234023596560, 'vq4': 5274716646285, 'u4': 5234023596560, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2630907252, 2488, 2630904764, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5206467840777, 'vq1': 979249658, 'vb2': -5124856789027, 'vq2': 5206467840777, 'vb3': -5045215418473, 'vq3': 5124856789027, 'vb4': -4955230647406, 'vq4': 5045215418473, 'u4': 4955230647406, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 5194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5147224169, 2488, 5147221681, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'a-wd-buy', 'steps': [('wd', (1000000000, 0, 0)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29019284, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 293125}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332254105589, 'vq1': 985438918, 'vb2': -5303971979889, 'vq2': 5332254105589, 'vb3': -5275988286514, 'vq3': 5303971979889, 'vb4': -5235278820388, 'vq4': 5275988286514, 'u4': 5235278820388, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631541487, 2488, 2631538999, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'a-wd-buy-cross', 'steps': [('wd', (1000000000, 0, 0)), ('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29019284, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 293125}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322836432407, 'vq1': 984565819, 'vb2': -5294653856627, 'vq2': 5322836432407, 'vb3': -5266768143028, 'vq3': 5294653856627, 'vb4': -5226177633730, 'vq4': 5266768143028, 'u4': 5226177633730, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626942911, 2488, 2626940423, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182912569736, 'vq1': 979249658, 'vb2': -5101871857178, 'vq2': 5182912569736, 'vb3': -5022781999430, 'vq3': 5101871857178, 'vb4': -4933384317028, 'vq4': 5022781999430, 'u4': 4933384317028, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5132071091, 2488, 5132068603, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'a-dep-sell', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997497009, 'vq1': -181191, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}]}, {'label': 'a-dep-sell-cross', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell4', (1000000000, 1)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': 176216, 'vb1': 997497009, 'vq1': -180017, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 2000}, 'pools': {'main': [-127903, 4509, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1780, 'bb22': 21}}, {'dPAYER': -5000, 'deltas': {'userquote': 178214, 'vb1': 997491035, 'vq1': -181025, 'vb2': 997494021, 'vq2': -997491035, 'vb3': 997497007, 'vq3': -997494021, 'vb4': 1000000000, 'vq4': -997497007, 'u4': -1000000000, 'bb22': 999}, 'pools': {'main': [-128914, 5520, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1125881, 2488, 1123393, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1801, 'bb22': 11}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (182349883978, (20, 222, 444))]}}, {'label': 'a-dep-exotic', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1)), ('swc', 'p4'), ('col', 'p4')], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5276007988474, 'vq3': 5303991891401, 'vb4': -5067841299433, 'vq4': 5276007988474, 'u4': 5067841299433, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-169618841866, 2488, 169618839378, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'vq4': -169618839378, 'creatorata4': 169618839378}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2488, 2488, 0, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 169618839378, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata4': -169618839378, 'dest4': 169618839378}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2488, 2488, 0, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 169618839378, 'vault_ata': '8d5c9e4f4e4cd5f55f61a3bde2d583d1113297184c3da32dd6537d71cc453aa9', 'dest': '6161616161616161616161616161616161616161616161616161616161616161'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}], 'fee_patch': {'exotic': (25, 5, 333)}}, {'label': 'a-dep-rebuild', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1)), ('swc', 'p4'), ('col', 'p4')], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322856485808, 'vq1': 984565819, 'vb2': -5294673698238, 'vq2': 5322856485808, 'vb3': -5266787776187, 'vq3': 5294673698238, 'vb4': -5226197013762, 'vq4': 5266787776187, 'u4': 5226197013762, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'vq4': -123394, 'creatorata4': 123394}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2488, 2488, 0, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata4': -123394, 'dest4': 123394}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2488, 2488, 0, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': '8d5c9e4f4e4cd5f55f61a3bde2d583d1113297184c3da32dd6537d71cc453aa9', 'dest': '6161616161616161616161616161616161616161616161616161616161616161'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}], 'fee_patch': {'tiers_rebuild': [(100, (10, 111, 333))]}}, {'label': 'b-buy-dep-buy', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5248527776010, 'vq1': 985438918, 'vb2': -5166029002075, 'vq2': 5248527776010, 'vb3': -5085527514594, 'vq3': 5166029002075, 'vb4': -4994612274242, 'vq4': 5085527514594, 'u4': 4994612274242, 'bb22': 4515471}, 'pools': {'main': [-9248046, 9124652, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5167969102, 2488, 5167966614, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'b-buy-wd-buy', 'steps': [('mhbuy4', (1000000000, 1)), ('wd', (1000000000, 0, 0)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': 159348598958, 'userquote': 29250802, 'userlp': -1000000000, 'vb1': -159348598958, 'vq1': -29546265}, 'pools': {'main': [-4686964, 4563570, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 159348598958, 'quote': 29546265}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 295463}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5248508123132, 'vq1': 985438918, 'vb2': -5166009758574, 'vq2': 5248508123132, 'vb3': -5085508667811, 'vq3': 5166009758574, 'vb4': -4994593857324, 'vq4': 5085508667811, 'u4': 4994593857324, 'bb22': 4515471}, 'pools': {'main': [-9248046, 9124652, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5167959702, 2488, 5167957214, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'b-buy-dep-sell', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'userquote': 187248, 'vb1': 1029649551, 'vq1': -190028, 'vb2': 1018757076, 'vq2': -1029649551, 'vb3': 1008036536, 'vq3': -1018757076, 'vb4': 1000000000, 'vq4': -1008036536, 'u4': -1000000000, 'bb22': 879}, 'pools': {'main': [-4687852, 4564458, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2632051683, 2488, 2632049195, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1892, 'bb22': 9}}]}, {'label': 'b-sell-dep-sell', 'steps': [('mhsell4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997497009, 'vq1': -181191, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}, {'dPAYER': -5000, 'deltas': {'userbase': -160620133043, 'userquote': -29608451, 'userlp': 1000000000, 'vb1': 160620133043, 'vq1': 29312366}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160620133043, 'quote': 29312366}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {'userquote': 178539, 'vb1': 997491035, 'vq1': -181189, 'vb2': 997494021, 'vq2': -997491035, 'vb3': 997497007, 'vq3': -997494021, 'vb4': 1000000000, 'vq4': -997497007, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-127576, 4182, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1125881, 2488, 1123393, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}]}, {'label': 'b-buy-dep-swc-col', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('swc22',), ('col22',), ('swp22',)], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-4563570, 4563570, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -5000, 'deltas': {'creat22': -122160, 'dest22': 120938}, 'pools': {'main': [-4563570, 4563570, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 122160, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'dest22': 1222}}, {'dPAYER': -5000, 'deltas': {'vq1': -4563570, 'proto22': 4517934}, 'pools': {'main': [0, 0, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 4563570, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'proto22': 45636}}]}, {'label': 'b-buy-dep-buy-cross', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322846461501, 'vq1': 984565819, 'vb2': -5294663779801, 'vq2': 5322846461501, 'vb3': -5266777961951, 'vq3': 5294663779801, 'vb4': -5226187326059, 'vq4': 5266777961951, 'u4': 5226187326059, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626947809, 2488, 2626945321, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userbase': -159350844289, 'userquote': -29844293, 'userlp': 1000000000, 'vb1': 159350844289, 'vq1': 29545850}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626947809, 2488, 2626945321, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159350844289, 'quote': 29545850}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298443}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182951189442, 'vq1': 979249658, 'vb2': -5101909576503, 'vq2': 5182951189442, 'vb3': -5022818847608, 'vq3': 5101909576503, 'vb4': -4933420233884, 'vq4': 5022818847608, 'u4': 4933420233884, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5132094367, 2488, 5132091879, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'c-swc-buy', 'steps': [('swc22',), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4563570, 4563570, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'c-swp-buy', 'steps': [('swp22',), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'vq1': -2488, 'proto22': 2463}, 'pools': {'main': [-123394, 0, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 2488, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'proto22': 25}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4684476, 4561082, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'c-swc-buy-cross', 'steps': [('swc22',), ('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322846461501, 'vq1': 984565819, 'vb2': -5294663779801, 'vq2': 5322846461501, 'vb3': -5266777961951, 'vq3': 5294663779801, 'vb4': -5226187326059, 'vq4': 5266777961951, 'u4': 5226187326059, 'bb22': 5379839}, 'pools': {'main': [-5436669, 5436669, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626947809, 2488, 2626945321, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182941609453, 'vq1': 979249658, 'vb2': -5101900194677, 'vq2': 5182941609453, 'vb3': -5022809657859, 'vq3': 5101900194677, 'vb4': -4933411252464, 'vq4': 5022809657859, 'u4': 4933411252464, 'bb22': 10642838}, 'pools': {'main': [-16187012, 16187012, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5132089783, 2488, 5132087295, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'c-swc-sell', 'steps': [('swc22',), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997497009, 'vq1': -181191, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-3335, 3335, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}]}, {'label': 'e-vq0-buy', 'steps': [('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332258753845, 'vq1': 985438918, 'vb2': -5303976578968, 'vq2': 5332258753845, 'vb3': -5275992837191, 'vq3': 5303976578968, 'vb4': -5235283312313, 'vq4': 5275992837191, 'u4': 5235283312313, 'bb22': 4515471}, 'pools': {'main': [-4561082, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631543756, 2488, 2631541268, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'vq_patch': 0}, {'label': 'z-buy', 'steps': [('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'z-sell', 'steps': [('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997497009, 'vq1': -181191, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}]}, {'label': 'z-buy-buy', 'steps': [('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5248517951916, 'vq1': 985438918, 'vb2': -5166019382620, 'vq2': 5248517951916, 'vb3': -5085518093451, 'vq3': 5166019382620, 'vb4': -4994603067981, 'vq4': 5085518093451, 'u4': 4994603067981, 'bb22': 4515471}, 'pools': {'main': [-9248046, 9124652, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5167964403, 2488, 5167961915, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]}, {'label': 'z-sell-sell', 'steps': [('mhsell4', (1000000000, 1)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997497009, 'vq1': -181191, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}, {'dPAYER': -5000, 'deltas': {'userquote': 178539, 'vb1': 997491035, 'vq1': -181189, 'vb2': 997494021, 'vq2': -997491035, 'vb3': 997497007, 'vq3': -997494021, 'vb4': 1000000000, 'vq4': -997497007, 'u4': -1000000000, 'bb22': 837}, 'pools': {'main': [-127576, 4182, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1125881, 2488, 1123393, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}]}, {'label': 'z-buy-sell', 'steps': [('mhbuy4', (1000000000, 1)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userquote': 187248, 'vb1': 1029649551, 'vq1': -190028, 'vb2': 1018757076, 'vq2': -1029649551, 'vb3': 1008036536, 'vq3': -1018757076, 'vb4': 1000000000, 'vq4': -1008036536, 'u4': -1000000000, 'bb22': 879}, 'pools': {'main': [-4687852, 4564458, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2632051683, 2488, 2632049195, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1892, 'bb22': 9}}]}, {'label': 'z-buy-cross', 'steps': [('mhbuy4', (1000000000, 1)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322846461501, 'vq1': 984565819, 'vb2': -5294663779801, 'vq2': 5322846461501, 'vb3': -5266777961951, 'vq3': 5294663779801, 'vb4': -5226187326059, 'vq4': 5266777961951, 'u4': 5226187326059, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2626947809, 2488, 2626945321, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182941609453, 'vq1': 979249658, 'vb2': -5101900194677, 'vq2': 5182941609453, 'vb3': -5022809657859, 'vq3': 5101900194677, 'vb4': -4933411252464, 'vq4': 5022809657859, 'u4': 4933411252464, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-5132089783, 2488, 5132087295, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}}, {'label': 'z-sell-cross', 'steps': [('mhsell4', (1000000000, 1)), ('mhsell4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': 176216, 'vb1': 997497009, 'vq1': -180017, 'vb2': 997498005, 'vq2': -997497009, 'vb3': 997499001, 'vq3': -997498005, 'vb4': 1000000000, 'vq4': -997499001, 'u4': -1000000000, 'bb22': 2000}, 'pools': {'main': [-127903, 4509, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-625882, 2488, 623394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1780, 'bb22': 21}}, {'dPAYER': -5000, 'deltas': {'userquote': 178214, 'vb1': 997491035, 'vq1': -181025, 'vb2': 997494021, 'vq2': -997491035, 'vb3': 997497007, 'vq3': -997494021, 'vb4': 1000000000, 'vq4': -997497007, 'u4': -1000000000, 'bb22': 999}, 'pools': {'main': [-128914, 5520, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1125881, 2488, 1123393, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'userquote': 1801, 'bb22': 11}}], 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (182349883978, (20, 222, 444))]}}, {'label': 'd-buy-dep-limit-low', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 29844713))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True, 'withheld': {}}]}, {'label': 'd-buy-dep-limit-exact', 'steps': [('mhbuy4', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 29844714))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}]}, {'label': 'd-buy-wd-limit-high', 'steps': [('mhbuy4', (1000000000, 1)), ('wd', (1000000000, 0, 29250803))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True, 'withheld': {}}]}, {'label': 'd-buy-wd-limit-exact', 'steps': [('mhbuy4', (1000000000, 1)), ('wd', (1000000000, 0, 29250802))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'vb4': -5235288546505, 'vq4': 5275998139846, 'u4': 5235288546505, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': 159348598958, 'userquote': 29250802, 'userlp': -1000000000, 'vb1': -159348598958, 'vq1': -29546265}, 'pools': {'main': [-4686964, 4563570, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631546401, 2488, 2631543913, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 159348598958, 'quote': 29546265}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 295463}}]}, {'label': 'e-vq0-dep-buy', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [30, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332268813636, 'vq1': 985438918, 'vb2': -5303986532328, 'vq2': 5332268813636, 'vb3': -5276002685801, 'vq3': 5303986532328, 'vb4': -5235293033768, 'vq4': 5276002685801, 'u4': 5235293033768, 'bb22': 4515471}, 'pools': {'main': [-4561052, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-2631548668, 2488, 2631546180, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'vq_patch': 0}, {'label': 'f-tf5000-buy', 'steps': [('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -2703654255828, 'vq1': 497696423, 'vb2': -2696364219568, 'vq2': 2703654255828, 'vb3': -2689113390776, 'vq3': 2696364219568, 'vb4': -2675231312484, 'vq4': 2689113390776, 'u4': 2675231312484, 'bb22': 1151788}, 'pools': {'main': [-2429459, 2306065, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1341329569, 2488, 1341327081, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 500000000, 'bb22': 1151789}}], 'bps': 5000}, {'label': 'f-tf5000-dep-buy', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy4', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -58624820, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 29312410}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -2703656842056, 'vq1': 497696423, 'vb2': -2696366791868, 'vq2': 2703656842056, 'vb3': -2689115949260, 'vq3': 2696366791868, 'vb4': -2675233850951, 'vq4': 2689115949260, 'u4': 2675233850951, 'bb22': 1151788}, 'pools': {'main': [-2429459, 2306065, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-1341330845, 2488, 1341328357, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 4, 'error': None, 'rollback': False, 'withheld': {'vq1': 500000000, 'bb22': 1151789}}], 'bps': 5000}]
MEASURE = bool(os.environ.get("MEASURE"))
STEP_KIND = {"mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "mhbuy4": "mhbuy4", "mhsell4": "mhsell4", "mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1", "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd", "swp22": "swp", "swc22": "swc", "col22": "col"}


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
    if case.get("bps", 100):
        for r in routes.values():
            m6 = r[6]
            r[6] = AccountMeta(BB22, m6.is_signer, m6.is_writable)
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
                    "withheld": {role: wh_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if wh_delta(rec, ROLE_KEY[role]) != 0},
                    "decoded": [decode_event(STEP_KIND[kind], raw) for raw in ev_list(rec["logs"])],
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
    if MEASURE:
        for case in CASES:
            run_case(case, "original", IMAGES["original"])
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
        report_cases.append({"label": case["label"], "bps": case.get("bps", 100),
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
    for name, key in [("POOL", pool), ("POOL2", POOL2), ("P3", P3),
                      ("BASE2", BASE2), ("BASE3", BASE3),
                      ("VB2", VB2), ("VQ2", VQ2), ("VB3", VB3), ("VQ3", VQ3), ("U3", U3),
                      ("CREATOR", CREATOR), ("CREATOR_VAULT", CREATOR_VAULT),
                      ("PROTOCOL", PROTOCOL),
                      ("PROTOCOL_ATA", PROTOCOL_ATA), ("CREATOR_ATA", CREATOR_ATA),
                      ("DEST", DEST),
                      ("PROTOCOL_ATA_P3", PROTOCOL_ATA_P3), ("CREATOR_ATA_P3", CREATOR_ATA_P3),
                      ("DEST3", DEST3),
                      ("PROTOCOL_ATA_P2", PROTOCOL_ATA_P2), ("CREATOR_ATA_P2", CREATOR_ATA_P2),
                      ("DEST2", DEST2),
                      ("P4", P4), ("P5", P5),
                      ("BASE4", BASE4), ("BASE5", BASE5),
                      ("VB4", VB4), ("VQ4", VQ4), ("VB5", VB5), ("VQ5", VQ5), ("U4", U4), ("U5", U5),
                      ("PROTOCOL_ATA_P4", PROTOCOL_ATA_P4), ("CREATOR_ATA_P4", CREATOR_ATA_P4),
                      ("DEST4", DEST4),
                      ("PROTOCOL_ATA_P5", PROTOCOL_ATA_P5), ("CREATOR_ATA_P5", CREATOR_ATA_P5),
                      ("DEST5", DEST5),
                      ("BB22", BB22), ("PROTO22", PROTO22), ("CREAT22", CREAT22), ("DEST22", DEST22)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
