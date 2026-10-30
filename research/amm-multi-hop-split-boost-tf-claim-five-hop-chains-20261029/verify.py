#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-claim-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 59 cases, 438 receipts, 44 parts
  (43x10 + 8), part sha256/byte counts match the part files.
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
  event, sweep 185-byte fields, collect 120-byte fields, token-claim
  104-byte fields, cashback-claim 72-byte fields, sync 64-byte fields,
  admin 88-byte fields, close 80-byte fields, init 80-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the claim x boost behaviour at
  depth 5 agrees on all three images).
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events and the 5-hop sell payout is 178541
  with 5 hop events; the 5-hop buy leaves a seeded UVA byte-identical
  and initializes an empty UVA (137 bytes, rent 1844400) when none
  exists, so the following token claim is a 0-event zero claim
  stamping last 0 -> 21; the seeded token claim pays 3334551
  (event disc 4facf631cd5bcee8, total_claimed 3334773) in every chain
  position without moving the burn (5254679949141) or the tail; the
  plain-quote cashback claim pays the ATA balance 5475 in both
  positions while token fields stay untouched, the zero-balance claim
  pays 0 despite earned 5475, the second cashback claim is a 1-event
  zero claim (unlike the token claim's 0-event zero claim), and a
  boost under a plain quote mint fails IncorrectProgramId; the
  cashback claim under any transfer-fee quote mint (even 0 bps)
  fails 2021; token-claim failure isolation holds (missing GVA 3012,
  short vault Token custom 1, missing user ATA created by
  init_if_needed for 2157600 rent + 5000 fee, missing UVA 3012);
  the sync reset gate fires only when now < start AND last < start
  (claimed 222 -> 0, has 1 -> 0, 64-byte event), and the claim after a
  reset pays only the pre-existing unclaimed 111 while the 333444
  volume stays unconverted on the same day; close strands the 111
  unclaimed (refund 999995000) and re-init never recovers it; an
  admin start-change wipes GVA supply/volume then sets supply[0] to
  2000, and a second pre-start claim re-resets total_claimed to 0,
  erasing the just-claimed 111 from the books; claim-mint tf100 pays
  net 3301205 / withheld 33346 and tf5000 pays net 1667275 /
  withheld 1667276 on the gross 3334551 event, while quote-mint
  tf5000 leaves the token claim whole.
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
    check(report["case_count"] == 59, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 59, "receipts": 438, "parts": 44},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 438, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 438, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 59 * 3, f"groups {len(grouped)}")
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

    def tev(label, idx):
        # The single decoded event of a claim/sync/admin/close/init step.
        ds = x(label, idx)["decoded"] or []
        return ds[0] if ds else None

    # A: anchors and bare legs at depth 5.
    check(x("A-buy5", 0)["deltas"]["u5"] == 5207955235891, "5-hop buy tail anchor")
    check(x("A-buy5", 0)["events"] == 5 and [d["len"] for d in x("A-buy5", 0)["decoded"]] == [508] * 5,
          "5-hop buy emits exactly 5 hop events (true 5-hop route)")
    check(x("A-sell5", 0)["deltas"]["userquote"] == 178541, "5-hop sell payout anchor")
    check(x("A-sell5", 0)["events"] == 5 and [d["len"] for d in x("A-sell5", 0)["decoded"]] == [449] * 5,
          "5-hop sell emits exactly 5 hop events (true 5-hop route)")
    check(burn("A-buy5-boost", 2) == 5254679949141, "buy-then-boost burn")
    check(burn("A-sell5-boost", 2) == 5338394848076, "sell-then-boost burn")
    check(x("A-buy5", 0)["dPAYER"] == -1849400, "unseeded 5-hop buy pays 1844400 rent to create the UVA")
    check(x("A-buy5-uva", 0)["dPAYER"] == -5000, "seeded 5-hop buy pays fee only")
    check(x("A-buy5-uva", 0)["uva"] == {"needs": 1, "unclaimed": 111, "claimed": 222, "volume": 333444,
          "last": 20, "has": 1, "earned": 555, "cb_claimed": 666}, "5-hop buy leaves a seeded UVA byte-identical")
    check(x("A-buy5-tclaim-noseed", 1)["events"] == 0 and x("A-buy5-tclaim-noseed", 1)["deltas"] == {}
          and x("A-buy5-tclaim-noseed", 1)["uva"]["last"] == 21,
          "claim after a fresh buy is a 0-event zero claim stamping last 0 -> 21")
    check(burn("A-buy5-boost-tclaim-noseed", 2) == 5254679949141
          and x("A-buy5-boost-tclaim-noseed", 3)["events"] == 0,
          "buy-boost-claim without a seed: anchor burn, then a 0-event zero claim")
    # B: seeded token claim in every chain position at depth 5.
    for _lbl, _idx in (("B-buy5-tclaim", 1), ("B-tclaim-buy5", 0), ("B-buy5-boost-tclaim", 3),
                       ("B-buy5-tclaim-boost", 1), ("B-tclaim-buy5-boost", 0),
                       ("B-buy5-swc-col-tclaim", 3), ("B-buy5-tclaim-swc-col", 1),
                       ("B-sell5-tclaim", 1), ("B-tclaim-sell5", 0)):
        _e = tev(_lbl, _idx)
        check(_e["disc"] == "4facf631cd5bcee8" and _e["len"] == 104 and _e["amount"] == 3334551
              and _e["total_claimed"] == 3334773 and _e["current_sol_volume"] == 0
              and _e["ts"] == 21, f"{_lbl}: seeded token claim pays 3334551 wherever it sits")
    check(burn("B-buy5-boost-tclaim", 2) == 5254679949141
          and burn("B-buy5-tclaim-boost", 3) == 5254679949141
          and burn("B-tclaim-buy5-boost", 3) == 5254679949141,
          "the token claim moves neither the boost burn in any position")
    check(x("B-buy5-tclaim", 0)["deltas"]["u5"] == 5207955235891
          and x("B-tclaim-buy5", 1)["deltas"]["u5"] == 5207955235891,
          "the token claim moves neither the 5-hop tail in any position")
    check(x("B-buy5-tclaim-tclaim", 2)["events"] == 0 and x("B-buy5-tclaim-tclaim", 2)["deltas"] == {},
          "second token claim is a 0-event zero claim")
    check(x("B-buy5-swc-col-tclaim", 1)["deltas"] == {"vq1": -4563570, "proto22": 4517934}
          and x("B-buy5-swc-col-tclaim", 1)["withheld"] == {"proto22": 45636},
          "protocol sweep after a 5-hop buy discharges 4563570 (net 4517934, withheld 45636)")
    check(x("B-buy5-swc-col-tclaim", 2)["events"] == 0,
          "creator collect without a prior creator sweep is a 0-event no-op")
    # C: cashback claim on a plain-quote 5-hop chain.
    check(x("C-buy5-cclaim", 0)["deltas"]["u5"] == 5259040470738, "plain-quote 5-hop buy tail")
    for _lbl, _idx in (("C-buy5-cclaim", 1), ("C-cclaim-buy5", 0)):
        _e = tev(_lbl, _idx)
        check(_e["disc"] == "e2d6f62107f293e5" and _e["len"] == 72 and _e["amount"] == 5475
              and _e["total_claimed"] == 5475 and _e["total_earned"] == 5475,
              f"{_lbl}: plain-quote cashback claim pays the ATA balance 5475")
    check(x("C-buy5-cclaim", 1)["uva"]["claimed"] == 222 and x("C-buy5-cclaim", 1)["uva"]["volume"] == 333444,
          "cashback claim leaves token fields untouched")
    check("IncorrectProgramId" in err("C-buy5-cclaim-boost", "original", 3)
          and "IncorrectProgramId" in err("C-cclaim-boost", "original", 2),
          "boost under a plain quote mint fails IncorrectProgramId with full rollback")
    check("3012" in err("C-cclaim-nouva", "original", 0), "cashback claim without a UVA fails 3012")
    _e = tev("C-cclaim-zero", 0)
    check(_e["amount"] == 0 and _e["total_claimed"] == 0 and _e["total_earned"] == 5475,
          "zero-balance cashback claim pays 0 despite earned 5475 (pays the balance, not earned)")
    check(x("C-buy5-cclaim-swc-col", 2)["deltas"] == {"vq1": -4609642, "protoata": 4609642}
          and x("C-buy5-cclaim-swc-col", 2)["withheld"] == {},
          "plain SPL protocol sweep discharges 4609642 with no withholding")
    check(x("C-buy5-cclaim-swc-col", 3)["events"] == 0,
          "plain SPL creator collect without a prior creator sweep is a 0-event no-op")
    check(tev("C-cclaim-tclaim", 1)["amount"] == 3334551 and tev("C-tclaim-cclaim", 1)["amount"] == 5475,
          "cashback and token claims stay field-disjoint in both orders")
    _e = tev("C-buy5-cclaim-cclaim", 2)
    check(_e["amount"] == 0 and _e["total_claimed"] == 5475 and x("C-buy5-cclaim-cclaim", 2)["events"] == 1,
          "second cashback claim is a 1-event zero claim (unlike the token claim's 0-event zero claim)")
    # D: cashback claim gate under a transfer-fee quote mint.
    for _lbl, _idx in (("D-cclaim-tf", 0), ("D-buy5-cclaim-tf", 1),
                       ("D-buy5-cclaim-tf5000", 1), ("D-cclaim-tf0", 0)):
        check("2021" in err(_lbl, "original", _idx), f"{_lbl}: cashback claim under a tf quote mint fails 2021")
    check(x("D-cclaim-tf-swc-col", 1)["deltas"] == {"vq1": -2488, "proto22": 2463}
          and x("D-cclaim-tf-swc-col", 1)["withheld"] == {"proto22": 25},
          "after a failed tf cashback claim the fixture protocol sweep still drains 2488")
    # E: token-claim failure isolation at depth 5.
    check("3012" in err("E-tclaim-nogva", "original", 0)
          and x("E-tclaim-nogva", 1)["deltas"]["u5"] == 5207955235891,
          "missing GVA fails 3012, following 5-hop buy is the anchor tail")
    check("3012" in err("E-tclaim-nogva-boost", "original", 0)
          and burn("E-tclaim-nogva-boost", 3) == 5254679949141,
          "missing GVA fails 3012, following buy-boost is the anchor burn")
    check("Custom(1)" in err("E-tclaim-shortvault", "original", 0)
          and x("E-tclaim-shortvault", 1)["deltas"]["u5"] == 5207955235891,
          "short vault fails Token custom 1 with rollback, following buy is the anchor tail")
    check(x("E-tclaim-missingata", 0)["dPAYER"] == -2162600
          and tev("E-tclaim-missingata", 0)["amount"] == 3334551,
          "missing user ATA is created by init_if_needed (2157600 rent + 5000 fee) and the full claim lands")
    check("3012" in err("E-tclaim-nouva", "original", 0)
          and x("E-tclaim-nouva", 1)["dPAYER"] == -1849400
          and x("E-tclaim-nouva", 1)["deltas"]["u5"] == 5207955235891,
          "claim without a UVA fails 3012, but the following buy creates the empty UVA at rent cost")
    check(x("E-init-tclaim", 0)["dPAYER"] == -1849400
          and tev("E-init-tclaim", 0)["disc"] == "86240d48e86582d8"
          and x("E-init-tclaim", 1)["events"] == 0 and x("E-init-tclaim", 1)["uva"]["last"] == 21,
          "init creates the UVA for 1844400 rent, then the claim is a 0-event zero claim")
    check(x("E-buy5-init-tclaim", 1)["dPAYER"] == -5000,
          "init after a buy costs fee only: the buy already created the UVA")
    # F: sync / close / admin at depth 5.
    check(x("F-buy5-sync", 1)["events"] == 0,
          "sync after a buy with last == start is a 0-event no-op (reset gate needs last < start)")
    _e = tev("F-sync", 0)
    check(_e["disc"] == "c57aa77c74515bff" and _e["before"] == 222 and _e["after"] == 0
          and _e["ts"] == 10 and _e["len"] == 64
          and x("F-sync", 0)["uva"]["claimed"] == 0 and x("F-sync", 0)["uva"]["has"] == 0
          and x("F-sync", 0)["uva"]["volume"] == 333444 and x("F-sync", 0)["uva"]["unclaimed"] == 111,
          "sync reset fires when now < start AND last < start: claimed 222 -> 0, has 1 -> 0, volume untouched")
    _e = tev("F-sync-tclaim", 1)
    check(_e["amount"] == 111 and _e["total_claimed"] == 111 and _e["current_sol_volume"] == 333444,
          "the claim after a reset pays only the pre-existing unclaimed 111; volume stays unconverted")
    check(x("F-sync-tclaim-tclaim", 2)["events"] == 0
          and x("F-sync-tclaim-tclaim", 2)["uva"]["volume"] == 333444,
          "a second same-day claim after a reset is a 0-event zero claim with volume still stranded")
    check(x("F-close-restore-tclaim", 0)["dPAYER"] == 999995000
          and tev("F-close-restore-tclaim", 0)["unc"] == 111
          and x("F-close-restore-tclaim", 1)["dPAYER"] == -1849400
          and x("F-close-restore-tclaim", 3)["events"] == 0
          and x("F-close-restore-tclaim", 3)["uva"]["unclaimed"] == 0,
          "close refunds 999995000 and strands the 111 unclaimed; re-init never recovers it")
    check(x("F-close-buy5", 1)["dPAYER"] == -1849400
          and x("F-close-buy5", 1)["deltas"]["u5"] == 5207955235891,
          "a buy after close re-creates the empty UVA at rent cost and keeps the anchor tail")
    _e = tev("F-admin-tclaim-tclaim", 0)
    check(_e["disc"] == "93fa6c78f71d43de" and _e["len"] == 88 and _e["start"] == 30
          and _e["end"] == 49 and _e["day"] == 0 and _e["supply"] == 2000,
          "admin start-change event: start 30, end 49, day 0, supply 2000")
    check(x("F-admin-tclaim-tclaim", 0)["gva"]["supply"][:1] == [2000]
          and x("F-admin-tclaim-tclaim", 0)["gva"]["supply"][1:] == [0] * 29
          and x("F-admin-tclaim-tclaim", 0)["gva"]["vol"] == [0] * 30,
          "admin start-change wipes GVA supply/volume, then sets supply[day 0] to 2000")
    check(tev("F-admin-tclaim-tclaim", 1)["amount"] == 111
          and x("F-admin-tclaim-tclaim", 3)["events"] == 0
          and x("F-admin-tclaim-tclaim", 3)["uva"]["claimed"] == 0
          and x("F-admin-tclaim-tclaim", 3)["uva"]["has"] == 0,
          "pre-start claim pays 111, then the next pre-start claim re-resets claimed to 0, erasing it")
    check("6005" in err("F-admin-outsider-tclaim", "original", 0)
          and tev("F-admin-outsider-tclaim", 1)["amount"] == 3334551,
          "outsider admin fails 6005 and the following claim is unaffected")
    check("3012" in err("F-admin-nogva-tclaim", "original", 0)
          and "3012" in err("F-admin-nogva-tclaim", "original", 1),
          "admin and claim both fail 3012 without a GVA")
    # G: tf variants at depth 5.
    check(x("G-buy5-tclaim-cbps100", 1)["deltas"] == {"gata": -3334551, "uata": 3301205}
          and x("G-buy5-tclaim-cbps100", 1)["withheld"] == {"uata": 33346},
          "claim-mint tf100 pays net 3301205 / withheld 33346 on the gross 3334551 event")
    check(x("G-buy5-tclaim-cbps5000", 1)["deltas"] == {"gata": -3334551, "uata": 1667275}
          and x("G-buy5-tclaim-cbps5000", 1)["withheld"] == {"uata": 1667276},
          "claim-mint tf5000 pays net 1667275 / withheld 1667276 on the gross 3334551 event")
    check(burn("G-buy5-tclaim-cbps100-boost", 3) == 5254679949141,
          "a tf-withheld token claim does not move the following boost burn")
    check(burn("G-buy5-boost-tclaim-cbps5000", 2) == 5254679949141
          and x("G-buy5-boost-tclaim-cbps5000", 3)["deltas"] == {"gata": -3334551, "uata": 1667275},
          "boost-then-tf5000-claim: anchor burn, then the tf5000 split")
    check(x("G-buy5-tclaim-tf5000", 1)["deltas"] == {"gata": -3334551, "uata": 3334551}
          and x("G-buy5-tclaim-tf5000", 1)["withheld"] == {},
          "quote-mint tf5000 leaves the token claim whole (no withholding on the claim mint)")
    print("PASS: 59 cases, 438 receipts, 44 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, buy-created empty UVA at rent cost, seeded token claim 3334551 in every chain position with burn and tail untouched, plain-quote cashback claim paying the ATA balance with IncorrectProgramId boost failure, tf cashback claim gate 2021 at any bps, token-claim failure isolation, sync reset gate with same-day volume stranding, close stranding, admin start-change wipe with pre-start claimed erasure, claim-mint tf gross/net splits); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
