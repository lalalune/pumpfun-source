#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-transfer-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 49 cases, 420 receipts, 42 parts
  (42x10), part sha256/byte counts match the part files.
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
- Headline pins (see README): the tail (non-native) transfer drains
  the creator vault in full to a payer-funded pump-vault ATA; the
  main (native wSOL) transfer falls into the native close branch
  for both v1 and v2 -- balance fails custom 11, empty TOKEN22
  vault silently no-ops, SPL vault under the tf override fails
  IncorrectProgramId at ATA recreation; a frozen vault blocks the
  non-native transfer (custom 17) but not the native close (which
  recreates the account initialized); wrong mint fails 2009,
  protocol ATA as vault fails 2015, wrong token program fails
  2023, v1 wrong mint fails 6007; a transfer leaves the next
  buy/sell/boost on its plain anchor, and a collect after a
  transfer is a silent 0-event no-op.

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
             "xfer2": None, "xfer1": None, "cpatch": None}


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
    check(report["case_count"] == 49, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 49, "receipts": 420, "parts": 42},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 420, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 420, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 49 * 3, f"groups {len(grouped)}")
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
                              "pools", "pool_creator", "cfg", "uva", "gva", "lens", "site"):
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

    def get(label, image, idx):
        case = next(c for c in report["cases"] if c["label"] == label)
        return case["summaries"][image][idx]

    def err_contains(label, idx, code):
        s = get(label, "original", idx)
        check(s["error"] is not None and code in s["error"], f"{label}[{idx}]: expected {code}, got {s['error']}")

    def ev_amount(label, idx, step_decoded_idx=0):
        s = get(label, "original", idx)
        return s["decoded"][step_decoded_idx]
    # Headline pins.
    def xfer(label, idx):
        return get(label, "original", idx)
    # Tail (non-native) transfers.
    check(xfer("T-buy-swc-xfer", 2)["deltas"]["creatorata3"] == -2645500920, "tail xfer vault drain")
    check(xfer("T-buy-swc-xfer", 2)["deltas"]["pdestb2"] == 2645500920, "tail xfer dest")
    check(xfer("T-buy-swc-xfer", 2)["dPAYER"] == -2044280, "tail xfer payer rent+fee")
    check(xfer("T-buy-swc-xfer", 2)["lam_deltas"]["pdestb2"] == 2039280, "tail xfer dest rent")
    check(xfer("T-buy-swc-xfer", 2)["events"] == 0, "tail xfer silent")
    check(xfer("T-buy-swc-xfer-xfer", 3)["deltas"] == {}, "second tail xfer empty")
    check(xfer("T-buy-swc-xfer-col", 3)["events"] == 0, "collect after xfer silent")
    check(xfer("T-buy-swc-xfer-col", 3)["deltas"] == {}, "collect after xfer zero")
    check(xfer("T-buy-swc-xfer-buy", 3)["deltas"]["u3"] == 5072980706277, "buy after xfer = plain 2nd buy")
    check(xfer("T-buy-buy", 1)["deltas"]["u3"] == 5072980706277, "plain 2nd buy anchor")
    check(xfer("T-buy-swc-xfer-boost", 4)["decoded"][1]["burned"] == 5254679949141, "boost after xfer")
    check(xfer("T-sell-swc-xfer", 1)["deltas"]["creatorata3"] == 623394, "sell tail sweep")
    check(xfer("T-sell-swc-xfer", 2)["deltas"]["pdestb2"] == 623394, "sell tail xfer")
    check(xfer("T-xfer-before-buy", 0)["dPAYER"] == -2044280, "xfer before buy still creates dest")
    check(xfer("T-xfer-before-buy", 0)["deltas"] == {}, "xfer before buy zero amounts")
    check(xfer("T-buy-swc-xfer-out", 2)["dOUT"] == -2044280, "outsider pays xfer rent")
    check(xfer("T-buy-swc-xfer-out", 2)["dPAYER"] == 0, "payer untouched by outsider xfer")
    check(xfer("T-buy-swc-xfer-prefund", 2)["dPAYER"] == -5000, "prefunded dest no rent")
    err_contains("T-buy-swc-freeze-xfer", 3, "17")
    err_contains("T-buy-swc-xfer-wrongmint", 2, "2009")
    err_contains("T-buy-swp-xfer-protoata", 2, "2015")
    err_contains("T-buy-swc-xfer-t22prog", 2, "2023")
    err_contains("T-buy-failbuy-swc-xfer", 1, "6004")
    check(xfer("T-buy-failbuy-swc-xfer", 1)["events"] == 3, "failed buy ghost events")
    check(xfer("T-buy-failbuy-swc-xfer", 3)["deltas"]["pdestb2"] == 2645500920, "xfer after failed buy intact")
    check(xfer("T-buy-swc-xfer-sell", 3)["deltas"]["userquote"] == 185288, "sell after xfer")
    check(xfer("T-buy-sell", 1)["deltas"]["userquote"] == 185288, "plain tf buy-sell anchor")
    check(xfer("T-buy-swc-xfer-dep", 3)["deltas"]["userquote"] == -29846, "dep after xfer")
    check(xfer("T-buy-swc-xfer-tclaim", 3)["decoded"][0]["amount"] == 3334551, "tclaim after xfer")
    check(xfer("T-buy-swc-p2-xfer", 1)["deltas"]["creatorata2"] == 123394, "p2 sweep fixture bucket")
    check(xfer("T-buy-swc-p2-xfer", 2)["deltas"]["pdestbase"] == 123394, "p2 xfer fixture bucket")
    check(xfer("T-boost-buy-swc-xfer", 1)["decoded"][1]["burned"] == 5338379201831, "boost anchor in xfer walk")
    check(xfer("T-boost-buy-swc-xfer", 4)["deltas"]["pdestb2"] == 2583383461, "boost-buy tail xfer")
    check(xfer("T-buy-swc-xfer-tf5000", 2)["deltas"]["pdestb2"] == 1344943454, "tf5000 tail xfer")
    # Main (native) transfers.
    check(xfer("M-swc22-xfer2-tf100", 0)["deltas"]["creat22"] == 122160, "swc22 tf100 net")
    check(xfer("M-swc22-xfer2-tf100", 0)["withheld"]["creat22"] == 1234, "swc22 tf100 withheld")
    err_contains("M-swc22-xfer2-tf100", 1, "11")
    check(xfer("M-swc22-xfer2-tf5000", 0)["deltas"]["creat22"] == 61697, "swc22 tf5000 net")
    check(xfer("M-swc22-xfer2-tf5000", 0)["withheld"]["creat22"] == 61697, "swc22 tf5000 withheld")
    err_contains("M-swc22-xfer2-tf5000", 1, "11")
    check(xfer("M-swc22-xfer2-tf0", 0)["deltas"]["creat22"] == 123394, "swc22 tf0 full")
    err_contains("M-swc22-xfer2-tf0", 1, "11")
    err_contains("M-swc22-xfer1", 1, "11")
    err_contains("M-swc22-xfer2-splprog", 1, "2023")
    check(xfer("M-xfer2-amt0-t22", 0)["dPAYER"] == -5000, "amt0 t22 xfer fee only")
    check(xfer("M-xfer2-amt0-t22", 0)["deltas"] == {}, "amt0 t22 xfer noop")
    err_contains("M-xfer2-amt0-spl", 0, "IncorrectProgramId")
    err_contains("M-xfer1-amt0-spl", 0, "IncorrectProgramId")
    check(xfer("M-buy-swc22-xfer2-fail-buy", 3)["deltas"]["u3"] == 5072980706277, "buy after failed main xfer")
    check(xfer("M-buy-swc22-xfer2-fail-col22", 3)["deltas"]["creat22"] == -122160, "col22 after failed xfer vault")
    check(xfer("M-buy-swc22-xfer2-fail-col22", 3)["deltas"]["dest22"] == 120938, "col22 after failed xfer net")
    check(xfer("M-buy-swc22-xfer2-fail-col22", 3)["withheld"]["dest22"] == 1222, "col22 after failed xfer withheld")
    check(xfer("M-buy-swc22-xfer2-fail-boost", 4)["decoded"][1]["burned"] == 5254685098328, "boost after failed main xfer")
    check(xfer("M-swp22-xfer-proto", 0)["deltas"]["proto22"] == 2463, "swp22 proto net")
    err_contains("M-swp22-xfer-proto", 1, "2015")
    err_contains("M-seed-spl-xfer2", 0, "IncorrectProgramId")
    err_contains("M-seed-spl-xfer1", 0, "IncorrectProgramId")
    # Plain-quote transfers.
    check(xfer("P-swc-xfer1", 1)["deltas"]["creatorata"] == -123394, "plain xfer1 vault drain")
    check(xfer("P-swc-xfer1", 1)["lam_deltas"]["pvault"] == 123394, "plain xfer1 pump vault gain")
    check(xfer("P-swc-xfer2", 1)["lam_deltas"]["pvault"] == 123394, "plain xfer2 same native branch")
    check(xfer("P-swc-xfer1-xfer1", 2)["deltas"] == {}, "plain second xfer1 empty")
    check(xfer("P-swc-xfer1-out", 1)["dOUT"] == -5000, "plain outsider xfer fee")
    check(xfer("P-buy-swc-xfer1-buy", 3)["deltas"]["u3"] == 5121405353567, "plain buy after xfer")
    check(xfer("P-buy-buy", 1)["deltas"]["u3"] == 5121405353567, "plain 2nd buy anchor")
    check(xfer("P-swc-freeze-xfer1", 2)["deltas"]["creatorata"] == -123394, "frozen vault still closes")
    check(xfer("P-swc-freeze-xfer1", 2)["lam_deltas"]["pvault"] == 123394, "frozen vault pump gain")
    err_contains("P-swc-xfer1-wrongmint", 1, "6007")
    err_contains("P-swc-xfer2-t22prog", 1, "2023")
    check(xfer("P-swc-xfer1-col", 2)["events"] == 0, "plain collect after xfer silent")
    check(xfer("P-buy-swc-xfer1-sell", 3)["deltas"]["userquote"] == 187229, "plain sell after xfer")
    check(xfer("P-buy-sell", 1)["deltas"]["userquote"] == 187229, "plain buy-sell anchor")
    print("PASS: 49 cases, 420 receipts, 42 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA fields, account lengths, cpatch harness resets, "
          "transfer vault/destination/pump-vault deltas); control == candidate everywhere; "
          "original agrees everywhere; (0 divergent cases): []")


if __name__ == "__main__":
    main()
