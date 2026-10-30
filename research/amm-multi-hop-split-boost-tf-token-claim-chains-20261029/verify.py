#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-token-claim-chains-20261029.

Checks, from the packet files alone (plus the three program images):
- MANIFEST.json lists every packet file (except itself) with a matching sha256.
- runtime/report.json.gz: 21 cases, 261 receipts, 27 parts
  (26x10 + 1), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures verify.
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer lamport deltas, the
  token-leg deltas (user base/quote/LP, vault base/quote per hop,
  tail output U3, SPL buyback in plain mode, TOKEN22 buyback in
  transfer-fee mode, boost ATA, claim vault/user ATAs, cashback
  UVA token account), the Token-2022 withheld deltas (claim-mint
  and quote-mint pipes), the five pool states
  (virtual_quote_reserves i128, protocol_fees, creator_fees,
  lp_supply), the user volume accumulator state (absent before the
  first successful multi-hop, 1,844,400 lamports / 137 bytes /
  payer user after it; seeded 10**9-lamport accounts where the
  case seeds one) and its full field tuple (needs_claim,
  total_unclaimed, total_claimed, current_sol_volume,
  last_update_timestamp, has_total_claimed_tokens, cashback_earned,
  total_cashback_claimed), the decoded event fields (multi-hop
  disc/len per hop event, sweep amount/bucket/recipient, collect
  fee/creator/vault-ATA/dest, boost requested/used/burned/vq/
  quote-after/base-after/remaining plus the leading 512-byte
  BuyEvent, token-claim amount/total-claimed/volume, cashback-claim
  amount/total-claimed/total-earned), and the pinned lamport
  values (created Token-2022 user claim ATA 2,157,600; cashback
  UVA token account back to rent 2,039,280 after a successful
  cashback claim).
