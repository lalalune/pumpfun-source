#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-creator-fee-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 48 cases, 375 receipts, 38 parts
  (37x10 + 5), part sha256/byte counts match the part files.
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
  lp_supply) plus the pool coin_creator bytes after every step, the
  GlobalConfig state, the user volume accumulator state, the global
  volume accumulator state, the account lengths (pool / config /
  UVA / GVA / fee-table / extend target) after every step, and the
  decoded event fields (multi-hop 5 hop events, boost 512-byte
  BuyEvent + 208-byte boost event, sweep 185-byte fields, collect
  120-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every
  case; the original agrees with both in every case (0 divergent
  cases -- a pinned-interaction packet, like #115).
- Headline pins (see README): the 5-hop creator-fee rule -- only the
  terminal hop (P5) charges the creator fee in either direction
  (buys: last hop P5; sells: first-executed hop P5), main/P2/P3/P4
  creator_fee_bps are inert, P5 10000 sells overflow 6023 with full
  rollback, the main boost burn reads buckets rather than the rate,
  the P5 boost needs the SPL-derived ATA (BA5S) on the SPL-mint hop
  pool and burns the hop anchor plus a creator-bucket nudge, the
  configurable gate falls back to the fee-table rate when off, the
  real update_creator_fee_config setter writes configurable/max with
  outsider 6005 and unsigned 3010 gates, and single-pool legs still
  charge the main creator fee.
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
             "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "boost": "boost", "boost5": "boost",
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
    check(report["case_count"] == 48, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 48, "receipts": 375, "parts": 38},
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
    check(len(grouped) == 48 * 3, f"groups {len(grouped)}")
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

    def y(label, idx):
        return get(label, "candidate", idx)

    def err(label, image, idx):
        return str(get(label, image, idx)["error"])

    def burn(summary):
        for ev in summary["decoded"] or []:
            if ev and "burned" in ev:
                return ev["burned"]
        raise AssertionError(f"no burn event in {summary}")

    # A: true-5-hop anchors (tf100, spend 1e9). Five hop events on
    # every successful swap confirm the route is really 5 hops.
    check(x("A-mhbuy5", 0)["deltas"]["u5"] == 5207955235891, "mhbuy5 tail")
    check(x("A-mhbuy5", 0)["events"] == 5, "mhbuy5 emits 5 hop events")
    check(x("A-mhsell5", 0)["deltas"]["userquote"] == 178541, "mhsell5 payout")
    check(x("A-mhsell5", 0)["events"] == 5, "mhsell5 emits 5 hop events")
    check(burn(x("A-boost", 1)) == 5338379201831, "boost anchor burn")
    check(burn(x("A-mhbuy5-boost", 2)) == 5254679949141, "buy then VQ-patch then boost burn")
    check(x("A-boost-mhbuy5", 2)["deltas"]["u5"] == 5087534167771, "boost then buy tail")
    # B: hop-pool creator-fee ladder, buys. Only P5 moves the tail.
    check(x("B-cf300-main-buy", 0)["deltas"]["u5"] == 5207955235891, "main 300 buy inert")
    check(x("B-cf300-p2-buy", 0)["deltas"]["u5"] == 5207955235891, "p2 300 buy inert")
    check(x("B-cf300-p3-buy", 0)["deltas"]["u5"] == 5207955235891, "p3 300 buy inert")
    check(x("B-cf300-p4-buy", 0)["deltas"]["u5"] == 5207955235891, "p4 300 buy inert")
    check(x("B-cf300-p5-buy", 0)["deltas"]["u5"] == 5059837684614, "p5 300 buy tail")
    check(x("B-cf300-p5-buy", 0)["pools"]["p5"][2] == 152567218652, "p5 300 buy creator bucket")
    check(x("B-cf10000-p5-buy", 0)["deltas"]["u5"] == 2614678042767, "p5 10000 buy tail roughly halved")
    check(x("B-cf10000-p5-buy", 0)["pools"]["p5"][2] == 2621532629315, "p5 10000 buy creator bucket")
    # C: the main boost burn reads buckets, not the creator rate.
    check(burn(x("C-cf300-main-buy-boost", 2)) == 5254679949141, "main 300 buy then boost = anchor post-buy burn")
    check(burn(x("C-cf300-p5-buy-boost", 2)) == 5254679949141, "p5 300 buy then main boost = anchor post-buy burn")
    check(burn(x("C-cf10000-p5-buy-boost", 2)) == 5254679949141, "p5 10000 buy then main boost = anchor post-buy burn")
    # D: sells. Only P5 moves the payout (first-executed hop); P5 10000 overflows.
    check(x("D-cf300-main-sell", 0)["deltas"]["userquote"] == 178541, "main 300 sell inert")
    check(x("D-cf300-p4-sell", 0)["deltas"]["userquote"] == 178541, "p4 300 sell inert")
    check(x("D-cf300-p5-sell", 0)["deltas"]["userquote"] == 173260, "p5 300 sell payout")
    check(x("D-cf300-p5-sell", 0)["pools"]["p5"][2] == 30123364, "p5 300 sell creator bucket")
    check("6023" in err("D-cf10000-p5-sell", "original", 0), "p5 10000 sell overflows 6023")
    check(x("D-cf10000-p5-sell", 0)["events"] == 0, "p5 10000 sell 0 events, full rollback")
    # E: mid-walk p5 fee edits. The second-buy burn is identical no
    # matter what the second buy's fee was: the main boost reads main
    # buckets only.
    check(x("E-buy-p5cf300-buy-boost", 2)["deltas"]["u5"] == 4778179428711, "buy, patch p5 300, second buy tail")
    check(burn(x("E-buy-p5cf300-buy-boost", 4)) == 5172933848347, "buy, patch p5 300, second buy then boost")
    check(burn(x("E-boost-p5cf300-buy-boost", 5)) == 5173028765024, "boost, patch p5 300, buy then boost")
    check(x("E-p5cf300-buy-p5cf0-buy-boost", 2)["deltas"]["u5"] == 4919551558605, "p5 300 buy, patch 0, second buy tail")
    check(burn(x("E-p5cf300-buy-p5cf0-buy-boost", 4)) == 5172933848347, "p5 300 buy, patch 0, second buy then boost")
    check(x("E-p5cf300-buy-p5cf10000-buy-boost", 2)["deltas"]["u5"] == 2469558059660, "p5 300 buy, patch 10000, second buy tail")
    check(burn(x("E-p5cf300-buy-p5cf10000-buy-boost", 4)) == 5172933848347, "p5 300 buy, patch 10000, second buy then boost")
    # F: configurable gate and the real setter.
    check(x("F-p5cf300-noconfig-buy", 0)["deltas"]["u5"] == 5207955235891, "configurable off falls back to fee-table rate")
    check(x("F-p5cf300-config-buy", 0)["deltas"]["u5"] == 5059837684614, "configurable on applies p5 300")
    check(x("F-ucfc-off-p5cf300-buy", 0)["error"] is None, "ucfc off succeeds")
    check(x("F-ucfc-off-p5cf300-buy", 1)["deltas"]["u5"] == 5207955235891, "ucfc off then buy = anchor tail")
    check(x("F-ucfc-on-p5cf300-buy", 1)["deltas"]["u5"] == 5059837684614, "ucfc on then buy = p5 300 tail")
    check("6005" in err("F-ucfc-outsider-buy", "original", 0), "ucfc outsider 6005")
    check(x("F-ucfc-outsider-buy", 1)["deltas"]["u5"] == 5059837684614, "outsider setter leaves config, buy = p5 300 tail")
    check("3010" in err("F-ucfc-unsigned-buy", "original", 0), "ucfc unsigned 3010")
    check(x("F-ucfc-unsigned-buy", 1)["deltas"]["u5"] == 5059837684614, "unsigned setter leaves config, buy = p5 300 tail")
    # G: the GlobalConfig creator_fee field alone moves nothing.
    check(burn(x("G-cfgcf0-buy-boost", 2)) == 5254679949141, "config creator_fee 0 buy then boost = anchor")
    check(burn(x("G-cfgcf10000-buy-boost", 2)) == 5254679949141, "config creator_fee 10000 buy then boost = anchor")
    # H: p5 sweeps/collects never move the MAIN boost (p5 fees never
    # touch main buckets), but they discharge in full.
    check(x("H-p5cf300-buy-swc5-col5-boost", 1)["deltas"]["creatorata5"] == 152567218652, "p5 300 buy creator sweep discharges full bucket")
    check(x("H-p5cf300-buy-swc5-col5-boost", 2)["deltas"]["dest5"] == 152567218652, "p5 300 buy collect pays full bucket")
    check(burn(x("H-p5cf300-buy-swc5-col5-boost", 4)) == 5254679949141, "p5 sweep+collect then main boost = anchor post-buy burn")
    check(x("H-p5cf300-buy-swp5-boost", 1)["deltas"]["protoata5"] == 2488, "p5 protocol sweep discharges fixture 2488")
    check(burn(x("H-p5cf300-buy-swp5-boost", 3)) == 5254679949141, "p5 protocol sweep then main boost = anchor post-buy burn")
    check(x("H-cf0-buy-swc5-col5-boost", 1)["deltas"]["creatorata5"] == 2617733408, "cf0 buy creator sweep discharges fee-table bucket")
    check(burn(x("H-cf0-buy-swc5-col5-boost", 4)) == 5254679949141, "cf0 sweep+collect then main boost = anchor post-buy burn")
    # I: p5 boosts need the SPL-derived ATA; the burn is the hop
    # anchor plus a creator-bucket nudge.
    check(burn(x("I-p5boost-anchor", 1)) == 999997999, "p5 boost anchor")
    check(burn(x("I-cf300-main-buy-p5boost", 2)) == 989596358, "main 300 buy then p5 boost")
    check(burn(x("I-p5cf300-buy-p5boost", 2)) == 989743701, "p5 300 buy then p5 boost = main-buy p5 boost + 147343")
    check(burn(x("I-p5cf10000-buy-p5boost", 2)) == 992176090, "p5 10000 buy then p5 boost")
    # J: tf variants under a p5 creator fee.
    check(x("J-p5cf300-buy-tf0-boost", 0)["deltas"]["u5"] == 5109477485375, "p5 300 buy tf0 tail")
    check(burn(x("J-p5cf300-buy-tf0-boost", 2)) == 5306492329463, "p5 300 buy tf0 then boost")
    check(x("J-p5cf300-buy-tf5000-boost", 0)["deltas"]["u5"] == 2592005765796, "p5 300 buy tf5000 tail")
    check(burn(x("J-p5cf300-buy-tf5000-boost", 2)) == 2685165599125, "p5 300 buy tf5000 then boost")
    # K: single-pool legs DO charge the main creator fee.
    check(x("K-cf300-legbuy", 0)["deltas"]["userquote"] == -191550, "legacy buy at 300 quote paid")
    check(x("K-cf300-legbuy", 0)["deltas"]["userbase"] == 1000000000, "legacy buy at 300 base out")
    check(x("K-cf300-buy2", 0)["deltas"]["userquote"] == -191614, "v2 buy at 300 quote paid")
    check(x("K-cf300-buy2", 0)["pools"]["main"][2] == 128869, "v2 buy at 300 accrues to main creator bucket")
    # L: walks under a p5 creator fee.
    check(x("L-p5cf300-buy-sell-boost", 1)["deltas"]["userquote"] == 183568, "p5 300 buy then sell payout")
    check(burn(x("L-p5cf300-buy-sell-boost", 3)) == 5254695659101, "p5 300 buy-sell then boost")
    check(burn(x("L-p5cf300-sell-boost", 2)) == 5338394385335, "p5 300 sell then boost")
    check(x("L-p5cf300-buy-buy-boost", 1)["deltas"]["u5"] == 4779600400262, "p5 300 buy-buy second tail")
    check(burn(x("L-p5cf300-buy-buy-boost", 3)) == 5172933848347, "p5 300 buy-buy then boost")
    check(burn(x("L-p5cf300-boost-boost", 3)) == 5254441549265, "p5 300 boost-boost second burn")
    # M: terminal-hop sells then boosts; a failed sell leaves no residue.
    check(burn(x("M-p5cf300-sell-boost", 2)) == 5338394385335, "p5 300 sell then boost")
    check("6023" in err("M-p5cf10000-sell-boost", "original", 0), "p5 10000 sell overflows, then boost")
    check(burn(x("M-p5cf10000-sell-boost", 2)) == 5338379201831, "failed p5 10000 sell then boost = anchor")
    check(burn(x("M-p5cf300-buy-p5boost-boost", 2)) == 989743701, "p5 300 buy then p5 boost in a longer walk")
    check(burn(x("M-p5cf300-buy-p5boost-boost", 4)) == 5254679949141, "p5 boost does not move the following main boost")
    print("PASS: 48 cases, 375 receipts, 38 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, "
          "terminal-hop-only creator fee at depth 5 (P5 lever both directions, "
          "main/P2/P3/P4 inert), P5 10000 sell Overflow 6023, boost reads buckets "
          "not the rate, P5 boost SPL-ATA burn ladder, configurable fallback, "
          "update_creator_fee_config gates 6005/3010, sweep/collect discharge, "
          "tf variants, single-pool creator-fee legs); "
          "control == candidate everywhere; original agrees everywhere; "
          "(0 divergent cases): []")
if __name__ == "__main__":
    main()
