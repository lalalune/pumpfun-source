#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-buyback-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 42 cases, 375 receipts, 38 parts
  (44x10 + 7), part sha256/byte counts match the part files.
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
  lp_supply) plus the pool coin_creator bytes after every step, the
  GlobalConfig state (including boost authority 907..939 and the
  boost_enabled / disable flags), the user volume accumulator state,
  the global volume accumulator state (start/end/sec/mint/
  total_token_supply/sol_volumes), the account lengths (pool / config
  / UVA / GVA / fee-table / extend target) after every step, and the
  decoded event fields (multi-hop 508/449-byte hop events, boost
  512-byte BuyEvent + 208-byte boost event, sweep 185-byte fields,
  collect 120-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the buyback legs and boosts agree on
  all three images).
- Headline pins (see README): the hop-1 quote credit is a fixed
  9,122,164 at 10^9 quote in and the buyback leg and the protocol
  accrual split it by bps (0 -> protocol takes all, 10000 -> buyback
  takes all); a prior boost leaves the buy leg byte-identical but
  moves the sell leg 837 -> 858; the route buyback account gates by
  program (6027 for SPL or absent), mint (6009) and owner membership
  (6053, 0 events on buy, 2 ghosts on sell); a hop boost leaves the
  buyback leg unchanged on both sides; at 10^12 the buy leg is
  4,515,471,118 and at 10^6 it is 4,515; bps 10001 patched past the
  setter panics the buy (ProgramFailedToComplete) while the sell
  succeeds with the 10000 leg and the boost still burns the anchor;
  harvest clears BB22 withheld without moving the next burn, and a
  creator sweep followed by collect is a 0-event no-op.

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
            "boost_auth": raw[907:939].hex(), "boost_enabled": raw[939]}


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
                "boostauth": None, "initb": None,
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
    check(report["case_count"] == 42, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 42, "receipts": 375, "parts": 38},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 375, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 375, "report receipt_count")
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
                              "pools", "pool_creator", "cfg", "uva", "gva", "mint", "lens", "site"):
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
    # B: buyback ladder after a boost splits the fixed hop-1 credit 9122164.
    check(x("B-boost-bb0-buy", 3)["deltas"].get("bb22") is None and x("B-boost-bb0-buy", 3)["pools"]["main"] == [990877836, 9124652, 123394, SUP], "bps 0: no leg, protocol takes the whole 9122164 credit")
    check(x("B-boost-bb2500-buy", 3)["deltas"]["bb22"] == 2257735 and x("B-boost-bb2500-buy", 3)["withheld"]["bb22"] == 22806, "bps 2500 leg after boost")
    check(x("B-boost-bb7500-buy", 3)["deltas"]["bb22"] == 6773206 and x("B-boost-bb7500-buy", 3)["withheld"]["bb22"] == 68417, "bps 7500 leg after boost")
    check(x("B-boost-bb10000-buy", 3)["deltas"]["bb22"] == 9030942 and x("B-boost-bb10000-buy", 3)["pools"]["main"] == [1000000000, 2488, 123394, SUP], "bps 10000: buyback takes the whole credit, protocol bucket does not grow")
    check(x("B-boost-sell", 2)["deltas"]["bb22"] == 858 and x("B-boost-sell", 2)["deltas"]["userquote"] == 182879, "sell leg moves 837 -> 858 after a boost, payout 182879")
    check(x("B-boost-buy-buy", 3)["deltas"]["bb22"] == 4515471, "second buy after boost takes the same leg again")
    # C: route buyback-account gates.
    check("6053" in err("C-bb-nonowner-buy", "original", 0) and x("C-bb-nonowner-buy", 0)["events"] == 0, "non-owner route account fails 6053, 0 events")
    check("6053" in err("C-bb-payer-buy", "original", 0), "payer route account fails 6053")
    check("6027" in err("C-bb-spl-buy", "original", 0), "SPL route account fails 6027")
    check("6009" in err("C-bb-wrongmint-buy", "original", 0), "wrong-mint route account fails 6009")
    check("6027" in err("C-bb-absent-buy", "original", 0), "absent route account fails 6027, not 3012")
    check("6053" in err("C-bb-nonowner-sell", "original", 0) and x("C-bb-nonowner-sell", 0)["events"] == 2, "non-owner sell fails 6053 with 2 ghost events")
    check(burn("C-bb-fail-boost", 2) == 5338379201831, "failed route-account buy leaves the anchor boost")
    # D: hop boosts leave the buyback leg unchanged.
    check(x("D-p2boost-buy", 2)["deltas"]["bb22"] == 4515471 and x("D-p2boost-buy", 2)["deltas"]["u3"] == 5262894631186, "P2 boost then buy: leg unchanged, tail moves")
    check(x("D-p3boost-buy", 2)["deltas"]["bb22"] == 4515471 and x("D-p3boost-buy", 2)["deltas"]["u3"] == 5262894547951, "P3 boost then buy: leg unchanged, tail moves differently")
    check(x("D-p2boost-sell", 2)["deltas"]["bb22"] == 837 and x("D-p2boost-sell", 2)["deltas"]["userquote"] == 178542, "P2 boost then sell: leg unchanged, payout +1 (#111)")
    check(x("D-boost-p2boost-buy", 4)["deltas"]["bb22"] == 4515471, "main + P2 boost then buy: leg unchanged")
    # E: sizes.
    check(x("E-buy-huge", 0)["deltas"]["bb22"] == 4515471118 and x("E-buy-huge", 0)["withheld"]["bb22"] == 45610820, "10^12 buy leg")
    check(x("E-buy-small", 0)["deltas"]["bb22"] == 4515 and x("E-buy-small", 0)["withheld"]["bb22"] == 46, "10^6 buy leg")
    check(x("E-sell-huge", 0)["deltas"]["bb22"] == 835113 and x("E-sell-huge", 0)["deltas"]["userquote"] == 177923993, "10^12 sell leg and payout")
    check(x("E-sell-small", 0)["deltas"].get("bb22") is None and x("E-sell-small", 0)["withheld"]["bb22"] == 1 and x("E-sell-small", 0)["deltas"]["userquote"] == 178, "10^6 sell leg rounds to 0 net with 1 withheld, payout 178")
    # F: out-of-range config past the setter.
    check("ProgramFailedToComplete" in err("F-panic-buy", "original", 1) and x("F-panic-buy", 3)["deltas"]["bb22"] == 4515471, "buy at bps 10001 panics, restore returns the anchor leg")
    check(x("F-panic-sell", 1)["deltas"]["bb22"] == 1676 and x("F-panic-sell", 1)["deltas"]["userquote"] == 178541, "sell at bps 10001 succeeds with the 10000 leg, as if capped")
    check(burn("F-panic-boost", 2) == 5338379201831, "boost at bps 10001 still burns the anchor")
    check(x("F-panic-swp", 2)["pools"]["main"][1] == 0, "protocol sweep after a panicked buy discharges only the fixture 2488")
    # G: setter mid-walk after a boost.
    check(x("G-boost-bbcfg-buy", 3)["deltas"]["bb22"] == 6773206, "boost then setter 7500 then buy leg")
    check(x("G-buy-boost-bbcfg-buy", 4)["deltas"]["bb22"] == 6773206, "buy, boost, setter 7500, second buy leg")
    check("6005" in err("G-boost-bbcfg-outsider-buy", "original", 2) and x("G-boost-bbcfg-outsider-buy", 3)["deltas"]["bb22"] == 4515471, "outsider setter fails 6005, following buy is anchor")
    check("6053" in err("G-boost-bbcfg-excl-buy", "original", 3), "excluded-owner setter then buy fails 6053")
    check(x("G-bbcfg-none-boost-buy", 3)["deltas"]["bb22"] == 4515471, "None setter is a no-op, boost then buy is anchor")
    # H: harvest / sweep after a boost.
    check(x("H-boost-buy-swp", 3)["pools"]["main"][1] == 0, "boost, buy, protocol sweep discharges the full 4563570")
    check(x("H-boost-buy-harvest-boost", 3)["withheld"]["bb22"] == -45611 and burn("H-boost-buy-harvest-boost", 5) == 5173028765024, "harvest clears BB22 withheld, second boost is the #112 boost-buy-boost burn")
    check(burn("H-buy-harvest-boost", 3) == 5254679949141, "harvest does not move the post-buy boost")
    check(x("H-boost-buy-swc-col", 4)["events"] == 0, "collect after a creator sweep is a 0-event no-op")
    check(x("H-boost-buy-buy-swp", 4)["pools"]["main"][1] == 0, "boost, buy, buy, sweep discharges the cumulative 9124652")
    # I: tf variants, boost first.
    check(x("I-boost-buy-tf0", 2)["deltas"]["bb22"] == 4607153 and x("I-boost-buy-tf0", 2)["withheld"].get("bb22") is None, "tf0 boost-first buy leg, no withholding")
    check(x("I-boost-buy-tf5000", 2)["deltas"]["bb22"] == 1151788 and x("I-boost-buy-tf5000", 2)["withheld"]["bb22"] == 1151789, "tf5000 boost-first buy leg splits 50/50")
    check(x("I-boost-sell-tf5000", 2)["deltas"]["bb22"] == 430 and x("I-boost-sell-tf5000", 2)["withheld"]["bb22"] == 430 and x("I-boost-sell-tf5000", 2)["deltas"]["userquote"] == 91641, "tf5000 boost-first sell leg and payout")
    print("PASS: 42 cases, 375 receipts, 38 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, fixed hop-1 credit split by bps, boost-invariant buy leg vs boost-sensitive sell leg, route-account gates 6027/6009/6053, hop-boost buyback invariance, size ladder, bps-10001 buy panic vs sell cap, boost-blind panic config, harvest/sweep after boost, tf variants); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []")
if __name__ == "__main__":
    main()
