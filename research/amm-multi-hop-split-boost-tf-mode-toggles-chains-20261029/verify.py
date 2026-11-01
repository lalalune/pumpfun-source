#!/usr/bin/env python3
"""Independent re-verification for amm-multi-hop-split-boost-tf-mode-toggles-chains-20261029.

Checks, from the packet files alone (plus the three program images):
- MANIFEST.json lists every packet file (except itself) with a matching sha256.
- runtime/report.json.gz: 35 cases, 240 receipts, 24 parts
  (24x10), part sha256/byte counts match the part files.
- Every receipt transaction parses (solders) and all signatures verify.
- Every receipt's recorded before/after snapshots reproduce the
  report's per-image expected values: fee-payer and outsider lamport
  deltas, the token-leg deltas (fixture user base/quote/LP, vault
  base/quote per hop, tail output U3, TOKEN22 buyback in
  transfer-fee mode, protocol/creator ATAs, boost ATA), the
  Token-2022 withheld deltas and the mint-level withheld balance,
  the native-mint token-account lamport deltas, the five fixture
  pool states (virtual_quote_reserves i128, protocol_fees,
  creator_fees, lp_supply), the user volume accumulator state
  (lamports, length, user, needs/unclaimed/claimed/volume/last/
  has/earned/cb_claimed), the GlobalConfig fields (admin 8..40,
  fee authority 321..353, boost authority 907..939, disable
  flags, fees, recipients, buyback bps, mode flags), and the
  decoded event fields (multi-hop disc/len per hop event,
  sweep/collect fields, boost requested/used/burned/
  vq/quote_after/base_after/remaining, cashback claim
  user/amount/ts/total_claimed/total_earned).
- Failure steps roll back every watched account except the fee
  payer (fee 5,000) and carry the expected error code: re-toggling
  an already-off mayhem flag 6043, re-toggling an already-off
  cashback flag 6051, outsider toggle 6005, unsigned toggle 3010,
  mayhem-flagged hop 6080, cashback-flagged non-terminal hop on
  the rebuild 6079, boost with boost disabled 6066, boost on a
  zero-size window 6065.
- The global volume accumulator never changes in any step.
- Control and candidate observed surfaces are identical in every
  case; the original agrees with both except in 7 divergent cases,
  all the cashback-flagged non-terminal hop pattern: original
  succeeds where the rebuild fails 6079, and on a both-flagged
  hop the original fails 6080 (mayhem checked first) while the
  rebuild fails 6079 (cashback checked first). The pinned
  behaviour: global toggles are separate from per-pool flags
  (toggling the global flag neither rescues nor breaks a flagged
  pool); toggling back restores the anchor exactly (no residual);
  boost follows the boost-enabled flag (off -> 6066, on ->
  identical burn); cashback claim pays the earned amount
  regardless of the global cashback flag.

Usage: python3 verify.py   (run from this packet directory)
"""
import base64
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path

