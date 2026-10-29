#!/usr/bin/env python3
"""Build research/amm-multi-hop-fee-table-split-liquidity-mode-tf-chains-20261029 receipts.

Multi-hop fee-table split x liquidity x mode chains under transfer
fee, 3 hops: the split x liquidity x mode chains of #55 with the
quote mint under transfer fee (tf100). The original image prices mode-blind legs
exactly as in #49; its cashback gate fires only at the last-listed
pool (p3), so main/pool2-cashback buys succeed on the original
while the rebuilt images fail 6079 at the gated hop in execution
order (buys head-first: main 0, pool2 1, p3 2 ghosts; sells
tail-first: p3 0, pool2 1, main 2 ghosts), and main/pool2-cashback
sells succeed on the original and fail 6079 on the rebuilt images.
Mayhem gates every hop on all images (6080); on both-flag pools
the original reports mayhem (6080) and the rebuilt images report
cashback (6079). Liquidity (deposit/withdraw) is mode-blind on
all images.

3rd run packet #55: multi-hop fee-table split x liquidity x mode, under tf. The split
route (main -> POOL2 -> P3, hop 1 = fee-tier cap selection, tail =
exotic flat fees, from 3rd #37) meets main-pool deposit/withdraw:

- A main-pool deposit/withdraw before a split trade moves the hop-1
  cap (supply * effective_quote / vault_base) and the vault balances,
  so it moves the tail legs; but a proportional deposit leaves the
  cap exactly invariant, so even a 10^12 deposit does NOT flip the
  first buy's tier.
- A deposit/withdraw between two split trades reprices the second
  trade off post-trade vaults and post-trade accrued buckets, and
  the dep/wd legs themselves price off post-trade available
  reserves; limit gates pin the post-trade basis.
- Sweeps stay leg-neutral for the split route too: sweeping the
  main buckets converts accrued to vq 1:1, so the next split trade
  has byte-identical token legs (only the pool relabel differs).
- The vq + accrued sum is invariant (0) across split trades and
  sweeps on this fixture, so dep/wd never hit the can_boost drift
  branch here; patching main vq to 0 makes dep drift vq (+30 floor),
  and vq itself still prices the split buy (vq0 buy differs from
  the as-is buy), while the dep move on top is the same ~+10M
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
OUT = ROOT / "research/amm-multi-hop-fee-table-split-liquidity-mode-tf-chains-20261029"
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
PROTO22, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN22), bytes(quote)], ATA_PROG)
CREAT22, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN22), bytes(quote)], ATA_PROG)
DEST22 = Pubkey.from_bytes(bytes([98]) * 32)
_BB_OWNER = None
for _row in f["accounts"].values():
    if _row["address"] == str(buyback):
        _BB_OWNER = Pubkey.from_bytes(base64.b64decode(_row["data_base64"])[32:64])
assert _BB_OWNER is not None, "buyback fixture row not found"
BB22, _ = Pubkey.find_program_address([bytes(_BB_OWNER), bytes(TOKEN22), bytes(quote)], ATA_PROG)


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
}
WATCH = [PAYER_KEY, pool, POOL2, P3, base, quote, BASE2, BASE3, lp, userbase,
         userquote, userlp, vaultbase, vaultquote, VB2, VQ2, VB3, VQ3, U3,
         buyback, volume, feeconfig, CONFIG_KEY,
         PROTOCOL_ATA, CREATOR_ATA, DEST,
         PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3,
         PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2,
         PROTO22, CREAT22, DEST22, BB22]
ROLE_KEY = {"userbase": userbase, "userquote": userquote, "userlp": userlp,
            "vaultbase": vaultbase, "vaultquote": vaultquote, "buyback": buyback,
            "vb1": vaultbase, "vq1": vaultquote, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "u3": U3,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "u3", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata2", "creatorata2", "dest2",
               "bb22", "proto22", "creat22", "dest22"]
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


POOLKEYS = {"main": pool, "p2": POOL2, "p3": P3}


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
    if kind in ("mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
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
    if kind in ("mhbuy3", "mhsell3", "mhbuy1", "mhsell1"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell3": "sell", "mhbuy3": "buy",
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


def MH(dPAYER, deltas, pools, event, withheld=None):
    return E(dPAYER, deltas, pools, VOL, event=event, events=3, withheld=withheld)


def SWC(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3"}[pool_tag]: -amount,
                     "creatorata" + {"main": "", "p2": "2", "p3": "3"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 1, CREATOR_VAULT), withheld=withheld)


def SWP(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3"}[pool_tag]: -amount,
                     "protoata" + {"main": "", "p2": "2", "p3": "3"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 0, PROTOCOL), withheld=withheld)


def COL(pool_tag, amount, pools, volume=VOL, withheld=None):
    suffix = {"main": "", "p2": "2", "p3": "3"}[pool_tag]
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3}[pool_tag]
    dest = {"main": DEST, "p2": DEST2, "p3": DEST3}[pool_tag]
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
    {'label': 'a-cb-dep-buy', 'flags': {'main': 'cb'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5262920106229, 'vq3': 5303991891401, 'u3': 5262920106229, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645508372, 2488, 2645505884, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'a-cb-dep-buy-cross', 'flags': {'main': 'cb'}, 'fee_patch': {'tiers_inplace': [(100, (10, 111, 333)), (183350153971, (20, 222, 444))]}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322856485808, 'vq1': 984565819, 'vb2': -5294673698238, 'vq2': 5322856485808, 'vb3': -5253722645178, 'vq3': 5294673698238, 'u3': 5253722645178, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2640860894, 2488, 2640858406, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5182970635538, 'vq1': 979249658, 'vb2': -5101928518871, 'vq2': 5182970635538, 'vb3': -5010453518716, 'vq3': 5101928518871, 'u3': 5010453518716, 'bb22': 10642838}, 'pools': {'main': [-16310406, 16187012, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-5185463647, 2488, 5185461159, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 107504}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'a-cb-dep-sell', 'flags': {'main': 'cb'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997498005, 'vq1': -181191, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'a-mayhem-dep-buy', 'flags': {'main': 'mayhem'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}]},
    {'label': 'a-both-dep-buy', 'flags': {'main': 'both'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'a-cb-dep-exotic', 'flags': {'main': 'cb'}, 'fee_patch': {'exotic': (25, 5, 333)}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1)), ('swc', 'p3'), ('col', 'p3')], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5094584146611, 'vq3': 5303991891401, 'u3': 5094584146611, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-170518498139, 2488, 170518495651, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'vq3': -170518495651, 'creatorata3': 170518495651}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 170518495651, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata3': -170518495651, 'dest3': 170518495651}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 170518495651, 'vault_ata': 'a766c164ccff777faced808989459a69f80413e5a60dd639342dd36e47704344', 'dest': '5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'vq3': -123394, 'creatorata3': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata3': -123394, 'dest3': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'a766c164ccff777faced808989459a69f80413e5a60dd639342dd36e47704344', 'dest': '5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}]}},
    {'label': 'a-cb-dep-rebuild', 'flags': {'main': 'cb'}, 'fee_patch': {'tiers_rebuild': [(100, (10, 111, 333))]}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1)), ('swc', 'p3'), ('col', 'p3')], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5322856485808, 'vq1': 984565819, 'vb2': -5294673698238, 'vq2': 5322856485808, 'vb3': -5253722645179, 'vq3': 5294673698238, 'u3': 5253722645179, 'bb22': 5379839}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 54342}}, {'dPAYER': -5000, 'deltas': {'vq3': -123394, 'creatorata3': 123394}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata3': -123394, 'dest3': 123394}, 'pools': {'main': [-5560063, 5436669, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'a766c164ccff777faced808989459a69f80413e5a60dd639342dd36e47704344', 'dest': '5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'vq3': -123394, 'creatorata3': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'creatorata3': -123394, 'dest3': 123394}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2488, 2488, 0, 4194352106721]}, 'volume': None, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 123394, 'vault_ata': 'a766c164ccff777faced808989459a69f80413e5a60dd639342dd36e47704344', 'dest': '5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f5f'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {}}]}},
    {'label': 'a-p2-cb-dep-buy', 'flags': {'p2': 'cb'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5262920106229, 'vq3': 5303991891401, 'u3': 5262920106229, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645508372, 2488, 2645505884, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 1, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'a-p3-cb-dep-buy', 'flags': {'p3': 'cb'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]},
    {'label': 'a-mayhem-dep-sell', 'flags': {'main': 'mayhem'}, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6080', 'rollback': True, 'withheld': {}}]},
    {'label': 'a-cb-wd-buy', 'flags': {'main': 'cb'}, 'steps': [('wd', (1000000000, 0, 0)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29019284, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 293125}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332254105589, 'vq1': 985438918, 'vb2': -5303971979889, 'vq2': 5332254105589, 'vb3': -5262900452883, 'vq3': 5303971979889, 'u3': 5262900452883, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645498441, 2488, 2645495953, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': 160619895223, 'userquote': 29019284, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'userquote': 293125}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4193352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'b-cb-buy-dep-buy', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'userquote': -1000000000, 'vb1': -5248527776010, 'vq1': 985438918, 'vb2': -5166029002075, 'vq2': 5248527776010, 'vb3': -5072990104313, 'vq3': 5166029002075, 'u3': 5072990104313, 'bb22': 4515471}, 'pools': {'main': [-9248046, 9124652, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-5222076477, 2488, 5222073989, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'b-cb-buy-dep-sell', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'userquote': 185288, 'vb1': 1018871036, 'vq1': -188038, 'vb2': 1008092574, 'vq2': -1018871036, 'vb3': 1000000000, 'vq3': -1008092574, 'u3': -1000000000, 'bb22': 869}, 'pools': {'main': [-4687843, 4564449, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2646008718, 2488, 2646006230, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1872, 'bb22': 9}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'b-mayhem-buy-dep-buy', 'flags': {'main': 'mayhem'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}]},
    {'label': 'b-cb-buy-dep-swc-col', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('swc22', 'main'), ('col22', 'main'), ('swp22', 'main')], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}, {'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-4563570, 4563570, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -5000, 'deltas': {'creat22': -122160, 'dest22': 120938}, 'pools': {'main': [-4563570, 4563570, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 122160, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'dest22': 1222}}, {'dPAYER': -5000, 'deltas': {'vq1': -4563570, 'proto22': 4517934}, 'pools': {'main': [0, 0, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 4563570, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'proto22': 45636}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -5000, 'deltas': {'creat22': -122160, 'dest22': 120938}, 'pools': {'main': [-2488, 2488, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 122160, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'dest22': 1222}}, {'dPAYER': -5000, 'deltas': {'vq1': -2488, 'proto22': 2463}, 'pools': {'main': [0, 0, 0, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 2488, 'bucket': 0}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'proto22': 25}}]}},
    {'label': 'b-cb-sell-dep-sell', 'flags': {'main': 'cb'}, 'steps': [('mhsell3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997498005, 'vq1': -181191, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}, {'dPAYER': -5000, 'deltas': {'userbase': -160620133044, 'userquote': -29608451, 'userlp': 1000000000, 'vb1': 160620133044, 'vq1': 29312366}, 'pools': {'main': [-126729, 3335, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160620133044, 'quote': 29312366}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {'userquote': 178540, 'vb1': 997494021, 'vq1': -181190, 'vb2': 997497007, 'vq2': -997494021, 'vb3': 1000000000, 'vq3': -997497007, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-127576, 4182, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-1125881, 2488, 1123393, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'c-cb-swc-buy', 'flags': {'main': 'cb'}, 'steps': [('swc22', 'main'), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4563570, 4563570, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'c-mayhem-swp-buy', 'flags': {'main': 'mayhem'}, 'steps': [('swp22', 'main'), ('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6013', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}]},
    {'label': 'c-cb-swc-sell', 'flags': {'main': 'cb'}, 'steps': [('swc22', 'main'), ('mhsell3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997498005, 'vq1': -181191, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-3335, 3335, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'creat22': 1234}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-2488, 2488, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'd-cb-buy-dep-limit-low', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 29844713))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}]}},
    {'label': 'd-cb-buy-dep-limit-exact', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 29844714))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {'userbase': -159348598959, 'userquote': -29844714, 'userlp': 1000000000, 'vb1': 159348598959, 'vq1': 29546266}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 159348598959, 'quote': 29546266}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 298448}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}]}},
    {'label': 'd-cb-buy-wd-limit-high', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1)), ('wd', (1000000000, 0, 29250803))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': None, 'events': 0, 'error': '6004', 'rollback': True, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6004', 'rollback': True, 'withheld': {}}]}},
    {'label': 'd-mayhem-buy-dep-limit', 'flags': {'main': 'mayhem'}, 'steps': [('mhbuy3', (1000000000, 1)), ('dep', (1000000000, 18446744073709551615, 29844713))], 'expect': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}, {'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}]},
    {'label': 'e-cb-dep-buy1', 'flags': {'main': 'cb'}, 'onehop': True, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy1', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]},
    {'label': 'e-cb-dep-sell1', 'flags': {'main': 'cb'}, 'onehop': True, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhsell1', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]},
    {'label': 'z-cb-buy', 'flags': {'main': 'cb'}, 'steps': [('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'z-cb-sell', 'flags': {'main': 'cb'}, 'steps': [('mhsell3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -1849400, 'deltas': {'userquote': 178541, 'vb1': 997498005, 'vq1': -181191, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'userquote': 1804, 'bb22': 9}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}, 'events': 2, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'z-mayhem-buy', 'flags': {'main': 'mayhem'}, 'steps': [('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}]},
    {'label': 'z-both-buy', 'flags': {'main': 'both'}, 'steps': [('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6080', 'rollback': True, 'withheld': {}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
    {'label': 'z-dep-buy', 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 296085}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -5332274230014, 'vq1': 985438918, 'vb2': -5303991891401, 'vq2': 5332274230014, 'vb3': -5262920106229, 'vq3': 5303991891401, 'u3': 5262920106229, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645508372, 2488, 2645505884, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 10000000, 'bb22': 45611}}]},
    {'label': 'f-tf5000-dep-buy', 'flags': {'main': 'cb'}, 'bps': 5000, 'steps': [('dep', (1000000000, 18446744073709551615, 18446744073709551615)), ('mhbuy3', (1000000000, 1))], 'expect': {'original': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -58624820, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 29312410}}, {'dPAYER': -1849400, 'deltas': {'userquote': -1000000000, 'vb1': -2703656842056, 'vq1': 497696423, 'vb2': -2696366791868, 'vq2': 2703656842056, 'vb3': -2682427912876, 'vq3': 2696366791868, 'u3': 2682427912876, 'bb22': 1151788}, 'pools': {'main': [-2429459, 2306065, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-1344947225, 2488, 1344944737, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}, 'events': 3, 'error': None, 'rollback': False, 'withheld': {'vq1': 500000000, 'bb22': 1151789}}], 'rebuilt': [{'dPAYER': -5000, 'deltas': {'userbase': -160619895224, 'userquote': -58624820, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}, 'events': 1, 'error': None, 'rollback': False, 'withheld': {'vq1': 29312410}}, {'dPAYER': -5000, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'event': None, 'events': 0, 'error': '6079', 'rollback': True, 'withheld': {}}]}},
]

MEASURE = bool(os.environ.get("MEASURE"))
STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1", "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd", "swp22": "swp", "swc22": "swc", "col22": "col"}


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
                    "pools": {name: pool_state(rec["after"][str(key)]) for name, key in (("main", pool), ("pool2", POOL2), ("p3", P3))},
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
        for pool_name, pool_key in (("main", pool), ("pool2", POOL2), ("p3", P3)):
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
                      ("DEST2", DEST2)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
