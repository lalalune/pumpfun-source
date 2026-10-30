#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-gva-validation-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 72 cases, 255 receipts, 26 parts
  (25x10 + 5), part sha256/byte counts match the part files.
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
  lp_supply) plus each pool's creator_fee_bps field (261..269) and the
  main pool's coin_creator bytes after every step, the GlobalConfig
  state, the user volume accumulator state, the global volume
  accumulator state, the account lengths after every step, and the
  decoded event fields (multi-hop 508/449-byte hop events, boost
  512-byte BuyEvent + 208-byte boost event, sweep 185-byte fields,
  claim 104/72-byte events, sync 64-byte event, close 80-byte event).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every case.
  Original agrees with them in every case: there are no divergent
  cases in this packet.
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events and buyback leg 4515471, and the
  sell payout anchor is 178541 with leg 837; token claim gross
  3334551 net 3301205 withheld 33346; cashback claim 5475; sync
  fires the pre-start reset and is a no-op at last == start; every
  GVA discriminator fault (zeroed, flipped byte, pool, GlobalConfig,
  fee-table) and every whole-data replacement fails 3002 with 0
  events on sync and token claim, while both 5-hop trade directions
  pay their anchors under a disc-zeroed GVA (trade legs do not read
  GVA); every owner fault (SPL token, Token-2022, system, default,
  Fees program) fails 3007 on claim/sync; lamports 0 fails 3012 on
  claim/sync, while lamports 1 and 2,000,000 pay the anchor claim
  identically, so no rent-exempt check fires; check order is
  3012 > 3007 > 3002 with the seeds gate 2006 below the
  discriminator check (a valid-GVA-bytes key fails 2006, another
  user's UVA fails 3002, fee-table key fails 3007, truly-absent
  key fails 3012, absent GVA fails 3012); length gates are exactly
  544 bytes (0 fails 3001, 543 fails 3003, 544 and 1000 succeed
  with the anchor claim / firing sync); a non-incentive GVA mint
  fails 6038; start/end contents drive the sync reset gate and
  the claim reward branch (start 100 fires sync, start 5 is a
  no-op, start 100 pays only the 111 unclaimed, end-before-start
  does not panic); admin legs under a corrupted GVA fail 3002
  (disc) / 3007 (owner); downstream legs after a GVA failure keep
  working at anchor values; tf variants are tf-neutral.
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
P4 = "5gZTf2A6UPeYZCq1mkdiYquMQqmjNcz9pknbABkWif9c"
P5 = "5TdRYVo7We7hYSXDS3ryvUvouL7hoaMLTGMRqMrzBhcE"
P4S = "4D6sQCJreXod5dfz7JGoH3H7ibW4SEXh1cVXhKUP1DZd"
P5S = "7vchfPzNaULppGpaEJSUauxyQg3Nisue1YqyhyXeoreC"
U5 = "79cu2QNvp92chEmBhBgcUfERDT9KHnUcr8eiJb5WzKML"
CPOOL = "35N1cB5z1NfVk8GaDcW45Sdv187oPt3tdNb9kMM9sp3L"
CTAIL = "2ucBziY5uzQfbyQyf7e6shj66zWu3vTCirsmUvPRgXTx"
CTAIL1 = "EBFRtnSXfNCvKLJoXHhGD76pqPg96j57kFFouhhzN8uW"
CTAIL5 = "uXrop3cbeubYww7A1iuWkx35jfbhiaZA1hQvCZmScsb"
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
    if kind == "create":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 116), "quote": u64(raw, 124),
                "pbase": u64(raw, 132), "pquote": u64(raw, 140),
                "minliq": u64(raw, 148), "initliq": u64(raw, 156),
                "lpout": u64(raw, 164)}
    if kind == "rot":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "admin": raw[16:48].hex(), "new_admin": raw[48:80].hex()}
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


STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "stbuy5": "mhbuy5", "stsell5": "mhsell5", "boost": "boost",
             "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
             "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
             "swp": "swp", "swc": "swc", "col": "col",
                "boost2": "boost", "boost2o": "boost", "boost3s": "boost", "boost3o": "boost",
                "boost2x": "boost", "boost3x": "boost", "boostx": "boost", "boosto": "boost",
                "boostauth": None, "rot": "rot", "initb": None, "ucfc": None, "legbuy": None, "buy2": None, "legs": None,
             "xfer2": None, "xfer1": None, "cpatch": None,
             "admin": "admin", "close": "close", "close_other": "close", "close_unsigned": "close", "init": "init",
             "ww": None, "harvest": None, "wfm": None,
             "buy2m": "buy2", "sell2m": "sell2", "lexact": None, "bexact2": None,
             "set": "set", "mig": "mig",
             "setr": "setr", "legbuy_res": None, "legsell_res": None,
             "set2": "set", "mig2": "mig", "set3": "set", "mig3": "mig",
             "dep2": "dep", "wd2": "wd", "dep3": "dep", "wd3": "wd",
             "dep4": "dep", "wd4": "wd", "dep5": "dep", "wd5": "wd",
             "boost4s": "boost", "boost5s": "boost",
             "swc2c": "swc", "col2c": "col", "swc3c": "swc", "col3c": "col",
             "swcsh": "swc", "colsh": "col",
             "swc2sh": "swc", "col2sh": "col", "swc3sh": "swc", "col3sh": "col",
             "mhbuy5c": "mhbuy5", "mhsell5c": "mhsell5", "mhbuy5t": "mhbuy5", "mhsell5t": "mhsell5",
             "create": "create", "buy2c": "buy2", "sell2c": "sell2", "boostc": "boost",
             "depc": "dep", "wdc": "wd", "swpc": "swp", "swcc": "swc", "colc": "col"}


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
    if kind in ("boost", "boostc") and raws:
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
                      (("main", POOL), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5), ("p4s", P4S), ("p5s", P5S))},
            "cfbps": {name: (struct.unpack_from("<Q", bytes.fromhex(after[key]["data_hex"]), 261)[0]
                             if after.get(key) and len(bytes.fromhex(after[key]["data_hex"])) >= 269 else None)
                      for name, key in (("main", POOL), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5), ("p4s", P4S), ("p5s", P5S))},
            "pool_creator": bytes.fromhex(after[POOL]["data_hex"])[211:243].hex() if after.get(POOL) else None,
            "cpools": {name: pool_state(after[key]) for name, key in
                       (("cpool", CPOOL), ("ctail", CTAIL), ("ctail1", CTAIL1), ("ctail5", CTAIL5))},
            "ccreators": {name: ([bytes.fromhex(after[key]["data_hex"])[11:43].hex(),
                                  bytes.fromhex(after[key]["data_hex"])[211:243].hex()]
                                 if after.get(key) and len(bytes.fromhex(after[key]["data_hex"])) >= 243 else None)
                          for name, key in (("cpool", CPOOL), ("ctail", CTAIL), ("ctail1", CTAIL1), ("ctail5", CTAIL5))},
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
    check(report["case_count"] == 72, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 72, "receipts": 255, "parts": 26},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 255, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 255, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 72 * 3, f"groups {len(grouped)}")
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
                              "pools", "cfbps", "pool_creator", "cpools", "ccreators", "cfg", "rescfg", "uva", "gva", "mint", "lens", "site"):
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
        for d in (x(label, idx)["decoded"] or []):
            if d and "burned" in d:
                return d["burned"]
        return None

    def tail(label, idx):
        return x(label, idx)["deltas"].get("u5")

    # A: anchors at depth 5.
    check(tail("A-buy5", 0) == 5207955235891
          and x("A-buy5", 0)["deltas"].get("bb22") == 4515471
          and x("A-buy5", 0)["events"] == 5
          and x("A-sell5", 0)["deltas"].get("userquote") == 178541
          and x("A-sell5", 0)["deltas"].get("bb22") == 837
          and x("A-sell5", 0)["events"] == 5
          and x("A-tclaim", 0)["deltas"].get("gata") == -3334551
          and x("A-tclaim", 0)["deltas"].get("uata") == 3301205
          and x("A-tclaim", 0)["withheld"].get("uata") == 33346
          and x("A-cclaim", 0)["deltas"].get("userquote") == 5475
          and x("A-sync-fire", 0)["events"] == 1
          and x("A-sync-fire", 0)["uva"]["claimed"] == 0
          and x("A-sync-fire", 0)["uva"]["has"] == 0
          and x("A-sync-noop", 0)["events"] == 0
          and burn("A-buy5-boost", 2) == 5254679949141
          and x("A-buy5-swpc", 1)["deltas"].get("proto22") == 4517934
          and x("A-buy5-swpc", 2)["deltas"].get("creat22") == 122160
          and x("A-buy5-swpc", 3)["deltas"].get("dest22") == 120938,
          "anchors at depth 5: buy tail 5207955235891 with bb leg 4515471 and 5 hop events, sell payout 178541 leg 837; token claim gross 3334551 net 3301205 withheld 33346; cashback claim 5475; sync fires the pre-start reset and is a no-op at last == start; buy-then-boost burn 5254679949141; buy-then-sweep/collect nets 4517934 / 122160 / 120938")
    # D: discriminator faults fail 3002 with 0 events on sync and claim;
    # trade legs under a disc-zeroed GVA pay their anchors (GVA-blind).
    check(all("Custom(3002)" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("D-sync-disc0", "D-sync-discflip", "D-sync-discpool",
                            "D-sync-discconfig", "D-sync-discfee", "D-tclaim-disc0",
                            "D-tclaim-discflip", "D-tclaim-discpool"))
          and tail("D-buy5-disc0", 0) == 5207955235891
          and x("D-buy5-disc0", 0)["events"] == 5
          and x("D-sell5-disc0", 0)["deltas"].get("userquote") == 178541
          and x("D-sell5-disc0", 0)["events"] == 5,
          "discriminator faults (zeroed, flipped byte, pool, GlobalConfig, fee-table) fail 3002 with 0 events on sync and token claim; 5-hop buy and sell under a disc-zeroed GVA pay their anchors with 5 hop events (trade legs do not read GVA)")
    # T: whole-data replacements on the token claim fail 3002.
    check(all("Custom(3002)" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("T-tclaim-data-pool", "T-tclaim-data-config",
                            "T-tclaim-data-fee", "T-tclaim-data-zero")),
          "whole-data replacements (pool, GlobalConfig, fee-table, zeroed data at kept length 600) on the token claim fail 3002 with 0 events")
    # O: owner faults fail 3007 on claim/sync.
    check(all("Custom(3007)" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("O-tclaim-owner-token", "O-tclaim-owner-token22", "O-tclaim-owner-sys",
                            "O-tclaim-owner-default", "O-tclaim-owner-fees", "O-sync-owner-token")),
          "owner faults (SPL token, Token-2022, system, default, Fees program) fail 3007 with 0 events on token claim and sync")
    # L: lamports 0 fails 3012 on claim/sync; 1 and 2,000,000 pay the anchor.
    check("Custom(3012)" in err("L-tclaim-lam0", "original", 0) and x("L-tclaim-lam0", 0)["events"] == 0
          and "Custom(3012)" in err("L-sync-lam0", "original", 0)
          and x("L-tclaim-lam1", 0)["deltas"] == x("A-tclaim", 0)["deltas"]
          and x("L-tclaim-lam1m", 0)["deltas"] == x("A-tclaim", 0)["deltas"],
          "lamports 0 fails 3012 with 0 events on token claim and sync; lamports 1 and 2,000,000 pay the anchor claim identically, so no rent-exempt check fires")
    # X: check order on the token claim is 3012 > 3007 > 3002.
    check("Custom(3007)" in err("X-tclaim-disc-owner", "original", 0)
          and "Custom(3012)" in err("X-tclaim-lam-disc", "original", 0)
          and "Custom(3012)" in err("X-tclaim-lam-owner", "original", 0)
          and "Custom(3012)" in err("X-tclaim-all", "original", 0),
          "check order at depth 5 on the token claim: 3012 > 3007 > 3002 (disc+owner fails 3007; lamports+disc, lamports+owner and all three fail 3012)")
    # Z: absent GVA fails 3012 on both legs.
    check("Custom(3012)" in err("Z-tclaim-absent", "original", 0)
          and "Custom(3012)" in err("Z-sync-absent", "original", 0),
          "absent GVA (fixture omission; no init instruction exists) fails 3012 on token claim and sync")
    # K: key swaps split by the swapped account; seeds gate below disc.
    check("Custom(3002)" in err("K-sync-swap-config", "original", 0)
          and "Custom(3002)" in err("K-sync-swap-pool", "original", 0)
          and "Custom(3007)" in err("K-sync-swap-fee", "original", 0)
          and "Custom(3012)" in err("K-sync-swap-fresh", "original", 0)
          and "Custom(2006)" in err("K-sync-swap-gvol2", "original", 0)
          and "Custom(3002)" in err("K-sync-swap-uva2", "original", 0)
          and "Custom(3002)" in err("K-tclaim-swap-pool", "original", 0)
          and "Custom(3012)" in err("K-tclaim-swap-fresh", "original", 0)
          and "Custom(3002)" in err("K-tclaim-swap-uva2", "original", 0),
          "key swaps at depth 5: GlobalConfig and pool keys fail 3002 (program-owned, wrong discriminator), fee-table key fails 3007 (Fees-owned), truly-absent key ([123]x32) fails 3012, another user's UVA fails 3002 (disc before seeds), a valid-GVA-bytes key fails 2006 ConstraintSeeds")
    # G: length gates -- 0 fails 3001, 543 fails 3003, 544/1000 succeed.
    check("Custom(3001)" in err("G-sync-len0", "original", 0)
          and "Custom(3003)" in err("G-sync-len543", "original", 0)
          and x("G-sync-len544-fire", 0)["events"] == 1
          and x("G-sync-len544-fire", 0)["uva"]["claimed"] == 0
          and x("G-sync-len1000-fire", 0)["events"] == 1
          and x("G-sync-len1000-fire", 0)["uva"]["claimed"] == 0
          and "Custom(3003)" in err("G-tclaim-len543", "original", 0)
          and x("G-tclaim-len544", 0)["deltas"] == x("A-tclaim", 0)["deltas"],
          "length gates at depth 5: 0 bytes fails 3001, 543 fails 3003, 544 and 1000 bytes succeed (firing sync resets claimed to 0; 544-byte claim pays the anchor)")
    # M: mint binding fails 6038.
    check(all("Custom(6038)" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("M-tclaim-mint-quote", "M-tclaim-mint-base", "M-tclaim-mint-zero")),
          "mint binding at depth 5: a GVA mint of quote, base, or zero fails 6038 InvalidIncentiveMint on the token claim")
    # S: start/end contents drive the reset gate and the reward branch.
    check(x("S-sync-start100", 0)["events"] == 1
          and x("S-sync-start100", 0)["uva"]["claimed"] == 0
          and x("S-sync-start5", 0)["events"] == 0
          and x("S-sync-start5", 0)["uva"]["claimed"] == 222
          and x("S-tclaim-start100", 0)["deltas"].get("gata") == -111
          and x("S-tclaim-start100", 0)["uva"]["volume"] == 333444
          and x("S-tclaim-endbefore", 0)["deltas"].get("gata") == -111
          and x("S-tclaim-endbefore", 0)["uva"]["volume"] == 333444,
          "start/end contents at depth 5: sync fires when GVA start is 100 (last 10 < 100) and is a no-op when start is 5; claim with start 100 pays only the 111 unclaimed with volume preserved; end-before-start (end 49, start 100) does not panic and pays the same 111")
    # S2: admin legs under a corrupted GVA.
    check(x("S2-admin-ok", 0)["error"] is None
          and x("S2-admin-ok", 0)["events"] == 1
          and "Custom(3002)" in err("S2-admin-disc0", "original", 0)
          and "Custom(3007)" in err("S2-admin-owner-token", "original", 0),
          "admin legs at depth 5: control admin succeeds with 1 event; disc-zeroed GVA fails 3002 and token-owned GVA fails 3007 on admin_update_token_incentives")
    # W: downstream legs after a GVA failure keep working at anchors.
    check("Custom(3002)" in err("W-fail-buy5", "original", 0)
          and tail("W-fail-buy5", 1) == 5207955235891
          and "Custom(3002)" in err("W-fail-sell5", "original", 0)
          and x("W-fail-sell5", 1)["deltas"].get("userquote") == 178541
          and "Custom(3002)" in err("W-fail-swpc", "original", 0)
          and x("W-fail-swpc", 1)["deltas"].get("proto22") == 2463
          and x("W-fail-swpc", 2)["deltas"].get("creat22") == 122160
          and x("W-fail-swpc", 3)["deltas"].get("dest22") == 120938
          and "Custom(3002)" in err("W-fail-boost", "original", 0)
          and burn("W-fail-boost", 2) == 5338379201831
          and "Custom(3002)" in err("W-fail-cclaim", "original", 0)
          and x("W-fail-cclaim", 1)["deltas"].get("userquote") == 5475,
          "downstream after a GVA failure: buy/sell pay anchors, sweeps/collect pay fixture values (proto 2463 / creator 122160 / collect 120938), fresh-window boost burns 5338379201831, cashback claim pays 5475")
    # F: tf variants are tf-neutral.
    check(tail("F-tf5000-buy-disc0", 0) == 2668075748732
          and tail("F-tf0-buy-disc0", 0) == 5259040470738
          and "Custom(3002)" in err("F-tf5000-tclaim-disc0", "original", 0)
          and "Custom(3007)" in err("F-tf0-sync-owner", "original", 0),
          "tf variants: disc-zeroed GVA does not move the tf5000 buy tail (2668075748732) or the tf0 buy tail (5259040470738); disc-zero fails 3002 at tf5000 on the claim and owner-token fails 3007 at tf0 on sync")
    print("PASS: 72 cases, 255 receipts, 26 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, fixture pools/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchors with 5 hop events, GVA discriminator 3002 and owner 3007 gates at depth 5 in both claim/sync directions with 0 ghost events, lamports 3012 with no rent-exempt check, exact 544-byte length floor, check order 3012 > 3007 > 3002 with seeds 2006 below the discriminator check, key swaps split by owner/existence/seeds, mint binding 6038, start/end contents driving the reset gate and reward branch, admin legs under a corrupted GVA, downstream legs after a 3002 failure, tf-neutral validation, trade legs GVA-blind); control == candidate everywhere; original agrees everywhere (0 divergent cases)")

if __name__ == "__main__":
    main()