from solders.pubkey import Pubkey
from solders.transaction import Transaction

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]
IMAGES = REPO / "research/amm-multi-hop-images"
IMAGE_PATHS = {
    "original": REPO / "evidence/original/pump_amm/deployed.so",
    "control": IMAGES / "control.so.gz",
    "candidate": IMAGES / "candidate.so.gz",
}
PAYER_KEY = Pubkey.from_string("DXyM8yAHqpMzDtvwz5DXoEUQmPxjJPMKCASCPhLMKpEx")
POOL = Pubkey.from_string("GseMAnNDvntR5uFePZ51yZBXzNSn7GdFPkfHwfr6d77J")
POOL2 = Pubkey.from_string("Fpyw25Qi4beJtjo22e1iLZ8PeGkKXFBkF2WbdSuxsaZa")
P3 = Pubkey.from_string("3tvv2kFkoHENFctvg9VKJi2z6pagcMPoHMFP3m9FfruF")
P4 = Pubkey.from_string("5gZTf2A6UPeYZCq1mkdiYquMQqmjNcz9pknbABkWif9c")
P5 = Pubkey.from_string("5TdRYVo7We7hYSXDS3ryvUvouL7hoaMLTGMRqMrzBhcE")
BASE4 = Pubkey.from_string("6ws1bVyu3F8wGy1fPHhrc2v8UyWiGbRAAuek8SwikKPD")
BASE5 = Pubkey.from_string("75hbt6uvDqjPZ9WgFtMhBnTeyHw7cinoHiz4FD2vEz2d")
VB4 = Pubkey.from_string("3qw1dQGA7eW3m2BsiAhUB5R3sXEYnr7NbMFBuqUSotYn")
VQ4 = Pubkey.from_string("6WdSUBTULBFY4FE31WymuxQqJcWeLoLBCucMFsprkUAM")
VB5 = Pubkey.from_string("EbswyL8rkPriwr3sfAftkGBRutDHAtQWK1pT7GMcJH9t")
VQ5 = Pubkey.from_string("5m89K1EMCbe1PYwQ7aJeZ8vEsSYrCRkcGMzf53Nxhvs8")
U4 = Pubkey.from_string("71nJjoSudYSAR4GApb2mtugtj8iuwf6yjKKQBpzKVehv")
U5 = Pubkey.from_string("79cu2QNvp92chEmBhBgcUfERDT9KHnUcr8eiJb5WzKML")
USERBASE = Pubkey.from_string("5jKh25biPsnrmLWXXuqKNH2Q67j69T4Q7Zew5c8wJKaV")
USERQUOTE = Pubkey.from_string("5oEzAP4izB65uRm2yDAEf9oALGwHpWkDfyKb8zBY3euC")
USERLP = Pubkey.from_string("5sAHJgXjaUPK3X1YQWV9x2ZvaS9VVaS3ENzFCNE8nzDu")
VAULTBASE = Pubkey.from_string("5jMpkf4JF4noHftLgNKyPNh6roVfPSGSjuEk3U4eLKRa")
VAULTQUOTE = Pubkey.from_string("43DVcZR4kQFjh4Xm2i3DcneRxNjZp7HMud8yDrJWrDr8")
VB2 = Pubkey.from_string("3WojBK9kk5fHnhZfDb16jNJxGu6RtVdKpxYfFUKExGjg")
VQ2 = Pubkey.from_string("7S39XJ3FdyipvwLvgrf65cDWxC1dFaXUSaoNR6wvy59t")
VB3 = Pubkey.from_string("HWrvLRAYVW6NC4QK4mofY6wcuztVZXLNm4syGwQarZnM")
VQ3 = Pubkey.from_string("8fXWArssNK14eGw3puZgFqRRDrXjMMxuWX63nYUggKXi")
U3 = Pubkey.from_string("6swiTCWtSwqi8sm9wzNwKA9NEpJWbXjLcVz654u7zz4W")
BUYBACK = Pubkey.from_string("HjQjngTDqoHE6aaGhUqfz9aQ7WZcBRjy5xB8PScLSr8i")
VOLUME = Pubkey.from_string("8NyBnxo9mS5MsqY4qoKmrt7MS89d7MNV6rh5fu2YsQPT")
PROTOCOL_ATA = Pubkey.from_string("94qWNrtmfn42h3ZjUZwWvK1MEo9uVmmrBPd2hpNjYDjb")
CREATOR_ATA = Pubkey.from_string("3E6RtRCxo7Yz64zi8aSmC9DtNKcaMp5rFUcBnJKsc2fg")
DEST = Pubkey.from_string("7MNnTJmxb2vJ7WWi15fNMHYhwvmvJyY5XMegUjDKEKKT")
PROTOCOL_ATA_P2 = Pubkey.from_string("FHJxZKyxVkCC9d4wKWs97VAYY6b9JYFjqhLBgbGnjrFA")
CREATOR_ATA_P2 = Pubkey.from_string("DwhA1oGtJr1TXh7Ubs3V31evWEkomMbaU4Bhsbqr1Vde")
DEST2 = Pubkey.from_string("7VDNjuhymdWkPh1isgKCw36ESFCKf6uieAyzbVJWiyxs")
PROTOCOL_ATA_P3 = Pubkey.from_string("Ec3s4QjSwS71dgHCBxk1H1Q8gDfWD2Qy5XzZA34wdYQi")
CREATOR_ATA_P3 = Pubkey.from_string("CGTxrQSoWdAxMRAajQHKoCuBVoKbDrczzUddHVdRdwPH")
DEST3 = Pubkey.from_string("7RJ5bcEyBLDXFbmDSNzHeAKUC5z7z3Du5mKLY7FuyeeA")
PROTOCOL_ATA_P4 = Pubkey.from_string("2W8N7FVcdvQYvTthT6xgmnKoPCBKGMRscfM6pzvQD9Zg")
CREATOR_ATA_P4 = Pubkey.from_string("AWpQ4QeMTAv4UWkkUvMymkWcBT7xDovAQDtHymwc2C9v")
DEST4 = Pubkey.from_string("7Z8ftDAzMvoyXnGEJye8DurzgQQXLAbYCaeeesM7UKHa")
PROTOCOL_ATA_P5 = Pubkey.from_string("JBAC3QYSgSavuqrPocD353ZuXJqU3YbfRvzSYEMBvGpu")
CREATOR_ATA_P5 = Pubkey.from_string("6sGd476UhAawRUjd4K4vFwopnGo9ftbmywrND12R99Qa")
DEST5 = Pubkey.from_string("7gyGAp71YXQRoxmFBaHxofQXAipvgHyBKPyxmdSJxyvz")
BB22 = Pubkey.from_string("8imwZyx4D4zdUQ67TvftjjyGattafMNWMLs6HV8WNn1Y")
PROTO22 = Pubkey.from_string("2tZUDAsQqirqn1pdnYBVM7pDao57zsTSUspuFD2tAwTS")
CREAT22 = Pubkey.from_string("HShRmMRVQBgRz1eCD1aSr1hUm2BdrALVimjNXRduJwZB")
DEST22 = Pubkey.from_string("7d3y2WdzxE7CfsWjkGy3WndkvZcj1EHMkzKJiFPiDecH")
BOOST = Pubkey.from_string("5HkYU1vqHFZDZTz5LWcDynGvbg84aiGPVG8kNUcnbbC1")
BATA = Pubkey.from_string("Cd8K5QT4ninw4jnWP7nhmPbEJb8VsECTHUzeBf7KueMS")
BP3 = Pubkey.from_string("9Kn4eTXdasQr6ELbrd7fHT4JcPTSS9LoGW2sbh8CwZPZ")
BA3 = Pubkey.from_string("5mWEub2Js9ep2Em82qCPacPcBtEaPhxyQhU9QtT9V5Tn")
GVOL = Pubkey.from_string("C2aFPdENg4A2HQsmrd5rTw5TaYBX5Ku887cWjbFKtZpw")
IMINT = Pubkey.from_string("GGfoM4FJeQ8CXTXhaWiekqRQAtYVDNAKHDdJAu8PrHtm")
GA_ATA = Pubkey.from_string("9pVmg8pt6PR5UL8FphDN6QSfEvTiPbgUvA7YBUwPrgi")
UA_ATA = Pubkey.from_string("HM5XNiWUtZACr5dE6FRAvZeUDE4cUfbXNHdR7N9RwmCS")
UVATA = Pubkey.from_string("BEaaJNs1cVZKv29qYcXaaDSgm6Defa5b6kt5pRcUkHWe")
QUOTE = Pubkey.from_string("So11111111111111111111111111111111111111112")
OUTSIDER_KEY = Pubkey.from_string("5jotNjSnm9ZJRefVfqHato9FC4d9t6CHb2xS1726MTyY")
WDEST = Pubkey.from_string("43HYZhSLzJVSwUAccwX2dmWmKBxhHDxjA1LQKJkzTg7w")
BASE22 = Pubkey.from_string("6Gg4AVKo8GAft4Wb2JSfhHCW3PQhXxYxapzBYeVjGzA9")
PLAIN = Pubkey.from_string("6Ckm2BrnXxsSjyG5b17kQQRjoECVrts92RKXVGT8XeqS")
CREATOR0 = Pubkey.from_string("29d2S7vB453rNYFdR5Ycwt7y9haRT5fwVwL9zTmBhfV2")
BC_CREATOR = Pubkey.from_string("4Ss5JMkXAD9Z7cktFEdrqeMuT6jGMF1pVozTyPHZ6zT4")
NEWVAULT = Pubkey.from_string("Gag9L2gntnWxsH4uB24Cs7rmKHgHexqVBHDmtv2443UA")
NEWVAULT22 = Pubkey.from_string("5GWYW1giwv9JvNFLjbWA4yUG6STzp93E3jRybpTXDBTy")
NEWDEST22 = Pubkey.from_string("HiaDPjMojq8s9nxZfR7A8WLFpc6fvBXe2uBk4TYRyCjc")
BCVAULT = Pubkey.from_string("6XPmtWMyuHivDoEXaDJF43utbMHopjoBieCkq6XrQxve")
BCVAULT22 = Pubkey.from_string("AsXUCL3rpZmKgqXUsX3TFffsy6tjk78EbycoQ8aoRq1k")
BCDEST22 = Pubkey.from_string("3D6PeVh59L9i8GNhYWjKDqyKyPTrnvJFevyvFT3z9ivN")
SHARING_PDA = Pubkey.from_string("1XVkGUKWHkGEnvhwiHMtTgwjs1RkdjahTMnSwrqop5D")
SHVAULT = Pubkey.from_string("12bftMSgeQFFHpeeiw5ykvhuueW5jEzrLTMXWGMBMRqs")
SHVAULT22 = Pubkey.from_string("7vmDZC25QefmsBzpCdxcNe3vKLZo18fYjFVqAdUTr1iH")
SHDEST22 = Pubkey.from_string("Ea1RHzBD6Nuh6X5Lk8GKfujd6AUXqXYZTZspk4gXBJSj")
ZEROVAULT = Pubkey.from_string("8N3GDaZ2iwN65oxVatKTLPNooAVUJTbfiVJ1ahyqwjSk")
ZEROVAULT22 = Pubkey.from_string("CtzzHDfaH7NX6Zu6w5JpRiJRTctPVE5wMhqcnohx9mig")
ZERODEST22 = Pubkey.from_string("2sZUUBGq1i6aE47ZoxCaCW89jmYm2EXLPPmNMgMDXHMS")
ORIGDEST22 = Pubkey.from_string("Dv7PMRUFDTJywhzw88zJ3tpyBmj9HqLbNq8BZwXWb7MW")
META_PDA = Pubkey.from_string("DmwqzAppxfZoXLB3CXRxMxMWTkG2DSWeMfup9JBg7Kzx")
BC_PDA = Pubkey.from_string("3MUkKMbuornHohtAtzrToSzqkj1gEEhQqYVz8sZnmQg1")
POOLV2 = Pubkey.from_string("4Jjna3h73QbgmdqwnV5NJxjCidKWB7Q26jeuj9jtFetC")
CONFIG_KEY = Pubkey.from_string("ADyA8hdefvWN2dbGGWFotbzWxrAvLW83WG6QCVXvJKqw")
RES0_ATA = Pubkey.from_string("2dmiSdVXhau9JVgrW7BFhYZCnPhDX8vKZ4Rj8vsowAb3")
CPOOL = Pubkey.from_string("35N1cB5z1NfVk8GaDcW45Sdv187oPt3tdNb9kMM9sp3L")
CTAIL = Pubkey.from_string("2ucBziY5uzQfbyQyf7e6shj66zWu3vTCirsmUvPRgXTx")
CTAIL1 = Pubkey.from_string("EBFRtnSXfNCvKLJoXHhGD76pqPg96j57kFFouhhzN8uW")
CLP = Pubkey.from_string("CNvXYXQLeRBKMqmAu65cTp6uT3AVJg3GasG9kmMGXd6k")
CTLP = Pubkey.from_string("DA3oVLWTd5kKxKQxtNbzxW4j9fjN1uSr9ZBK9bod2SV2")
CT1LP = Pubkey.from_string("56QHt5rCvx33cbAWFLdU1kFRvjSNi2rFp1tMpsBzhkjh")
CVB = Pubkey.from_string("7wgw5PUWo4RDP5Ar4okz5PRXc6G9UsCuAaQthSdR6vQG")
CVQ = Pubkey.from_string("28cykPNdfF2QycG7zb83UiznDEqFt82fhpdhfJCN9xto")
CULP = Pubkey.from_string("9HFUKF9zA7Gx6p2h4Li16wVYkqJzkd8TBnHfFLXogLLb")
CTVB = Pubkey.from_string("DEeKAvh6d59uoCPdTtuTmqAzf6DpqFThdjU5kHzyDRJN")
CTVQ = Pubkey.from_string("52jQ4iLDjG2PtFypb7wxisr7tgTKPKGmZPmbsdaLYVd8")
CTULP = Pubkey.from_string("2pqcF3UycykBAPaW7AjnuhR5K8CMswqWXkcHG7wqS511")
CT1VB = Pubkey.from_string("87VmdGga8NfdqThcngGBVgWHiUL8UGLjTA7qPXYBHTf6")
CT1VQ = Pubkey.from_string("2PRzV3coJ31Qj4Kms1MiCVKamjNtccaEMJ1rLKDhCSDp")
CT1ULP = Pubkey.from_string("GrtaxrpBk1xYdy7nm5oCUMPS1bLBES3EnY27uZsWjavv")
CUB = Pubkey.from_string("548jb4wcUtpbNS1TAva8TXJmeXd5QpCCXUzNVogwpzMR")
CUQ = Pubkey.from_string("5842jNQd5C7pWXFxcDu3kQ5XtgqH5st25tf2ZBjYaKg8")
CUB3 = Pubkey.from_string("5Ftd1yLeFniGnhkyUpYtL9d4P1FgS1FfChzLfwpk4zKY")
CUQ2 = Pubkey.from_string("5KovAGoer61Vvo1Uv7sod2PpdATt74wUm7ezjKsLpKeF")
ZVAULT = Pubkey.from_string("8N3GDaZ2iwN65oxVatKTLPNooAVUJTbfiVJ1ahyqwjSk")
ZATA = Pubkey.from_string("Ei6iux5MMYG8JxCTr58goADqFTtMroL9TXJityF3fAQc")
ZDEST = Pubkey.from_string("5ByKsfsdfVR3ecWU3XDy3GrJ8r3UkwZqeJKgcZn9Kezq")
CBV = Pubkey.from_string("E92NYMp5WH7fGhEicYdTqA7tK5BDH3b4uTSjjD8xHMuB")
CBA = Pubkey.from_string("C4Xp5zYy2UEbQ1GzCdwwPQtgvyW1mRqi88ra76nvuk8A")
ROLE_KEY = {"userbase": USERBASE, "userquote": USERQUOTE, "userlp": USERLP,
            "vaultbase": VAULTBASE, "vaultquote": VAULTQUOTE, "buyback": BUYBACK,
            "vb1": VAULTBASE, "vq1": VAULTQUOTE, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22,
            "wdest": WDEST, "base22": BASE22, "plain": PLAIN,
            "boostata": BATA, "boostata3": BA3,
            "gata": GA_ATA, "uata": UA_ATA, "uvata": UVATA,
            "newvault": NEWVAULT22, "newdest": NEWDEST22,
            "bcvault": BCVAULT22, "bcdest": BCDEST22,
            "shvault": SHVAULT22, "shdest": SHDEST22,
            "zerovault": ZEROVAULT22, "zerodest": ZERODEST22,
            "origdest": ORIGDEST22,
            "cvb": CVB, "cvq": CVQ, "culp": CULP, "cub": CUB, "cuq": CUQ,
            "ctvb": CTVB, "ctvq": CTVQ, "ctulp": CTULP, "cub3": CUB3, "cuq2": CUQ2,
            "ct1vb": CT1VB, "ct1vq": CT1VQ, "ct1ulp": CT1ULP,
            "zata": ZATA, "zdest": ZDEST, "cba": CBA, "cbv": CBV,
            "res0ata": RES0_ATA}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata2", "creatorata2", "dest2",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "bb22", "proto22", "creat22", "dest22",
               "wdest", "base22", "plain",
               "boostata", "boostata3",
               "gata", "uata", "uvata",
               "newvault", "newdest", "bcvault", "bcdest",
               "cvb", "cvq", "culp", "cub", "cuq",
               "ctvb", "ctvq", "ctulp", "cub3", "cuq2",
               "ct1vb", "ct1vq", "ct1ulp",
               "zata", "zdest", "cba", "cbv",
               "shvault", "shdest", "zerovault", "zerodest", "origdest",
               "res0ata"]