- Failure steps roll back every watched account except the fee
  payer (fee 5,000) and carry the expected error code plus the
  recorded per-image site line in their logs. A token claim after
  a fresh split trade is a silent zero claim (0 events, "No
  tokens to claim" in the logs, payer 5,000 only). Site lines are
  checked per image, never compared across images, because
  original and rebuilt sources differ in line numbers.
- The global volume accumulator never changes in any step.
- Control and candidate observed surfaces are identical in every
  case. Twenty cases agree on all three images; exactly one case
  diverges, and the report flags it: f-cbflag-buy-cclaim-tclaim-
  swc-col (original gates cashback only at the terminal hop, so
  the split buy on the cashback-flagged main pool succeeds and
  earns no cashback; the rebuilds gate at every hop, so the buy
  fails 6079 CashbackCoinNotSupported at multi_hop_swap.rs:500
  and the following claims fail 3012 on the still-absent volume
  accumulator -- the 3rd #25 mode-gate divergence, reproduced on
  the split chain). The pinned behaviour: a fresh split trade or
  boost feeds the token claim nothing; a seeded token claim pays
  3,334,551 wherever it sits in the chain (net 3,301,205 /
  withheld 33,346 at claim-mint tf100, net 1,667,275 / withheld
  1,667,276 at tf5000, event gross-reported in all cases); the
  claim moves neither the boost burn (0-bps 5,307,028,789,111,
  tf100 5,255,205,915,165 with or without an interleaved claim)
  nor the tier-cap crossing second buy (5,019,668,351,471) nor
  the tail output; failed claims isolate fully and the chain
  still drains in full afterwards (missing global accumulator
  3012, short vault Token custom 1, missing user ATA created by
  init_if_needed for 2,157,600 rent); cashback and token claims
  touch disjoint fields in both orders on the split chain, and a
  split buy on a cashback-flagged pool earns no cashback at all
  (the following cashback claim is a zero claim: 1 event, amount
  0). Claim_cashback cannot run on the transfer-fee-overridden
  quote mint at all (Anchor ConstraintTokenTokenProgram 2021:
  the mint's program is Token-2022 while the claim's token
  accounts are SPL) -- so the cashback family runs in plain-quote
  mode, where the split buy tail (5,315,084,721,958) equals the
  0-bps transfer-fee-mode tail exactly.
- The three program images hash to the values recorded in the report.

Usage: python3 verify.py   (run from this packet directory)
"""
import base64
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parent
WS = Path.home() / "workspace/slop-verify"
SPARSE = Path.home() / "workspace/pumpfun-sparse"
IMAGE_PATHS = {
    "original": SPARSE / "evidence/original/pump_amm/deployed.so",
    "control": WS / "control.so",
    "candidate": WS / "candidate.so",
}
PAYER_KEY = Pubkey.from_string("DXyM8yAHqpMzDtvwz5DXoEUQmPxjJPMKCASCPhLMKpEx")
POOL = Pubkey.from_string("GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J")
POOL2 = Pubkey.from_string("Fpyw25Qi4beJtjo22e1iLZ8PeGkKXFBkF2WbdSuxsaZa")
P3 = Pubkey.from_string("3tvv2kFkoHENFctvg9VKJi2z6pagcMPoHMFP3m9FfruF")
P4 = Pubkey.from_string("5gZTf2A6UPeYZCq1mkdiYquMQqmjNcz9pknbABkWif9c")
P5 = Pubkey.from_string("5TdRYVo7We7hYSXDS3ryvUvouL7hoaMLTGMRqMrzBhcE")
BASE4 = Pubkey.from_string("6ws1bVyu3F8wGy1fPHhrc2v8UyWiGbRAAuek8SwikKPD")
BASE5 = Pubkey.from_string("75hbt6uvDqjPZ9WgFtMhBnTeyHw7cinoHiz4FD2vEz2d")
VB4 = Pubkey.from_string("3qw1dQGA7eW3m2BsiAhUB5R3sXEYnr7NbMFBuqUSotYn")
VQ4 = Pubkey.from_string("6WdSUBTULBFY4FE31WymuxQqJcWeLoLBCucMFsprkUAM")
VB5 = Pubkey.from_string("EbswyL8rkPriwr3sfAftkGBRutDHAtQWK1pT7GMcJH9t")
VQ5 = Pubkey.from_string("5m89K1EMCbe1PYwQ7aJeZ8vEsSYrCRkcGMzf53Nxhvs8")
U4 = Pubkey.from_string("71nJjoSudYSAR4GApb2mtugtj8iuwf6yjKKQBpzKVehv")
U5 = Pubkey.from_string("79cu2QNvp92chEmBhBgcUfERDT9KHnUcr8eiJb5WzKML")
USERBASE = Pubkey.from_string("5jKh25biPsnrmLWXXuqKNH2Q67j69T4Q7Zew5c8wJKaV")
USERQUOTE = Pubkey.from_string("5oEzAP4izB65uRm2yDAEf9oALGwHpWkDfyKb8zBY3euC")
USERLP = Pubkey.from_string("5sAHJgXjaUPK3X1YQWV9x2ZvaS9VVaS3ENzFCNE8nzDu")
VAULTBASE = Pubkey.from_string("5jMpkf4JF4noHftLgNKyPNh6roVfPSGSjuEk3U4eLKRa")
VAULTQUOTE = Pubkey.from_string("43DVcZR4kQFjh4Xm2i3DcneRxNjZp7HMud8yDrJWrDr8")
VB2 = Pubkey.from_string("3WojBK9kk5fHnhZfDb16jNJxGu6RtVdKpxYfFUKExGjg")
VQ2 = Pubkey.from_string("7S39XJ3FdyipvwLvgrf65cDWxC1dFaXUSaoNR6wvy59t")
VB3 = Pubkey.from_string("HWrvLRAYVW6NC4QK4mofY6wcuztVZXLNm4syGwQarZnM")
VQ3 = Pubkey.from_string("8fXWArssNK14eGw3puZgFqRRDrXjMMxuWX63nYUggKXi")
U3 = Pubkey.from_string("6swiTCWtSwqi8sm9wzNwKA9NEpJWbXjLcVz654u7zz4W")
BUYBACK = Pubkey.from_string("HjQjngTDqoHE6aaGhUqfz9aQ7WZcBRjy5xB8PScLSr8i")
VOLUME = Pubkey.from_string("8NyBnxo9mS5MsqY4qoKmrt7MS89d7MNV6rh5fu2YsQPT")
PROTOCOL_ATA = Pubkey.from_string("94qWNrtmfn42h3ZjUZwWvK1MEo9uVmmrBPd2hpNjYDjb")
CREATOR_ATA = Pubkey.from_string("3E6RtRCxo7Yz64zi8aSmC9DtNKcaMp5rFUcBnJKsc2fg")
DEST = Pubkey.from_string("7MNnTJmxb2vJ7WWi15fNMHYhwvmvJyY5XMegUjDKEKKT")
PROTOCOL_ATA_P2 = Pubkey.from_string("FHJxZKyxVkCC9d4wKWs97VAYY6b9JYFjqhLBgbGnjrFA")
CREATOR_ATA_P2 = Pubkey.from_string("DwhA1oGtJr1TXh7Ubs3V31evWEkomMbaU4Bhsbqr1Vde")
DEST2 = Pubkey.from_string("7VDNjuhymdWkPh1isgKCw36ESFCKf6uieAyzbVJWiyxs")
PROTOCOL_ATA_P3 = Pubkey.from_string("Ec3s4QjSwS71dgHCBxk1H1Q8gDfWD2Qy5XzZA34wdYQi")
CREATOR_ATA_P3 = Pubkey.from_string("CGTxrQSoWdAxMRAajQHKoCuBVoKbDrczzUddHVdRdwPH")
DEST3 = Pubkey.from_string("7RJ5bcEyBLDXFbmDSNzHeAKUC5z7z3Du5mKLY7FuyeeA")
PROTOCOL_ATA_P4 = Pubkey.from_string("2W8N7FVcdvQYvTthT6xgmnKoPCBKGMRscfM6pzvQD9Zg")
CREATOR_ATA_P4 = Pubkey.from_string("AWpQ4QeMTAv4UWkkUvMymkWcBT7xDovAQDtHymwc2C9v")
DEST4 = Pubkey.from_string("7Z8ftDAzMvoyXnGEJye8DurzgQQXLAbYCaeeesM7UKHa")
PROTOCOL_ATA_P5 = Pubkey.from_string("JBAC3QYSgSavuqrPocD353ZuXJqU3YbfRvzSYEMBvGpu")
CREATOR_ATA_P5 = Pubkey.from_string("6sGd476UhAawRUjd4K4vFwopnGo9ftbmywrND12R99Qa")
DEST5 = Pubkey.from_string("7gyGAp71YXQRoxmFBaHxofQXAipvgHyBKPyxmdSJxyvz")
BB22 = Pubkey.from_string("8imwZyx4D4zdUQ67TvftjjyGattafMNWMLs6HV8WNn1Y")
PROTO22 = Pubkey.from_string("2tZUDAsQqirqn1pdnYBVM7pDao57zsTSUspuFD2tAwTS")
CREAT22 = Pubkey.from_string("HShRmMRVQBgRz1eCD1aSr1hUm2BdrALVimjNXRduJwZB")
DEST22 = Pubkey.from_string("7d3y2WdzxE7CfsWjkGy3WndkvZcj1EHMkzKJiFPiDecH")
BOOST = Pubkey.from_string("5HkYU1vqHFZDZTz5LWcDynGvbg84aiGPVG8kNUcnbbC1")
BATA = Pubkey.from_string("Cd8K5QT4ninw4jnWP7nhmPbEJb8VsECTHUzeBf7KueMS")
BP3 = Pubkey.from_string("9Kn4eTXdasQr6ELbrd7fHT4JcPTSS9LoGW2sbh8CwZPZ")
BA3 = Pubkey.from_string("5mWEub2Js9ep2Em82qCPacPcBtEaPhxyQhU9QtT9V5Tn")
GVOL = Pubkey.from_string("C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw")
IMINT = Pubkey.from_string("GGfoM4FJeQ8CXTXhaWiekqRQAtYVDNAKHDdJAu8PrHtm")
GA_ATA = Pubkey.from_string("9pVmg8pt6PR5UL8FphDN6QSfEvTiPbgUvA7YBUwPrgi")
UA_ATA = Pubkey.from_string("HM5XNiWUtZACr5dE6FRAvZeUDE4cUfbXNHdR7N9RwmCS")
UVATA = Pubkey.from_string("BEaaJNs1cVZKv29qYcXaaDSgm6Defa5b6kt5pRcUkHWe")
ROLE_KEY = {"userbase": USERBASE, "userquote": USERQUOTE, "userlp": USERLP,
            "vaultbase": VAULTBASE, "vaultquote": VAULTQUOTE, "buyback": BUYBACK,
            "vb1": VAULTBASE, "vq1": VAULTQUOTE, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22,
            "boostata": BATA, "boostata3": BA3,
            "gata": GA_ATA, "uata": UA_ATA, "uvata": UVATA}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata2", "creatorata2", "dest2",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "bb22", "proto22", "creat22", "dest22",
               "boostata", "boostata3",
               "gata", "uata", "uvata"]
POOL_KEYS = {"main": POOL, "pool2": POOL2, "p3": P3, "p4": P4, "p5": P5}


def fail(msg):
    raise SystemExit(f"FAIL: {msg}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def tok_amount(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 72:
        return None
    return struct.unpack_from("<Q", raw, 64)[0]


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
    if entry is None:
        return None
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


def uva_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 90:
        return {"len": len(raw)}
    needs, unc, cla, vol, last, hasc, earn, cbcl = struct.unpack_from('<BQQQqBQQ', raw, 40)
    return {"needs": needs, "unclaimed": unc, "claimed": cla, "volume": vol,
            "last": last, "has": hasc, "earned": earn, "cb_claimed": cbcl}


def u64(raw, off):
    return struct.unpack_from("<Q", raw, off)[0]


def ev_list(logs):
    return [base64.b64decode(l.split("Program data: ", 1)[1].strip())
            for l in logs if l.startswith("Program data: ")]


def decode_event(kind, raw):
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind in ("swp", "swc", "swp22", "swc22"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "recipient": raw[112:144].hex(),
                "amount": u64(raw, 176), "bucket": raw[184]}
    if kind in ("dep", "wd"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 72), "quote": u64(raw, 80)}
    if kind in ("col", "col22"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "creator": raw[16:48].hex(), "fee": u64(raw, 48),
                "vault_ata": raw[56:88].hex(), "dest": raw[88:120].hex()}
    if kind == "tclaim":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "user": raw[8:40].hex(), "mint": raw[40:72].hex(),
                "amount": u64(raw, 72), "ts": struct.unpack_from("<q", raw, 80)[0],
                "total_claimed": u64(raw, 88), "current_sol_volume": u64(raw, 96)}
    if kind == "cclaim":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "user": raw[8:40].hex(), "amount": u64(raw, 40),
                "ts": struct.unpack_from("<q", raw, 48)[0],
                "total_claimed": u64(raw, 56), "total_earned": u64(raw, 64)}
    if kind in ("boost", "boost3", "boost4", "boost5"):
        if raw[:8].hex() != "3f451c16305cc2b9":
            return {"disc": raw[:8].hex(), "len": len(raw)}
        return {"disc": raw[:8].hex(), "len": len(raw),
                "requested": u64(raw, 144), "used": u64(raw, 152),
                "burned": u64(raw, 160),
                "vq": int.from_bytes(raw[168:184], "little", signed=True),
                "quote_after": u64(raw, 184), "base_after": u64(raw, 192),
                "remaining": u64(raw, 200)}
    return None


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


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.exists():
            fail(f"missing file {entry['path']}")
        if sha(path.read_bytes()) != entry["sha256"]:
            fail(f"sha mismatch {entry['path']}")
    with gzip.open(ROOT / "runtime" / "report.json.gz", "rt", encoding="utf-8") as fh:
        report = json.load(fh)
    if report["case_count"] != 21 or report["receipt_count"] != 261:
        fail(f"counts {report['case_count']} cases / {report['receipt_count']} receipts")
    if report["counts"] != {"cases": 21, "receipts": 261, "parts": 27}:
        fail(f"counts block {report['counts']}")
    if report["mismatches"] != []:
        fail(f"mismatches recorded: {report['mismatches']}")
    for name, path in IMAGE_PATHS.items():
        if sha(path.read_bytes()) != report["images"][name]:
            fail(f"image hash mismatch {name}")
    receipts = []
    for part in report["parts"]:
        path = ROOT / part["file"]
        data = path.read_bytes()
        if sha(data) != part["sha256"] or len(data) != part["bytes"]:
            fail(f"part hash/size mismatch {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            chunk = [json.loads(line) for line in fh if line.strip()]
        if len(chunk) != part["count"]:
            fail(f"part count mismatch {part['file']}")
        receipts.extend(chunk)
    if len(receipts) != 261:
        fail(f"receipt total {len(receipts)}")
    by_case = {}
    for rec in receipts:
        by_case.setdefault(rec["case"], {}).setdefault(rec["image"], []).append(rec)
    divergent_labels = []
    for case in report["cases"]:
        label = case["label"]
        steps = case["steps"]
        for image in ("original", "control", "candidate"):
            expect = steps["original" if image == "original" else "rebuilt"] \
                if isinstance(steps, dict) else steps
            recs = by_case.get(label, {}).get(image)
            if recs is None or len(recs) != len(expect):
                fail(f"{label}/{image}: {0 if recs is None else len(recs)} receipts, expected {len(expect)}")
            for rec, exp in zip(recs, expect):
                tag = f"{label}/{image}/{rec['step']}"
                tx = Transaction.from_bytes(base64.b64decode(rec["transaction_base64"]))
                if not all(tx.verify_with_results()):
                    fail(f"{tag}: signature verification failed")
                if exp["error"] is None:
                    if rec["error"] is not None:
                        fail(f"{tag}: unexpected error {rec['error']}")
                else:
                    if rec["error"] is None or exp["error"] not in rec["error"]:
                        fail(f"{tag}: expected error {exp['error']}, got {rec['error']}")
                if len(rec["events"]) != exp["events"]:
                    fail(f"{tag}: events {len(rec['events'])} != {exp['events']}")
                if lam_delta(rec, PAYER_KEY) != exp["dPAYER"]:
                    fail(f"{tag}: dPAYER {lam_delta(rec, PAYER_KEY)} != {exp['dPAYER']}")
                for role, want in exp["deltas"].items():
                    if tok_delta(rec, ROLE_KEY[role]) != want:
                        fail(f"{tag}: delta {role} {tok_delta(rec, ROLE_KEY[role])} != {want}")
                for role in TOKEN_ROLES:
                    if role in exp["deltas"]:
                        continue
                    if tok_delta(rec, ROLE_KEY[role]) != 0:
                        fail(f"{tag}: unexpected delta {role} {tok_delta(rec, ROLE_KEY[role])}")
                for role, want in exp.get("withheld", {}).items():
                    if wh_delta(rec, ROLE_KEY[role]) != want:
                        fail(f"{tag}: withheld {role} {wh_delta(rec, ROLE_KEY[role])} != {want}")
                for role in TOKEN_ROLES:
                    if role in exp.get("withheld", {}):
                        continue
                    if wh_delta(rec, ROLE_KEY[role]) != 0:
                        fail(f"{tag}: unexpected withheld {role} {wh_delta(rec, ROLE_KEY[role])}")
                for pool_name, pool_key in POOL_KEYS.items():
                    if pool_state(rec["after"][str(pool_key)]) != exp["pools"][pool_name]:
                        fail(f"{tag}: pool {pool_name} {pool_state(rec['after'][str(pool_key)])} != {exp['pools'][pool_name]}")
                if vol_state(rec["after"][str(VOLUME)]) != exp["volume"]:
                    fail(f"{tag}: volume {vol_state(rec['after'][str(VOLUME)])} != {exp['volume']}")
                if exp.get("uva") is not None:
                    got_uva = uva_fields(rec["after"][str(VOLUME)])
                    if got_uva != exp["uva"]:
                        fail(f"{tag}: uva {got_uva} != {exp['uva']}")
                if exp.get("uva_absent"):
                    if rec["after"][str(VOLUME)] is not None:
                        fail(f"{tag}: volume should stay absent")
                for role, want in exp.get("lam_after", {}).items():
                    got = rec["after"][str(ROLE_KEY[role])]
                    if got is None or got["lamports"] != want:
                        fail(f"{tag}: lam_after {role} {None if got is None else got['lamports']} != {want}")
                if rec["after"][str(GVOL)] != rec["before"][str(GVOL)]:
                    fail(f"{tag}: global volume accumulator changed")
                if exp.get("log_fragment"):
                    if exp["log_fragment"] not in "\n".join(rec["logs"]):
                        fail(f"{tag}: log fragment missing")
                if exp.get("site_fragment"):
                    if exp["site_fragment"] not in "\n".join(rec["logs"]):
                        fail(f"{tag}: site fragment missing")
                if exp.get("rollback"):
                    for k, b in rec["before"].items():
                        if k == str(PAYER_KEY):
                            continue
                        if rec["after"][k] != b:
                            fail(f"{tag}: rollback violated for {k}")
                if exp.get("boost_event") is not None:
                    raws = ev_list(rec["logs"])
                    if len(raws) != 2:
                        fail(f"{tag}: boost events {len(raws)} != 2")
                    first = decode_event(rec["step"], raws[0])
                    if first != {"disc": "67f4521f2cf57777", "len": 512}:
                        fail(f"{tag}: boost first event {first}")
                    got = decode_event(rec["step"], raws[1])
                    if got is None:
                        fail(f"{tag}: boost event decode failed")
                    for fkey, want in exp["boost_event"].items():
                        if got.get(fkey) != want:
                            fail(f"{tag}: boost event {fkey} {got.get(fkey)} != {want}")
                if exp.get("event") is not None:
                    raws = ev_list(rec["logs"])
                    if len(raws) != exp["events"]:
                        fail(f"{tag}: decoded events {len(raws)} != {exp['events']}")
                    for raw in raws:
                        got = decode_event(rec["step"], raw)
                        if got is None:
                            fail(f"{tag}: event decode failed")
                        for fkey, want in exp["event"].items():
                            if got.get(fkey) != want:
                                fail(f"{tag}: event {fkey} {got.get(fkey)} != {want}")
        base = surface(by_case[label]["original"])
        if surface(by_case[label]["control"]) != surface(by_case[label]["candidate"]):
            fail(f"{label}: control and candidate surfaces differ")
        computed_divergent = (surface(by_case[label]["control"]) != base
                              or surface(by_case[label]["candidate"]) != base)
        if computed_divergent:
            divergent_labels.append(label)
        if computed_divergent != case["divergent"]:
            fail(f"{label}: divergent flag {case['divergent']} != computed {computed_divergent}")
        for image in ("original", "control", "candidate"):
            sites = case["error_sites"][image]
            recs = by_case[label][image]
            if len(sites) != len(recs):
                fail(f"{label}/{image}: site count mismatch")
            for rec, site in zip(recs, sites):
                if site is not None and site not in "\n".join(rec["logs"]):
                    fail(f"{label}/{image}: recorded site line not in logs: {site}")
    print(f"PASS: 21 cases, 261 receipts, 27 parts, per-image expectations hold "
          f"(signatures, deltas, withheld, events, error codes/sites, rollback, "
          f"UVA fields, claim lamports, GVOL invariance); "
          f"control == candidate everywhere; original agrees everywhere except "
          f"({len(divergent_labels)} divergent cases): {divergent_labels}")


if __name__ == "__main__":
    main()
