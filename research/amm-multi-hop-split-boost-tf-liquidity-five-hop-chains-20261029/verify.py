#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-liquidity-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 71 cases, 684 receipts, 69 parts
  (68x10 + 4), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures verify
  (cpatch steps carry an empty transaction by design -- a harness field
  reset, never an instruction -- and are asserted as such instead, and
  the following step's before snapshot must equal the cpatch after
  snapshot).
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer and outsider lamport
  deltas, the token-leg deltas, the Token-2022 withheld deltas, the
  native-mint token-account lamport deltas, the five fixture pool
  states (virtual_quote_reserves i128, protocol_fees, creator_fees,
  lp_supply) plus each pool's creator_fee_bps field (261..269) and the
  main pool's coin_creator bytes after every step, the GlobalConfig state
  (including boost authority 907..939, boost_enabled, disable flags,
  creator_fee 313..321, creator_fee_configurable 940 and
  max_configurable_creator_fee_bps 941..949), the user volume
  accumulator state, the global volume accumulator state, the account
  lengths after every step, and the decoded event fields (multi-hop
  508/449-byte hop events, boost 512-byte BuyEvent + 208-byte boost
  event, sweep 185-byte fields, collect 120-byte fields, deposit /
  withdraw event base/quote amounts).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the liquidity x boost behaviour at
  depth 5 agrees on all three images).
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events and the 5-hop sell payout is 178541
  with 5 hop events; deposit 10^6/10^9/10^12 moves the next
  patched-window main boost burn by +10079/+10082934/+8156169732 and
  the vq field by +238/+238445/+238445856, while withdraw moves it by
  -10079/-10087705 with vq -239/-238446; the deposit-then-withdraw
  round trip leaves vq at -1 but the burn byte-identical to the
  anchor; deposit/withdraw slippage gates fail 6004, zero-amount legs
  succeed as 1-event no-ops, deposit/withdraw disable bits fail
  6018/6019, and clearing the bit restores the +20248 vault-only
  deposit burn; a deposit before a 5-hop buy lifts the tail by 9597
  while a deposit before a 5-hop sell leaves the 178541 payout
  byte-identical; hop-pool deposits fail Token-2022 MintTo OwnerMismatch
  (4) on P2/P3/P4/P5 alike because the fixture's shared LP mint
  authority is the main-pool PDA, and patching the mint authority to
  the hop pool makes the deposit succeed while the hop boost stays
  byte-identical at 999997999; a patched P4 deposit lifts the 5-hop
  tail by 6482 and a patched P5 deposit by 6466; tf5000 deposit grosses
  the quote leg up to 58626 and tf0 deposit pays 29313 flat.
