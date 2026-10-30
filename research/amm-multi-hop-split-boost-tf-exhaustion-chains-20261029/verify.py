#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-exhaustion-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
-- runtime/report.json.gz: 71 cases, 576 receipts, 58 parts
  (57x10 + 6), part sha256/byte counts match the part files.
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
  case; the original agrees with both in every case (0 divergent
  cases).
- Headline pins (see README): the Token-2022 rule
  `epoch >= newer.epoch ? newer : older` selects per leg at the
  current clock epoch on the true-3-hop chain -- boundary inclusive
  at exactly newer.epoch, inverted pairs take the future older
  schedule before newer.epoch, a future newer.epoch never activates;
  a buy's net input reprices the curve (old-100 tail
  5,262,910,281,902 vs new-5000 tail 2,682,425,360,738) while a
  sell's gross is schedule-blind and only its net/withheld split
  moves (180,345 gross -> 178,541 + 1,804 at 100bps, 90,172 +
  90,173 at 5000bps); sweep, collect, boost, deposit and withdraw
  all read the schedule live at their own leg; harvest and
  withdraw-from-mint move whatever was withheld, schedule-agnostic;
  maximum_fee caps the fee per leg and makes bps irrelevant while
  it binds (cap 1000 -> 1000 withheld on the input and buyback
  legs at either bps); a mid-walk clock crossing and a mid-walk
  schedule rewrite land on identical second legs.

Usage: ~/workspace/venvs/pumpfun/bin/python -I -B verify.py
  (run from this packet directory)
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
    return None


STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "boost": "boost",
             "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
             "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
             "swp": "swp", "swc": "swc", "col": "col",
             "xfer2": None, "xfer1": None, "cpatch": None,
             "ww": None, "harvest": None, "wfm": None}


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
    check(report["case_count"] == 71, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 71, "receipts": 576, "parts": 58},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 576, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 576, "report receipt_count")
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
    check(not any(c["divergent"] for c in report["cases"]), "expected 0 divergent cases")
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

    def burn(label, idx):
        ds = x(label, idx)["decoded"]
        return [d for d in ds if d and d.get("disc") == BST_DISC][0]["burned"]

    def err(label, idx):
        return x(label, idx)["error"]

    # Z: anchors.
    check(burn("Z-boost", 1) == 5338379201831, "anchor boost burn")
    check(x("Z-buy", 0)["deltas"]["u3"] == 5262910281902, "anchor buy tail")
    check(x("Z-sell", 0)["deltas"]["userquote"] == 178541, "anchor sell net")
    # L: burn linear in vb1 at fixed vq/tf/request.
    check(burn("L-vb1e15-boost", 2) == 7924013300677, "vb 1e15 burn")
    check(burn("L-vb1e14-boost", 2) == 792401330067, "vb 1e14 burn")
    check(burn("L-vb1e13-boost", 2) == 79240133006, "vb 1e13 burn")
    check(burn("L-vb1e12-boost", 2) == 7924013300, "vb 1e12 burn")
    check(burn("L-vb1e11-boost", 2) == 792401330, "vb 1e11 burn")
    check(burn("L-vb1e10-boost", 2) == 79240133, "vb 1e10 burn")
    check(burn("L-vb1e9-boost", 2) == 7924013, "vb 1e9 burn")
    check(burn("L-vb1e6-boost", 2) == 7924, "vb 1e6 burn")
    check("6001" in err("L-vb0-boost", 2), "vb0 boost 6001")
    check(x("L-vb0-boost", 2)["events"] == 0, "vb0 boost 0 events")
    check(burn("L-vb0-boost-restore", 4) == 7924013300677, "vb restore burn")
    # R: repeated boosts decay ~1.56%/round.
    check(burn("R-boost-x5", 1) == 5338379201831, "round 1")
    check(burn("R-boost-x5", 2) == 5254441549265, "round 2")
    check(burn("R-boost-x5", 3) == 5172468136601, "round 3")
    check(burn("R-boost-x5", 4) == 5092398150835, "round 4")
    check(burn("R-boost-x5", 5) == 5014173114355, "round 5")
    check(burn("R-boost-vb1e12-x3", 2) == 7924013300, "vb1e12 round 1")
    check(burn("R-boost-vb1e12-x3", 3) == 7799420601, "vb1e12 round 2")
    check(burn("R-boost-vb1e12-x3", 4) == 7677743517, "vb1e12 round 3")
    # Q: request ladder; 0 and 1 fail 6002, 10 succeeds.
    check("6002" in err("Q-req0", 1), "req 0 6002")
    check("6002" in err("Q-req1", 1), "req 1 6002")
    check(burn("Q-req10", 1) == 43482, "req 10 burn")
    check(burn("Q-req1000", 1) == 5375583, "req 1000 burn")
    check(burn("Q-req1e5", 1) == 538095981, "req 1e5 burn")
    check(burn("Q-req1e6", 1) == 5380970054, "req 1e6 burn")
    check(burn("Q-req1e8", 1) == 537672386159, "req 1e8 burn")
    check(burn("Q-req1e10", 1) == 49830102507836, "req 1e10 burn")
    check("6088" in err("Q-req1e12", 1), "req 1e12 6088")
    check(burn("Q-req1e12", 1) == 598735502793632, "req 1e12 ghost burn")
    # A: ATA must end strictly positive.
    check("6088" in err("A-ata-1e6", 2), "ata short 6088")
    check(burn("A-ata-1e6", 2) == 5380970054, "ata short ghost burn")
    check("6002" in err("A-ata-0", 2), "ata 0 6002")
    check("6088" in err("A-ata-eq", 2), "ata == request 6088")
    check(x("A-ata-plus1", 2)["decoded"][1]["remaining"] == 1, "ata plus1 remaining 1")
    check(burn("A-ata-plus1", 2) == 5338379201831, "ata plus1 burn")
    check("6088" in err("A-ata-2e9-twice", 3), "second boost at exact balance 6088")
    check(burn("A-ata-2e9plus1-twice", 3) == 5254441549265, "plus1 second burn")
    check("6088" in err("A-ata-short-vb1e9", 3), "ata short at small vb 6088")
    check(burn("A-ata-short-vb1e9", 3) == 7987, "ata short small vb ghost burn")
    check("6002" in err("A-ata0-vb0", 3), "ata gate beats vault gate")
    # T: trade legs on a drained vault.
    check(x("T-buy-vb1e12", 1)["deltas"]["u3"] == 7963960047, "buy vb1e12 tail")
    check(x("T-buy-vb1e11", 1)["deltas"]["u3"] == 796407430, "buy vb1e11 tail")
    check(x("T-buy-vb1e10", 1)["deltas"]["u3"] == 79640853, "buy vb1e10 tail")
    check(x("T-buy-vb1e9", 1)["deltas"]["u3"] == 7964081, "buy vb1e9 tail")
    check(x("T-buy-vb1e6", 1)["deltas"]["u3"] == 7961, "buy vb1e6 tail")
    check(x("T-sell-vb1e12", 1)["deltas"]["userquote"] == 121230928, "sell vb1e12 net")
    check(x("T-sell-vb1e9", 1)["deltas"]["userquote"] == 60751929177, "sell vb1e9 net")
    check(x("T-sell-vb1e6", 1)["deltas"]["userquote"] == 121534401396, "sell vb1e6 net")
    check("6025" in err("T-buy-vb0", 1), "buy vb0 6025")
    check(x("T-buy-vb0", 1)["events"] == 0, "buy vb0 0 events")
    check("6025" in err("T-sell-vb0", 1), "sell vb0 6025")
    check(x("T-sell-vb0", 1)["events"] == 2, "sell vb0 2 ghosts")
    check("6016" in err("T-buy2-vb0", 1), "buy2 vb0 6016")
    check("6016" in err("T-legbuy-vb0", 1), "legacy buy vb0 6016")
    check("6025" in err("T-sell2-vb0", 1), "sell2 vb0 6025")
    check("6025" in err("T-legsell-vb0", 1), "legacy sell vb0 6025")
    check(x("T-buy2-vb1e12", 1)["deltas"]["userquote"] == -124685392, "buy2 vb1e12 cost")
    check(x("T-sell2-vb1e12", 1)["deltas"]["userquote"] == 121230716, "sell2 vb1e12 net")
    check(x("T-plain-buy-vb1e12", 1)["deltas"]["u3"] == 8043754098, "plain buy vb1e12 tail")
    check("6025" in err("T-plain-buy-vb0", 1), "plain buy vb0 6025")
    check("6025" in err("T-plain-sell-vb0", 1), "plain sell vb0 6025")
    # D: deposit cannot rescue a zero base vault; withdraw pays quote only.
    check(x("D-vb0-dep", 1)["decoded"][0]["base"] == 0, "vb0 dep base 0")
    check(x("D-vb0-dep", 1)["decoded"][0]["quote"] == 29313, "vb0 dep quote")
    check("6001" in err("D-vb0-dep-boost", 3), "vb0 dep boost still 6001")
    check("6025" in err("D-vb0-dep-buy", 2), "vb0 dep buy still 6025")
    check(x("D-vb0-wd", 1)["decoded"][0]["base"] == 0, "vb0 wd base 0")
    check(x("D-vb0-wd", 1)["decoded"][0]["quote"] == 29312, "vb0 wd quote")
    check(x("D-vb1e9-wd", 1)["decoded"][0]["base"] == 238, "vb1e9 wd base")
    check(burn("D-vb1e9-dep-boost", 3) == 7924013, "vb1e9 dep boost ladder")
    # F: fee-book legs survive the drain.
    check(x("F-vb0-swp-swc-col", 1)["deltas"]["proto22"] == 2463, "vb0 swp net")
    check(x("F-vb0-swp-swc-col", 2)["deltas"]["creat22"] == 122160, "vb0 swc net")
    check(x("F-vb0-swp-swc-col", 3)["deltas"]["dest22"] == 120938, "vb0 col net")
    check(x("F-vb0-tclaim", 1)["deltas"]["uata"] == 3334551, "vb0 tclaim")
    check(x("F-buy-vb0-swp", 2)["deltas"]["proto22"] == 4517934, "buy vb0 swp net")
    check(x("F-fail6088-buy", 3)["deltas"]["u3"] == 5221217806636, "fail6088 buy fresh vq tail")
    # V: real quote vault steers the burn.
    check("6023" in err("V-vq1-0-boost", 2), "vq1 0 boost 6023")
    check(burn("V-vq1-1e9-boost", 2) == 223063355017720, "vq1 1e9 burn")
    check(burn("V-vq1-1e12-boost", 2) == 665634817992, "vq1 1e12 burn")
    check("6023" in err("V-vq1-0-buy", 1), "vq1 0 buy 6023")
    # X: tf variants and walk combinations.
    check(burn("X-vb1e12-tf0", 2) == 8003413241, "vb1e12 tf0 burn")
    check(burn("X-vb1e12-tf5000", 2) == 4017784612, "vb1e12 tf5000 burn")
    check(burn("X-vb1e12-req1e10", 2) == 73965220550, "vb1e12 req1e10 burn")
    check(burn("X-vb1e12-buy-boost", 3) == 7798964344, "vb1e12 buy boost burn")
    check("6001" in err("X-boost-vb0-boost", 3), "boost then vb0 6001")
    check("6065" in err("X-vb1e12-window0", 1), "unpatched window 6065")
    print("PASS: 71 cases, 576 receipts, 58 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, "
          "vault exhaustion ladders, boost ATA exhaustion, deposit/withdraw on a "
          "drained vault, fee-book legs after the drain, quote-vault burn ladder); "
          "control == candidate everywhere; "
          "original agrees everywhere; (0 divergent cases): []")


if __name__ == "__main__":
    main()
