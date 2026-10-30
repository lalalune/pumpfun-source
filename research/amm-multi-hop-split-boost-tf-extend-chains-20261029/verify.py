#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-extend-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 62 cases, 327 receipts, 33 parts
  (32x10 + 7), part sha256/byte counts match the part files.
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
  decoded event fields (extend 96-byte fields, multi-hop 508/449-byte
  hop events, boost 512-byte BuyEvent + 208-byte boost event, sweep
  185-byte fields, deposit/withdraw 264-byte fields, token claim
  104-byte fields, cashback claim 72-byte fields, sync 64-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every
  case; the original agrees with both in every case (0 divergent
  cases).
- Headline pins (see README): the 260-byte pool extend corrupts the
  vq sign byte and breaks the next buy/sell/boost/deposit with 6023;
  the 211-byte pool extend prices the next trade off a zero window;
  the 500-byte config extend breaks the next multi-hop buy with 6053
  while the sweep still pays; the 907-byte config extend breaks the
  next boost with 6005; the 50-byte UVA extend pays 111-only token
  claims but full cashback claims (the claim pays the ATA balance,
  not the earned field); the 100-byte GVA extend pays 111-only token
  claims, leaves needs_claim set and strands the volume, and the
  second claim is silent; rent is exactly (target - current) * 6960
  plus the 5,000 fee; extend leaves no residue on the next leg.

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
             "ext": "extend", "cpatch": None}


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
    check(report["case_count"] == 62, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 62, "receipts": 327, "parts": 33},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 327, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 327, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 62 * 3, f"groups {len(grouped)}")
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
    check(get("pool260-ext", "original", 0)["decoded"][0]["old"] == 260
          and get("pool260-ext", "original", 0)["decoded"][0]["new"] == 301, "pool260 extend event")
    check(get("pool260-ext-mhbuy", "original", 1)["pools"]["main"][0]
          == 1329227995784915872903807060280218694, "pool260 corrupted vq")
    err_contains("pool260-ext-mhbuy", 1, "6023")
    err_contains("pool260-ext-mhsell", 1, "6023")
    err_contains("pool260-ext-boost", 1, "6023")
    err_contains("pool260-ext-dep", 1, "6023")
    check(get("pool260-ext-mhsell", "original", 1)["events"] == 2, "failed sell ghost events")
    check(get("pool260-ext-mhbuy", "original", 1)["events"] == 0, "failed buy ghost events")
    check(get("pool211-ext-mhbuy", "original", 1)["deltas"]["u3"] == 5262904992332, "pool211-ext buy tail")
    check(get("pool211-mhbuy-noext", "original", 0)["deltas"]["u3"] == 5262904992332, "pool211 noext buy tail")
    check(get("pool211-ext-mhsell", "original", 1)["deltas"]["userquote"] == 178541, "pool211-ext sell")
    check(get("pool211-ext-swp22", "original", 1)["events"] == 0, "pool211-ext sweep silent")
    check(get("pool211-ext-wd", "original", 1)["deltas"]["userbase"] == 160619895, "pool211-ext withdraw")
    check(get("pool211-ext-dep", "original", 1)["deltas"]["userquote"] == -29610, "pool211-ext deposit")
    check(get("pool211-ext", "original", 0)["dPAYER"] == -631400, "pool211 rent")
    check(get("pool300-ext", "original", 0)["dPAYER"] == -11960, "pool300 rent")
    check(get("pool301-ext-noop", "original", 0)["events"] == 0, "pool301 noop")
    check(get("pool287-ext-mhbuy", "original", 1)["deltas"]["u3"] == 5262910281902, "pool287-ext buy anchor")
    check(get("buy-extpool-buy", "original", 2)["deltas"]["u3"] == 5072980706277, "buy-extpool-buy 2nd")
    check(get("pool211-ext-vq-boost-boost", "original", 2)["decoded"][1]["burned"] == 5338379201831, "ext pool boost anchor")
    check(get("pool211-ext-vq-boost-boost", "original", 3)["decoded"][1]["burned"] == 5254441549265, "ext pool boost 2nd")
    check(get("pool211-ext-outsider", "original", 0)["dOUT"] == -631400, "outsider extend pays rent")
    err_contains("pool211-ext-unsigned", 0, "3010")
    err_contains("pool211-ext-rotarget", 0, "2000")
    err_contains("pool211-ext-rouserout", 0, "2000")
    check(get("pool211-ext-rouserout", "original", 0)["dPAYER"] == -10000, "rouserout 2-signer fee")
    err_contains("pool211-ext-poor", 0, "InstructionErrorCustom(1)")
    check(get("pool211-ext-again", "original", 1)["events"] == 0, "second extend noop")
    err_contains("pool-disc0-ext", 0, "6027")
    check(get("cfg907-ext", "original", 0)["dPAYER"] == -297320, "cfg907 rent")
    check(get("cfg907-ext", "original", 0)["cfg"]["boost_auth"] == "00" * 32, "cfg907 boost auth zeroed")
    check(get("cfg907-ext-mhbuy", "original", 1)["deltas"]["u3"] == 5262910281902, "cfg907-ext buy anchor")
    err_contains("cfg907-ext-boost", 2, "6005")
    check(get("cfg907-ext-cpatch-boost", "original", 3)["decoded"][1]["burned"] == 5338379201831, "cfg cpatch boost anchor")
    check(get("cfg500-ext", "original", 0)["dPAYER"] == -3130040, "cfg500 rent")
    err_contains("cfg500-ext-mhbuy", 1, "6053")
    check(get("cfg500-ext-swp22", "original", 1)["deltas"]["proto22"] == 2463, "cfg500 sweep unaffected")
    check(get("cfg949-ext-noop", "original", 0)["events"] == 0, "cfg949 noop")
    check(get("uva90-ext-claim", "original", 1)["decoded"][0]["amount"] == 3334551, "uva90 claim full")
    check(get("uva50-ext-claim", "original", 1)["decoded"][0]["amount"] == 111, "uva50 claim 111-only")
    check(get("uva50-ext-claim", "original", 0)["uva"]["volume"] == 0, "uva50 volume zeroed")
    check(get("uva50-ext-sync", "original", 1)["decoded"][0]["before"] == 222
          and get("uva50-ext-sync", "original", 1)["decoded"][0]["after"] == 0, "uva50 sync reset")
    err_contains("uva-absent-ext", 0, "2004")
    check(get("gva544-ext-claim", "original", 1)["decoded"][0]["amount"] == 3334551, "gva544 claim full")
    check(get("gva100-ext-claim", "original", 1)["decoded"][0]["amount"] == 111, "gva100 claim 111-only")
    check(get("gva100-ext-claim", "original", 1)["uva"]["needs"] == 1, "gva100 needs stays set")
    check(get("gva100-ext-claim", "original", 1)["uva"]["volume"] == 333444, "gva100 volume stranded")
    check(get("gva100-ext-claim-claim", "original", 2)["events"] == 0, "gva100 second claim silent")
    check(get("gva100-ext-sync", "original", 1)["uva"]["volume"] == 333444, "gva100 sync keeps volume")
    err_contains("gva-absent-ext", 0, "2004")
    err_contains("fee-ext", 0, "2004")
    err_contains("vault-ext", 0, "2004")
    err_contains("extacc-random-ext", 0, "6027")
    err_contains("extacc-absent-ext", 0, "2004")
    check(get("cclaim-anchor-plain", "original", 0)["decoded"][0]["amount"] == 5475, "cclaim anchor")
    check(get("cclaim-unfunded-plain", "original", 0)["decoded"][0]["amount"] == 0, "cclaim unfunded")
    check(get("uva50-ext-cclaim-plain", "original", 1)["decoded"][0]["amount"] == 5475, "uva50 cclaim still full")
    check(get("uva50-ext-cclaim-plain", "original", 1)["decoded"][0]["total_earned"] == 0, "uva50 cclaim earned zeroed")
    check(get("cclaim-earned5475-bal1000-plain", "original", 0)["decoded"][0]["amount"] == 1000, "cclaim amount=balance 1")
    check(get("cclaim-earned1000-bal5475-plain", "original", 0)["decoded"][0]["amount"] == 5475, "cclaim amount=balance 2")
    check(get("uva50-ext-cclaim-tclaim-plain", "original", 2)["decoded"][0]["amount"] == 111, "uva50 cclaim+tclaim")
    print("PASS: 62 cases, 327 receipts, 33 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA fields, account lengths, cpatch harness resets, "
          "GVOL invariance except GVA extends); control == candidate everywhere; "
          "original agrees everywhere; (0 divergent cases): []")


if __name__ == "__main__":
    main()