POOL_KEYS = {"main": POOL, "pool2": POOL2, "p3": P3, "p4": P4, "p5": P5}
CPOOL_KEYS = {"cpool": CPOOL, "ctail": CTAIL, "ctail1": CTAIL1}


def fail(msg):
    raise SystemExit(f"FAIL: {msg}")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def error_matches(recorded, expected):
    """Match an expectation against a receipt error; program codes by value.

    The expectation is usually the bare program code ("6004") and the record
    is the full transaction error ("...Custom(6004)"). A substring test also
    accepts Custom(16004), and accepts Custom(6014) for the code "1".
    """
    if not expected.isdigit():
        return expected in recorded
    return any(code.split(")", 1)[0] == expected
               for code in recorded.split("Custom(")[1:])


def require_prefix(expect, key):
    """A step may omit a field its sequence has not reached, never one it has.

    Steps before the first declared value legitimately leave the key out. A
    later step that drops it would skip the check while the PASS line still
    claims the field was compared, so the sequence has to keep it.
    """
    seen = False
    for index, exp in enumerate(expect):
        present = key in exp
        if seen and not present:
            fail(f"expectation {index} drops {key}")
        seen = seen or present


def tok_amount(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 72:
        return None
    return struct.unpack_from("<Q", raw, 64)[0]


def tok_delta(rec, key):
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
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
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
    return (wh_of(a) or 0) - (wh_of(b) or 0)


def mint_wh(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return struct.unpack_from("<Q", raw, 234)[0] if len(raw) >= 242 else None


def lam_delta(rec, key):
    b = rec["before"][str(key)]
    a = rec["after"][str(key)]
    return (a["lamports"] if a else 0) - (b["lamports"] if b else 0)


def pool_state(entry):
    if entry is None:
        return None
    d = bytes.fromhex(entry["data_hex"])
    return [int.from_bytes(d[245:261], "little", signed=True),
            struct.unpack_from("<Q", d, 271)[0],
            struct.unpack_from("<Q", d, 279)[0],
            struct.unpack_from("<Q", d, 203)[0]]


def vol_state(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return {"lamports": entry["lamports"], "len": len(raw),
            "user": raw[8:40].hex()}


def uva_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 90:
        return {"len": len(raw)}
    needs, unc, cla, vol, last, hasc, earn, cbcl = struct.unpack_from('<BQQQqBQQ', raw, 40)
    return {"needs": needs, "unclaimed": unc, "claimed": cla, "volume": vol,
            "last": last, "has": hasc, "earned": earn, "cb_claimed": cbcl}


def u64(raw, off):
    return struct.unpack_from("<Q", raw, off)[0]


def cfg_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 949:
        return {"len": len(raw)}
    return {"admin": raw[8:40].hex(), "disable": raw[56], "lp": u64(raw, 40), "proto": u64(raw, 48),
            "recipients": [raw[57 + i * 32:57 + (i + 1) * 32].hex() for i in range(8)],
            "creator_fee": u64(raw, 313), "fee_auth": raw[321:353].hex(),
            "bps": u64(raw, 899),
            "bb_recipients": [raw[643 + i * 32:643 + (i + 1) * 32].hex() for i in range(8)],
            "mayhem": raw[417], "cashback": raw[642],
            "boost_auth": raw[907:939].hex(), "boost_enabled": raw[939]}


def cfgres_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 949:
        return {"len": len(raw)}
    return {"wl": raw[353:385].hex(),
            "res": [raw[385:417].hex()] + [raw[418 + i * 32:418 + (i + 1) * 32].hex() for i in range(7)]}


def ev_list(logs):
    return [base64.b64decode(l.split("Program data: ", 1)[1].strip())
            for l in logs if l.startswith("Program data: ")]


def decode_event(kind, raw):
    if kind == "setr":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "recip": raw[16:48].hex(),
                "recips": [raw[48 + i * 32:48 + (i + 1) * 32].hex() for i in range(7)]}
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1",
                "mhbuy3c", "mhsell3c"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind == "create":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 116), "quote": u64(raw, 124),
                "pbase": u64(raw, 132), "pquote": u64(raw, 140),
                "minliq": u64(raw, 148), "initliq": u64(raw, 156),
                "lpout": u64(raw, 164)}
    if kind in ("swp", "swc", "swp22", "swc22", "swc22c", "swpc", "swcc", "swp22o", "swc22o"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "recipient": raw[112:144].hex(),
                "amount": u64(raw, 176), "bucket": raw[184]}
    if kind in ("dep", "wd", "depc", "wdc"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 72), "quote": u64(raw, 80)}
    if kind in ("col", "col22", "col22c", "colc", "col22o"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "creator": raw[16:48].hex(), "fee": u64(raw, 48),
                "vault_ata": raw[56:88].hex(), "dest": raw[88:120].hex()}
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
    if kind == "sync":
        return {"disc": raw[:8].hex(), "user": raw[8:40].hex(),
                "before": u64(raw, 40), "after": u64(raw, 48),
                "ts": struct.unpack_from("<q", raw, 56)[0], "len": len(raw)}
    if kind in ("extend", "extend_unsigned", "extend_readonly"):
        return {"disc": raw[:8].hex(),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "account": raw[16:48].hex(), "user": raw[48:80].hex(),
                "old": u64(raw, 80), "new": u64(raw, 88), "len": len(raw)}
    if kind == "ufc":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "admin": raw[16:48].hex(), "lp": u64(raw, 48), "proto": u64(raw, 56),
                "recipients": [raw[64 + i * 32:64 + (i + 1) * 32].hex() for i in range(8)],
                "creator": u64(raw, 320), "authority": raw[328:360].hex()}
    if kind == "dis":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "admin": raw[16:48].hex(),
                "bools": [raw[48 + i] for i in range(5)]}
    if kind == "set":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "creator": raw[112:144].hex()}
    if kind == "mig":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "old": raw[112:144].hex(), "new": raw[144:176].hex()}
    if kind in ("buy2", "buy2c"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "curve": u64(raw, 64), "lp_bps": u64(raw, 72),
                "lp_fee": u64(raw, 80), "proto_bps": u64(raw, 88),
                "proto_fee": u64(raw, 96), "qwlp": u64(raw, 104),
                "uin": u64(raw, 112)}
    if kind in ("sell2", "sell2c"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "curve": u64(raw, 64), "lp_bps": u64(raw, 72),
                "lp_fee": u64(raw, 80), "proto_bps": u64(raw, 88),
                "proto_fee": u64(raw, 96), "quote": u64(raw, 104),
                "uout": u64(raw, 112)}
    if kind == "rot":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "admin": raw[16:48].hex(), "new_admin": raw[48:80].hex()}
    if kind == "boostauth":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "ts": struct.unpack_from("<q", raw, 8)[0],
                "admin": raw[16:48].hex(), "old": raw[48:80].hex(),
                "new": raw[80:112].hex()}
    if kind in ("boost", "boosto", "boost3", "boost4", "boost5", "boostc"):
        if raw[:8].hex() != "3f451c16305cc2b9":
            return {"disc": raw[:8].hex(), "len": len(raw)}
        return {"disc": raw[:8].hex(), "len": len(raw),
                "requested": u64(raw, 144), "used": u64(raw, 152),
                "burned": u64(raw, 160),
                "vq": int.from_bytes(raw[168:184], "little", signed=True),
                "quote_after": u64(raw, 184), "base_after": u64(raw, 192),
                "remaining": u64(raw, 200)}
    return None


