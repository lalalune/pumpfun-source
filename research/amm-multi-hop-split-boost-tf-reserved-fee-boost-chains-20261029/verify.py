#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-coin-creator-boost-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 32 cases, 522 receipts, 53 parts
  (52x10 + 2), part sha256/byte counts match the part files.
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
  main pool's coin_creator bytes after every step, the GlobalConfig state
  (including boost authority 907..939, boost_enabled, disable flags,
  creator_fee 313..321, creator_fee_configurable 940 and
  max_configurable_creator_fee_bps 941..949), the user volume
  accumulator state, the global volume accumulator state, the account
  lengths after every step, and the decoded event fields (multi-hop
  508/449-byte hop events, boost 512-byte BuyEvent + 208-byte boost
  event, sweep 185-byte fields, collect 120-byte fields, set 144-byte
  events, migrate 176-byte events).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the reassignment x boost behaviour
  agrees on all three images).
- Headline pins (see README): the set no-op leaves the patched-window
  boost burn byte-identical; a zero pool boosts at the anchor burn and
  set fires to CREATOR0; sweeping the seeded bucket to the NEW vault
  moves the next main boost burn by exactly +5,272,467 (the #109
  creator-sweep slope) while the same sweep leaves the hop-pool boost
  burn byte-identical; migrate succeeds only after sweep+collect and
  leaves the boost burn at the swept value, while a post-migrate
  collect fails 6048 and a pre-sweep migrate fails 6081; hop-pool
  set2/set3 and migrate2 reproduce the main-pool gates on P2/P3, with
  the sharing-config PDA as the new coin_creator; cashback claim after
  set still fails 2021 under the tf quote mint; tf5000 reroute pipes
  halve twice (61697 then 30848).
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
             "buy2m": "buy2", "sell2m": "sell2", "lexact": None, "bexact2": None,
             "set": "set", "mig": "mig",
             "setr": "setr", "legbuy_res": None, "legsell_res": None,
             "set2": "set", "mig2": "mig", "set3": "set", "mig3": "mig",
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
                      (("main", POOL), ("pool2", POOL2), ("p3", P3))},
            "cfbps": {name: (struct.unpack_from("<Q", bytes.fromhex(after[key]["data_hex"]), 261)[0]
                             if after.get(key) and len(bytes.fromhex(after[key]["data_hex"])) >= 269 else None)
                      for name, key in (("main", POOL), ("pool2", POOL2), ("p3", P3))},
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
    check(report["case_count"] == 32, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 32, "receipts": 342, "parts": 35},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 342, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 342, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 32 * 3, f"groups {len(grouped)}")
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
        return x(label, idx)["decoded"][1]["burned"]

    PAYER_HEX = "ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5"
    R_HEX = ["61" * 32, "62" * 32, "63" * 32, "64" * 32, "65" * 32, "66" * 32, "67" * 32, "68" * 32]
    PROTO_HEX = "4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6"
    WL_OTHER = "69" * 32
    # A: anchors.
    check(burn("A-boost", 1) == 5338379201831, "fresh patched-window main boost burn")
    check(burn("A-buy-boost", 2) == 5254679949141, "buy-then-boost burn")
    check(x("A-buy-boost", 0)["deltas"]["u3"] == 5262910281902, "anchor buy tail")
    check(burn("A-mayhem-boost", 1) == 5338379201831, "boost on a mayhem-flagged pool is the anchor burn: boost is mayhem-blind")
    # B: the boost burn is reserved-list-blind.
    check(x("B-setr-boost", 0)["decoded"][0]["disc"] == SETR_DISC and x("B-setr-boost", 0)["decoded"][0]["len"] == 272, "setr emits the 272-byte ReservedFeeRecipientsEvent")
    check(x("B-setr-boost", 0)["rescfg"]["wl"] == PAYER_HEX and x("B-setr-boost", 0)["rescfg"]["res0"] == R_HEX[0] and x("B-setr-boost", 0)["rescfg"]["res"] == R_HEX[1:], "setr writes whitelist PDA, first recipient, and the other seven")
    check(burn("B-setr-boost", 2) == 5338379201831, "boost after setr is the anchor burn")
    check(burn("B-boost-setr-boost", 4) == 5254441549265, "second boost after mid-walk setr is the #100 decay burn")
    check(x("B-boost-replace-boost", 2)["rescfg"]["res0"] == PROTO_HEX, "replacement installs PROTOCOL as the first reserved recipient")
    check(burn("B-boost-replace-boost", 4) == 5254441549265, "second boost after replacement is the same decay burn")
    check("6005" in err("B-setr-outsider-boost", "original", 0) and x("B-setr-outsider-boost", 0)["dOUT"] == -5000, "outsider setter fails 6005, paid by the outsider")
    check("3010" in err("B-setr-unsigned-boost", "original", 0) and x("B-setr-unsigned-boost", 0)["dOUT"] == -5000, "unsigned setter fails 3010")
    check("6044" in err("B-setr-7fail-boost", "original", 0), "7-recipient setter fails 6044")
    check(burn("B-setr-outsider-boost", 2) == 5338379201831 and burn("B-setr-unsigned-boost", 2) == 5338379201831 and burn("B-setr-7fail-boost", 2) == 5338379201831, "failed setters leave the following boost at the anchor burn")
    check(x("B-setr-dup-boost", 0)["rescfg"]["res0"] == R_HEX[0] and x("B-setr-dup-boost", 0)["rescfg"]["res"] == [R_HEX[0]] * 7, "duplicate list writes without a uniqueness check")
    check(burn("B-setr-dup-boost", 2) == 5338379201831, "boost after the duplicate list is the anchor burn")
    check(x("B-setr-wl-other-boost", 0)["rescfg"]["wl"] == WL_OTHER and burn("B-setr-wl-other-boost", 2) == 5338379201831, "unrelated whitelist writes and leaves the boost at the anchor burn")
    # C: mayhem legs and the mayhem multi-hop gate.
    check(x("C-mayhem-legbuy-res-boost", 0)["deltas"]["res0ata"] == 1681 and x("C-mayhem-legbuy-res-boost", 0)["withheld"]["res0ata"] == 17, "mayhem buy pays the protocol leg 1681 net to the reserved member ATA (gross 1698, withheld 17)")
    check(x("C-mayhem-legbuy-res-boost", 0)["deltas"]["userquote"] == -186623 and x("C-mayhem-legbuy-res-boost", 0)["deltas"]["creat22"] == 542, "mayhem buy costs 186623 and pays the creator 542")
    check(burn("C-mayhem-legbuy-res-boost", 2) == 5338363478447, "boost after the mayhem reserved buy is anchor - 15723384")
    check("6013" in err("C-mayhem-legbuy-proto-fail-boost", "original", 0) and burn("C-mayhem-legbuy-proto-fail-boost", 2) == 5338379201831, "mayhem buy with PROTOCOL as recipient fails 6013; the following boost is the anchor burn")
    check(x("C-mayhem-legsell-res-boost", 0)["deltas"]["userquote"] == 178409 and x("C-mayhem-legsell-res-boost", 0)["deltas"]["res0ata"] == 1681, "mayhem sell pays 178409 and the protocol leg 1681 to the reserved member ATA")
    check(burn("C-mayhem-legsell-res-boost", 2) == 5338394922055, "boost after the mayhem reserved sell is anchor + 15720224")
    check("6080" in err("C-mayhem-mhbuy-fail-boost", "original", 0) and x("C-mayhem-mhbuy-fail-boost", 0)["events"] == 0, "mayhem multi-hop buy fails 6080 at hop 1 with 0 events")
    check("6080" in err("C-mayhem-mhsell-fail-boost", "original", 0) and x("C-mayhem-mhsell-fail-boost", 0)["events"] == 2, "mayhem multi-hop sell fails 6080 at the terminal hop with 2 ghost hop events")
    for _img in ("original", "control", "candidate"):
        check("6080" in err("C-mayhem-mhbuy-fail-boost", _img, 0) and "6080" in err("C-mayhem-mhsell-fail-boost", _img, 0), "mayhem multi-hop gate is 6080 on all three images")
    check(burn("C-mayhem-mhbuy-fail-boost", 2) == 5338379201831 and burn("C-mayhem-mhsell-fail-boost", 2) == 5338379201831, "boost after a failed mayhem chain is the anchor burn")
    check(x("C-mayhem-setr-replace-legbuy-res-fail-boost", 0)["rescfg"]["res0"] == PROTO_HEX, "replacement writes PROTOCOL before the leg")
    check("6013" in err("C-mayhem-setr-replace-legbuy-res-fail-boost", "original", 1), "replacement immediately invalidates the old reserved member")
    check(burn("C-mayhem-setr-replace-legbuy-res-fail-boost", 3) == 5338379201831, "boost after the invalidated leg is the anchor burn")
    check(x("C-mayhem-setr-proto-legbuy-boost", 0)["rescfg"]["wl"] == WL_OTHER and x("C-mayhem-setr-proto-legbuy-boost", 0)["rescfg"]["res0"] == PROTO_HEX, "unrelated-whitelist replacement installs PROTOCOL")
    check(x("C-mayhem-setr-proto-legbuy-boost", 1)["deltas"]["proto22"] == 1681 and x("C-mayhem-setr-proto-legbuy-boost", 1)["withheld"]["proto22"] == 17, "installed-PROTOCOL leg pays 1681 net to PROTO22")
    check(burn("C-mayhem-setr-proto-legbuy-boost", 3) == 5338363478447, "installed-PROTOCOL leg then boost equals the reserved-member leg then boost")
    check("6013" in err("C-plain-legbuy-res-fail-boost", "original", 0), "non-mayhem leg with a reserved recipient fails 6013 (protocol_fee_recipients list membership)")
    # D: sweep/collect vs rotation.
    check(x("D-buy-swp-setr-boost", 1)["deltas"]["proto22"] == 4517934 and x("D-buy-swp-setr-boost", 1)["withheld"]["proto22"] == 45636, "protocol sweep after a buy discharges 4563570 (net 4517934, withheld 45636)")
    check(burn("D-buy-swp-setr-boost", 4) == 5254870391988 and burn("D-buy-setr-swp-boost", 4) == 5254870391988, "sweep before or after the setter leaves the same swept burn")
    check(x("D-buy-swp-col-setr-boost", 2)["events"] == 0, "collect after a protocol-only sweep is a 0-event no-op")
    check(burn("D-buy-swp-col-setr-boost", 5) == 5254870391988 and burn("D-buy-swp-col-replace-boost", 5) == 5254870391988, "collect and replacement after the sweep leave the swept burn unchanged")
    check(x("D-sell-swp-setr-boost", 0)["deltas"]["userquote"] == 178541 and x("D-sell-swp-setr-boost", 1)["deltas"]["proto22"] == 3301 and burn("D-sell-swp-setr-boost", 4) == 5338394990593, "sell, protocol sweep (3301 net), setter, boost is the post-sell swept burn")
    # E: tf variants.
    check(x("E-setr-buy-boost-tf5000", 1)["deltas"]["u3"] == 2682425360738 and burn("E-setr-buy-boost-tf5000", 3) == 2685165599125, "tf5000 setr-buy-boost matches the #106/#112 tf5000 anchors")
    check(x("E-mayhem-legbuy-res-boost-tf0", 0)["deltas"]["userquote"] == -184779 and x("E-mayhem-legbuy-res-boost-tf0", 0)["deltas"]["res0ata"] == 1698 and x("E-mayhem-legbuy-res-boost-tf0", 0)["withheld"] == {}, "tf0 mayhem reserved buy costs 184779 with a 1698 gross protocol leg and no withholding")
    check(burn("E-mayhem-legbuy-res-boost-tf0", 2) == 5391854775591, "tf0 mayhem reserved buy then boost")
    check(x("E-setr-buy-boost-tf0", 1)["deltas"]["u3"] == 5315084721958 and burn("E-setr-buy-boost-tf0", 3) == 5306492329463, "tf0 setr-buy-boost matches the #115 tf0 anchors")
    # F: hop-pool boosts are reserved-list-blind.
    check(burn("F-setr-p2boost", 2) == 999997999, "P2 boost after setr is the anchor hop burn")
    check(burn("F-replace-p3boost", 2) == 999997999, "P3 boost after replacement is the anchor hop burn")
    check(burn("F-mayhem-p2boost", 1) == 999997999, "P2 boost on a mayhem-flagged hop pool is the anchor hop burn")
    check(burn("F-mhbuy-p2boost", 2) == 989418199 and burn("F-mhbuy-setr-p2boost", 3) == 989418199, "P2 boost after a buy is the post-buy hop burn with and without a mid-walk setter")
    print("PASS: 32 cases, 342 receipts, 35 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config reserved-fee fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, setr storage and gates 6005/3010/6044, boost reserved-list-blindness, mayhem multi-hop gate 6080, mayhem reserved-leg pipes, sweep-before-or-after-setter equality, tf variants, hop-pool boost reserved-list-blindness); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
