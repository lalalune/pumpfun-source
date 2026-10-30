#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-admin-setter-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 42 cases, 330 receipts, 33 parts
  (33x10), part sha256/byte counts match the part files.
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
  (including buyback bps 899..907, buyback recipients 643..899, lp 40..48,
  protocol 48..56, fee authority 321..353, creator_fee 313..321,
  creator_fee_configurable 940, max_configurable_creator_fee_bps 941..949,
  mayhem flag 417, cashback flag 642, boost authority 907..939,
  boost_enabled 939, disable flags 56), the user volume
  accumulator state, the global volume accumulator state, the account
  lengths after every step, and the decoded event fields (multi-hop
  508/449-byte hop events, boost 512-byte BuyEvent + 208-byte boost
  event, sweep 185-byte fields, collect 120-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every case.
  Original agrees with them in every case except the two marked
  divergent cases: the rebuild's per-hop cashback gate fails 6079 on a
  non-terminal cb-flagged hop (P4) where the original succeeds, with
  or without the global cashback toggle off -- the same rebuild
  divergence seen in #71/#109/#119, not a setter difference.
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events; the buyback bps ladder at depth 5
  is 5000 -> leg 4515471 / vq1 credit 985438918, 7500 -> 6773206 /
  983158377, 10000 -> 9030942 / 980877836, 0 -> no leg / 990000000,
  with the tail unmoved at every bps; bps 10001 fails 6056;
  buyback recipients excluding the fixture owner fail the following
  buy 6053; setter gates are 6005 (outsider) and 3010 (unsigned);
  bps None + no recipients is a silent no-op; update_fee_config
  rewrites lp 20 -> 30, proto 5 -> 40, creator 5 -> 100 and the fee
  authority yet leaves the 5-hop buy, sell, sweep, collect and boost
  byte-identical; fee-config gates are 6012 (ordering) and 6000
  (bps bound, checked first); mayhem/cashback toggles fail same-state
  6043/6051 while boost toggle has no same-state check; boost
  toggle off fails the boost 6066 and re-enable restores the anchor
  burn 5338379201831; the global flags do not rescue the per-hop
  gates (mayhem-flagged P4 buy fails 6080 with 3 ghosts even with
  the global mayhem flag off); disable bits bind buy 6020, sell
  6021, deposit 6018, withdraw 6019, all-bits 6020, with exact
  recovery; boost under the buy bit fails 6020; the VQ-patched
  recovery buy tail 5167125538753 is pinned by its own control case;
  the no-op setter trio leaves buy + boost byte-identical; the
  creator-fee-config off setter leaves the chain byte-identical
  with gates 6005/3010; setter-before-buy moves the post-buy burn
  (bb7500: 5254775116926 vs anchor 5254679949141, +95167785)
  while setter-after-buy leaves the anchor burn; tf variants hold
  (bb7500 at tf5000: tail 2668075748732, leg 1727682; at tf0:
  tail 5259040470738, leg 6910730).
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
    check(report["case_count"] == 42, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 42, "receipts": 330, "parts": 33},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 330, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 330, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 42 * 3, f"groups {len(grouped)}")
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
    expected_divergent = {"C-cbflag-p4-buy5-anchor", "C-tog-cb-off-cbflag-p4-buy5"}
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

    def tail(label, idx):
        return x(label, idx)["deltas"].get("u5")

    def cfg(label, idx):
        return x(label, idx)["cfg"]

    # A: buyback bps ladder at depth 5, tail unmoved.
    check(tail("A-anchor-mhbuy5-swc-col", 0) == 5207955235891
          and x("A-anchor-mhbuy5-swc-col", 0)["deltas"].get("bb22") == 4515471
          and x("A-anchor-mhbuy5-swc-col", 0)["deltas"].get("vq1") == 985438918
          and x("A-anchor-mhbuy5-swc-col", 0)["events"] == 5,
          "anchor 5-hop buy: tail 5207955235891, bb leg 4515471, vq1 credit 985438918, 5 hop events")
    check(cfg("A-bb7500-mhbuy5-swc-col", 0)["bps"] == 7500
          and tail("A-bb7500-mhbuy5-swc-col", 1) == 5207955235891
          and x("A-bb7500-mhbuy5-swc-col", 1)["deltas"].get("bb22") == 6773206
          and x("A-bb7500-mhbuy5-swc-col", 1)["deltas"].get("vq1") == 983158377,
          "bb7500: leg 6773206, vq1 credit 983158377, tail unmoved")
    check(cfg("A-bb10000-mhbuy5", 0)["bps"] == 10000
          and tail("A-bb10000-mhbuy5", 1) == 5207955235891
          and x("A-bb10000-mhbuy5", 1)["deltas"].get("bb22") == 9030942
          and x("A-bb10000-mhbuy5", 1)["deltas"].get("vq1") == 980877836,
          "bb10000: leg 9030942, vq1 credit 980877836, tail unmoved")
    check(cfg("A-bb0-mhbuy5", 0)["bps"] == 0
          and tail("A-bb0-mhbuy5", 1) == 5207955235891
          and x("A-bb0-mhbuy5", 1)["deltas"].get("bb22") is None
          and x("A-bb0-mhbuy5", 1)["deltas"].get("vq1") == 990000000,
          "bb0: no buyback leg, vq1 credit 990000000, tail unmoved")
    check("Custom(6056)" in err("A-bb10001-fail-mhbuy5", "original", 0)
          and cfg("A-bb10001-fail-mhbuy5", 0)["bps"] == 5000
          and tail("A-bb10001-fail-mhbuy5", 1) == 5207955235891,
          "bb10001 fails 6056, config unchanged, following buy is the anchor")
    check("Custom(6053)" in err("A-bb-recip-excl-mhbuy5", "original", 1)
          and x("A-bb-recip-excl-mhbuy5", 1)["events"] == 0,
          "buyback recipients excluding the fixture owner fail the following buy 6053")
    for lbl in ("A-bb-outsider", "A-bb-unsigned"):
        code = "Custom(6005)" if "outsider" in lbl else "Custom(3010)"
        check(code in err(lbl, "original", 0) and cfg(lbl, 0)["bps"] == 5000,
              f"buyback setter gate {code}: {lbl}")
    check(cfg("A-bb-none-noop-mhbuy5", 0)["bps"] == 5000
          and tail("A-bb-none-noop-mhbuy5", 1) == 5207955235891,
          "bps None + no recipients is a silent no-op, following buy is the anchor")
    check(burn("A-bb7500-mhbuy5-boost", 3) == 5254775116926,
          "setter-before-buy moves the post-buy burn: bb7500 burn 5254775116926 vs anchor 5254679949141")
    check(x("A-bb7500-mhsell5", 1)["deltas"].get("bb22") == 1256,
          "bb7500 sell buyback leg 1256 (anchor sell leg 837 x 1.5, ceil)")
    # B: fee config rewrite, chain byte-identical; gates.
    check(cfg("B-ufc-base-mhbuy5-swc-col", 0)["lp"] == 30
          and cfg("B-ufc-base-mhbuy5-swc-col", 0)["proto"] == 40
          and cfg("B-ufc-base-mhbuy5-swc-col", 0)["creator_fee"] == 100
          and cfg("B-ufc-base-mhbuy5-swc-col", 0)["fee_auth"] == "6363636363636363636363636363636363636363636363636363636363636363"
          and tail("B-ufc-base-mhbuy5-swc-col", 1) == 5207955235891
          and x("B-ufc-base-mhbuy5-swc-col", 1)["deltas"].get("bb22") == 4515471
          and x("B-ufc-base-mhbuy5-swc-col", 2)["deltas"] == {"vq1": -123394, "creat22": 122160}
          and x("B-ufc-base-mhbuy5-swc-col", 3)["deltas"] == {"creat22": -122160, "dest22": 120938},
          "fee-config rewrite leaves buy, sweep and collect byte-identical")
    check(burn("B-ufc-mhbuy5-boost", 3) == 5254679949141,
          "fee-config rewrite leaves the post-buy burn at the anchor")
    check(x("B-ufc-mhsell5", 1)["deltas"].get("bb22") == 837,
          "fee-config rewrite leaves the sell buyback leg at 837")
    check("Custom(6012)" in err("B-ufc-unsorted-fail-mhbuy5", "original", 0)
          and cfg("B-ufc-unsorted-fail-mhbuy5", 0)["lp"] == 20
          and tail("B-ufc-unsorted-fail-mhbuy5", 1) == 5207955235891,
          "unsorted recipients fail 6012 with no config change, following buy is the anchor")
    check("Custom(6000)" in err("B-ufc-lp1001-fail", "original", 0)
          and cfg("B-ufc-lp1001-fail", 0)["lp"] == 20,
          "lp 1001 with unsorted recipients fails 6000 (bps bound checked first)")
    check("Custom(6005)" in err("B-ufc-outsider", "original", 0)
          and cfg("B-ufc-outsider", 0)["lp"] == 20,
          "fee-config outsider fails 6005 with no config change")
    # C: toggles.
    check(cfg("C-tog-mayhem-off-twice", 0)["mayhem"] == 0
          and "Custom(6043)" in err("C-tog-mayhem-off-twice", "original", 1),
          "mayhem toggle off rewrites byte 417, second off fails 6043")
    check(cfg("C-tog-cb-off-twice", 0)["cashback"] == 0
          and "Custom(6051)" in err("C-tog-cb-off-twice", "original", 1),
          "cashback toggle off rewrites byte 642, second off fails 6051")
    check(cfg("C-tog-boost-samestate", 0)["boost_enabled"] == 1
          and x("C-tog-boost-samestate", 0)["error"] is None,
          "boost toggle same-state succeeds silently")
    check("Custom(6005)" in err("C-tog-outsider", "original", 0)
          and cfg("C-tog-outsider", 0)["mayhem"] == 1,
          "toggle outsider fails 6005 with no config change")
    check(cfg("C-tog-boost-off-boost-on", 1)["boost_enabled"] == 0
          and "Custom(6066)" in err("C-tog-boost-off-boost-on", "original", 2)
          and cfg("C-tog-boost-off-boost-on", 3)["boost_enabled"] == 1
          and burn("C-tog-boost-off-boost-on", 4) == 5338379201831,
          "boost toggle off fails the boost 6066, re-enable restores the anchor burn")
    check("Custom(6079)" in err("C-cbflag-p4-buy5-anchor", "control", 0)
          and x("C-cbflag-p4-buy5-anchor", 0)["events"] == 5
          and get("C-cbflag-p4-buy5-anchor", "control", 0)["events"] == 3
          and "Custom(6079)" in err("C-tog-cb-off-cbflag-p4-buy5", "control", 1),
          "rebuild per-hop cashback gate fails 6079 with 3 ghosts on non-terminal cb P4, global cb off does not rescue it")
    check("Custom(6080)" in err("C-tog-mayhem-off-mayhemflag-p4-buy5", "original", 1)
          and x("C-tog-mayhem-off-mayhemflag-p4-buy5", 1)["events"] == 3,
          "mayhem-flagged P4 buy fails 6080 with 3 ghosts even with the global mayhem flag off")
    # D: disable bits.
    check("Custom(6020)" in err("D-dis-buy-mhbuy5", "original", 1)
          and cfg("D-dis-buy-mhbuy5", 0)["disable"] == 8
          and tail("D-dis-buy-mhbuy5", 3) == 5207955235891,
          "buy bit fails the 5-hop buy 6020, clearing restores the anchor")
    check("Custom(6021)" in err("D-dis-sell-mhsell5", "original", 1)
          and cfg("D-dis-sell-mhsell5", 0)["disable"] == 16
          and x("D-dis-sell-mhsell5", 3)["deltas"].get("bb22") == 837,
          "sell bit fails the 5-hop sell 6021, clearing restores the anchor sell")
    check("Custom(6018)" in err("D-dis-dep", "original", 1)
          and x("D-dis-dep", 3)["deltas"] == {"userbase": -160619896, "userquote": -29610, "userlp": 1000000, "vb1": 160619896, "vq1": 29313},
          "deposit bit fails deposit 6018, clearing restores the deposit")
    check("Custom(6019)" in err("D-dis-wd", "original", 1)
          and x("D-dis-wd", 3)["deltas"] == {"userbase": 160619895, "userquote": 29018, "userlp": -1000000, "vb1": -160619895, "vq1": -29312},
          "withdraw bit fails withdraw 6019, clearing restores the withdraw")
    check("Custom(6020)" in err("D-dis-buy-boost", "original", 2)
          and tail("D-dis-buy-boost", 4) == 5167125538753
          and tail("D-vqpatch-buy5-control", 1) == 5167125538753,
          "boost under the buy bit fails 6020; the recovery buy tail equals the VQ-patch control buy")
    check("Custom(6020)" in err("D-dis-all-mhbuy5", "original", 1)
          and cfg("D-dis-all-mhbuy5", 0)["disable"] == 31
          and tail("D-dis-all-mhbuy5", 3) == 5207955235891,
          "all-bits disable fails the buy 6020 (buy bit dominates), clearing restores the anchor")
    # E: neutrality, creator-fee config, ordering.
    check(tail("E-neutral-mhbuy5-boost", 3) == 5207955235891
          and burn("E-neutral-mhbuy5-boost", 5) == 5254679949141,
          "no-op setter trio leaves buy + boost byte-identical to the anchor")
    check(cfg("E-ucfc-off-mhbuy5", 0)["cfgable"] == 0
          and tail("E-ucfc-off-mhbuy5", 1) == 5207955235891,
          "creator-fee-config off leaves the 5-hop buy byte-identical")
    check("Custom(6005)" in err("E-ucfc-outsider", "original", 0)
          and "Custom(3010)" in err("E-ucfc-unsigned", "original", 0)
          and cfg("E-ucfc-outsider", 0)["cfgable"] == 1,
          "creator-fee-config gates are 6005/3010")
    check(burn("E-buy5-bbcfg7500-boost", 3) == 5254679949141,
          "setter-after-buy leaves the anchor burn: the burn moves only when the buy itself ran under the new bps")
    check(burn("E-buy5-ufc-boost", 3) == 5254679949141,
          "fee-config after the buy leaves the anchor burn")
    # F: tf variants.
    check(tail("F-bb7500-tf5000", 1) == 2668075748732
          and x("F-bb7500-tf5000", 1)["deltas"].get("bb22") == 1727682,
          "bb7500 at tf5000: tail 2668075748732, leg 1727682")
    check(tail("F-bb7500-tf0", 1) == 5259040470738
          and x("F-bb7500-tf0", 1)["deltas"].get("bb22") == 6910730,
          "bb7500 at tf0: tail 5259040470738, leg 6910730")
    check(tail("F-ufc-tf5000", 1) == 2668075748732
          and x("F-ufc-tf5000", 1)["deltas"].get("bb22") == 1151788,
          "fee-config at tf5000 leaves the tf5000 buy byte-identical")
    check("Custom(6020)" in err("F-dis-buy-tf5000", "original", 1)
          and tail("F-dis-buy-tf5000", 3) == 2668075748732,
          "buy bit at tf5000 fails the buy 6020, clearing restores the tf5000 anchor")
    print("PASS: 42 cases, 330 receipts, 33 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, buyback bps ladder with unmoved tail, fee-config rewrite with byte-identical chain, toggle same-state gates, global-vs-pool flag separation, disable bits with exact recovery, setter neutrality and setter ordering on the burn, tf variants); control == candidate everywhere; original agrees except the 2 marked divergent cases (C-cbflag-p4-buy5-anchor, C-tog-cb-off-cbflag-p4-buy5)")
if __name__ == "__main__":
    main()