def surface(recs):
    out = []
    for rec in recs:
        def strip(snap):
            d = dict(snap)
            if d.get(str(PAYER_KEY)) is not None:
                d[str(PAYER_KEY)] = dict(d[str(PAYER_KEY)])
                d[str(PAYER_KEY)]["lamports"] = 0
            return d
        out.append({"step": rec["step"], "error": rec["error"],
                    "events": len(ev_list(rec["logs"])),
                    "before": strip(rec["before"]), "after": strip(rec["after"])})
    return out


def main():
    manifest = json.loads((ROOT / "MANIFEST.json").read_text())
    # The loop below checks the files the manifest names; a file the packet ships
    # with no entry passes every check it makes. Compare the two sets first.
    manifest_paths = {entry['path'] for entry in manifest['files']}
    if len(manifest_paths) != len(manifest['files']):
        raise SystemExit('duplicate packet manifest path')
    entries = list(ROOT.rglob('*'))
    # Python -B still reads cached bytecode; it must not bypass source admission.
    if any(p.is_symlink() or p.suffix in ('.pyc', '.pyo') for p in entries):
        raise SystemExit('packet contains a symlink or cached Python bytecode')
    packet_paths = {p.relative_to(ROOT).as_posix() for p in entries
                    if p.is_file() and p != ROOT / 'MANIFEST.json'
                    and p.name != '.DS_Store' and '.git' not in p.relative_to(ROOT).parts}
    if manifest_paths != packet_paths:
        raise SystemExit('packet file set differs from MANIFEST.json: '
                         f'missing={sorted(packet_paths - manifest_paths)} '
                         f'extra={sorted(manifest_paths - packet_paths)}')

    for entry in manifest["files"]:
        path = ROOT / entry["path"]
        if not path.exists():
            fail(f"missing file {entry['path']}")
        if sha(path.read_bytes()) != entry["sha256"]:
            fail(f"sha mismatch {entry['path']}")
    with gzip.open(ROOT / "runtime" / "report.json.gz", "rt", encoding="utf-8") as fh:
        report = json.load(fh)
    if report["case_count"] != 35 or report["receipt_count"] != 240:
        fail(f"counts {report['case_count']} cases / {report['receipt_count']} receipts")
    if len(report["cases"]) != report["case_count"]:
        fail(f"case list {len(report['cases'])} != {report['case_count']}")
    if report["counts"] != {"cases": 35, "receipts": 240, "parts": 24}:
        fail(f"counts block {report['counts']}")
    if report["mismatches"] != []:
        fail(f"mismatches recorded: {report['mismatches']}")
    for name, path in IMAGE_PATHS.items():
        image = path.read_bytes()
        if path.suffix == ".gz":
            image = gzip.decompress(image)
        if sha(image) != report["images"][name]:
            fail(f"image hash mismatch {name}")
    receipts = []
    for part in report["parts"]:
        path = ROOT / part["file"]
        data = path.read_bytes()
        if sha(data) != part["sha256"] or len(data) != part["bytes"]:
            fail(f"part hash/size mismatch {part['file']}")
        with gzip.open(path, "rt", encoding="utf-8") as fh:
            chunk = [json.loads(line) for line in fh if line.strip()]
        if len(chunk) != part["count"]:
            fail(f"part count mismatch {part['file']}")
        receipts.extend(chunk)
    if len(receipts) != 240:
        fail(f"receipt total {len(receipts)}")
    by_case = {}
    for rec in receipts:
        by_case.setdefault(rec["case"], {}).setdefault(rec["image"], []).append(rec)
    divergent_labels = []
    for case in report["cases"]:
        label = case["label"]
        steps = case["steps"]
        for image in ("original", "control", "candidate"):
            expect = steps["original" if image == "original" else "rebuilt"] \
                if isinstance(steps, dict) else steps
            recs = by_case.get(label, {}).get(image)
            if recs is None or len(recs) != len(expect):
                fail(f"{label}/{image}: {0 if recs is None else len(recs)} receipts, expected {len(expect)}")
            require_prefix(expect, "cfg")
            for rec, exp in zip(recs, expect):
                tag = f"{label}/{image}/{rec['step']}"
                tx = Transaction.from_bytes(base64.b64decode(rec["transaction_base64"]))
                # all() is true for an empty result list, so a receipt whose
                # signature vector was stripped would pass the bare all().
                results = tx.verify_with_results()
                if not results or not all(results):
                    fail(f"{tag}: signature verification failed")
                if exp["error"] is None:
                    if rec["error"] is not None:
                        fail(f"{tag}: unexpected error {rec['error']}")
                else:
                    if rec["error"] is None or not error_matches(rec["error"], exp["error"]):
                        fail(f"{tag}: expected error {exp['error']}, got {rec['error']}")
                events = len(ev_list(rec["logs"]))
                if events != exp["events"]:
                    fail(f"{tag}: events {events} != {exp['events']}")
                if lam_delta(rec, PAYER_KEY) != exp["dPAYER"]:
                    fail(f"{tag}: dPAYER {lam_delta(rec, PAYER_KEY)} != {exp['dPAYER']}")
                if lam_delta(rec, OUTSIDER_KEY) != exp.get("dOUT", 0):
                    fail(f"{tag}: dOUT {lam_delta(rec, OUTSIDER_KEY)} != {exp.get('dOUT', 0)}")
                for role, want in exp.get("lam_deltas", {}).items():
                    if lam_delta(rec, ROLE_KEY[role]) != want:
                        fail(f"{tag}: lam_delta {role} {lam_delta(rec, ROLE_KEY[role])} != {want}")
                for role in TOKEN_ROLES:
                    if role in exp.get("lam_deltas", {}):
                        continue
                    if lam_delta(rec, ROLE_KEY[role]) != 0:
                        fail(f"{tag}: unexpected lam_delta {role} {lam_delta(rec, ROLE_KEY[role])}")
                if "mint_wh" in exp:
                    if mint_wh(rec["after"][str(QUOTE)]) != exp["mint_wh"]:
                        fail(f"{tag}: mint_wh {mint_wh(rec['after'][str(QUOTE)])} != {exp['mint_wh']}")
                for role, want in exp["deltas"].items():
                    if tok_delta(rec, ROLE_KEY[role]) != want:
                        fail(f"{tag}: delta {role} {tok_delta(rec, ROLE_KEY[role])} != {want}")
                for role in TOKEN_ROLES:
                    if role in exp["deltas"]:
                        continue
                    if tok_delta(rec, ROLE_KEY[role]) != 0:
                        fail(f"{tag}: unexpected delta {role} {tok_delta(rec, ROLE_KEY[role])}")
                for role, want in exp.get("withheld", {}).items():
                    if wh_delta(rec, ROLE_KEY[role]) != want:
                        fail(f"{tag}: withheld {role} {wh_delta(rec, ROLE_KEY[role])} != {want}")
                for role in TOKEN_ROLES:
                    if role in exp.get("withheld", {}):
                        continue
                    if wh_delta(rec, ROLE_KEY[role]) != 0:
                        fail(f"{tag}: unexpected withheld {role} {wh_delta(rec, ROLE_KEY[role])}")
                for pool_name, pool_key in POOL_KEYS.items():
                    if pool_state(rec["after"][str(pool_key)]) != exp["pools"][pool_name]:
                        fail(f"{tag}: pool {pool_name} {pool_state(rec['after'][str(pool_key)])} != {exp['pools'][pool_name]}")
                if "pool_creator" in exp:
                    got_pc = bytes.fromhex(rec["after"][str(POOL)]["data_hex"])[211:243].hex()
                    if got_pc != exp["pool_creator"]:
                        fail(f"{tag}: pool_creator {got_pc} != {exp['pool_creator']}")
                if "cpools" in exp:
                    for cpool_name, cpool_key in CPOOL_KEYS.items():
                        if pool_state(rec["after"][str(cpool_key)]) != exp["cpools"][cpool_name]:
                            fail(f"{tag}: cpool {cpool_name} {pool_state(rec['after'][str(cpool_key)])} != {exp['cpools'][cpool_name]}")
                if "ccreators" in exp:
                    for cpool_name, cpool_key in CPOOL_KEYS.items():
                        entry = rec["after"][str(cpool_key)]
                        want = exp["ccreators"][cpool_name]
                        if entry is None:
                            got_cc = None
                        else:
                            raw_cc = bytes.fromhex(entry["data_hex"])
                            got_cc = (raw_cc[11:43].hex(), raw_cc[211:243].hex())
                        if got_cc != (tuple(want) if want is not None else None):
                            fail(f"{tag}: ccreator {cpool_name} {got_cc} != {want}")
                if vol_state(rec["after"][str(VOLUME)]) != exp["volume"]:
                    fail(f"{tag}: volume {vol_state(rec['after'][str(VOLUME)])} != {exp['volume']}")
                if exp.get("uva") is not None:
                    got_uva = uva_fields(rec["after"][str(VOLUME)])
                    if got_uva != exp["uva"]:
                        fail(f"{tag}: uva {got_uva} != {exp['uva']}")
                if "cfg" in exp:
                    got_cfg = cfg_fields(rec["after"][str(CONFIG_KEY)])
                    if got_cfg != exp["cfg"]:
                        fail(f"{tag}: cfg {got_cfg} != {exp['cfg']}")
                if "cfgres" in exp:
                    got_cr = cfgres_fields(rec["after"][str(CONFIG_KEY)])
                    if got_cr != exp["cfgres"]:
                        fail(f"{tag}: cfgres {got_cr} != {exp['cfgres']}")
                if exp.get("uva_absent"):
                    if rec["after"][str(VOLUME)] is not None:
                        fail(f"{tag}: volume should stay absent")
                for role, want in exp.get("lam_after", {}).items():
                    got = rec["after"][str(ROLE_KEY[role])]
                    if got is None or got["lamports"] != want:
                        fail(f"{tag}: lam_after {role} {None if got is None else got['lamports']} != {want}")
                if rec["after"][str(GVOL)] != rec["before"][str(GVOL)]:
                    fail(f"{tag}: global volume accumulator changed")
                if exp.get("log_fragment"):
                    if exp["log_fragment"] not in "\n".join(rec["logs"]):
                        fail(f"{tag}: log fragment missing")
                if exp.get("site_fragment"):
                    if exp["site_fragment"] not in "\n".join(rec["logs"]):
                        fail(f"{tag}: site fragment missing")
                if exp.get("rollback"):
                    for k, b in rec["before"].items():
                        if k in (str(PAYER_KEY), str(OUTSIDER_KEY)):
                            continue
                        if rec["after"][k] != b:
                            fail(f"{tag}: rollback violated for {k}")
                if exp.get("boost_event") is not None:
                    raws = ev_list(rec["logs"])
                    if len(raws) != 2:
                        fail(f"{tag}: boost events {len(raws)} != 2")
                    first = decode_event(rec["step"], raws[0])
                    if first != {"disc": "67f4521f2cf57777", "len": 512}:
                        fail(f"{tag}: boost first event {first}")
                    got = decode_event(rec["step"], raws[1])
                    if got is None:
                        fail(f"{tag}: boost event decode failed")
                    for fkey, want in exp["boost_event"].items():
                        if got.get(fkey) != want:
                            fail(f"{tag}: boost event {fkey} {got.get(fkey)} != {want}")
                if exp.get("event") is not None:
                    raws = ev_list(rec["logs"])
                    if len(raws) != exp["events"]:
                        fail(f"{tag}: decoded events {len(raws)} != {exp['events']}")
                    for raw in raws:
                        got = decode_event(rec["step"], raw)
                        if got is None:
                            fail(f"{tag}: event decode failed")
                        for fkey, want in exp["event"].items():
                            if got.get(fkey) != want:
                                fail(f"{tag}: event {fkey} {got.get(fkey)} != {want}")
        base = surface(by_case[label]["original"])
        if surface(by_case[label]["control"]) != surface(by_case[label]["candidate"]):
            fail(f"{label}: control and candidate surfaces differ")
        computed_divergent = (surface(by_case[label]["control"]) != base
                              or surface(by_case[label]["candidate"]) != base)
        if computed_divergent:
            divergent_labels.append(label)
        if computed_divergent != case["divergent"]:
            fail(f"{label}: divergent flag {case['divergent']} != computed {computed_divergent}")
        for image in ("original", "control", "candidate"):
            sites = case["error_sites"][image]
            recs = by_case[label][image]
            if len(sites) != len(recs):
                fail(f"{label}/{image}: site count mismatch")
            for rec, site in zip(recs, sites):
                if site is not None and site not in "\n".join(rec["logs"]):
                    fail(f"{label}/{image}: recorded site line not in logs: {site}")
    print(f"PASS: 35 cases, 240 receipts, 24 parts, per-image expectations hold "
          f"(signatures, deltas, withheld, mint withheld, lamports, events, "
          f"error codes, rollback, UVA fields, mode-flag config fields, "
          f"multi-hop/toggle/sweep/collect/boost/cashback-claim events, "
          f"GVOL invariance); control == candidate everywhere; "
          f"({len(divergent_labels)} divergent cases): {divergent_labels}")


if __name__ == "__main__":
    main()
