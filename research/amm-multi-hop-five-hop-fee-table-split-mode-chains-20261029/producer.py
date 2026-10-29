#!/usr/bin/env python3
"""Build research/amm-multi-hop-five-hop-fee-table-split-mode-chains-20261029 receipts.

3rd run packet #44: the multi-hop fee-table split (3rd #37/#38/#39)
meets the mode gates (3rd #25/#26/#29) at depth 5 -- the 5-hop
generalization of 3rd #43. The route is main -> POOL2 -> P3 -> P4
-> P5, with cashback / mayhem / both-flags set on individual
pools and the #38 fee patches (tier crossing, exotic legs,
stable-count, tiers-only rebuild) applied on top:

- The split survives on the original image wherever the mode gate
  does not fire: a cashback main or intermediate pool still pays
  the tier-crossed hop-1 legs (buy A -> buy B, sell B -> A,
  inclusive exact boundaries) and the tail hop still follows the
  exotic flat fees (333 scales it ~64x, 0 zeroes it, the
  stable-count-0 shift reproduces, the tiers-only rebuild still
  zeroes the tail fee), and the sweep/collect pipes still drain
  exactly. Intermediate pools accrue nothing.
- The rebuilt images gate cashback at EVERY hop, so every
  non-terminal cashback pool diverges: the original succeeds
  where the rebuilt images fail 6079 (ghost events equal to the
  hops completed before the flagged hop: 0 for main, 1 for POOL2,
  2 for P3, 3 for P4 on buys; sells run tail-first so the counts
  reverse: 4 for main, 3 for POOL2). After a rebuilt failure the
  seed buckets still sweep/collect exactly (123,394 / 2,488).
- Mayhem gates every hop on all three images (6080), and the
  terminal hop is cashback-gated on all three images (6079),
  so tail-cb, tail-both, main-mayhem and intermediate-mayhem
  agree across images. Exotic legs do not rescue a gated tail
  hop, and a mayhem tail pool's protocol sweep still fails
  6013 while its creator sweep/collect drain the seed.
- Mixed gates pin the hop order: main-cb + tail-mayhem buys
  diverge (original 6080 with 4 ghosts, rebuilt 6079 with 0),
  while the same flags on sells agree (6080 with 0 ghosts on
  all images: sells execute the tail hop first) and
  main-mayhem + tail-cb buys agree (6080 with 0 ghosts:
  buys execute the head hop first).

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
    base, f, lp, pool, poolraw, quote, supply, token,
    userbase, userlp, userquote, vaultbase, vaultquote,
)
from pump_amm_trade_v2_differential import FEES, buyback, feeconfig, volume
from pump_amm_multi_hop_differential import (
    BASE2, BASE3, P3, POOL2, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT,
    U3, VB2, VB3, VQ2, VQ3, three_amm,
)

ROOT = Path.home() / "workspace/pumpfun-sparse"
OUT = ROOT / "research/amm-multi-hop-five-hop-fee-table-split-mode-chains-20261029"
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
    if kind in ("mhbuy5", "mhsell5"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes["sell" if kind == "mhsell5" else "buy"]
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
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3,
                 "p4": CREATOR_ATA_P4, "p5": CREATOR_ATA_P5}[pool_tag]
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
    {"label": "a-main-cb-cross", "flags": {'main': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
        SWC('p5', 5128763359, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 5128763359, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "a-p2-cb-cross", "flags": {'p2': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
     ], "rebuilt": [
        FAIL("6079", 1, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 1, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "a-p3-cb-cross", "flags": {'p3': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
     ], "rebuilt": [
        FAIL("6079", 2, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 2, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "a-p4-cb-cross", "flags": {'p4': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
     ], "rebuilt": [
        FAIL("6079", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "a-main-cb-exact", "flags": {'main': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (185295721063, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "a-main-cb-loop", "flags": {'main': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1)), ('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235212, 'vq5': 5290849792672, 'u5': 5249948235212, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2638953709, 2488, 2638951221)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5234052314271, 'vq1': 989141068, 'vb2': -5151405929904, 'vq2': 5234052314271, 'vb3': -5070768454676, 'vq3': 5151405929904, 'vb4': -4992073336048, 'vq4': 5070768454676, 'vb5': -4903136904404, 'vq5': 4992073336048, 'u5': 4903136904404, 'buyback': 10858932}, POOLS5(P(-16473886, 16350492, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-5128765847, 2488, 5128763359)), MHBUY_EV),
        MH(-5000, {'userquote': -1000000000, 'vb1': -5152706815985, 'vq1': 989141068, 'vb2': -5019487475483, 'vq2': 5152706815985, 'vb3': -4891429398235, 'vq3': 5019487475483, 'vb4': -4768266422920, 'vq4': 4891429398235, 'vb5': -4638349859364, 'vq5': 4768266422920, 'u5': 4638349859364, 'buyback': 10858932}, POOLS5(P(-27332818, 27209424, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-7506953590, 2488, 7506951102)), MHBUY_EV),
        SWC('p5', 7506951102, POOLS5(P(-27332818, 27209424, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 7506951102, POOLS5(P(-27332818, 27209424, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "a-p2-cb-sell", "flags": {'p2': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (182349883978, (20, 222, 444))]},
     "steps": [('mhsell5', (1000000000, 1)), ('mhsell5', (1000000000, 1))],
     "expect": {"original": [
        MH(-1849400, {'userquote': 177996, 'vb1': 997496013, 'vq1': -180017, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 2021}, POOLS5(P(-127903, 4509, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-625882, 2488, 623394)), MHSELL_EV),
        MH(-5000, {'userquote': 180015, 'vb1': 997488049, 'vq1': -181025, 'vb2': 997491035, 'vq2': -997488049, 'vb3': 997494021, 'vq3': -997491035, 'vb4': 997497007, 'vq4': -997494021, 'vb5': 1000000000, 'vq5': -997497007, 'u5': -1000000000, 'buyback': 1010}, POOLS5(P(-128914, 5520, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-1125881, 2488, 1123393)), MHSELL_EV),
     ], "rebuilt": [
        FAIL("6079", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHSELL_EV, volume=None),
        FAIL("6079", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHSELL_EV, volume=None),
     ]}},
    {"label": "a-main-cb-sell-cross", "flags": {'main': 'cb'}, "fee_patch": {'tiers_inplace': [(100, (10, 111, 333)), (182349883978, (20, 222, 444))]},
     "steps": [('mhsell5', (1000000000, 1)), ('mhsell5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': 177996, 'vb1': 997496013, 'vq1': -180017, 'vb2': 997497009, 'vq2': -997496013, 'vb3': 997498005, 'vq3': -997497009, 'vb4': 997499001, 'vq4': -997498005, 'vb5': 1000000000, 'vq5': -997499001, 'u5': -1000000000, 'buyback': 2021}, POOLS5(P(-127903, 4509, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-625882, 2488, 623394)), MHSELL_EV),
        MH(-5000, {'userquote': 180015, 'vb1': 997488049, 'vq1': -181025, 'vb2': 997491035, 'vq2': -997488049, 'vb3': 997494021, 'vq3': -997491035, 'vb4': 997497007, 'vq4': -997494021, 'vb5': 1000000000, 'vq5': -997497007, 'u5': -1000000000, 'buyback': 1010}, POOLS5(P(-128914, 5520, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-1125881, 2488, 1123393)), MHSELL_EV),
        SWC('p5', 1123393, POOLS5(P(-128914, 5520, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 1123393, POOLS5(P(-128914, 5520, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHSELL_EV, volume=None),
        FAIL("6079", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHSELL_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "b-main-cb-exotic333", "flags": {'main': 'cb'}, "fee_patch": {'exotic': (25, 5, 333)},
     "steps": [('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5090827967268, 'vq5': 5300061308171, 'u5': 5090827967268, 'buyback': 4607153}, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-170392133569, 2488, 170392131081)), MHBUY_EV),
        SWC('p5', 170392131081, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 170392131081, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "b-main-cb-rebuild", "flags": {'main': 'cb'}, "fee_patch": {'tiers_rebuild': [(100, (10, 111, 333))]},
     "steps": [('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5376183529200, 'vq1': 994510929, 'vb2': -5347434739303, 'vq2': 5376183529200, 'vb3': -5318991778556, 'vq3': 5347434739303, 'vb4': -5290849792672, 'vq4': 5318991778556, 'vb5': -5249948235213, 'vq5': 5290849792672, 'u5': 5249948235213, 'buyback': 5489071}, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV),
        SWC('p5', 123394, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 123394, POOLS5(P(-5614954, 5491560, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "b-main-cb-count0", "flags": {'main': 'cb'}, "fee_patch": {'stable_count': 0},
     "steps": [('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5271070100122, 'vq5': 5300061308171, 'u5': 5271070100122, 'buyback': 4607153}, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-1059926184, 2488, 1059923696)), MHBUY_EV),
        SWC('p5', 1059923696, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 1059923696, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "b-main-cb-exotic0", "flags": {'main': 'cb'}, "fee_patch": {'exotic': (0, 0, 0)},
     "steps": [('mhbuy5', (1000000000, 1)), ('swc', 'p5'), ('col', 'p5')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV),
        SWC('p5', 123394, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
        COL('p5', 123394, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]}},
    {"label": "c-main-cb-sweep", "flags": {'main': 'cb'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1)), ('swp', 'main'), ('swc', 'main'), ('col', 'main')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2643547981, 2488, 2643545493)), MHBUY_EV),
        SWP('main', 4609642, POOLS5(P(-123394, 0, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2643547981, 2488, 2643545493))),
        SWC('main', 123394, POOLS5(P(0, 0, 0), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2643547981, 2488, 2643545493))),
        COL('main', 123394, POOLS5(P(0, 0, 0), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2643547981, 2488, 2643545493))),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWP('main', 2488, POOLS5(P(-123394, 0, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), volume=None),
        SWC('main', 123394, POOLS5(P(0, 0, 0), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), volume=None),
        COL('main', 123394, POOLS5(P(0, 0, 0), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), volume=None),
     ]}},
    {"label": "c-p4-cb-sweep", "flags": {'p4': 'cb'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1)), ('swc', 'p4'), ('col', 'p4')],
     "expect": {"original": [
        MH(-1849400, {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5328301632828, 'vq3': 5356844515538, 'vb4': -5300061308171, 'vq4': 5328301632828, 'vb5': -5259040470738, 'vq5': 5300061308171, 'u5': 5259040470738, 'buyback': 4607153}, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2643547981, 2488, 2643545493)), MHBUY_EV),
        SWC('p4', 123394, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0), P(-2643547981, 2488, 2643545493))),
        COL('p4', 123394, POOLS5(P(-4733036, 4609642, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0), P(-2643547981, 2488, 2643545493))),
     ], "rebuilt": [
        FAIL("6079", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        SWC('p4', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0), P(-125882, 2488, 123394)), volume=None),
        COL('p4', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0), P(-125882, 2488, 123394)), volume=None),
     ]}},
    {"label": "d-maincb-tailmayhem-buy", "flags": {'main': 'cb', 'p5': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        FAIL("6080", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "d-maincb-p4mayhem-buy", "flags": {'main': 'cb', 'p4': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        FAIL("6080", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ], "rebuilt": [
        FAIL("6079", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "d-p2cb-tailmayhem-buy", "flags": {'p2': 'cb', 'p5': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": {"original": [
        FAIL("6080", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ], "rebuilt": [
        FAIL("6079", 1, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]}},
    {"label": "e-tail-cb", "flags": {'p5': 'cb'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6079", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-main-mayhem", "flags": {'main': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6080", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-p2-mayhem", "flags": {'p2': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6080", 1, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-p4-mayhem", "flags": {'p4': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6080", 3, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-tail-both", "flags": {'p5': 'both'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6079", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-tail-cb-exotic", "flags": {'p5': 'cb'}, "fee_patch": {'exotic': (25, 5, 333)},
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6079", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
    {"label": "e-tail-mayhem-sweep", "flags": {'p5': 'mayhem'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1)), ('swp', 'p5'), ('swc', 'p5'), ('col', 'p5')],
     "expect": [
        FAIL("6080", 4, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
        FAIL("6013", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), None, volume=None),
        SWC('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
        COL('p5', 123394, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-2488, 2488, 0)), volume=None),
     ]},
    {"label": "e-order-sell-tail-first", "flags": {'main': 'cb', 'p5': 'mayhem'}, "fee_patch": None,
     "steps": [('mhsell5', (1000000000, 1))],
     "expect": [
        FAIL("6080", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHSELL_EV, volume=None),
     ]},
    {"label": "e-order-buy-head-first", "flags": {'main': 'mayhem', 'p5': 'cb'}, "fee_patch": None,
     "steps": [('mhbuy5', (1000000000, 1))],
     "expect": [
        FAIL("6080", 0, POOLS5(P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394), P(-125882, 2488, 123394)), MHBUY_EV, volume=None),
     ]},
]

MEASURE = bool(os.environ.get("MEASURE"))
STEP_KIND = {"mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "swp": "swp", "swc": "swc", "col": "col"}


def case_expect(case, image_name):
    exp = case["expect"]
    if isinstance(exp, dict):
        return exp["original" if image_name == "original" else "rebuilt"]
    return exp


def run_case(case, image_name, binary):
    h = setup_vm(binary)
    apply_fee_patch(h, case.get("fee_patch"))
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
                      ("VB4", VB4), ("VQ4", VQ4), ("VB5", VB5), ("VQ5", VQ5), ("U3", U3), ("U4", U4), ("U5", U5),
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
