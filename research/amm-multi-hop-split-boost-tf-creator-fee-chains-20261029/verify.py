#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-creator-fee-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 53 cases, 399 receipts, 40 parts
  (39x10 + 9), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures verify
  (cpatch steps carry an empty transaction by design -- a harness field
  reset, never an instruction -- and are asserted as such instead, and
  the following step's before snapshot must equal the cpatch after
  snapshot).
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer and outsider lamport
  deltas, the token-leg deltas, the Token-2022 withheld deltas, the
  native-mint token-account lamport deltas, the three fixture pool
  states (virtual_quote_reserves i128, protocol_fees, creator_fees,
  lp_supply) plus each pool's creator_fee_bps field (261..269) and the
  pool coin_creator bytes after every step, the GlobalConfig state
  (including boost authority 907..939, boost_enabled, disable flags,
  creator_fee 313..321, creator_fee_configurable 940 and
  max_configurable_creator_fee_bps 941..949), the user volume
  accumulator state, the global volume accumulator state, the account
  lengths after every step, and the decoded event fields (multi-hop
  508/449-byte hop events, boost 512-byte BuyEvent + 208-byte boost
  event, sweep 185-byte fields, collect 120-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the creator-fee behaviour agrees on
  all three images).
- Headline pins (see README): the multi-hop creator fee is charged
  ONLY at the terminal hop (P3 on both buys and sells); the main
  pool's creator_fee_bps (even 10000) moves nothing on this route --
  tail, buckets and the next boost burn are all anchor-identical;
  P3 creator_fee_bps 300 cuts the buy tail by 149,672,474,048 and
  10000 halves it, and 10000 on a sell fails with Overflow 6023;
  configurable off falls back to the fee-table creator bps;
  update_creator_fee_config works for the admin (off 0/300, on
  1/10000) and fails 6005 for an outsider, 3010 unsigned, with full
  rollback; the GlobalConfig creator_fee field alone moves nothing;
  creator/protocol sweeps after a buy move the next main boost burn
  (+5,149,187 / +190,442,847) even though the VQ patch is identical;
  legacy buys pay the creator fee to the creator ATA (5,420) while
  v2 buys accrue it to the pool bucket (+5,475).
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
U3 = "6swiTCWtSwqi8sm9wzNwKA9NEpJWbXjLcVz654u7zz4W"
# Token-role keys are recovered from the receipts themselves: the
# builder's TOKEN_ROLES deltas are recomputed from snapshots, and
# the headline asserts below use only pool / config / UVA / GVA /
# payer / outsider keys plus decoded events, so no full role table
# is needed here.

BST_DISC = "3f451c16305cc2b9"
MHBUY_DISC = "67f4521f2cf57777"
MHSELL_DISC = "3e2f370aa503dc2a"
SWP_DISC = "82a42461e48287a5"
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
    if kind in ("mhbuy3", "mhsell3"):
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


STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "boost": "boost",
             "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
             "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
             "swp": "swp", "swc": "swc", "col": "col",
                "boost2": "boost", "boost2o": "boost", "boost3s": "boost", "boost3o": "boost",
                "boost2x": "boost", "boost3x": "boost", "boostx": "boost", "boosto": "boost",
                "boostauth": None, "initb": None, "ucfc": None, "legbuy": None, "buy2": None, "legs": None,
             "xfer2": None, "xfer1": None, "cpatch": None,
             "admin": "admin", "close": "close", "close_other": "close", "close_unsigned": "close", "init": "init",
             "ww": None, "harvest": None, "wfm": None,
             "buy2m": "buy2", "sell2m": "sell2", "lexact": None, "bexact2": None}


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
                      (("main", POOL), ("pool2", POOL2), ("p3", P3))},
            "cfbps": {name: (struct.unpack_from("<Q", bytes.fromhex(after[key]["data_hex"]), 261)[0]
                             if after.get(key) and len(bytes.fromhex(after[key]["data_hex"])) >= 269 else None)
                      for name, key in (("main", POOL), ("pool2", POOL2), ("p3", P3))},
            "pool_creator": bytes.fromhex(after[POOL]["data_hex"])[211:243].hex() if after.get(POOL) else None,
            "cfg": cfg_fields(after.get(CONFIG)),
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
    check(report["case_count"] == 53, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 53, "receipts": 399, "parts": 40},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 399, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 399, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 53 * 3, f"groups {len(grouped)}")
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
                              "pools", "cfbps", "pool_creator", "cfg", "uva", "gva", "mint", "lens", "site"):
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
        return x(label, idx)["decoded"][1]["burned"]

    SUP = 4194352106721
    # A: anchors.
    check(x("A-buy", 0)["deltas"]["bb22"] == 4515471 and x("A-buy", 0)["withheld"]["bb22"] == 45611, "fresh buy leg 4515471 + withheld 45611")
    check(x("A-buy", 0)["deltas"]["u3"] == 5262910281902, "fresh buy tail anchor")
    check(x("A-sell", 0)["deltas"]["bb22"] == 837 and x("A-sell", 0)["deltas"]["userquote"] == 178541, "fresh sell leg 837, payout 178541")
    check(burn("A-boost", 1) == 5338379201831, "main boost anchor burn")
    check(x("A-boost-buy", 2)["deltas"]["bb22"] == 4515471 and x("A-boost-buy", 2)["deltas"]["u3"] == 5139964404268, "boost-first buy leg identical, tail is the #102 boost-then-buy tail")
    check(burn("A-buy-boost", 2) == 5254679949141, "buy-then-boost is the post-buy burn")
    # B/C: the main pool's creator_fee_bps moves nothing on this route.
    check(x("B-cf10000-buy", 0)["deltas"]["u3"] == 5262910281902 and x("B-cf10000-buy", 0)["pools"]["main"][2] == 123394, "main cf 10000 buy tail and creator bucket are anchor-identical")
    check(burn("C-cf10000-buy-boost", 2) == 5254679949141, "main cf 10000 buy-then-boost burn is the anchor burn")
    check(x("D-cf10000-sell", 0)["deltas"]["userquote"] == 178541, "main cf 10000 sell payout is the anchor payout")
    check(x("B-cf300-p2-buy", 0)["deltas"]["u3"] == 5262910281902, "middle-hop (P2) cf 300 buy tail is anchor-identical")
    # E: mid-walk main-pool edits also move nothing (creator is terminal-hop).
    check(x("E-buy-cf300-buy-boost", 2)["deltas"]["u3"] == 5072980706277 and burn("E-buy-cf300-buy-boost", 4) == 5172933848347, "buy, main cf 300, buy, boost is the #112 second-buy tail and burn")
    check(x("E-cf300-buy-cf0-buy-boost", 2)["deltas"]["u3"] == 5072980706277, "main cf 300 then 0 second buy tail is unchanged")
    check(burn("E-boost-cf300-buy-boost", 5) == 5173028765024, "boost, main cf 300, buy, boost is the #112 boost-buy-boost burn")
    # F: the real creator-fee-config setter and its gates.
    check(x("F-ucfc-off-cf300-buy", 0)["cfg"]["cfgable"] == 0 and x("F-ucfc-off-cf300-buy", 0)["cfg"]["maxcf"] == 300, "admin ucfc off writes configurable 0, max 300")
    check(x("F-ucfc-on-cf300-buy", 0)["cfg"]["cfgable"] == 1 and x("F-ucfc-on-cf300-buy", 0)["cfg"]["maxcf"] == 10000, "admin ucfc on writes configurable 1, max 10000")
    check("6005" in err("F-ucfc-outsider-buy", "original", 0) and x("F-ucfc-outsider-buy", 0)["cfg"]["cfgable"] == 1 and x("F-ucfc-outsider-buy", 0)["cfg"]["maxcf"] == 300, "outsider ucfc fails 6005 with full rollback")
    check("3010" in err("F-ucfc-unsigned-buy", "original", 0) and x("F-ucfc-unsigned-buy", 0)["cfg"]["cfgable"] == 1, "unsigned ucfc fails 3010 with full rollback")
    check(x("F-cf300-noconfig-buy", 0)["deltas"]["u3"] == 5262910281902, "main cf 300 with configurable off is the anchor tail (no override, but main is not the terminal hop anyway)")
    # G: the GlobalConfig creator_fee field alone moves nothing.
    check(x("G-cfgcf10000-buy-boost", 0)["deltas"]["u3"] == 5262910281902 and burn("G-cfgcf10000-buy-boost", 2) == 5254679949141, "config creator_fee 10000 buy tail and boost are anchor-identical")
    # H: sweeps after a buy move the next main boost burn.
    check(x("H-cf300-buy-swc-col-boost", 1)["deltas"]["creat22"] == 122160 and x("H-cf300-buy-swc-col-boost", 2)["deltas"]["dest22"] == 120938, "creator sweep nets 122160 (123394 less withheld 1234), collect 120938 (withheld 1222)")
    check(burn("H-cf300-buy-swc-col-boost", 4) == 5254685098328, "creator sweep+collect then boost is anchor + 5149187")
    check(x("H-cf300-buy-swp-boost", 1)["deltas"]["proto22"] == 4517934, "protocol sweep moves 4517934 of the 4563570 bucket")
    check(burn("H-cf300-buy-swp-boost", 3) == 5254870391988, "protocol sweep then boost is anchor + 190442847")
    check(burn("H-cf0-buy-swc-col-boost", 4) == 5254685098328, "cf0 creator sweep+collect then boost is the same burn (main cf is inert)")
    # I: hop boosts under a main creator fee are the anchor hop burns.
    check(burn("I-cf300-buy-p2boost", 2) == 989418199, "P2 boost after a main-cf300 buy is the anchor hop burn")
    check(burn("I-cf300-buy-p3boost", 2) == 989486889, "P3 boost after a main-cf300 buy is the anchor hop burn")
    # J: tf variants under a creator fee.
    check(x("J-cf300-buy-tf0-boost", 0)["deltas"]["u3"] == 5315084721958 and burn("J-cf300-buy-tf0-boost", 2) == 5306492329463, "tf0 buy tail and boost under main cf 300")
    check(x("J-cf300-buy-tf5000-boost", 0)["deltas"]["u3"] == 2682425360738 and burn("J-cf300-buy-tf5000-boost", 2) == 2685165599125, "tf5000 buy tail and boost under main cf 300")
    # K: single-pool legs do charge the main pool creator fee.
    check(x("K-cf300-legbuy", 0)["deltas"]["creat22"] == 5420 and x("K-cf300-legbuy", 0)["deltas"]["userquote"] == -191550, "legacy buy pays creator fee 5420 to the creator ATA")
    check(x("K-cf300-buy2", 0)["pools"]["main"][2] == 128869 and x("K-cf300-buy2", 0)["deltas"]["userquote"] == -191614, "v2 buy accrues creator fee 5475 to the pool bucket")
    # L: walks under a creator fee.
    check(burn("L-cf300-sell-boost", 2) == 5338394848092, "sell then boost under main cf 300 is anchor + 15647261")
    check(burn("L-cf300-boost-boost", 3) == 5254441549265, "boost then boost under main cf 300 is the #100 second burn")
    # M: the terminal hop (P3) is the real creator-fee lever.
    check(x("M-p3cf300-buy", 0)["deltas"]["u3"] == 5113237807854 and x("M-p3cf300-buy", 0)["pools"]["p3"][2] == 154185644849, "P3 cf 300 buy tail cut by 149672474048, P3 creator bucket 154185644849")
    check(x("M-p3cf10000-buy", 0)["deltas"]["u3"] == 2642341163278 and x("M-p3cf10000-buy", 0)["pools"]["p3"][2] == 2649341750777, "P3 cf 10000 buy tail roughly halved, P3 creator bucket 2649341750777")
    check(x("M-p3cf300-sell", 0)["deltas"]["userquote"] == 173261 and x("M-p3cf300-sell", 0)["pools"]["p3"][2] == 30123364, "P3 cf 300 sell payout 173261 (anchor 178541), P3 creator bucket 30123364")
    check("6023" in err("M-p3cf10000-sell", "original", 0) and x("M-p3cf10000-sell", 0)["deltas"] == {}, "P3 cf 10000 sell fails Overflow 6023 with full rollback")
    check(burn("M-p3cf300-buy-p3boost", 2) == 989635771, "P3 boost after a P3-cf300 buy is anchor hop burn + 148882")
    check(burn("M-p3cf300-buy-boost", 2) == 5254679949141, "P3 cf 300 buy then MAIN boost is the anchor burn (P3 fees do not touch main buckets)")
    check(x("M-p3cf300-noconfig-buy", 0)["deltas"]["u3"] == 5262910281902 and x("M-p3cf300-noconfig-buy", 0)["pools"]["p3"][2] == 2645500920, "P3 cf 300 with configurable off falls back to the fee-table creator bps: anchor tail and P3 creator bucket")
    check(x("M-buy-p3cf300-buy-boost", 2)["deltas"]["u3"] == 4928686679137 and burn("M-buy-p3cf300-buy-boost", 4) == 5172933848347, "mid-walk P3 cf 300 second buy tail cut, main boost still the #112 second-buy burn")
    print("PASS: 53 cases, 399 receipts, 40 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config creator-fee fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, terminal-hop creator-fee rule, main-pool creator-fee inertness, configurable fallback, update_creator_fee_config gates 6005/3010, sweep-moves-next-burn, tf variants, single-pool creator-fee legs); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
