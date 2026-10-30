#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-global-config-validation-five-hop-chains-20261029.

Checks, from the packet files alone (plus the three program images
when present at their workspace paths):
- MANIFEST.json lists every packet file (except itself) with a matching
  sha256 and byte count.
- runtime/report.json.gz: 73 cases, 291 receipts, 30 parts
  (29x10 + 1), part sha256/byte counts match the part files.
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
  main pool's coin_creator bytes after every step, the four created
  pool states and their (creator, coin_creator) fields, the
  GlobalConfig state, the user volume accumulator state, the global
  volume accumulator state, the account lengths after every step, and
  the decoded event fields (multi-hop 508/449-byte hop events, boost
  512-byte BuyEvent + 208-byte boost event, sweep 185-byte fields).
- Failure steps roll back every watched account's data, and only
  transaction signers may change lamports on a failed step.
- Control and candidate observed surfaces are identical in every case.
  Original agrees with them in every case: there are no divergent
  cases in this packet.
- Headline pins (see README): the 5-hop buy tail anchor is
  5207955235891 with 5 hop events and buyback leg 4515471, and the
  sell payout anchor is 178541 with leg 837; buy-then-patched-window
  burn 5254679949141, sell-then-patched-window burn 5338394848076;
  proto sweep net 4517934, creator sweep net 122160, collect net
  120938; every GlobalConfig discriminator fault (zeroed, flipped
  byte, pool discriminator, fee-table discriminator) and every
  whole-data replacement (fee-table, pool, zeroed data, length kept
  at 949) fails InvalidAccountData with 0 events in both directions;
  every owner fault (SPL token, Token-2022, system, default, Fees
  program) fails 3007 with 0 events while the pump program itself
  (the true owner) succeeds anchor-identically; lamports 0 fails
  3012 with 0 events in both directions while lamports 1 and
  2,000,000 (below the 949-byte rent-exempt minimum) succeed
  anchor-identically, so no rent-exempt check fires; the GlobalConfig
  length gate is exactly 907 bytes for the buy (100/500/906 fail
  InvalidAccountData, 907 and 948 succeed anchor-identically) and
  906 fails for the sell; check order is 3012 > 3007 >
  InvalidAccountData in both directions; key swaps split by the
  swapped account: fee-table key 3007, pool key InvalidAccountData,
  truly-absent key 3012, PLAIN key 3007 (PLAIN is a present
  Token-2022 token account, not the absent key the #137 builder's
  FRESH constant named -- FRESH and PLAIN are the same bytes
  [77]*32, so #137's "absent fresh key" label was wrong and this
  packet corrects it), user quote account 3007, Fees program key
  3007; leg parity holds for the discriminator fault on v2 buy, v2
  sell, legacy buy, legacy sell and the stable buy, and for the
  owner fault on the v2 buy; mid-chain corruption gates the second
  buy (disc InvalidAccountData, owner 3007, lamports 3012) and
  gates both sweeps while collect stays a silent 0-event no-op even
  though the good buy filled the creator bucket; after a failed buy,
  both sweeps fail InvalidAccountData, collect is a silent no-op,
  the patched-window boost fails InvalidAccountData, but the token
  claim still pays the full seeded 3334551 and the plain-quote
  cashback claim still pays the full 5475 (neither claim leg reads
  GlobalConfig); the buyback-config and disable setters fail
  InvalidAccountData under a zeroed discriminator while the control
  setter succeeds; tf variants (tf5000/tf0 discriminator, tf5000
  owner, tf0 fee-table-key swap) fail with the same codes, so
  validation is tf-neutral.
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
    check(report["case_count"] == 73, f"case_count {report['case_count']}")
    check(report["counts"] == {"cases": 73, "receipts": 291, "parts": 30},
          f"counts {report['counts']}")
    receipts = []
    for part in report["parts"]:
        path = HERE / part["file"]
        check(path.stat().st_size == part["bytes"], f"part bytes {part['file']}")
        check(sha(path.read_bytes()) == part["sha256"], f"part sha {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            for line in fh:
                receipts.append(json.loads(line))
    check(len(receipts) == 291, f"receipts {len(receipts)}")
    check(report["receipt_count"] == 291, "report receipt_count")
    # Group receipts by (case, image), preserving step order.
    grouped = {}
    order = []
    for rec in receipts:
        key = (rec["case"], rec["image"])
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].append(rec)
    check(len(grouped) == 73 * 3, f"groups {len(grouped)}")
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

    # A: 5-hop anchors (GlobalConfig unmutated, bps 100 tf).
    check(tail("A-buy5", 0) == 5207955235891
          and x("A-buy5", 0)["deltas"].get("bb22") == 4515471
          and x("A-buy5", 0)["events"] == 5
          and x("A-sell5", 0)["deltas"].get("userquote") == 178541
          and x("A-sell5", 0)["deltas"].get("bb22") == 837
          and x("A-sell5", 0)["events"] == 5
          and burn("A-buy-boost", 2) == 5254679949141
          and burn("A-sell-boost", 2) == 5338394848076
          and x("A-buy-swp-col", 1)["deltas"].get("proto22") == 4517934
          and x("A-buy-swp-col", 2)["deltas"].get("creat22") == 122160
          and x("A-buy-swp-col", 3)["deltas"].get("dest22") == 120938,
          "anchor 5-hop buy tail 5207955235891, bb leg 4515471, 5 hop events; sell payout 178541 leg 837; buy-then-patched-window burn 5254679949141; sell-then-patched-window burn 5338394848076; proto sweep net 4517934, creator sweep net 122160, collect net 120938")
    # D/W: every discriminator fault and whole-data replacement fails
    # InvalidAccountData with 0 events, both directions.
    check(all("InvalidAccountData" in err(f"D-{v}-{d}", "original", 0) and x(f"D-{v}-{d}", 0)["events"] == 0
              for v in ("disc0", "discflip", "discpool", "discfee") for d in ("buy", "sell"))
          and all("InvalidAccountData" in err(f"W-data{v}-{d}", "original", 0) and x(f"W-data{v}-{d}", 0)["events"] == 0
                  for v, d in (("fee", "buy"), ("pool", "buy"), ("zero", "buy"), ("zero", "sell"))),
          "discriminator faults (zeroed, flipped byte, pool, fee-table) and whole-data replacements (fee-table, pool, zeroed) all fail InvalidAccountData with 0 events in both directions at depth 5")
    # O: the true owner (pump program) succeeds; every wrong owner fails 3007.
    check(tail("O-ownerprog-buy", 0) == 5207955235891
          and x("O-ownerprog-buy", 0)["deltas"] == x("A-buy5", 0)["deltas"]
          and x("O-ownerprog-sell", 0)["deltas"].get("userquote") == 178541
          and all("Custom(3007)" in err(label, "original", 0) and x(label, 0)["events"] == 0
                  for label in ("O-ownertoken-buy", "O-ownertoken22-buy", "O-ownersys-buy",
                                "O-ownerdefault-buy", "O-ownerdefault-sell", "O-ownerfees-buy")),
          "owner faults (SPL token, Token-2022, system, default, Fees program) all fail 3007 with 0 events at depth 5; the pump program itself succeeds anchor-identically")
    # L: lamports 0 fails 3012; 1 and 2,000,000 succeed anchor-identically (no rent-exempt check).
    check("Custom(3012)" in err("L-lam0-buy", "original", 0) and x("L-lam0-buy", 0)["events"] == 0
          and "Custom(3012)" in err("L-lam0-sell", "original", 0) and x("L-lam0-sell", 0)["events"] == 0
          and tail("L-lam1-buy", 0) == 5207955235891
          and tail("L-lam2m-buy", 0) == 5207955235891
          and x("L-lam1-buy", 0)["deltas"] == x("A-buy5", 0)["deltas"]
          and x("L-lam2m-buy", 0)["deltas"] == x("A-buy5", 0)["deltas"],
          "lamports 0 fails 3012 with 0 events both directions; lamports 1 and 2,000,000 (below rent-exempt) succeed with anchor-identical deltas, so no rent-exempt check fires")
    # N: the buy length gate is exactly 907 bytes; 906 fails the sell too.
    check(all("InvalidAccountData" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("N-len100-buy", "N-len500-buy", "N-len906-buy", "N-len906-sell"))
          and tail("N-len907-buy", 0) == 5207955235891
          and tail("N-len948-buy", 0) == 5207955235891
          and x("N-len907-buy", 0)["deltas"] == x("A-buy5", 0)["deltas"]
          and x("N-len948-buy", 0)["deltas"] == x("A-buy5", 0)["deltas"],
          "GlobalConfig length gate at depth 5: 100/500/906 fail InvalidAccountData, 907 and 948 succeed anchor-identically for the buy; 906 fails for the sell")
    # R: check order at depth 5 is 3012 > 3007 > InvalidAccountData.
    check("Custom(3007)" in err("R-discowner-buy", "original", 0)
          and "Custom(3007)" in err("R-discowner-sell", "original", 0)
          and "Custom(3012)" in err("R-lam0disc-buy", "original", 0)
          and "Custom(3012)" in err("R-lam0owner-buy", "original", 0)
          and "Custom(3012)" in err("R-all3-buy", "original", 0)
          and "Custom(3007)" in err("R-discflipownersys-sell", "original", 0),
          "check order at depth 5: lamports 3012 beats owner 3007 and discriminator InvalidAccountData; owner 3007 beats discriminator, both directions")
    # S: key swaps split by the swapped account's owner/existence.
    check(all("Custom(3007)" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("S-swapfee-buy", "S-swapfee-sell", "S-swapplain-buy", "S-swapplain-sell",
                            "S-swapuserquote-buy", "S-swapfeesprog-buy"))
          and "InvalidAccountData" in err("S-swappool-buy", "original", 0) and x("S-swappool-buy", 0)["events"] == 0
          and "Custom(3012)" in err("S-swapfresh123-buy", "original", 0) and x("S-swapfresh123-buy", 0)["events"] == 0
          and "Custom(3012)" in err("S-swapfresh123-sell", "original", 0) and x("S-swapfresh123-sell", 0)["events"] == 0,
          "key swaps at depth 5: fee-table key 3007, pool key InvalidAccountData, truly-absent key 3012, PLAIN key 3007, user quote account 3007, Fees program key 3007, all with 0 events")
    # P: leg parity for the disc and owner faults.
    check(all("InvalidAccountData" in err(label, "original", 0) and x(label, 0)["events"] == 0
              for label in ("P-disc-buy2", "P-disc-sell2", "P-disc-legbuy", "P-disc-legsell", "P-disc-stbuy"))
          and "Custom(3007)" in err("P-owner-buy2", "original", 0)
          and "InvalidAccountData" in err("P-disc-boost", "original", 1)
          and "InvalidAccountData" in err("P-disc-swp", "original", 0),
          "leg parity: disc-zero fails InvalidAccountData on v2 buy, v2 sell, legacy buy, legacy sell, the stable buy, the patched-window boost and the protocol sweep; owner-token fails 3007 on the v2 buy")
    # M: mid-chain corruption gates the second buy and both sweeps; collect stays a silent no-op.
    check("InvalidAccountData" in err("M-buy-disc-buy", "original", 2)
          and "Custom(3007)" in err("M-buy-owner-buy", "original", 2)
          and "Custom(3012)" in err("M-buy-lam0-buy", "original", 2)
          and "InvalidAccountData" in err("M-buy-disc-swp-col", "original", 2)
          and "InvalidAccountData" in err("M-buy-disc-swp-col", "original", 3)
          and x("M-buy-disc-swp-col", 4)["error"] is None
          and x("M-buy-disc-swp-col", 4)["events"] == 0
          and x("M-buy-disc-swp-col", 4)["deltas"] == {},
          "mid-chain corruption: a good buy, then disc/owner/lamports corruption, then a second buy fails InvalidAccountData/3007/3012 respectively; both sweeps after corruption fail InvalidAccountData and collect stays a silent 0-event no-op even though the buy filled the creator bucket")
    # F: downstream legs after a failed buy split by whether they read GlobalConfig.
    check("InvalidAccountData" in err("F-fail-swp-col", "original", 1)
          and "InvalidAccountData" in err("F-fail-swp-col", "original", 2)
          and x("F-fail-swp-col", 3)["error"] is None
          and x("F-fail-swp-col", 3)["events"] == 0
          and "InvalidAccountData" in err("F-fail-boost", "original", 2)
          and x("F-fail-tclaim", 1)["deltas"].get("uata") == 3334551
          and x("F-fail-cclaim", 0)["deltas"].get("userquote") == 5475,
          "after an InvalidAccountData failure: both sweeps fail alike, collect is a silent no-op, the patched-window boost fails InvalidAccountData, but the token claim still pays the full seeded 3334551 and the plain-quote cashback claim still pays the full 5475")
    # S2: setters under a corrupted GlobalConfig.
    check(x("S2-ctl-bbcfg", 0)["error"] is None
          and "InvalidAccountData" in err("S2-disc-bbcfg", "original", 0)
          and "InvalidAccountData" in err("S2-disc-dis", "original", 0),
          "setters: the control buyback-config setter succeeds, but disc-zero fails InvalidAccountData on both the buyback-config setter and the disable setter")
    # T: tf variants of the faults are tf-neutral.
    check("InvalidAccountData" in err("T-tf5000-disc-buy", "original", 0)
          and "InvalidAccountData" in err("T-tf0-disc-buy", "original", 0)
          and "Custom(3007)" in err("T-tf5000-owner-buy", "original", 0)
          and "Custom(3007)" in err("T-tf0-swapfee-buy", "original", 0),
          "tf variants: disc-zero fails InvalidAccountData at tf5000 and tf0, owner-token fails 3007 at tf5000, fee-table-key swap fails 3007 at tf0 -- validation is tf-neutral")
    print("PASS: 73 cases, 291 receipts, 30 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, fixture pools/config/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchors with 5 hop events, GlobalConfig discriminator InvalidAccountData and owner 3007 gates at depth 5 in both directions with 0 ghost events, lamports 3012 with no rent-exempt check, 907-byte length gate, check order 3012 > 3007 > InvalidAccountData, key swaps split by owner/existence with the #137 fresh-key label corrected, leg parity, mid-chain corruption, downstream legs after an InvalidAccountData failure, setter gates, tf-neutral validation); control == candidate everywhere; original agrees everywhere (0 divergent cases)")

if __name__ == "__main__":
    main()
