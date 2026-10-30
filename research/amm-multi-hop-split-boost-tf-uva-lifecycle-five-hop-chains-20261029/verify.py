#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-uva-lifecycle-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 37 cases, 318 receipts, 32 parts
  (31x10 + 8), part sha256/byte counts match the part files.
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
  event, sweep 185-byte fields, close 80-byte fields, init 80-byte
  fields, claim 104-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the UVA lifecycle behaviour at
  depth 5 agrees on all three images).
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events; claim-then-close refunds the full
  999995000 while the 500 unclaimed tokens exist only in the
  CloseEvent; post-close token claim, sync, second close and
  cashback claim all fail 3012 at fee-only cost; re-init builds a
  fresh 137-byte zero account at 1849400 and the following token
  claim is a 0-event zero claim stamping last 0 to 21; init on an
  already-seeded account succeeds as a 1-event fee-only step with
  fields untouched; extend 90 to 137 preserves every field with an
  exact 332120 top-up and the following claim pays only the 500
  unclaimed; extend at 137 and 138 are silent no-ops; extend 50 to
  137 rewrites the truncated layout (claimed 700 to low byte 188)
  and the following claim pays 500 to 688; close-then-extend fails
  2004; close binds to the PDA seeds (other signer 2006, unsigned
  user 3010); extend authorization mirrors it (unsigned 3010,
  read-only 2000, second extend a no-op); the lifecycle moves
  nothing on the chain (buy-close-reinit-buy reproduces the
  uninterrupted second buy tail 4918089082874 exactly, likewise
  buy-boost-close-reinit-buy-boost with second burn 5093171141582,
  the fee-table second buy 4957670972204, and the tf5000 / tf0 /
  plain second buys 2590950921881 / 4963540456839 /
  4963540456839); a buy after a close re-creates the empty UVA at
  rent cost (payer -1849400) with the anchor tail, and the
  following claim is a 0-event zero claim.
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
    check(report["case_count"] == 37, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 37, "receipts": 318, "parts": 32},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 318, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 318, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 37 * 3, f"groups {len(grouped)}")
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

    def uva(label, idx):
        return x(label, idx)["uva"]

    SEED = {"needs": 1, "unclaimed": 111, "claimed": 222, "volume": 333444, "last": 20, "has": 1, "earned": 555, "cb_claimed": 666}
    ZERO = {"needs": 0, "unclaimed": 0, "claimed": 0, "volume": 0, "last": 0, "has": 0, "earned": 0, "cb_claimed": 0}
    CLAIMED = {"needs": 0, "unclaimed": 0, "claimed": 3334773, "volume": 0, "last": 21, "has": 1, "earned": 555, "cb_claimed": 666}
    SEED500 = {"needs": 1, "unclaimed": 500, "claimed": 700, "volume": 20, "last": 10, "has": 1, "earned": 55, "cb_claimed": 13}

    # A: claim-close-reinit at depth 5.
    check(x("A-tclaim-close-reinit-tclaim-swc-col", 0)["deltas"] == {"gata": -3334551, "uata": 3334551}
          and uva("A-tclaim-close-reinit-tclaim-swc-col", 0) == CLAIMED,
          "seeded token claim pays 3334551 at depth 5")
    check(x("A-tclaim-close-reinit-tclaim-swc-col", 1)["dPAYER"] == 999995000
          and uva("A-tclaim-close-reinit-tclaim-swc-col", 1) is None
          and [d["disc"] for d in x("A-tclaim-close-reinit-tclaim-swc-col", 1)["decoded"]] == ["929fbdac925838f4"],
          "claim-then-close refunds the full 999995000 and the account is gone")
    check(x("A-tclaim-close-reinit-tclaim-swc-col", 2)["dPAYER"] == -1849400
          and uva("A-tclaim-close-reinit-tclaim-swc-col", 2) == ZERO
          and x("A-tclaim-close-reinit-tclaim-swc-col", 2)["lens"]["uva"] == 137,
          "re-init builds a fresh 137-byte zero account at 1849400")
    check(x("A-tclaim-close-reinit-tclaim-swc-col", 3)["events"] == 0
          and x("A-tclaim-close-reinit-tclaim-swc-col", 3)["dPAYER"] == -5000
          and uva("A-tclaim-close-reinit-tclaim-swc-col", 3) == dict(ZERO, last=21),
          "token claim on the fresh account is a 0-event zero claim stamping last 0 to 21")
    check(x("A-tclaim-close-reinit-tclaim-swc-col", 4)["deltas"] == {"vq1": -123394, "creat22": 122160}
          and x("A-tclaim-close-reinit-tclaim-swc-col", 5)["deltas"] == {"creat22": -122160, "dest22": 120938},
          "sweep/collect after re-init drain the full creator bucket 123394")
    check(x("A-close-500", 0)["dPAYER"] == 999995000
          and x("A-close-500", 0)["deltas"] == {}
          and uva("A-close-500", 0) is None,
          "close of the 500-unclaimed seed refunds 999995000 with zero token deltas (the 500 exist only in the CloseEvent)")
    for lbl, step in (("A-tclaim-close-tclaim", 2), ("A-tclaim-close-sync", 2),
                      ("A-tclaim-close-close", 2), ("A-tclaim-close-cclaim-plain", 2)):
        check("Custom(3012)" in err(lbl, "original", step)
              and x(lbl, step)["dPAYER"] == -5000 and x(lbl, step)["events"] == 0
              and uva(lbl, step) is None,
              f"post-close step fails 3012 at fee-only cost: {lbl}")
    check("Custom(2006)" in err("A-close-other", "original", 0)
          and x("A-close-other", 0)["dPAYER"] == 0 and x("A-close-other", 0)["dOUT"] == -5000
          and uva("A-close-other", 0) == SEED,
          "close by another signer fails 2006 ConstraintSeeds (outsider pays only the fee)")
    check("Custom(3010)" in err("A-close-unsigned", "original", 0)
          and x("A-close-unsigned", 0)["dPAYER"] == 0 and x("A-close-unsigned", 0)["dOUT"] == -5000
          and uva("A-close-unsigned", 0) == SEED,
          "close with an unsigned user fails 3010 (outsider pays only the fee)")
    check(x("A-init-seeded", 0)["events"] == 1 and x("A-init-seeded", 0)["dPAYER"] == -5000
          and uva("A-init-seeded", 0) == SEED,
          "init on an already-seeded account succeeds as a 1-event fee-only step with fields untouched")
    check(x("A-init-absent", 0)["dPAYER"] == -1849400
          and uva("A-init-absent", 0) == ZERO and x("A-init-absent", 0)["lens"]["uva"] == 137,
          "init on an absent account builds the fresh 137-byte zero account at 1849400")
    check(x("A-init-absent-tclaim", 1)["events"] == 0
          and uva("A-init-absent-tclaim", 1) == dict(ZERO, last=21),
          "token claim after a fresh init is a 0-event zero claim stamping last 0 to 21")
    check(x("A-init-close-init", 0)["dPAYER"] == -1849400
          and x("A-init-close-init", 1)["dPAYER"] == 1839400
          and x("A-init-close-init", 2)["dPAYER"] == -1849400
          and uva("A-init-close-init", 2) == ZERO,
          "init-close-init: close refunds 1839400 and the second init rebuilds the fresh account")
    # B: extend chains at depth 5.
    check(x("B-extend90-tclaim-close", 0)["dPAYER"] == -332120
          and uva("B-extend90-tclaim-close", 0) == SEED500
          and x("B-extend90-tclaim-close", 0)["lens"]["uva"] == 137,
          "extend 90 to 137 preserves every field with an exact 332120 top-up")
    check(x("B-extend90-tclaim-close", 1)["deltas"] == {"gata": -500, "uata": 500}
          and uva("B-extend90-tclaim-close", 1) == {"needs": 1, "unclaimed": 0, "claimed": 1200, "volume": 20, "last": 21, "has": 1, "earned": 55, "cb_claimed": 13},
          "the claim after extend90 pays only the 500 unclaimed (pre-start: volume 20 stays)")
    check(x("B-extend90-tclaim-close", 2)["dPAYER"] == 1839400,
          "close after extend90-claim refunds 1839400")
    check(x("B-extend137-noop-tclaim-close", 0)["events"] == 0
          and x("B-extend137-noop-tclaim-close", 0)["dPAYER"] == -5000
          and uva("B-extend137-noop-tclaim-close", 0) == SEED,
          "extend at target 137 is a silent no-op")
    check(x("B-extend138-noop-close", 0)["events"] == 0
          and x("B-extend138-noop-close", 0)["dPAYER"] == -5000
          and x("B-extend138-noop-close", 0)["lens"]["uva"] == 138,
          "extend above target 138 is a silent no-op")
    check(x("B-extend50-tclaim-close", 0)["dPAYER"] == -610520
          and uva("B-extend50-tclaim-close", 0) == {"needs": 1, "unclaimed": 500, "claimed": 188, "volume": 0, "last": 0, "has": 0, "earned": 0, "cb_claimed": 0},
          "extend 50 to 137 rewrites the truncated layout (claimed 700 to low byte 188)")
    check(x("B-extend50-tclaim-close", 1)["deltas"] == {"gata": -500, "uata": 500}
          and uva("B-extend50-tclaim-close", 1)["claimed"] == 688
          and x("B-extend50-tclaim-close", 2)["dPAYER"] == 1000600520,
          "the claim after extend50 pays 500 to 688 and the close refunds 1000600520")
    check("Custom(2004)" in err("B-close-extend-init-extend", "original", 1)
          and x("B-close-extend-init-extend", 2)["dPAYER"] == -1849400
          and x("B-close-extend-init-extend", 3)["events"] == 0,
          "close-then-extend fails 2004; re-init succeeds and the further extend is a silent no-op")
    check("Custom(3010)" in err("B-extend-unsigned-then-signed", "original", 0)
          and x("B-extend-unsigned-then-signed", 1)["dPAYER"] == -332120,
          "extend with an unsigned user fails 3010; the signed extend right after succeeds")
    check("Custom(2000)" in err("B-extend-readonly-then-signed", "original", 0)
          and x("B-extend-readonly-then-signed", 1)["dPAYER"] == -332120,
          "extend with a read-only target fails 2000; the signed extend right after succeeds")
    check(x("B-extend-twice", 0)["dPAYER"] == -332120
          and x("B-extend-twice", 1)["events"] == 0 and x("B-extend-twice", 1)["dPAYER"] == -5000,
          "extend twice makes the second extend a silent no-op")
    # C: lifecycle inside 5-hop walks.
    check(x("C-buy5-close-reinit-buy5-swc-col", 0)["deltas"]["u5"] == 5207955235891
          and x("C-buy5-close-reinit-buy5-swc-col", 0)["events"] == 5
          and [d["len"] for d in x("C-buy5-close-reinit-buy5-swc-col", 0)["decoded"]] == [508] * 5,
          "5-hop buy tail anchor 5207955235891 with exactly 5 hop events (true 5-hop route)")
    check(x("C-buy5-close-reinit-buy5-swc-col", 3)["deltas"] == x("C-buy5-buy5-control", 1)["deltas"]
          and x("C-buy5-close-reinit-buy5-swc-col", 3)["deltas"]["u5"] == 4918089082874,
          "buy-close-reinit-buy reproduces the uninterrupted second buy exactly (tail 4918089082874)")
    check(burn("C-buy5-boost-close-reinit-buy5-boost", 2) == 5254679949141
          and burn("C-buy5-boost-close-reinit-buy5-boost", 7) == 5093171141582
          and burn("C-buy5-boost-buy5-boost-control", 5) == 5093171141582,
          "buy-boost-close-reinit-buy-boost reproduces the uninterrupted second burn 5093171141582")
    check(x("C-buy5-close-buy5", 2)["dPAYER"] == -1849400
          and x("C-buy5-close-buy5", 2)["deltas"]["u5"] == 4918089082874
          and uva("C-buy5-close-buy5", 2) == ZERO,
          "a buy after a close re-creates the empty UVA at rent cost with the uninterrupted second-buy tail")
    check(uva("C-buy5-seeded-unchanged", 0) == SEED,
          "a 5-hop buy leaves a seeded UVA byte-identical")
    check(x("C-buy5-seeded-tclaim", 1)["deltas"] == {"gata": -3334551, "uata": 3334551},
          "a 5-hop buy then token claim still pays the full 3334551")
    check(x("C-close-buy5-tclaim", 1)["dPAYER"] == -1849400
          and x("C-close-buy5-tclaim", 1)["deltas"]["u5"] == 5207955235891
          and x("C-close-buy5-tclaim", 2)["events"] == 0
          and uva("C-close-buy5-tclaim", 2) == dict(ZERO, last=21),
          "close-then-buy re-creates the empty UVA at rent cost with the anchor tail; the following claim is a 0-event zero claim")
    check(x("C-ft-buy5-close-reinit-buy5", 3)["deltas"] == x("C-ft-buy5-buy5-control", 1)["deltas"]
          and x("C-ft-buy5-close-reinit-buy5", 3)["deltas"]["u5"] == 4957670972204,
          "the fee-table lifecycle second buy reproduces the uninterrupted fee-table second buy (tail 4957670972204)")
    # D: tf / plain variants at depth 5.
    check(x("D-buy5-tf5000-close-reinit-buy5", 3)["deltas"]["u5"] == 2590950921881
          and x("D-buy5-tf5000-close-reinit-buy5", 3)["deltas"] == x("D-buy5-tf5000-buy5-control", 1)["deltas"],
          "tf5000 lifecycle second buy reproduces the uninterrupted tf5000 second buy (tail 2590950921881)")
    check(x("D-buy5-tf0-close-reinit-buy5", 3)["deltas"]["u5"] == 4963540456839
          and x("D-buy5-tf0-close-reinit-buy5", 3)["deltas"] == x("D-buy5-tf0-buy5-control", 1)["deltas"],
          "tf0 lifecycle second buy reproduces the uninterrupted tf0 second buy (tail 4963540456839)")
    check("Custom(3012)" in err("D-close-cclaim-plain", "original", 1),
          "cashback claim after a close fails 3012 in plain-quote mode")
    check(x("D-buy5-plain-close-reinit-buy5", 3)["deltas"]["u5"] == 4963540456839
          and x("D-buy5-plain-close-reinit-buy5", 3)["deltas"] == x("D-buy5-plain-buy5-control", 1)["deltas"],
          "plain-quote lifecycle second buy reproduces the uninterrupted plain second buy (tail 4963540456839)")
    print("PASS: 37 cases, 318 receipts, 32 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, claim-close-reinit chains, close gates 2006/3010, extend chains with exact rent top-ups and truncated-layout rewrite, close-then-extend 2004, lifecycle neutrality inside 5-hop walks against uninterrupted controls, buy-after-close recreation at rent cost, tf5000/tf0/plain variants); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
