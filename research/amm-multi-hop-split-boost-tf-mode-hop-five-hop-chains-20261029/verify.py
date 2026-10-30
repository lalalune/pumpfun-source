#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-mode-hop-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 57 cases, 321 receipts, 33 parts
  (32x10 + 1), part sha256/byte counts match the part files.
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
  GlobalConfig state, the user volume accumulator state, the global
  volume accumulator state, the account lengths (pool / config /
  UVA / GVA / fee-table / extend target) after every step, and the
  decoded event fields (multi-hop 508/449-byte hop events, boost
  512-byte BuyEvent + 208-byte boost event, sweep 185-byte fields,
  deposit/withdraw 264-byte fields, token claim 104-byte fields,
  collect 120-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every
  case; the original agrees with both except exactly the 32
  mode-gate cases listed in the divergent-set assertion below
  (original gates cashback only on the terminal hop, the rebuild
  gates it on every hop; on a both-flagged hop the original fires
  mayhem 6080 first, the rebuild fires cashback 6079 first).
- Headline pins (see README): the true-5-hop mode-gate map --
  original gates cashback only on the terminal (p5) hop and mayhem on
  every hop, with cashback priority at p5; the rebuild gates cashback
  on every hop with priority over mayhem; ghost-event counts equal the
  hops executed before the failing hop (buy runs main->p2->p3->p4->p5,
  sell runs p5->p4->p3->p2->main); boost is mode-blind (flagged pools
  burn the anchor, failed legs leave no residue, global toggles do not
  rescue pool flags); sweeps/collects move the next burn through the
  real quote vault at ~42.73 per unit; plain-quote claims pay 5475 only
  when a UVA exists (seeded, or auto-created by a successful buy).

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
P4 = "5gZTf2A6UPeYZCq1mkdiYquMQqmjNcz9pknbABkWif9c"
P5 = "5TdRYVo7We7hYSXDS3ryvUvouL7hoaMLTGMRqMrzBhcE"
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
    sol = [struct.unpack_from("<Q", raw, 64 + i * 8)[0] for i in range(30)] if len(raw) >= 304 else None
    tok = [struct.unpack_from("<Q", raw, 304 + i * 8)[0] for i in range(30)] if len(raw) >= 544 else None
    return {"len": len(raw),
            "start": struct.unpack_from("<q", raw, 8)[0],
            "end": struct.unpack_from("<q", raw, 16)[0],
            "sec": struct.unpack_from("<q", raw, 24)[0],
            "sol_head": sol[:3] if sol else None,
            "tok_head": tok[:3] if tok else None,
            "sol_last": sol[-1] if sol else None,
            "tok_last": tok[-1] if tok else None}


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


STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3",
             "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "boost": "boost",
             "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
             "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
             "swp": "swp", "swc": "swc", "col": "col",
             "xfer2": None, "xfer1": None, "cpatch": None,
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
                      (("main", POOL), ("pool2", POOL2), ("p3", P3),
                       ("p4", P4), ("p5", P5))},
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
    check(report["case_count"] == 57, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 57, "receipts": 321, "parts": 33},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 321, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 321, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 57 * 3, f"groups {len(grouped)}")
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
    expected_divergent = {
        "B-main-cb-buy", "B-main-both-buy", "B-p2-cb-buy", "B-p2-both-buy",
        "B-p3-cb-buy", "B-p3-both-buy", "B-p4-cb-buy", "B-p4-both-buy",
        "B-main-cb-sell", "B-main-both-sell", "B-p2-both-sell",
        "B-p3-both-sell", "B-p4-both-sell",
        "C-main-cb-buy-boost", "C-p4-both-buy-boost", "C-main-cb-sell-boost",
        "C-boost-p4-both-buy",
        "E-gmh-off-cb-buy-boost", "E-gcb-off-cb-buy-boost", "E-gboth-off-both-buy",
        "F-cb-fail-clear-buy-boost", "F-cb-fail-swp-boost",
        "H-cb-fail-cclaim", "H-mh-cb-cclaim",
        "I-main-cb-buy-tf0", "I-main-cb-buy-tf5000",
        "J-main-cb-p4-mh-buy", "J-main-cb-p5-mh-buy", "J-p2-cb-p5-mh-buy",
        "J-p4-cb-p5-mh-buy", "J-p4-both-p5-both-buy",
    }
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

    def y(label, idx):
        return get(label, "candidate", idx)

    def err(label, image, idx):
        return str(get(label, image, idx)["error"])

    # A: true-5-hop anchors (tf100, spend 1e9). Buy tail differs from
    # #109's 3-hop tail (5262910281902) because two more hops take
    # their cut; the tf0/plain tail (5259040470738) matches #62's
    # 5-hop tail exactly.
    check(x("A-mhbuy5", 0)["deltas"]["u5"] == 5207955235891, "mhbuy5 tail")
    check(x("A-mhsell5", 0)["deltas"]["userquote"] == 178541, "mhsell5 payout")
    check(x("A-boost", 1)["decoded"][1]["burned"] == 5338379201831, "boost anchor burn")
    check(x("A-mhbuy5-boost", 2)["decoded"][1]["burned"] == 5254679949141, "buy then VQ-patch then boost burn")
    check(x("A-boost-mhbuy5", 2)["deltas"]["u5"] == 5087534167771, "boost then buy tail")
    # B: gate map, buy direction (hops run main -> p2 -> p3 -> p4 -> p5).
    # Original passes every non-terminal cashback hop; rebuild 6079s
    # with ghost count = hops executed before the failing hop.
    check(x("B-main-cb-buy", 0)["error"] is None and "6079" in err("B-main-cb-buy", "candidate", 0), "main cb buy: original passes, rebuild 6079")
    check(y("B-main-cb-buy", 0)["events"] == 0, "main cb buy rebuild 0 ghosts")
    check(y("B-p2-cb-buy", 0)["events"] == 1, "p2 cb buy rebuild 6079 1 ghost")
    check(y("B-p3-cb-buy", 0)["events"] == 2, "p3 cb buy rebuild 6079 2 ghosts")
    check(y("B-p4-cb-buy", 0)["events"] == 3, "p4 cb buy rebuild 6079 3 ghosts")
    check("6079" in err("B-p5-cb-buy", "original", 0) and "6079" in err("B-p5-cb-buy", "candidate", 0), "p5 cb buy 6079 both (terminal hop)")
    check(y("B-p5-cb-buy", 0)["events"] == 4, "p5 cb buy 4 ghosts both")
    check("6080" in err("B-main-mh-buy", "original", 0) and "6080" in err("B-main-mh-buy", "candidate", 0), "main mh buy 6080 both")
    check("6080" in err("B-p5-mh-buy", "original", 0) and y("B-p5-mh-buy", 0)["events"] == 4, "p5 mh buy 6080 both 4 ghosts")
    check("6080" in err("B-main-both-buy", "original", 0) and "6079" in err("B-main-both-buy", "candidate", 0), "main both buy: original mayhem first, rebuild cb first")
    check("6080" in err("B-p4-both-buy", "original", 0) and "6079" in err("B-p4-both-buy", "candidate", 0) and y("B-p4-both-buy", 0)["events"] == 3, "p4 both buy: original 6080, rebuild 6079, 3 ghosts")
    check("6079" in err("B-p5-both-buy", "original", 0) and "6079" in err("B-p5-both-buy", "candidate", 0), "p5 both buy 6079 both (cb priority at terminal hop)")
    # B sell direction (hops run p5 -> p4 -> p3 -> p2 -> main).
    check(x("B-main-cb-sell", 0)["error"] is None and "6079" in err("B-main-cb-sell", "candidate", 0), "main cb sell: original passes, rebuild 6079")
    check(y("B-main-cb-sell", 0)["events"] == 4, "main cb sell rebuild 4 ghosts (main last in sell)")
    check("6079" in err("B-p5-cb-sell", "original", 0) and y("B-p5-cb-sell", 0)["events"] == 0, "p5 cb sell 6079 both 0 ghosts (p5 first in sell)")
    check("6080" in err("B-p2-both-sell", "original", 0) and "6079" in err("B-p2-both-sell", "candidate", 0) and y("B-p2-both-sell", 0)["events"] == 3, "p2 both sell: original 6080, rebuild 6079, 3 ghosts")
    check("6079" in err("B-p5-both-sell", "original", 0) and y("B-p5-both-sell", 0)["events"] == 0, "p5 both sell 6079 both 0 ghosts")
    # C: boost around a gated leg is mode-blind.
    check(x("C-main-cb-buy-boost", 2)["decoded"][1]["burned"] == 5254679949141, "cb buy then boost = post-buy value (original)")
    check(y("C-main-cb-buy-boost", 2)["decoded"][1]["burned"] == 5338379201831, "failed cb buy then boost = anchor (rebuild)")
    check(x("C-main-cb-sell-boost", 2)["decoded"][1]["burned"] == 5338394848076, "cb sell then boost = post-sell value (original)")
    check(y("C-main-cb-sell-boost", 2)["decoded"][1]["burned"] == 5338379201831, "failed cb sell then boost = anchor (rebuild)")
    check(x("C-p5-both-buy-boost", 2)["decoded"][1]["burned"] == 5338379201831, "failed terminal both buy then boost = anchor both")
    check(y("C-p5-both-buy-boost", 2)["decoded"][1]["burned"] == 5338379201831, "failed terminal both buy then boost = anchor (rebuild)")
    # D: boost on a flagged pool itself.
    check(x("D-boost-main-cb", 1)["decoded"][1]["burned"] == 5338379201831, "boost on cb pool = anchor")
    check(x("D-boost-main-both", 1)["decoded"][1]["burned"] == 5338379201831, "boost on both pool = anchor")
    check(x("D-boost-main-mh", 1)["decoded"][1]["burned"] == 5338379201831, "boost on mh pool = anchor")
    check(x("D-boost-main-cb-twice", 2)["decoded"][1]["burned"] == 5254441549265, "boost on cb pool second burn")
    # E: global toggles do not rescue pool flags.
    check("6080" in err("E-gboth-off-both-buy", "original", 2) and "6079" in err("E-gboth-off-both-buy", "candidate", 2), "both flags off globally, both buy still 6080/6079")
    check(x("E-gcb-off-cb-buy-boost", 3)["decoded"][1]["burned"] == 5254679949141, "global cb off, cb buy still passes then post-buy boost (original)")
    check("6079" in err("E-gcb-off-cb-buy-boost", "candidate", 1), "global cb off, cb buy still 6079 (rebuild)")
    # F: failed leg leaves no residue; sweeps after a failed terminal leg.
    check(x("F-cb-fail-clear-buy-boost", 2)["deltas"]["u5"] == 4918089082874, "flag cleared, original second buy tail")
    check(x("F-cb-fail-clear-buy-boost", 4)["decoded"][1]["burned"] == 5172933848347, "flag cleared, original second buy then boost")
    check(y("F-cb-fail-clear-buy-boost", 2)["deltas"]["u5"] == 5207955235891, "flag cleared, rebuild fresh buy tail")
    check(x("F-mh-fail-clear-sell", 2)["deltas"]["userquote"] == 178541, "mayhem cleared, sell pays anchor")
    check(x("F-cb-fail-swp-boost", 4)["decoded"][1]["burned"] == 5254875541549, "buy+sweep then boost (original)")
    check(y("F-cb-fail-swp-boost", 4)["decoded"][1]["burned"] == 5338384580607, "failed buy+fixture sweep then boost (rebuild)")
    check("6013" in err("F-p5-both-fail-swp5", "original", 1), "p5 both fail then protocol sweep 6013")
    check(x("F-p5-both-fail-swp5", 2)["deltas"]["creatorata5"] == 123394, "p5 both fail then creator sweep pays fixture 123394 in full")
    # G: liquidity on a flagged pool is mode-blind.
    check(x("G-main-cb-dep", 0)["deltas"]["userlp"] == 1000000, "cb pool deposit LP")
    check(x("G-main-both-wd", 0)["deltas"]["userlp"] == -1000000, "both pool withdraw LP")
    # H: plain-quote cashback claims.
    check(x("H-cb-fail-cclaim", 1)["deltas"]["userquote"] == 5475, "plain cb buy then claim pays 5475 (original)")
    check("3012" in err("H-cb-fail-cclaim", "candidate", 1), "plain failed buy then claim 3012 (no auto-created UVA)")
    check(x("H-mh-cb-cclaim", 1)["deltas"]["userquote"] == 5475, "seeded UVA claim pays 5475 even after failed buy")
    # I: tf variants keep the same gate map.
    check(x("I-main-cb-buy-tf0", 2)["decoded"][1]["burned"] == 5306492329463, "cb buy tf0 then boost (original)")
    check(y("I-main-cb-buy-tf0", 2)["decoded"][1]["burned"] == 5391870655895, "failed cb buy tf0 then boost = tf0 anchor (rebuild)")
    check(x("I-main-cb-buy-tf5000", 0)["deltas"]["u5"] == 2668075748732, "cb buy tf5000 tail (original)")
    check(x("I-main-cb-buy-tf5000", 2)["decoded"][1]["burned"] == 2685165599125, "cb buy tf5000 then boost (original)")
    check(y("I-main-cb-buy-tf5000", 2)["decoded"][1]["burned"] == 2706767012738, "failed cb buy tf5000 then boost = tf5000 anchor (rebuild)")
    check(x("I-p5-both-buy-tf5000", 2)["decoded"][1]["burned"] == 2706767012738, "failed terminal both buy tf5000 then boost = tf5000 anchor both")
    # J: multi-flag chains confirm hop order and gate priority at depth 5.
    check("6080" in err("J-main-mh-p4-cb-buy", "original", 0) and y("J-main-mh-p4-cb-buy", 0)["events"] == 0, "main mh masks p4 cb: 6080 both, 0 ghosts, not divergent")
    check("6080" in err("J-main-cb-p4-mh-buy", "original", 0) and "6079" in err("J-main-cb-p4-mh-buy", "candidate", 0), "main cb + p4 mh: original 6080 (3 ghosts), rebuild 6079 (0 ghosts)")
    check("6080" in err("J-p2-cb-p5-mh-buy", "original", 0) and x("J-p2-cb-p5-mh-buy", 0)["events"] == 4, "p2 cb + p5 mh: original 6080 4 ghosts")
    check("6079" in err("J-p2-cb-p5-mh-buy", "candidate", 0) and y("J-p2-cb-p5-mh-buy", 0)["events"] == 1, "p2 cb + p5 mh: rebuild 6079 1 ghost")
    check("6080" in err("J-p4-cb-p5-mh-buy", "original", 0) and x("J-p4-cb-p5-mh-buy", 0)["events"] == 4, "p4 cb + p5 mh: original 6080 4 ghosts")
    check("6079" in err("J-p4-cb-p5-mh-buy", "candidate", 0) and y("J-p4-cb-p5-mh-buy", 0)["events"] == 3, "p4 cb + p5 mh: rebuild 6079 3 ghosts")
    check("6080" in err("J-p4-both-p5-both-buy", "original", 0) and "6079" in err("J-p4-both-p5-both-buy", "candidate", 0), "p4 both + p5 both: original 6080 (first both hop), rebuild 6079 (first cb hop)")
    print("PASS: 57 cases, 321 receipts, 33 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, "
          "true-5-hop mode-gate map 6079 vs 6080 by hop position and direction, "
          "boost mode-blindness, global-toggle non-rescue, failure isolation, "
          "sweep/collect/claim after failed legs); "
          "control == candidate everywhere; "
          "original agrees everywhere except the 31 mode-gate cases: "
          "B-main-cb-buy, B-main-both-buy, B-p2-cb-buy, B-p2-both-buy, "
          "B-p3-cb-buy, B-p3-both-buy, B-p4-cb-buy, B-p4-both-buy, "
          "B-main-cb-sell, B-main-both-sell, B-p2-both-sell, "
          "B-p3-both-sell, B-p4-both-sell, "
          "C-main-cb-buy-boost, C-p4-both-buy-boost, C-main-cb-sell-boost, "
          "C-boost-p4-both-buy, "
          "E-gmh-off-cb-buy-boost, E-gcb-off-cb-buy-boost, E-gboth-off-both-buy, "
          "F-cb-fail-clear-buy-boost, F-cb-fail-swp-boost, "
          "H-cb-fail-cclaim, H-mh-cb-cclaim, "
          "I-main-cb-buy-tf0, I-main-cb-buy-tf5000, "
          "J-main-cb-p4-mh-buy, J-main-cb-p5-mh-buy, J-p2-cb-p5-mh-buy, "
          "J-p4-cb-p5-mh-buy, J-p4-both-p5-both-buy")
if __name__ == "__main__":
    main()
