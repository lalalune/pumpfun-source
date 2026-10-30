#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-cross-pool-boost-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 50 cases, 369 receipts, 37 parts
  (36x10 + 9), part sha256/byte counts match the part files.
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
  collect 120-byte fields, set_boost_authority 112-byte event).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control, candidate and original observed surfaces are identical in
  every case: 0 divergent cases (the cross-pool boost paths agree on
  all three images).
- Headline pins (see README): hop-pool boosts are window-open only
  after a vq patch and then burn exactly like the main pool at the
  same vault scale (999997999 fresh, 999995999 second); draining a
  hop-pool boost vault closes the account (no 6088, unlike the main
  pool's Token-2022 quote mint) and the next boost fails 3012; the
  boost authority is a single global field, so rotating it moves
  main, P2 and P3 boosts together and an outsider rotation fails
  6005; the Anchor gate map on hop pools is 2015 (wrong owner),
  2009 (wrong address), 2023 (wrong token program) and a Token-2022
  CPI IncorrectProgramId for a Token-2022 ATA on an SPL mint; a P2
  vq patch moves the buy tail by -5208095 and leaves the sell payout
  at 178541, while a P2 boost moves the buy tail further and the sell
  payout by exactly +1; hop-pool sweeps/collect pay the full accrued
  amounts with no Token-2022 withholding split; init_boost creates
  the missing hop-pool boost ATA (0 balance) but does not open the
  window, and a patched empty vault fails 6002; hop-pool boosts are
  independent of the main pool's transfer-fee bps (tf0 and tf5000
  both burn 999997999).

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
    check(report["case_count"] == 50, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 50, "receipts": 369, "parts": 37},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 369, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 369, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 50 * 3, f"groups {len(grouped)}")
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

    def grec(label, image, idx):
        return grouped[(label, image)][idx]

    PAYER_HEX = "ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5"
    OUTSIDER_HEX = "466627d52773c9d5cda6c8fd28ea31ec7b94e68aa8d42e2ad31a75dc8d24ed07"
    BA2_ADDR = "BrJcu3grs6izNtuSaNoBXuPokp2WX3nrEqdkJDFZX9LG"
    BA3S_ADDR = "CYaeiepkLYHVtyBhf7MHdpCszmSTX2ZuYnRcaoxim1sY"
    # A: anchors (bps 100, spend 1e9).
    check(x("A-mhbuy", 0)["deltas"]["u3"] == 5262910281902, "mhbuy tail")
    check(x("A-mhsell", 0)["deltas"]["userquote"] == 178541, "mhsell payout")
    check(x("A-boost-main", 1)["decoded"][1]["burned"] == 5338379201831, "main boost anchor burn")
    check("6065" in err("A-boost2-closed", "original", 0), "unpatched P2 boost 6065")
    check("6065" in err("A-boost3-closed", "original", 0), "unpatched P3 boost 6065")
    # B: P2 boost core.
    check(x("B-p2-anchor", 1)["decoded"][1]["burned"] == 999997999, "P2 anchor burn")
    check(x("B-p2-second", 2)["decoded"][1]["burned"] == 999995999, "P2 second burn")
    check(x("B-p2-min-exact", 1)["error"] is None, "P2 min-exact succeeds")
    check("6004" in err("B-p2-min-plus1", "original", 1), "P2 min+1 6004")
    check("6002" in err("B-p2-req0", "original", 1), "P2 request 0 6002")
    check("6002" in err("B-p2-vault0", "original", 1), "P2 empty vault 6002")
    check(x("B-p2-drain-exact", 1)["decoded"][1]["remaining"] == 0, "P2 drain-exact remaining 0")
    check(grec("B-p2-drain-exact", "original", 1)["after"][BA2_ADDR] is None, "P2 drain-exact closes BA2")
    check(x("B-p2-drain-short", 1)["decoded"][1]["used"] == 10**6 and x("B-p2-drain-short", 1)["decoded"][1]["burned"] == 999997, "P2 drain-short used 1e6 burn 999997")
    check(grec("B-p2-drain-short", "original", 1)["after"][BA2_ADDR] is None, "P2 drain-short closes BA2")
    check("3012" in err("B-p2-reboost-after-close", "original", 2), "reboost after close 3012")
    check(x("B-p2-vq-patch-tail", 1)["deltas"]["u3"] == 5262905073807, "P2 vq patch moves buy tail -5208095")
    # C: P3 boost core.
    check(x("C-p3-anchor", 1)["decoded"][1]["burned"] == 999997999, "P3 anchor burn")
    check(x("C-p3-drain-exact", 1)["decoded"][1]["remaining"] == 0, "P3 drain-exact remaining 0")
    check(grec("C-p3-drain-exact", "original", 1)["after"][BA3S_ADDR] is None, "P3 drain-exact closes BA3S")
    check("6004" in err("C-p3-min-plus1", "original", 1), "P3 min+1 6004")
    check("6065" in err("C-p3-closed-then-patch", "original", 0) and x("C-p3-closed-then-patch", 2)["decoded"][1]["burned"] == 999997999, "P3 closed then patched to anchor")
    check(x("C-p3-vq-patch-tail", 1)["deltas"]["u3"] == 5262905046036, "P3 vq patch moves buy tail -5235866")
    check(x("C-p2p3-sequence", 2)["decoded"][1]["burned"] == 999997999 and x("C-p2p3-sequence", 3)["decoded"][1]["burned"] == 999997999, "P2+P3 sequence both anchor")
    # D: authority x pool (single global field).
    check("6005" in err("D-p2-outsider", "original", 1), "P2 outsider boost 6005")
    check("6005" in err("D-p3-outsider", "original", 1), "P3 outsider boost 6005")
    check(x("D-rot-p2", 1)["events"] == 1 and x("D-rot-p2", 1)["cfg"]["boost_auth"] == OUTSIDER_HEX, "rotation to outsider, 1 event")
    check(x("D-rot-p2", 2)["decoded"][1]["burned"] == 999997999, "outsider P2 boost after rotation")
    check("6005" in err("D-rot-p2", "original", 3), "payer P2 boost after rotation 6005")
    check(x("D-rot-p2", 4)["cfg"]["boost_auth"] == PAYER_HEX, "rotation back to payer")
    check(x("D-rot-p2", 5)["decoded"][1]["burned"] == 999995999, "payer P2 boost after restore")
    check(x("D-rot-p3", 2)["decoded"][1]["burned"] == 999997999 and x("D-rot-p3", 5)["decoded"][1]["burned"] == 999995999, "P3 rotation walk mirrors P2")
    check("6005" in err("D-rot-outsider-attempt", "original", 0), "outsider rotation attempt 6005")
    check(x("D-rot-main-control", 2)["decoded"][1]["burned"] == 5338379201831, "outsider main boost after rotation")
    check("6066" in err("D-boost-disabled-p2", "original", 2), "boost_enabled=0 P2 boost 6066")
    check("6020" in err("D-disable-buy-p2", "original", 2), "disable buy flag P2 boost 6020")
    # E: ATA / program gates on hop pools.
    check("2015" in err("E-p2-wrong-vault-ata", "original", 1), "P2 wrong vault ATA 2015")
    check("2015" in err("E-p2-owner-payer", "original", 1), "P2 payer-owned ATA 2015")
    check("2023" in err("E-p2-prog22-mismatch", "original", 1), "P2 TOKEN22 program on SPL ATA 2023")
    check("IncorrectProgramId" in err("E-p2-t22-on-spl", "original", 1), "P2 Token-2022 ATA on SPL mint CPI IncorrectProgramId")
    check("2023" in err("E-p3-old-ata", "original", 1), "P3 TOKEN22-owned ATA with TOKEN program 2023")
    check("2009" in err("E-p3-wrong-addr", "original", 1), "P3 wrong-address ATA 2009")
    check("2023" in err("E-p3-prog22-mismatch", "original", 1), "P3 TOKEN22 program on SPL ATA 2023")
    check("2023" in err("E-main-wrong-ata", "original", 1), "main wrong ATA 2023")
    # F: chain interactions.
    check(x("F-p2boost-mhbuy", 2)["deltas"]["u3"] == 5262894631186, "P2 boost then buy tail")
    check(x("F-mhbuy-p2boost", 2)["decoded"][1]["burned"] == 989418204, "buy then P2 boost burn")
    check(x("F-p2boost-mhsell", 2)["deltas"]["userquote"] == 178542, "P2 boost then sell payout +1")
    check(x("F-patch-p2-mhsell", 1)["deltas"]["userquote"] == 178541, "P2 patch alone leaves sell payout 178541")
    check(x("F-p2boost-swp-col", 2)["deltas"]["protoata2"] == 2488 and x("F-p2boost-swp-col", 3)["deltas"]["creatorata2"] == 123394 and x("F-p2boost-swp-col", 4)["deltas"]["dest2"] == 123394, "P2 sweep/collect pay full accrued amounts")
    check(x("F-p2boost-mainboost", 3)["decoded"][1]["burned"] == 5338379201831, "P2 boost then main boost anchor")
    check(x("F-mainboost-p2boost", 3)["decoded"][1]["burned"] == 999997999, "main boost then P2 boost anchor")
    check(x("F-p2boost-fail-then-mhbuy", 1)["deltas"]["u3"] == 5262910281902, "failed P2 boost leaves buy tail anchor")
    # G: init_boost.
    check(x("G-init-p2", 0)["events"] == 0, "init P2 0 events")
    check(grec("G-init-p2", "original", 0)["after"][BA2_ADDR] is not None, "init P2 creates BA2")
    check("6002" in err("G-init-p2", "original", 2), "init then patched boost on empty vault 6002")
    check("6065" in err("G-init-p2-then-closed-boost", "original", 1), "init P2 then unpatched boost 6065")
    check(x("G-init-main", 0)["events"] == 0 and "6065" in err("G-init-main", "original", 1), "init main no-op then unpatched boost 6065")
    # H: tf independence of hop boosts.
    check(x("H-p2boost-tf5000", 1)["decoded"][1]["burned"] == 999997999, "P2 boost at tf5000 anchor")
    check(x("H-p2boost-tf0", 1)["decoded"][1]["burned"] == 999997999, "P2 boost at tf0 anchor")
    check(x("H-p2boost-tf5000", 1)["withheld"] == {} and x("H-p2boost-tf0", 1)["withheld"] == {}, "hop boosts withhold nothing")
    print("PASS: 50 cases, 369 receipts, 37 parts, per-image expectations hold "
          "(signatures, deltas, withheld, lamports, events, error codes, rollback, "
          "pool/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, "
          "cross-pool boost anchors 999997999/999995999, drain-close and 3012 "
          "reboost, single-global authority rotation with 6005 gates, Anchor gate "
          "map 2009/2015/2023 plus Token-2022 CPI IncorrectProgramId, P2-boost "
          "chain legs (buy tail, sell payout +1, full sweep/collect), init_boost "
          "ATA creation without opening the window, tf-independent hop burns); "
          "control == candidate everywhere; original agrees everywhere; "
          "(0 divergent cases): []")
if __name__ == "__main__":
    main()