"""
import base64
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYER = "DXyM8yAHqpMzDtvwz5DXoEUQmPxjJPMKCASCPhLMKpEx"
OUTSIDER = "5jotNjSnm9ZJRefVfqHato9FC4d9t6CHb2xS1726MTyY"
POOL = "GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J"
POOL2 = "Fpyw25Qi4beJtjo22e1iLZ8PeGkKXFBkF2WbdSuxsaZa"
P3 = "3tvv2kFkoHENFctvg9VKJi2z6pagcMPoHMFP3m9FfruF"
CONFIG = "ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw"
FEECONFIG = "5PHirr8joyTMp9JMm6nW7hNDVyEYdkzDqazxPD7RaTjx"
VOLUME = "8NyBnxo9mS5MsqY4qoKmrt7MS89d7MNV6rh5fu2YsQPT"
GVOL = "C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw"
EXTKEY = "B8qLUArXhjYyvaX8RovpeJmRcpZC2XyzpCyRk1is4yP3"
QUOTE = "So11111111111111111111111111111111111111112"
BB22 = "8imwZyx4D4zdUQ67TvftjjyGattafMNWMLs6HV8WNn1Y"
WDEST = "43HYZhSLzJVSwUAccwX2dmWmKBxhHDxjA1LQKJkzTg7w"
RES0_ATA = "2dmiSdVXhau9JVgrW7BFhYZCnPhDX8vKZ4Rj8vsowAb3"
U3 = "6swiTCWtSwqi8sm9wzNwKA9NEpJWbXjLcVz654u7zz4W"
P4 = "5gZTf2A6UPeYZCq1mkdiYquMQqmjNcz9pknbABkWif9c"
P5 = "5TdRYVo7We7hYSXDS3ryvUvouL7hoaMLTGMRqMrzBhcE"
U5 = "79cu2QNvp92chEmBhBgcUfERDT9KHnUcr8eiJb5WzKML"
# Token-role keys are recovered from the receipts themselves: the
# builder's TOKEN_ROLES deltas are recomputed from snapshots, and
# the headline asserts below use only pool / config / UVA / GVA /
# payer / outsider keys plus decoded events, so no full role table
# is needed here.

BST_DISC = "3f451c16305cc2b9"
MHBUY_DISC = "67f4521f2cf57777"
MHSELL_DISC = "3e2f370aa503dc2a"
SWP_DISC = "82a42461e48287a5"
SETR_DISC = "2bbcfa12dd4bbb5f"
COL_DISC = "e8f5c2eeeada3a59"


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def u64(raw, off):
    return struct.unpack_from("<Q", raw, off)[0]


def tok_amount(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return struct.unpack_from("<Q", raw, 64)[0] if len(raw) >= 72 else None


def tok_delta(rec, key):
    b, a = rec["before"].get(str(key)), rec["after"].get(str(key))
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
    b, a = rec["before"].get(str(key)), rec["after"].get(str(key))
    return (wh_of(a) or 0) - (wh_of(b) or 0)


def lam_delta(rec, key):
    b, a = rec["before"].get(str(key)), rec["after"].get(str(key))
    return (a["lamports"] if a else 0) - (b["lamports"] if b else 0)


def pool_state(entry):
    if entry is None:
        return None
    d = bytes.fromhex(entry["data_hex"])
    if len(d) < 287:
        return {"len": len(d)}
    return [int.from_bytes(d[245:261], "little", signed=True),
            struct.unpack_from("<Q", d, 271)[0],
            struct.unpack_from("<Q", d, 279)[0],
            struct.unpack_from("<Q", d, 203)[0]]


def cfg_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 949:
        return {"len": len(raw)}
    return {"disable": raw[56], "lp": u64(raw, 40), "proto": u64(raw, 48),
            "recipients": [raw[57 + i * 32:57 + (i + 1) * 32].hex() for i in range(8)],
            "creator_fee": u64(raw, 313), "fee_auth": raw[321:353].hex(),
            "bps": u64(raw, 899),
            "bb_recipients": [raw[643 + i * 32:643 + (i + 1) * 32].hex() for i in range(8)],
            "mayhem": raw[417], "cashback": raw[642],
            "boost_auth": raw[907:939].hex(), "boost_enabled": raw[939],
            "cfgable": raw[940], "maxcf": u64(raw, 941)}


def uva_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 90:
        return {"len": len(raw)}
    needs, unc, cla, vol, last, hasc, earn, cbcl = struct.unpack_from('<BQQQqBQQ', raw, 40)
    return {"needs": needs, "unclaimed": unc, "claimed": cla, "volume": vol,
            "last": last, "has": hasc, "earned": earn, "cb_claimed": cbcl}


def gva_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 64:
        return {"len": len(raw)}
    sup = [struct.unpack_from("<Q", raw, 64 + i * 8)[0] for i in range(30)] if len(raw) >= 304 else None
    vol = [struct.unpack_from("<Q", raw, 304 + i * 8)[0] for i in range(30)] if len(raw) >= 544 else None
    return {"len": len(raw),
            "start": struct.unpack_from("<q", raw, 8)[0],
            "end": struct.unpack_from("<q", raw, 16)[0],
            "sec": struct.unpack_from("<q", raw, 24)[0],
            "mint": raw[32:64].hex(),
            "supply": sup, "vol": vol}


def mint_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 278:
        return {"len": len(raw)}
    return {"oe": struct.unpack_from("<Q", raw, 242)[0],
            "omax": struct.unpack_from("<Q", raw, 250)[0],
            "ob": struct.unpack_from("<H", raw, 258)[0],
            "ne": struct.unpack_from("<Q", raw, 260)[0],
            "nmax": struct.unpack_from("<Q", raw, 268)[0],
            "nb": struct.unpack_from("<H", raw, 276)[0],
            "wh": u64(raw, 234) if len(raw) >= 242 else None}


def acct_len(entry):
    return None if entry is None else len(bytes.fromhex(entry["data_hex"]))


def ev_list(logs):
    out = []
    for l in logs:
        if l.startswith("Program data: "):
            out.append(base64.b64decode(l.split("Program data: ", 1)[1].strip()))
    return out


def decode_event(kind, raw):
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind == "boost":
        if raw[:8].hex() != BST_DISC:
            return {"disc": raw[:8].hex(), "len": len(raw)}
        return {"disc": raw[:8].hex(), "len": len(raw),
                "requested": u64(raw, 144), "used": u64(raw, 152),
                "burned": u64(raw, 160),
                "vq": int.from_bytes(raw[168:184], "little", signed=True),
                "quote_after": u64(raw, 184), "base_after": u64(raw, 192),
                "remaining": u64(raw, 200)}
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
    if kind in ("dep", "wd"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 72), "quote": u64(raw, 80)}
    if kind == "extend":
        return {"disc": raw[:8].hex(),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "account": raw[16:48].hex(), "user": raw[48:80].hex(),
                "old": u64(raw, 80), "new": u64(raw, 88), "len": len(raw)}
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
    if kind == "sync":
        return {"disc": raw[:8].hex(), "user": raw[8:40].hex(),
                "before": u64(raw, 40), "after": u64(raw, 48),
                "ts": struct.unpack_from("<q", raw, 56)[0], "len": len(raw)}
    if kind == "admin":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "start": struct.unpack_from("<q", raw, 8)[0],
                "end": struct.unpack_from("<q", raw, 16)[0],
                "day": u64(raw, 24), "supply": u64(raw, 32),
                "mint": raw[40:72].hex(),
                "sec": struct.unpack_from("<q", raw, 72)[0],
                "timestamp": struct.unpack_from("<q", raw, 80)[0]}
    if kind in ("close", "close_other", "close_unsigned"):
        return {"disc": raw[:8].hex(), "user": raw[8:40].hex(),
                "ts": struct.unpack_from("<q", raw, 40)[0],
                "unc": u64(raw, 48), "claimed": u64(raw, 56),
                "vol": u64(raw, 64), "last": struct.unpack_from("<q", raw, 72)[0],
                "len": len(raw)}
    if kind == "init":
        return {"disc": raw[:8].hex(), "payer": raw[8:40].hex(),
                "user": raw[40:72].hex(),
                "ts": struct.unpack_from("<q", raw, 72)[0], "len": len(raw)}
    if kind == "setr":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "first": raw[16:48].hex(),
                "rest": [raw[48 + i * 32:48 + (i + 1) * 32].hex() for i in range(7)]}
    if kind == "set":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "creator": raw[112:144].hex()}
    if kind == "mig":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "old": raw[112:144].hex(), "new": raw[144:176].hex()}
    if kind == "buy2":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "curve": u64(raw, 64), "lp_bps": u64(raw, 72),
                "lp_fee": u64(raw, 80), "proto_bps": u64(raw, 88),
                "proto_fee": u64(raw, 96), "qwlp": u64(raw, 104),
                "uin": u64(raw, 112)}
    if kind == "sell2":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "curve": u64(raw, 64), "lp_bps": u64(raw, 72),
                "lp_fee": u64(raw, 80), "proto_bps": u64(raw, 88),
                "proto_fee": u64(raw, 96), "quote": u64(raw, 104),
                "uout": u64(raw, 112)}
    return None


STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "boost": "boost",
             "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
             "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
             "swp": "swp", "swc": "swc", "col": "col",
                "boost2": "boost", "boost2o": "boost", "boost3s": "boost", "boost3o": "boost",
                "boost2x": "boost", "boost3x": "boost", "boostx": "boost", "boosto": "boost",
                "boostauth": None, "initb": None, "ucfc": None, "legbuy": None, "buy2": None, "legs": None,
             "xfer2": None, "xfer1": None, "cpatch": None,
             "admin": "admin", "close": "close", "close_other": "close", "close_unsigned": "close", "init": "init",
             "ww": None, "harvest": None, "wfm": None,
             "buy2m": "buy2", "sell2m": "sell2", "lexact": None, "bexact2": None,
             "set": "set", "mig": "mig",
             "setr": "setr", "legbuy_res": None, "legsell_res": None,
             "set2": "set", "mig2": "mig", "set3": "set", "mig3": "mig",
             "dep2": "dep", "wd2": "wd", "dep3": "dep", "wd3": "wd",
             "dep4": "dep", "wd4": "wd", "dep5": "dep", "wd5": "wd",
             "boost4s": "boost", "boost5s": "boost",
             "swc2c": "swc", "col2c": "col", "swc3c": "swc", "col3c": "col",
             "swcsh": "swc", "colsh": "col",
             "swc2sh": "swc", "col2sh": "col", "swc3sh": "swc", "col3sh": "col"}


def res_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 642:
        return {"len": len(raw)}
    return {"wl": raw[353:385].hex(), "res0": raw[385:417].hex(),
            "res": [raw[418 + i * 32:418 + (i + 1) * 32].hex() for i in range(7)]}


def recompute(rec):
    sys.path.insert(0, str(HERE))
    import producer
    ROLE_KEY = producer.ROLE_KEY
    TOKEN_ROLES = producer.TOKEN_ROLES
    kind = rec["step"]
    raws = ev_list(rec["logs"])
    dk = STEP_KIND.get(kind)
    decoded = None
    if dk is not None:
        decoded = [decode_event(dk, raw) for raw in raws]
    if kind == "boost" and raws:
        decoded = [decode_event("boost", raw) for raw in raws]
    if kind == "cpatch":
        decoded = []
    after = rec["after"]
    # Token/withheld/lamport deltas use the producer's role table
    # (address constants only); all values are recomputed from the
    # receipt snapshots here.
    return {"step": kind, "error": rec["error"], "events": len(rec["events"]),
            "decoded": decoded,
            "dPAYER": lam_delta(rec, PAYER), "dOUT": lam_delta(rec, OUTSIDER),
            "pools": {name: pool_state(after[key]) for name, key in
                      (("main", POOL), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5))},
            "cfbps": {name: (struct.unpack_from("<Q", bytes.fromhex(after[key]["data_hex"]), 261)[0]
                             if after.get(key) and len(bytes.fromhex(after[key]["data_hex"])) >= 269 else None)
                      for name, key in (("main", POOL), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5))},
            "pool_creator": bytes.fromhex(after[POOL]["data_hex"])[211:243].hex() if after.get(POOL) else None,
            "cfg": cfg_fields(after.get(CONFIG)),
            "rescfg": res_fields(after.get(CONFIG)),
            "uva": uva_fields(after.get(VOLUME)),
            "gva": gva_fields(after.get(GVOL)),
            "mint": mint_fields(after.get(QUOTE)),
            "lens": {"pool": acct_len(after.get(POOL)), "cfg": acct_len(after.get(CONFIG)),
                     "uva": acct_len(after.get(VOLUME)), "gva": acct_len(after.get(GVOL)),
                     "fee": acct_len(after.get(FEECONFIG)), "extacc": acct_len(after.get(EXTKEY))},
            "site": rec["site"],
            "deltas": {role: tok_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if tok_delta(rec, ROLE_KEY[role]) != 0},
            "withheld": {role: wh_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if wh_delta(rec, ROLE_KEY[role]) != 0},
            "lam_deltas": {role: lam_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if lam_delta(rec, ROLE_KEY[role]) != 0}}


def main():
    from solders.transaction import Transaction
    manifest = json.loads((HERE / "MANIFEST.json").read_text())
    listed = {f["path"]: f for f in manifest["files"]}
    actual = {}
    for p in sorted(HERE.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json" and ".git" not in p.parts:
            rel = str(p.relative_to(HERE))
            actual[rel] = {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
    check(set(listed) == set(actual),
          f"manifest file set mismatch: missing={set(actual) - set(listed)} extra={set(listed) - set(actual)}")
    for rel, f in listed.items():
        check(f["sha256"] == actual[rel]["sha256"] and f["bytes"] == actual[rel]["bytes"],
              f"manifest mismatch for {rel}")
    report = json.loads(gzip.open(HERE / "runtime" / "report.json.gz", "rt").read())
    check(report["case_count"] == 71, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 71, "receipts": 684, "parts": 69},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 684, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 684, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 71 * 3, f"groups {len(grouped)}")
    for case in report["cases"]:
        for image in ("original", "control", "candidate"):
            recs = grouped[(case["label"], image)]
            check([r["step"] for r in recs] == case["steps"],
                  f"{case['label']}/{image}: steps {[r['step'] for r in recs]} != {case['steps']}")
            sums = case["summaries"][image]
            check(len(sums) == len(recs), f"{case['label']}/{image}: summary count")
            for rec, s in zip(recs, sums):
                got = recompute(rec)
                for field in ("step", "error", "events", "decoded", "dPAYER", "dOUT",
                              "deltas", "withheld", "lam_deltas",
                              "pools", "cfbps", "pool_creator", "cfg", "rescfg", "uva", "gva", "mint", "lens", "site"):
                    check(got[field] == s[field],
                          f"{case['label']}/{image}/{rec['step']}: {field} {got[field]} != {s[field]}")
                # Role-address tables come from the packet's own
                # producer (constants only); every delta above is
                # recomputed from the receipt snapshots here.
                if rec["step"] == "cpatch":
                    check(rec["transaction_base64"] == "", "cpatch must carry an empty transaction")
                    check(rec["error"] is None, "cpatch must succeed")
                else:
                    tx = Transaction.from_bytes(base64.b64decode(rec["transaction_base64"]))
                    check(tx.verify_with_results() and all(tx.verify_with_results()),
                          f"{case['label']}/{image}/{rec['step']}: bad signature")
                if rec["error"] is not None:
                    signers = set()
                    if rec["transaction_base64"]:
                        tx = Transaction.from_bytes(base64.b64decode(rec["transaction_base64"]))
                        for i, k in enumerate(tx.message.account_keys):
                            if tx.message.is_signer(i):
                                signers.add(str(k))
                    for k, b in rec["before"].items():
                        a = rec["after"][k]
                        if b is None or a is None:
                            check(b == a, f"{case['label']}/{image}/{rec['step']}: rollback absent mismatch {k}")
                            continue
                        check(a["data_hex"] == b["data_hex"],
                              f"{case['label']}/{image}/{rec['step']}: rollback data mismatch {k}")
                        if a["lamports"] != b["lamports"]:
                            check(k in signers,
                                  f"{case['label']}/{image}/{rec['step']}: non-signer lamport change {k}")
            # cpatch chain consistency
            for i, rec in enumerate(recs):
                if rec["step"] == "cpatch" and i + 1 < len(recs):
                    check(recs[i + 1]["before"] == rec["after"],
                          f"{case['label']}/{image}: cpatch does not carry into next step")
        # 3-image surface agreement (fee-payer lamports stripped per receipt)
        def surface(image):
            out = []
            for rec in grouped[(case["label"], image)]:
                def strip(snap):
                    d = dict(snap)
                    if rec["transaction_base64"]:
                        tx = Transaction.from_bytes(base64.b64decode(rec["transaction_base64"]))
                        fp = str(tx.message.account_keys[0])
                        if d.get(fp) is not None:
                            d[fp] = dict(d[fp])
                            d[fp]["lamports"] = 0
                    return d
                out.append({"step": rec["step"], "error": rec["error"],
                            "events": len(rec["events"]),
                            "before": strip(rec["before"]), "after": strip(rec["after"])})
            return out
        check(surface("control") == surface("candidate"),
              f"{case['label']}: control != candidate")
        if not case["divergent"]:
            check(surface("original") == surface("control"),
                  f"{case['label']}: original diverges but not marked divergent")
    expected_divergent = set()
    got_divergent = {c["label"] for c in report["cases"] if c["divergent"]}
    check(got_divergent == expected_divergent,
          f"divergent set mismatch: extra={got_divergent - expected_divergent} missing={expected_divergent - got_divergent}")
    # Image hashes when the images are present at workspace paths.
    ws = HERE.parent.parent.parent
    for name, path in (("original", ws / "evidence" / "original" / "pump_amm" / "deployed.so"),
                       ("control", ws / "slop-verify" / "control.so"),
                       ("candidate", ws / "slop-verify" / "candidate.so")):
        if path.exists():
            check(sha(path.read_bytes()) == report["input_sha256"][name], f"image hash {name}")

    # Headline pins.
    def get(label, image, idx):
        case = next(c for c in report["cases"] if c["label"] == label)
        return case["summaries"][image][idx]

    def x(label, idx):
        return get(label, "original", idx)

    def err(label, image, idx):
        return str(get(label, image, idx)["error"])

    def burn(label, idx):
        for d in (x(label, idx)["decoded"] or []):
            if d and "burned" in d:
                return d["burned"]
        return None

    def hburn(label, idx):
        return burn(label, idx)

    # A: anchors and bare legs at depth 5.
    check(burn("A-boost", 1) == 5338379201831, "fresh patched-window main boost burn")
    check(burn("A-buy-boost", 2) == 5254679949141, "buy-then-boost burn")
    check(burn("A-sell-boost", 2) == 5338394848076, "sell-then-boost burn")
    check(x("A-buy5", 0)["deltas"]["u5"] == 5207955235891, "5-hop buy tail anchor")
    check(x("A-buy5", 0)["events"] == 5 and [d["len"] for d in x("A-buy5", 0)["decoded"]] == [508] * 5,
          "5-hop buy emits exactly 5 hop events (true 5-hop route)")
    check(x("A-sell5", 0)["deltas"]["userquote"] == 178541, "5-hop sell payout anchor")
    check(x("A-sell5", 0)["events"] == 5 and [d["len"] for d in x("A-sell5", 0)["decoded"]] == [449] * 5,
          "5-hop sell emits exactly 5 hop events (true 5-hop route)")
    d = x("A-dep", 0)["deltas"]
    check(d == {"userbase": -160619896, "userquote": -29610, "userlp": 1000000, "vb1": 160619896, "vq1": 29313}, f"deposit 10^6 leg deltas {d}")
    check(x("A-dep", 0)["withheld"] == {"vq1": 297}, "deposit quote leg withholds 297 in the vault")
    check(x("A-dep", 0)["pools"]["main"] == [-125882, 2488, 123394, 4194353106721], "deposit without a vq patch leaves the vq field untouched (can_boost false)")
    d = x("A-wd", 0)["deltas"]
    check(d == {"userbase": 160619895, "userquote": 29018, "userlp": -1000000, "vb1": -160619895, "vq1": -29312}, f"withdraw 10^6 leg deltas {d}")
    check(x("A-wd", 0)["withheld"] == {"userquote": 294}, "withdraw leaves 294 withheld in the user quote account")
    check(x("A-dep-wd", 1)["pools"]["main"] == [-125882, 2488, 123394, 4194352106721], "deposit then withdraw restores supply and vq exactly")
    # B: main-pool deposit ladder and walks at depth 5.
    check(x("B-dep1m-boost", 1)["pools"]["main"][0] == 1000000238 and burn("B-dep1m-boost", 2) == 5338379211910, "deposit 10^6: vq +238, burn anchor +10079")
    check(x("B-dep1b-boost", 1)["pools"]["main"][0] == 1000238445 and burn("B-dep1b-boost", 2) == 5338389284765, "deposit 10^9: vq +238445, burn anchor +10082934")
    check(x("B-dep1t-boost", 1)["pools"]["main"][0] == 1238445856 and burn("B-dep1t-boost", 2) == 5346535371563, "deposit 10^12: vq +238445856, burn anchor +8156169732")
    check(burn("B-dep-boost-boost", 3) == 5254441578883, "second burn after a deposit is the decay burn +29618")
    check(burn("B-boost-dep-boost", 3) == 5254441559109, "deposit after a boost costs less base and the second burn follows")
    check(burn("B-buy-dep-boost", 3) == 5254679958982, "deposit after a buy lifts the post-buy burn by 9841")
    check(x("B-dep-buy", 1)["deltas"]["u5"] == 5207955245488, "deposit before a 5-hop buy lifts the tail by 9597 (3-hop lift was 9801)")
    check(burn("B-dep-buy-boost", 3) == 5254679988636, "deposit, buy, boost is the post-buy burn +39495")
    check(x("B-dep-sell", 1)["deltas"]["userquote"] == 178541, "deposit before a 5-hop sell leaves the payout byte-identical at 178541")
    check(burn("B-sell-dep-boost", 3) == 5338394858154, "deposit after a sell lifts the post-sell burn by 10078")
    check(burn("B-dep-swp-boost", 3) == 5338379328388, "deposit, protocol sweep, boost is anchor +126557")
    # C: withdraw ladder and round trips at depth 5.
    check(x("C-wd1m-boost", 1)["pools"]["main"][0] == 999999761 and burn("C-wd1m-boost", 2) == 5338379191752, "withdraw 10^6: vq -239 (ceil), burn anchor -10079")
    check(x("C-wd1b-boost", 1)["pools"]["main"][0] == 999761554 and burn("C-wd1b-boost", 2) == 5338369114126, "withdraw 10^9: vq -238446, burn anchor -10087705")
    check(burn("C-buy-wd-boost", 3) == 5254679939300, "withdraw after a buy cuts the post-buy burn by 9841")
    check(burn("C-sell-wd-boost", 3) == 5338394837999, "withdraw after a sell cuts the post-sell burn by 10077")
    check(x("C-dep-wd-boost", 2)["pools"]["main"][0] == 999999999 and burn("C-dep-wd-boost", 3) == 5338379201831, "deposit-withdraw round trip leaves vq -1 but the burn byte-identical to the anchor")
    check(x("C-wd-dep-boost", 2)["pools"]["main"][0] == 999999999 and burn("C-wd-dep-boost", 3) == 5338379201831, "withdraw-deposit round trip is the same -1 vq with the anchor burn")
    check(x("C-dep-wd-dep-boost", 3)["pools"]["main"][0] == 1000000237 and burn("C-dep-wd-dep-boost", 4) == 5338379211910, "deposit-withdraw-deposit lands 1 vq below the single-deposit value with the identical burn")
    check(burn("C-wd-swp-boost", 3) == 5338379287848, "withdraw, protocol sweep, boost is anchor +86017")
    # D: gates at depth 5.
    for _lbl in ("D-dep-slip-base", "D-dep-slip-quote", "D-wd-slip-base", "D-wd-slip-quote"):
        check("6004" in err(_lbl, "original", 0) and burn(_lbl, 2) == 5338379201831, f"{_lbl}: slippage gate 6004, following boost is the anchor burn")
    check(x("D-dep-zero", 0)["events"] == 1 and x("D-dep-zero", 0)["deltas"] == {} and burn("D-dep-zero", 2) == 5338379201831, "zero deposit succeeds as a 1-event no-op")
    check(x("D-wd-zero", 0)["events"] == 1 and x("D-wd-zero", 0)["deltas"] == {} and burn("D-wd-zero", 2) == 5338379201831, "zero withdraw succeeds as a 1-event no-op")
    check("6018" in err("D-dep-disable-boost", "original", 0) and burn("D-dep-disable-boost", 2) == 5338379201831, "deposit under the deposit bit fails 6018, following boost is the anchor burn")
    check("6019" in err("D-wd-disable-boost", "original", 0) and burn("D-wd-disable-boost", 2) == 5338379201831, "withdraw under the withdraw bit fails 6019, following boost is the anchor burn")
    check("6018" in err("D-dep-disable-clear-boost", "original", 0) and x("D-dep-disable-clear-boost", 2)["deltas"]["userlp"] == 1000000 and burn("D-dep-disable-clear-boost", 4) == 5338379222079, "clearing the bit restores the deposit and the vault-only +20248 burn")
    # E: hop pools at depth 5.
    for _lbl, _idx in (("E-dep2-boost", 1), ("E-dep2-1b-boost", 1), ("E-dep3-boost", 1),
                       ("E-dep4-boost", 1), ("E-dep4-1b-boost", 1), ("E-dep5-boost", 1),
                       ("F-dep2-fail-tf5000", 1), ("F-dep4-fail-tf5000", 1), ("F-dep5-fail-tf5000", 1)):
        for _img in ("original", "control", "candidate"):
            e = err(_lbl, _img, _idx)
            check("Custom(4)" in e and "6004" not in e, f"{_lbl}/{_img}: hop deposit fails Token-2022 OwnerMismatch (4), not a pump slippage code")
    check(hburn("E-dep2-boost", 2) == 999997999 and hburn("E-dep2-1b-boost", 2) == 999997999 and hburn("E-dep3-boost", 2) == 999997999
          and hburn("E-dep4-boost", 2) == 999997999 and hburn("E-dep4-1b-boost", 2) == 999997999 and hburn("E-dep5-boost", 2) == 999997999,
          "hop boost after a failed hop deposit is the anchor hop burn on every hop pool")
    check(x("E-dep2-mhbuy", 1)["deltas"]["u5"] == 5207955235891 and x("E-dep4-mhbuy", 1)["deltas"]["u5"] == 5207955235891
          and x("E-dep5-mhbuy", 1)["deltas"]["u5"] == 5207955235891, "failed hop deposit leaves the 5-hop tail at the anchor")
    check(hburn("E-mhbuy-dep2-boost", 3) == 989418199 and hburn("E-mhbuy-dep4-boost", 3) == 989528958 and hburn("E-mhbuy-dep5-boost", 3) == 989596358,
          "hop boost after buy and failed hop deposit is the post-buy hop burn per hop")
    d = x("E-wd2-boost", 1)["deltas"]
    check(d == {"userbase": 238415844, "userlp": -1000000, "vb2": -238415844, "vq2": -238415844, "ubase2": 238415844}, f"hop withdraw 10^6 leg deltas {d}")
    check(x("E-wd2-boost", 1)["pools"]["pool2"][0] == 999999761 and hburn("E-wd2-boost", 2) == 999997999, "hop withdraw moves the hop vq by -239 but the hop burn stays byte-identical")
    d = x("E-wd4-boost", 1)["deltas"]
    check(d == {"userlp": -1000000, "vb4": -238415844, "vq4": -238415844, "ubase3": 238415844, "ubase4": 238415844}, f"P4 withdraw 10^6 leg deltas {d}")
    check(x("E-wd4-boost", 1)["pools"]["p4"][0] == 999999761 and hburn("E-wd4-boost", 2) == 999997999, "P4 withdraw moves the P4 vq by -239 but the P4 boost stays byte-identical")
    d = x("E-wd5-boost", 1)["deltas"]
    check(d == {"userlp": -1000000, "vb5": -238415844, "vq5": -238415844, "ubase4": 238415844, "ubase5": 238415844}, f"P5 withdraw 10^6 leg deltas {d}")
    check(x("E-wd5-boost", 1)["pools"]["p5"][0] == 999999761 and hburn("E-wd5-boost", 2) == 999997999, "P5 withdraw moves the P5 vq by -239 but the P5 boost stays byte-identical")
    d = x("E-dep2-auth-boost", 2)["deltas"]
    check(d == {"userbase": -238415845, "userlp": 1000000, "vb2": 238415845, "vq2": 238415845, "ubase2": -238415845}, f"authority-patched hop deposit leg deltas {d}")
    check(x("E-dep2-auth-boost", 2)["pools"]["pool2"][0] == 1000000238 and hburn("E-dep2-auth-boost", 3) == 999997999, "patched hop deposit moves the hop vq by +238 yet the hop burn stays byte-identical")
    d = x("E-dep3-auth-boost", 2)["deltas"]
    check(d == {"userlp": 1000000, "vb3": 238415845, "vq3": 238415845, "ubase2": -238415845, "ubase3": -238415845}, f"authority-patched P3 deposit leg deltas {d}")
    check(x("E-dep3-auth-boost", 2)["pools"]["p3"][0] == 1000000238 and hburn("E-dep3-auth-boost", 3) == 999997999, "patched P3 deposit moves the P3 vq by +238 yet the P3 boost stays byte-identical")
    d = x("E-dep4-auth-boost", 2)["deltas"]
    check(d == {"userlp": 1000000, "vb4": 238415845, "vq4": 238415845, "ubase3": -238415845, "ubase4": -238415845}, f"authority-patched P4 deposit leg deltas {d}")
    check(x("E-dep4-auth-boost", 2)["pools"]["p4"][0] == 1000000238 and hburn("E-dep4-auth-boost", 3) == 999997999, "patched P4 deposit moves the P4 vq by +238 yet the P4 boost stays byte-identical")
    d = x("E-dep5-auth-boost", 2)["deltas"]
    check(d == {"userlp": 1000000, "vb5": 238415845, "vq5": 238415845, "ubase4": -238415845, "ubase5": -238415845}, f"authority-patched P5 deposit leg deltas {d}")
    check(x("E-dep5-auth-boost", 2)["pools"]["p5"][0] == 1000000238 and hburn("E-dep5-auth-boost", 3) == 999997999, "patched P5 deposit moves the P5 vq by +238 yet the P5 boost stays byte-identical")
    check(x("E-dep2-auth-wd2-boost", 3)["pools"]["pool2"][0] == 999999999 and hburn("E-dep2-auth-wd2-boost", 4) == 999997999, "patched hop deposit-withdraw round trip leaves hop vq -1 with the anchor hop burn")
    check(x("E-dep4-auth-wd4-boost", 3)["pools"]["p4"][0] == 999999999 and hburn("E-dep4-auth-wd4-boost", 4) == 999997999, "patched P4 deposit-withdraw round trip leaves P4 vq -1 with the anchor hop burn")
    check(x("E-dep5-auth-wd5-boost", 3)["pools"]["p5"][0] == 999999999 and hburn("E-dep5-auth-wd5-boost", 4) == 999997999, "patched P5 deposit-withdraw round trip leaves P5 vq -1 with the anchor hop burn")
    check(x("E-dep2-auth-mhbuy", 2)["deltas"]["u5"] == 5207955242373, "patched P2 deposit lifts the 5-hop tail by 6482")
    check(x("E-dep4-auth-mhbuy", 2)["deltas"]["u5"] == 5207955242373, "patched P4 deposit lifts the 5-hop tail by 6482")
    check(x("E-dep5-auth-mhbuy", 2)["deltas"]["u5"] == 5207955242357, "patched P5 deposit lifts the 5-hop tail by 6466")
    # F: tf variants at depth 5.
    check(x("F-dep-boost-tf5000", 1)["deltas"]["userquote"] == -58626 and x("F-dep-boost-tf5000", 1)["withheld"] == {"vq1": 29313} and burn("F-dep-boost-tf5000", 2) == 2706767015328, "tf5000 deposit grosses the quote leg to 58626 (29313 + 29313 withheld)")
    check(x("F-wd-boost-tf5000", 1)["deltas"]["userquote"] == 14656 and burn("F-wd-boost-tf5000", 2) == 2706767010148, "tf5000 withdraw pays 14656 net and the tf5000 burn follows")
    check(x("F-dep-boost-tf0", 1)["deltas"]["userquote"] == -29313 and x("F-dep-boost-tf0", 1)["withheld"] == {} and burn("F-dep-boost-tf0", 2) == 5391870666177, "tf0 deposit pays 29313 flat and the tf0 burn is anchor +10282")
    check(x("F-dep-buy-tf5000", 1)["deltas"]["u5"] == 2668075751246, "tf5000 5-hop buy tail after a deposit")
    print("PASS: 71 cases, 684 receipts, 69 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, deposit/withdraw vq ladder and burn ladder at depth 5, round-trip -1 vq with anchor burn, deposit-before-buy tail lift +9597 and deposit-before-sell payout unchanged, slippage 6004, zero-amount no-ops, disable 6018/6019, hop deposit Token-2022 OwnerMismatch (4) on P2/P3/P4/P5 and authority-patch recovery with byte-identical hop burns, patched hop deposit tail lifts +6482/+6466, tf5000 gross-up and tf0 flat legs); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
