#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-gva-lifecycle-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 60 cases, 294 receipts, 30 parts
  (29x10 + 4), part sha256/byte counts match the part files.
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
  volume accumulator state (start/end/sec/mint/total_token_supply/
  sol_volumes), the account lengths (pool / config / UVA / GVA /
  fee-table / extend target) after every step, and the decoded event
  fields (multi-hop 508/449-byte hop events, boost 512-byte BuyEvent
  + 208-byte boost event, sweep 185-byte fields, deposit/withdraw
  264-byte fields, token claim 104-byte fields, collect 120-byte
  fields, admin-update 88-byte fields, sync 64-byte fields, close
  80-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the GVA lifecycle paths agree on all
  three images).
- Headline pins (see README): no init/close instruction exists for
  the GVA, so an absent GVA breaks claim, sync and admin with 3012
  while trades and boost stay anchor; the admin gate map
  (6030/6031/6032/6033/6035/6036/6037/6005/3010); a start change wipes
  all supplies and sol_volumes and the next claim pays only the seeded
  unclaimed 111; mid-range admin zeroes future sol_volumes only and
  sets one supply slot; supply-slot edits move the next claim reward
  (day-0 2000 -> 6668991, all-days 500 -> 1667331); mint rotation
  breaks claims with 6038 and restoration re-enables them; sync fires
  only when now < start and last < start; closing the UVA strands its
  unclaimed 111, breaks the next claim with 3012, and re-init never
  restores it, while the next chain buy recreates a fresh UVA and the
  boost stays anchor.

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
    check(report["case_count"] == 60, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 60, "receipts": 294, "parts": 30},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 294, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 294, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 60 * 3, f"groups {len(grouped)}")
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

    IMINT_HEX = "e2" * 32
    # A: anchors (tf100, spend 1e9, fixture GVA start 20 end 49 sec 1).
    check(x("A-mhbuy", 0)["deltas"]["u3"] == 5262910281902, "mhbuy tail")
    check(x("A-mhsell", 0)["deltas"]["userquote"] == 178541, "mhsell payout")
    check(x("A-boost", 1)["decoded"][1]["burned"] == 5338379201831, "boost anchor burn")
    check(x("A-tclaim", 0)["decoded"][0]["amount"] == 3334551, "tclaim amount")
    check(x("A-tclaim", 0)["uva"] == {"needs": 0, "unclaimed": 0, "claimed": 3334773, "volume": 0, "last": 21, "has": 1, "earned": 555, "cb_claimed": 666}, "tclaim UVA after")
    check(x("A-sync-noop", 0)["events"] == 0, "sync noop when last == start")
    check(x("A-sync-reset", 0)["decoded"][0]["before"] == 222 and x("A-sync-reset", 0)["decoded"][0]["after"] == 0, "sync reset 222 -> 0")
    check(x("A-tclaim-twice", 1)["events"] == 0 and x("A-tclaim-twice", 1)["deltas"] == {}, "second claim is a no-op")
    # B: absent / zeroed / truncated / wrong-owner GVA.
    check(x("B-absent-mhbuy", 0)["deltas"]["u3"] == 5262910281902, "absent GVA mhbuy anchor")
    check(x("B-absent-boost", 1)["decoded"][1]["burned"] == 5338379201831, "absent GVA boost anchor")
    check("3012" in err("B-absent-tclaim", "original", 0), "absent GVA tclaim 3012")
    check("3012" in err("B-absent-sync", "original", 0), "absent GVA sync 3012")
    check("3012" in err("B-absent-admin", "original", 0), "absent GVA admin 3012: no re-init path")
    check(x("B-absent-swp-col-dep", 0)["deltas"]["proto22"] == 2463, "absent GVA protocol sweep")
    check(x("B-absent-swp-col-dep", 2)["deltas"]["dest22"] == 120938, "absent GVA collect")
    check(x("B-zeroed-tclaim", 0)["decoded"][0]["amount"] == 111, "zeroed GVA tclaim pays unclaimed only")
    check(x("B-zeroed-tclaim", 0)["uva"]["volume"] == 333444 and x("B-zeroed-tclaim", 0)["uva"]["needs"] == 1, "zeroed GVA tclaim keeps volume, needs stays 1")
    check(x("B-zeroed-sync", 0)["events"] == 0, "zeroed GVA sync noop (start 0)")
    check(x("B-zeroed-admin-tclaim", 1)["decoded"][0]["amount"] == 111, "admin from zeroed GVA does not restore conversion")
    check(x("B-trunc-mhbuy", 0)["deltas"]["u3"] == 5262910281902, "truncated GVA mhbuy anchor")
    check("3003" in err("B-trunc-tclaim", "original", 0), "truncated GVA tclaim 3003")
    check("3003" in err("B-trunc-admin", "original", 0), "truncated GVA admin 3003")
    check("3007" in err("B-owner-tclaim", "original", 0), "wrong-owner GVA tclaim 3007")
    check(x("B-owner-mhbuy", 0)["deltas"]["u3"] == 5262910281902, "wrong-owner GVA mhbuy anchor")
    # C: admin gates and effects.
    check(x("C-same-start", 0)["gva"]["supply"][0] == 1000 and x("C-same-start", 0)["gva"]["vol"][0] == 100, "same-start admin leaves GVA unchanged")
    check(x("C-new-end-tclaim", 0)["gva"]["end"] == 40, "new-end admin end 40")
    check(x("C-new-end-tclaim", 1)["decoded"][0]["amount"] == 3334551, "new-end then claim normal")
    check(x("C-start-wipe-tclaim-sync", 0)["gva"]["supply"] == [0] * 30 and x("C-start-wipe-tclaim-sync", 0)["gva"]["vol"] == [0] * 30, "start change wipes supplies and vols")
    check(x("C-start-wipe-tclaim-sync", 1)["decoded"][0]["amount"] == 111, "wiped GVA claim pays 111 only")
    check(x("C-start-wipe-tclaim-sync", 1)["uva"]["volume"] == 333444, "wiped GVA claim keeps volume")
    check(x("C-start-wipe-tclaim-sync", 2)["decoded"][0]["before"] == 111 and x("C-start-wipe-tclaim-sync", 2)["decoded"][0]["after"] == 0, "sync after wipe resets 111 -> 0")
    check(x("C-supply-day0-tclaim", 0)["gva"]["supply"][0] == 2000, "supply day0 2000")
    check(x("C-supply-day0-tclaim", 1)["decoded"][0]["amount"] == 6668991 and x("C-supply-day0-tclaim", 1)["uva"]["claimed"] == 6669213, "supply day0 claim 6668991")
    check(x("C-supply-all-tclaim", 0)["gva"]["supply"] == [500] * 30, "supply all-days 500")
    check(x("C-supply-all-tclaim", 1)["decoded"][0]["amount"] == 1667331 and x("C-supply-all-tclaim", 1)["uva"]["claimed"] == 1667553, "supply all claim 1667331")
    check(x("C-midrange-zero-tclaim", 0)["gva"]["supply"][7] == 777, "midrange supply slot 7 = 777")
    check(x("C-midrange-zero-tclaim", 0)["gva"]["vol"][5] == 100 and x("C-midrange-zero-tclaim", 0)["gva"]["vol"][6] == 0 and x("C-midrange-zero-tclaim", 0)["gva"]["vol"][29] == 0, "midrange zeroes future vols only")
    check(x("C-midrange-zero-tclaim", 1)["decoded"][0]["amount"] == 3334551, "midrange then day-0 claim normal")
    check("6030" in err("C-start-past", "original", 0), "start in past 6030")
    check("6031" in err("C-end-past", "original", 0), "end in past 6031")
    check("6032" in err("C-end-before-start", "original", 0), "end before start 6032")
    check("6033" in err("C-range-large", "original", 0), "range too large 6033")
    check("6035" in err("C-supply-finished", "original", 0), "supply for finished range 6035")
    check("6036" in err("C-day-after-end", "original", 0), "day after end 6036")
    check("6037" in err("C-day-active", "original", 0), "day in active range 6037")
    check("6005" in err("C-outsider", "original", 0), "outsider admin 6005")
    check("3010" in err("C-unsigned", "original", 0), "unsigned admin 3010")
    check(x("C-mint-rotate", 0)["dPAYER"] == -2162600, "mint rotation admin pays ATA rent")
    check(x("C-mint-rotate", 0)["gva"]["mint"] != IMINT_HEX, "mint rotated away from IMINT")
    check("6038" in err("C-mint-rotate", "original", 1), "rotated mint claim 6038")
    check(x("C-mint-rotate", 2)["gva"]["mint"] == IMINT_HEX, "mint restored")
    check(x("C-mint-rotate", 3)["decoded"][0]["amount"] == 3334551, "restored mint claim normal")
    check(x("C-admin-boost", 2)["decoded"][1]["burned"] == 5338379201831, "admin then boost anchor")
    check(x("C-admin-mhbuy", 1)["deltas"]["u3"] == 5262910281902, "admin then mhbuy anchor")
    # D: claim lifecycle.
    check(x("D-claim-after-mhbuy", 1)["decoded"][0]["amount"] == 3334551, "claim after mhbuy pays seeded conversion only")
    check(x("D-claim-after-boost", 2)["decoded"][0]["amount"] == 3334551, "claim after boost pays seeded conversion only")
    check(x("D-claim-after-swp", 2)["decoded"][0]["amount"] == 3334551, "claim after sweeps pays seeded conversion only")
    check("3012" in err("D-claim-ga-absent", "original", 0), "claim with absent incentive ATA vault 3012")
    check("1" in err("D-claim-ga-empty", "original", 0) and "Custom(1)" in err("D-claim-ga-empty", "original", 0), "claim with empty vault fails token insufficient funds")
    check(x("D-claim-uata-absent", 0)["dPAYER"] == -2162600 and x("D-claim-uata-absent", 0)["decoded"][0]["amount"] == 3334551, "claim auto-creates user ATA then pays")
    check("6038" in err("D-claim-mint-mismatch", "original", 0), "seeded wrong-mint GVA claim 6038")
    # E: sync lifecycle.
    check(x("E-sync-after-claim-admin", 2)["decoded"][0]["before"] == 3334773 and x("E-sync-after-claim-admin", 2)["decoded"][0]["after"] == 0, "sync after claim+start-change resets 3334773 -> 0")
    check("3012" in err("E-sync-absent-gva", "original", 0), "sync absent GVA 3012")
    check(x("E-sync-zeroed-gva", 0)["events"] == 0, "sync zeroed GVA noop")
    # F: UVA close lifecycle.
    check(x("F-close-seeded", 0)["dPAYER"] == 999995000, "close refunds UVA lamports minus fee")
    check(x("F-close-seeded", 0)["decoded"][0]["unc"] == 111 and x("F-close-seeded", 0)["decoded"][0]["claimed"] == 222 and x("F-close-seeded", 0)["decoded"][0]["vol"] == 333444, "close event carries seeded state")
    check(x("F-close-seeded", 0)["uva"] is None, "close removes UVA")
    check("3012" in err("F-close-then-tclaim", "original", 1), "claim after close 3012")
    check(x("F-close-then-mhbuy", 1)["deltas"]["u3"] == 5262910281902, "mhbuy after close recreates UVA and tails anchor")
    check(x("F-close-mhbuy-tclaim", 2)["events"] == 0 and x("F-close-mhbuy-tclaim", 2)["uva"]["claimed"] == 0, "claim after close+mhbuy is a fresh no-op")
    check(x("F-close-init-tclaim", 1)["dPAYER"] == -1849400, "re-init after close pays UVA rent")
    check(x("F-close-init-tclaim", 2)["events"] == 0, "re-init claim never restores stranded 111")
    check("2006" in err("F-close-other", "original", 0), "close by other user 2006 seeds")
    check("3010" in err("F-close-unsigned", "original", 0), "close unsigned 3010")
    check(x("F-close-boost", 2)["decoded"][1]["burned"] == 5338379201831, "close then boost anchor")
    # G: GVA-blind chain legs.
    check(x("G-absent-dep-wd", 0)["deltas"]["userlp"] == 1000000, "absent GVA deposit LP")
    check(x("G-absent-dep-wd", 1)["deltas"]["userlp"] == -1000000, "absent GVA withdraw LP")
    check(x("G-admin-mhbuy-boost", 3)["decoded"][1]["burned"] == 5254679949141, "admin+mhbuy then boost = post-buy burn")
    check(x("G-zeroed-mhsell", 0)["deltas"]["userquote"] == 178541, "zeroed GVA mhsell anchor")
    print("PASS: 60 cases, 294 receipts, 30 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, "
          "GVA lifecycle: absent/zeroed/truncated/wrong-owner behaviour, admin gate map "
          "6030/6031/6032/6033/6035/6036/6037/6005/3010, start-change wipe, mid-range "
          "future-vol zeroing, supply-slot claim pricing, mint rotation 6038 and "
          "restoration, sync reset gate, UVA close stranding and re-init, GVA-blind "
          "chain legs); control == candidate everywhere; original agrees everywhere; "
          "(0 divergent cases): []")
if __name__ == "__main__":
    main()
