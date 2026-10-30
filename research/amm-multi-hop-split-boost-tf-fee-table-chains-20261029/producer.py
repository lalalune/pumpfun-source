#!/usr/bin/env python3
"""Build research/amm-multi-hop-split-boost-tf-fee-table-chains-20261029 receipts.

3rd run packet #80: the split x boost x tf chain at TRUE 3 hops
(three_amm only, final output U3 -- the route 3rd #63/#64 pinned)
meets the fee TABLE itself (2nd #8/#29, 3rd #35/#36/#79): tier
thresholds, tier counts, tier order, exotic flat fees and the
fee-table account are varied around the chain -- whether each hop
prices from its own table entry, where the tier boundary actually
moves the chain, what the table account itself gates, and whether
sweep/collect/boost/claim downstream legs notice a table change.
All cases are expected to agree on
all three images; error sites are pinned per image, never compared
across images.

Route check (read from this builder, not the packet name):
build_route calls three_amm only and appends NO g4/g5 hop group,
so the route is main -> POOL2 -> P3, final output U3: TRUE 3 hops.
The quote mint carries a per-case transfer-fee config (bps 0/100)
and the split legs route the buyback through the TOKEN22 ATA.
"""
import base64
import gzip
import hashlib
import json
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import os
sys.path.insert(0, str(Path.home() / "workspace/pumpfun-sparse/scripts"))
os.chdir(Path.home() / "workspace/pumpfun-sparse")
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

from pump_amm_admin_differential import Harness, OUTSIDER
from pump_amm_liquidity_differential import (
    CONFIG, CONFIG_KEY, EVENT, IDL, PAYER, PROGRAM, RAW, TOKEN, TOKEN22,
    base, f, lp, pool, poolraw, quote, supply, token, transferfee,
    userbase, userlp, userquote, vaultbase, vaultquote,
)
from pump_amm_trade_v2_differential import FEES, buyback, feeconfig, volume
from pump_amm_legacy_buy_differential import uvata
from pump_amm_multi_hop_differential import (
    BASE2, BASE3, P3, POOL2, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT,
    U3, VB2, VB3, VQ2, VQ3, three_amm,
)

ROOT = Path.home() / "workspace/pumpfun-sparse"
OUT = ROOT / "research/amm-multi-hop-split-boost-tf-fee-table-chains-20261029"
WS = Path.home() / "workspace/slop-verify"
IMAGES = {
    "original": ROOT / "evidence/original/pump_amm/deployed.so",
    "control": WS / "control.so",
    "candidate": WS / "candidate.so",
}
IMAGE_SHA = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in IMAGES.items()}

ATA_PROG = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
PAYER_KEY = PAYER.pubkey()
OUTSIDER_KEY = OUTSIDER.pubkey()
PAYER_HEX = bytes(PAYER_KEY).hex()
CREATOR = Pubkey.from_bytes(bytes(poolraw[211:243]))
CREATOR_VAULT, _ = Pubkey.find_program_address([b'creator_vault', bytes(CREATOR)], PROGRAM)
CREATOR_ATA, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(quote)], ATA_PROG)
PROTOCOL = Pubkey.from_bytes(bytes(RAW[57:89]))
PROTOCOL_ATA, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(quote)], ATA_PROG)
CREATOR_ATA_P3, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE2)], ATA_PROG)
PROTOCOL_ATA_P3, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE2)], ATA_PROG)
CREATOR_ATA_P2, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(base)], ATA_PROG)
PROTOCOL_ATA_P2, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(base)], ATA_PROG)
DEST = Pubkey.from_bytes(bytes([94]) * 32)
DEST3 = Pubkey.from_bytes(bytes([95]) * 32)
DEST2 = Pubkey.from_bytes(bytes([96]) * 32)
BASE4 = Pubkey.from_bytes(bytes([88]) * 32)
C4 = Pubkey.find_program_address([b'pool-authority', bytes(BASE4)], PUMP)[0]
P4, B4 = Pubkey.find_program_address([b'pool', bytes(2), bytes(C4), bytes(BASE4), bytes(BASE3)], PROGRAM)
VB4 = Pubkey.find_program_address([bytes(P4), bytes(TOKEN), bytes(BASE4)], ATA_PROG)[0]
VQ4 = Pubkey.find_program_address([bytes(P4), bytes(TOKEN), bytes(BASE3)], ATA_PROG)[0]
U4 = Pubkey.from_bytes(bytes([89]) * 32)
BASE5 = Pubkey.from_bytes(bytes([90]) * 32)
C5 = Pubkey.find_program_address([b'pool-authority', bytes(BASE5)], PUMP)[0]
P5, B5 = Pubkey.find_program_address([b'pool', bytes(2), bytes(C5), bytes(BASE5), bytes(BASE4)], PROGRAM)
VB5 = Pubkey.find_program_address([bytes(P5), bytes(TOKEN), bytes(BASE5)], ATA_PROG)[0]
VQ5 = Pubkey.find_program_address([bytes(P5), bytes(TOKEN), bytes(BASE4)], ATA_PROG)[0]
U5 = Pubkey.from_bytes(bytes([91]) * 32)
DEST4 = Pubkey.from_bytes(bytes([97]) * 32)
DEST5 = Pubkey.from_bytes(bytes([99]) * 32)
CREATOR_ATA_P4, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
PROTOCOL_ATA_P4, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE3)], ATA_PROG)
CREATOR_ATA_P5, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
PROTOCOL_ATA_P5, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN), bytes(BASE4)], ATA_PROG)
PROTO22, _ = Pubkey.find_program_address([bytes(PROTOCOL), bytes(TOKEN22), bytes(quote)], ATA_PROG)
CREAT22, _ = Pubkey.find_program_address([bytes(CREATOR_VAULT), bytes(TOKEN22), bytes(quote)], ATA_PROG)
DEST22 = Pubkey.from_bytes(bytes([98]) * 32)
META_PROG = Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
FEES_PROG = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
CREATOR0 = Pubkey.from_bytes(bytes([0x11]) * 32)
BC_CREATOR = Pubkey.from_bytes(bytes([0x33]) * 32)
ZERO_CREATOR = Pubkey.default()
META_PDA, _ = Pubkey.find_program_address([b'metadata', bytes(META_PROG), bytes(base)], META_PROG)
BC_PDA, _ = Pubkey.find_program_address([b'bonding-curve', bytes(base)], PUMP)
SHARING_PDA, _ = Pubkey.find_program_address([b'sharing-config', bytes(base)], FEES_PROG)
POOLV2 = Pubkey.find_program_address([b'pool-v2', bytes(base)], PROGRAM)[0]


def vault_of(creator):
    return Pubkey.find_program_address([b'creator_vault', bytes(creator)], PROGRAM)[0]


def ata22_of(owner):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN22), bytes(quote)], ATA_PROG)[0]


NEWVAULT = vault_of(CREATOR0)
NEWVAULT22 = ata22_of(NEWVAULT)
NEWDEST22 = ata22_of(CREATOR0)
BCVAULT = vault_of(BC_CREATOR)
BCVAULT22 = ata22_of(BCVAULT)
BCDEST22 = ata22_of(BC_CREATOR)
SHVAULT = vault_of(SHARING_PDA)
SHVAULT22 = ata22_of(SHVAULT)
SHDEST22 = ata22_of(SHARING_PDA)
ZEROVAULT = vault_of(ZERO_CREATOR)
ZEROVAULT22 = ata22_of(ZEROVAULT)
ZERODEST22 = ata22_of(ZERO_CREATOR)
ORIGDEST22 = ata22_of(CREATOR)
SET_KEYS = [pool, META_PDA, BC_PDA, EVENT, PROGRAM]
MIG_KEYS = [pool, SHARING_PDA, EVENT, PROGRAM]
SET_DISC = "966bc77b7ccf66e4"
SETBC_DISC = "f2e7eb664163bdd3"
MIG_DISC = "aadd52c793a5f72e"
BC_DISC = bytes([23, 183, 248, 55, 96, 216, 172, 96])
BB_DISC = bytes.fromhex("fbe0ab92a01a71e9")
UFC_DISC = bytes([104, 184, 103, 242, 88, 151, 107, 20])
DISABLE_DISC = bytes.fromhex("b9adbb5ad80feee9")
UFC_EV_DISC = "5a1741233ef4bcd0"
DIS_EV_DISC = "6bfdc14ce4ca1b68"
NEW8 = [Pubkey.from_bytes(bytes([210 + i]) * 32) for i in range(8)]
NEW_SORTED = sorted(NEW8, key=bytes)
NEW_DESC = sorted(NEW8, key=bytes, reverse=True)
AUTH_NEW = bytes([99]) * 32
SH_DISC = bytes([216, 74, 9, 0, 56, 140, 93, 75])


def s32(b):
    return struct.pack('<I', len(b)) + b


def metadata(creators, key=4):
    d = bytearray()
    d += bytes([key])
    d += bytes([0x44]) * 32
    d += bytes(base)
    d += s32(b'TEST') + s32(b'TST') + s32(b'https://example.invalid/x.json')
    d += struct.pack('<H', 500)
    if creators is None:
        d += bytes([0])
    else:
        d += bytes([1]) + struct.pack('<I', len(creators))
        for c in creators:
            d += bytes(c) + bytes([1, 100])
    d += bytes([0]) + bytes([0]) + bytes([1, 1]) + bytes([0]) + bytes([0]) + bytes([0])
    return bytes(d)


def bonding_curve(creator=BC_CREATOR):
    d = bytearray(BC_DISC)
    d += struct.pack('<QQQQQ', 10**9, 10**9, 10**9, 10**9, 10**12)
    d += bytes([0]) + bytes(creator) + bytes([0, 0])
    return bytes(d)


def sharing(admin, mint, status=1, revoked=0):
    d = bytearray(80)
    d[0:8] = SH_DISC
    d[10] = status
    d[11:43] = bytes(mint)
    d[43:75] = bytes(admin)
    d[75] = revoked
    d[76:80] = struct.pack('<I', 0)
    return bytes(d)

WDEST, _ = Pubkey.find_program_address([bytes(PAYER_KEY), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BASE22 = Pubkey.from_bytes(bytes([78]) * 32)
PLAIN = Pubkey.from_bytes(bytes([77]) * 32)
_BB_OWNER = None
for _row in f["accounts"].values():
    if _row["address"] == str(buyback):
        _BB_OWNER = Pubkey.from_bytes(base64.b64decode(_row["data_base64"])[32:64])
assert _BB_OWNER is not None, "buyback fixture row not found"
BB22, _ = Pubkey.find_program_address([bytes(_BB_OWNER), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BOOST, _ = Pubkey.find_program_address([b'boost_vault', bytes(pool)], PROGRAM)
BATA, _ = Pubkey.find_program_address([bytes(BOOST), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BP3, _ = Pubkey.find_program_address([b'boost_vault', bytes(P3)], PROGRAM)
BA3, _ = Pubkey.find_program_address([bytes(BP3), bytes(TOKEN22), bytes(BASE2)], ATA_PROG)

GVOL = Pubkey.find_program_address([b'global_volume_accumulator'], PROGRAM)[0]
GDISC = bytes(next(x for x in IDL['accounts'] if x['name'] == 'GlobalVolumeAccumulator')['discriminator'])
UVA_DISC = bytes(next(x for x in IDL['accounts'] if x['name'] == 'UserVolumeAccumulator')['discriminator'])
IMINT = Pubkey.from_bytes(bytes([226]) * 32)
GA_ATA, _ = Pubkey.find_program_address([bytes(GVOL), bytes(TOKEN22), bytes(IMINT)], ATA_PROG)
UA_ATA, _ = Pubkey.find_program_address([bytes(PAYER_KEY), bytes(TOKEN22), bytes(IMINT)], ATA_PROG)
TCLAIM_KEYS = [PAYER_KEY, UA_ATA, GVOL, GA_ATA, volume, IMINT, TOKEN22,
               Pubkey.default(), ATA_PROG, EVENT, PROGRAM, PAYER_KEY]
CLAIM_KEYS = [PAYER_KEY, volume, quote, TOKEN, uvata, userquote,
              Pubkey.default(), EVENT, PROGRAM]


def t22acct(owner, amount, withheld=0):
    data = bytearray(165)
    data[0:32] = bytes(quote)
    data[32:64] = bytes(owner)
    struct.pack_into("<Q", data, 64, amount)
    data[108] = 1
    return bytes(data) + bytes([2]) + struct.pack("<HH", 7, 0) + struct.pack("<HHQ", 2, 8, withheld)
def t22acct_mint(mint, owner, amount, withheld=0):
    data = bytearray(165)
    data[0:32] = bytes(mint)
    data[32:64] = bytes(owner)
    struct.pack_into("<Q", data, 64, amount)
    data[108] = 1
    return bytes(data) + bytes([2]) + struct.pack("<HH", 7, 0) + struct.pack("<HHQ", 2, 8, withheld)


def t22acct_imint(mint, owner, amount, withheld=0):
    data = bytearray(165)
    data[0:32] = bytes(mint)
    data[32:64] = bytes(owner)
    struct.pack_into("<Q", data, 64, amount)
    data[108] = 1
    return bytes(data) + bytes([2]) + struct.pack("<HH", 7, 0) + struct.pack("<HHQ", 2, 8, withheld)


def tf_mint_data(base82, bps, maxfee=2**64 - 1):
    d = bytearray(base82)
    d += bytes(83) + bytes([1])
    conf = bytes(72) + struct.pack('<QQH', 0, maxfee, bps) * 2
    d += struct.pack('<HH', 1, len(conf)) + conf
    return bytes(d)
S_ASIS = 4194352106721

MH_KEYS_BUY = [PAYER_KEY, userquote, userbase, CONFIG_KEY, feeconfig, volume, buyback,
               TOKEN, TOKEN22, Pubkey.default(), EVENT, PROGRAM, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]
MH_KEYS_SELL = [PAYER_KEY, userbase, userquote, CONFIG_KEY, feeconfig, volume, buyback,
                TOKEN, TOKEN22, Pubkey.default(), EVENT, PROGRAM, PUMP, PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]
MH_TAIL = [AccountMeta(base, False, False), AccountMeta(quote, False, False),
           AccountMeta(pool, False, True), AccountMeta(vaultbase, False, True),
           AccountMeta(vaultquote, False, True)]
DEP_KEYS = [pool, CONFIG_KEY, PAYER_KEY, base, quote, lp, userbase, userquote,
            userlp, vaultbase, vaultquote, TOKEN, TOKEN22, EVENT, PROGRAM]
DEP_DISC = "78f83d531f8e6b90"
WD_DISC = "1609851aa02c47c0"
MX = 2**64 - 1
# pool tag -> (pool, quote mint, quote vault, protocol ATA, creator ATA, dest)
POOLS = {
    "main": (pool, quote, vaultquote, PROTOCOL_ATA, CREATOR_ATA, DEST),
    "p2": (POOL2, base, VQ2, PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2),
    "p3": (P3, BASE2, VQ3, PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3),
    "p4": (P4, BASE3, VQ4, PROTOCOL_ATA_P4, CREATOR_ATA_P4, DEST4),
    "p5": (P5, BASE4, VQ5, PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5),
}
WATCH = [PAYER_KEY, OUTSIDER_KEY, pool, POOL2, P3, P4, P5, base, quote, BASE2, BASE3, BASE4, BASE5, lp, userbase,
         userquote, userlp, vaultbase, vaultquote, VB2, VQ2, VB3, VQ3, VB4, VQ4, VB5, VQ5, U3, U4, U5,
         buyback, volume, feeconfig, CONFIG_KEY,
         PROTOCOL_ATA, CREATOR_ATA, DEST,
         PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3,
         PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2,
         PROTOCOL_ATA_P4, CREATOR_ATA_P4, DEST4,
         PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5,
         PROTO22, CREAT22, DEST22, BB22, BOOST, BATA, BP3, BA3,
         GVOL, IMINT, GA_ATA, UA_ATA, uvata, WDEST, BASE22, PLAIN,
         NEWVAULT22, NEWDEST22, BCVAULT22, BCDEST22, SHVAULT22, SHDEST22,
         ZEROVAULT22, ZERODEST22, ORIGDEST22, META_PDA, BC_PDA, SHARING_PDA,
         NEWVAULT, BCVAULT, SHVAULT, ZEROVAULT, POOLV2]
ROLE_KEY = {"userbase": userbase, "userquote": userquote, "userlp": userlp,
            "vaultbase": vaultbase, "vaultquote": vaultquote, "buyback": buyback,
            "vb1": vaultbase, "vq1": vaultquote, "vb2": VB2, "vq2": VQ2,
            "vb3": VB3, "vq3": VQ3, "vb4": VB4, "vq4": VQ4,
            "vb5": VB5, "vq5": VQ5, "u3": U3, "u4": U4, "u5": U5,
            "protoata": PROTOCOL_ATA, "creatorata": CREATOR_ATA, "dest": DEST,
            "protoata3": PROTOCOL_ATA_P3, "creatorata3": CREATOR_ATA_P3, "dest3": DEST3,
            "protoata4": PROTOCOL_ATA_P4, "creatorata4": CREATOR_ATA_P4, "dest4": DEST4,
            "protoata5": PROTOCOL_ATA_P5, "creatorata5": CREATOR_ATA_P5, "dest5": DEST5,
            "protoata2": PROTOCOL_ATA_P2, "creatorata2": CREATOR_ATA_P2, "dest2": DEST2,
            "bb22": BB22, "proto22": PROTO22, "creat22": CREAT22, "dest22": DEST22,
            "wdest": WDEST, "base22": BASE22, "plain": PLAIN,
            "boostata": BATA, "boostata3": BA3,
            "gata": GA_ATA, "uata": UA_ATA, "uvata": uvata,
            "newvault": NEWVAULT22, "newdest": NEWDEST22,
            "bcvault": BCVAULT22, "bcdest": BCDEST22,
            "shvault": SHVAULT22, "shdest": SHDEST22,
            "zerovault": ZEROVAULT22, "zerodest": ZERODEST22,
            "origdest": ORIGDEST22}
TOKEN_ROLES = ["userbase", "userquote", "userlp", "vb1", "vq1", "vb2", "vq2",
               "vb3", "vq3", "vb4", "vq4", "vb5", "vq5", "u3", "u4", "u5", "buyback",
               "protoata", "creatorata", "dest",
               "protoata3", "creatorata3", "dest3",
               "protoata4", "creatorata4", "dest4",
               "protoata5", "creatorata5", "dest5",
               "protoata2", "creatorata2", "dest2",
               "bb22", "proto22", "creat22", "dest22",
               "wdest", "base22", "plain",
               "boostata", "boostata3",
               "gata", "uata", "uvata",
               "newvault", "newdest", "bcvault", "bcdest",
               "shvault", "shdest", "zerovault", "zerodest", "origdest"]
SWP_DISC = "82a42461e48287a5"
COL_DISC = "e8f5c2eeeada3a59"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def setup_vm(binary, case):
    bps = case.get("bps", 0)
    h = Harness(binary)
    vm = h.vm
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    for pid, p in [(TOKEN, "evidence/dependencies/spl_token/deployed.so"),
                   (TOKEN22, "evidence/dependencies/spl_token_2022/deployed.so"),
                   (FEES, "evidence/original/pump_fees/deployed.so"),
                   (ATA_PROG, "evidence/dependencies/associated_token/deployed.so"),
                   (PUMP, "evidence/original/pump/deployed.so")]:
        vm.add_program_from_file(pid, ROOT / p)
    glob = bytearray(RAW)
    glob[56] = 0
    # boost authority = payer, boost enabled (else 6005 InvalidAdmin).
    glob[907:939] = bytes(PAYER_KEY)
    glob[939] = 1
    vm.set_account(CONFIG_KEY, Account(CONFIG["lamports"], bytes(glob), PROGRAM))
    for n, row in f["accounts"].items():
        vm.set_account(Pubkey.from_string(row["address"]),
                       Account(row["lamports"], base64.b64decode(row["data_base64"]),
                               Pubkey.from_string(row["owner"])))
    vm.set_account(pool, Account(f["accounts"]["pool"]["lamports"], bytes(poolraw), PROGRAM))
    mint = struct.pack("<I", 1) + bytes(pool) + struct.pack("<Q", supply) + bytes([9, 1]) + bytes(36)
    vm.set_account(lp, Account(10**9, mint, TOKEN22))
    vm.set_account(userbase, Account(10**9, token(base, PAYER_KEY, 10**15, False), TOKEN))
    vm.set_account(userquote, Account(10**15 + 2039280, token(quote, PAYER_KEY, 10**15, True), TOKEN))
    vm.set_account(userlp, Account(10**9, token(lp, PAYER_KEY, supply // 2, False), TOKEN22))
    if case.get("uva_seed") is not None:
        raw = UVA_DISC + bytes(PAYER_KEY) + struct.pack('<BQQQqBQQ', *case["uva_seed"])
        ulen = case.get("uva_len", 137)
        vm.set_account(volume, Account(case.get("uva_lamports", 10**9),
                                       raw.ljust(ulen, b'\0')[:ulen], PROGRAM))
    else:
        vm.set_account(volume, Account(0, b"", Pubkey.default()))
    if case.get("gva", True):
        g = GDISC + struct.pack('<qqq', 20, 49, 1) + bytes(IMINT) \
            + struct.pack('<30Q', *([1000] * 30)) + struct.pack('<30Q', *([100] * 30))
        vm.set_account(GVOL, Account(10**9, g.ljust(600, b'\0'), PROGRAM))
    else:
        vm.set_account(GVOL, Account(0, b'', Pubkey.default()))
    base82 = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**12) + bytes([6, 1]) + bytes(36)
    vm.set_account(IMINT, Account(10**9, tf_mint_data(base82, case.get("claim_bps", 0), 2**64 - 1), TOKEN22))
    vm.set_account(GA_ATA, Account(10**9, t22acct_imint(IMINT, GVOL, case.get("vault", 10**9)), TOKEN22))
    if case.get("uata", True):
        vm.set_account(UA_ATA, Account(10**9, t22acct_imint(IMINT, PAYER_KEY, case.get("uata_amt", 17), case.get("uata_wh", 0)), TOKEN22))
    else:
        vm.set_account(UA_ATA, Account(0, b'', Pubkey.default()))
    # quote is the native mint in this harness: a native token account's
    # lamports must equal rent + amount, or a transfer out fails the
    # runtime rent check (measured: seeded uvata with amount 5475 but
    # lamports 2039280 fails InsufficientFundsForRent on claim).
    vm.set_account(uvata, Account(2039280 + case.get("uvata_amt", 0),
                                  token(quote, volume, case.get("uvata_amt", 0), True), TOKEN))
    vm.set_account(OUTSIDER_KEY, Account(10**12, b"", Pubkey.default()))
    vm.set_account(DEST, Account(2039280, token(quote, CREATOR, 0, True), TOKEN))
    vm.set_account(CREATOR_ATA, Account(2039280, token(quote, CREATOR_VAULT, 0, True), TOKEN))
    vm.set_account(PROTOCOL_ATA, Account(2039280, token(quote, PROTOCOL, 0, True), TOKEN))
    # BASE2/base are SPL mints, NOT the native SOL mint: non-native layout.
    vm.set_account(DEST3, Account(2039280, token(BASE2, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P3, Account(2039280, token(BASE2, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P3, Account(2039280, token(BASE2, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST2, Account(2039280, token(base, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P2, Account(2039280, token(base, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P2, Account(2039280, token(base, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST4, Account(2039280, token(BASE3, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P4, Account(2039280, token(BASE3, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P4, Account(2039280, token(BASE3, PROTOCOL, 0, False), TOKEN))
    vm.set_account(DEST5, Account(2039280, token(BASE4, CREATOR, 0, False), TOKEN))
    vm.set_account(CREATOR_ATA_P5, Account(2039280, token(BASE4, CREATOR_VAULT, 0, False), TOKEN))
    vm.set_account(PROTOCOL_ATA_P5, Account(2039280, token(BASE4, PROTOCOL, 0, False), TOKEN))
    for k in [PUMP_GLOBAL, PUMP_FEES, PUMP_EVENT]:
        vm.set_account(k, Account(10**9, b"", Pubkey.default()))
    # 0-bps transfer-fee config on quote: the boost instruction requires
    # TOKEN22 quote accounts, and the split legs route the buyback
    # through BB22. Set the TOKEN22 ATAs before the override (as in #34).
    h.vm.set_account(BB22, Account(2157600, t22acct(_BB_OWNER, 0), TOKEN22))
    h.vm.set_account(PROTO22, Account(2157600, t22acct(PROTOCOL, 0), TOKEN22))
    h.vm.set_account(CREAT22, Account(2157600, t22acct(CREATOR_VAULT, 0), TOKEN22))
    h.vm.set_account(DEST22, Account(2157600, t22acct(CREATOR, 0), TOKEN22))
    if not case.get("plain"):
        transferfee(quote, bps, 2**64 - 1)(h, [])
    # Token-2022 withdraw-withheld authority on the quote mint (3rd #28
    # pattern: the transfer-fee override leaves the authority slot zero,
    # so patch it to the payer unless the case wants the zero form).
    if not case.get("no_ww"):
        m = h.vm.get_account(quote)
        d = bytearray(m.data)
        d[202:234] = bytes(PAYER_KEY) if case.get("ww_auth", True) else bytes(32)
        h.vm.set_account(quote, Account(m.lamports, bytes(d), TOKEN22))
    h.vm.set_account(WDEST, Account(2157600, t22acct(PAYER_KEY, 0), TOKEN22))
    h.vm.set_account(BASE22, Account(2157600, t22acct_mint(base, PAYER_KEY, 7000, 999), TOKEN22))
    h.vm.set_account(PLAIN, Account(2157600, token(quote, PAYER_KEY, 5000, False), TOKEN22))
    # Coin-creator accounts (mirror 3rd #33).
    vm.set_account(META_PDA, Account(10**9, metadata(case.get("meta", [CREATOR0])), META_PROG))
    vm.set_account(BC_PDA, Account(10**9, bonding_curve(), PUMP))
    if case.get("sharing") is not None:
        vm.set_account(SHARING_PDA, Account(10**9, sharing(case["sharing"], bytes(base)), FEES_PROG))
    else:
        vm.set_account(SHARING_PDA, Account(0, b'', Pubkey.default()))
    for v in (NEWVAULT, BCVAULT, SHVAULT, ZEROVAULT):
        vm.set_account(v, Account(10**9, b'', Pubkey.default()))
    vm.set_account(POOLV2, Account(10**9, b'', Pubkey.default()))
    for cr in (CREATOR, CREATOR0, BC_CREATOR, SHARING_PDA, ZERO_CREATOR):
        vm.set_account(ata22_of(vault_of(cr)), Account(2157600, t22acct(vault_of(cr), 0), TOKEN22))
        vm.set_account(ata22_of(cr), Account(2157600, t22acct(cr, 0), TOKEN22))
    # Main-pool boost accounts (mirror #34).
    h.vm.set_account(BOOST, Account(10**9, b"", Pubkey.default()))
    ex = h.vm.get_account(BATA)
    if ex is None:
        raw = token(quote, BOOST, 10**12, True)
        d = bytes(raw[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    else:
        d = bytes(ex.data[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BATA, Account(10**12 + 10**9, d, TOKEN22))
    # Tail-pool boost accounts (P3 boost is only ever attempted, never
    # expected to succeed: its window sum is 0 on every fixture here).
    h.vm.set_account(BP3, Account(10**9, b"", Pubkey.default()))
    raw3 = token(BASE2, BP3, 10**12, False)
    d3 = bytes(raw3[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    h.vm.set_account(BA3, Account(10**12 + 10**9, d3, TOKEN22))
    return h


def build_route(h, sell, plain=False):
    keys = MH_KEYS_SELL if sell else MH_KEYS_BUY
    ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
    metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
             for k, a in zip(keys, ix["accounts"])] + list(MH_TAIL)
    three_amm(sell)(SimpleNamespace(vm=h.vm), metas)
    h.vm.set_account(BASE4, h.vm.get_account(base))
    d = bytearray(poolraw)
    d[8] = B4
    d[9:11] = bytes(2)
    d[11:43] = bytes(C4)
    d[43:75] = bytes(BASE4)
    d[75:107] = bytes(BASE3)
    d[139:171] = bytes(VB4)
    d[171:203] = bytes(VQ4)
    h.vm.set_account(P4, Account(10**9, bytes(d), PROGRAM))
    for k, mi, ow in [(VB4, BASE4, P4), (VQ4, BASE3, P4), (U4, BASE4, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    # P4/P5 stay fixture-only (outside the route) but must exist for snapshots.
    # NOTE: no g4/g5 hop group is appended here: this is the TRUE 3-hop
    # route (three_amm only), final output U3. #61 appended g4 and was
    # actually 4 hops; do NOT re-add it.
    h.vm.set_account(BASE5, h.vm.get_account(base))
    h.vm.set_account(P5, Account(10**9, bytes(poolraw), PROGRAM))
    for k, mi, ow in [(VB5, BASE5, P5), (VQ5, BASE4, P5), (U5, BASE5, PAYER_KEY)]:
        h.vm.set_account(k, Account(10**9, token(mi, ow, 10**15), TOKEN))
    # three_amm already set the tail output to U3 (metas[1] for sells,
    # metas[2] for buys); nothing further is appended.
    # With a transfer-fee-configured quote mint the program requires
    # the TOKEN22 buyback; in plain mode the SPL buyback stays.
    if not plain:
        m6 = metas[6]
        metas[6] = AccountMeta(BB22, m6.is_signer, m6.is_writable)
    return metas


def flag_pool(h, poolkey, mode):
    a = h.vm.get_account(poolkey)
    d = bytearray(a.data)
    if mode in ("cb", "both"):
        d[244] = 1
    if mode in ("mayhem", "both"):
        d[243] = 1
    h.vm.set_account(poolkey, Account(a.lamports, bytes(d), a.owner))


def apply_fee_patch(h, patch):
    if not patch:
        return
    a = h.vm.get_account(feeconfig)
    raw = bytearray(a.data)
    if "tiers_inplace" in patch:
        for i, (t, fs) in enumerate(patch["tiers_inplace"]):
            off = 69 + i * 40
            raw[off:off + 16] = t.to_bytes(16, "little")
            struct.pack_into("<QQQ", raw, off + 16, *fs)
    if "tiers_rebuild" in patch:
        tiers = patch["tiers_rebuild"]
        new = bytes(raw[:41]) + struct.pack("<QQQ", 25, 5, 0) + struct.pack("<I", len(tiers))
        for t, fs in tiers:
            new += t.to_bytes(16, "little") + struct.pack("<QQQ", *fs)
        new += struct.pack("<I", 0) + bytes(24)
        raw = bytearray(new.ljust(4097, b"\0"))
    if "stable_inplace" in patch:
        for i, (t, fs) in enumerate(patch["stable_inplace"]):
            off = 1073 + i * 40
            raw[off:off + 16] = t.to_bytes(16, "little")
            struct.pack_into("<QQQ", raw, off + 16, *fs)
    if "stable_count" in patch:
        struct.pack_into("<I", raw, 1069, patch["stable_count"])
    if "exotic" in patch:
        struct.pack_into("<QQQ", raw, 2073, *patch["exotic"])
    h.vm.set_account(feeconfig, Account(a.lamports, bytes(raw), a.owner))


POOLKEYS = {"main": pool, "p2": POOL2, "p3": P3, "p4": P4, "p5": P5}


def build_route_1hop(h, sell):
    keys = MH_KEYS_SELL if sell else MH_KEYS_BUY
    ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
    metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
             for k, a in zip(keys, ix["accounts"])] + list(MH_TAIL)
    # Unused hop pools sit at the INIT state so snapshots stay complete.
    for pk in (POOL2, P3, P4, P5):
        h.vm.set_account(pk, Account(10**9, bytes(poolraw), PROGRAM))
    return metas


def snap(vm):
    out = {}
    for k in WATCH:
        a = vm.get_account(k)
        out[str(k)] = None if a is None else {
            "lamports": a.lamports, "owner": str(a.owner),
            "data_hex": bytes(a.data).hex()}
    return out


def tok_amount(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    return struct.unpack_from("<Q", raw, 64)[0] if len(raw) >= 72 else None


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
    d = bytes.fromhex(entry["data_hex"])
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


def ev_list(logs):
    out = []
    for l in logs:
        if l.startswith("Program data: "):
            raw = base64.b64decode(l.split("Program data: ", 1)[1].strip())
            out.append(raw)
    return out


def u64(raw, off):
    return struct.unpack_from("<Q", raw, off)[0]


def decode_event(kind, raw):
    if kind == "ww":
        return None
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind in ("swp", "swc"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "recipient": raw[112:144].hex(),
                "amount": u64(raw, 176), "bucket": raw[184]}
    if kind in ("dep", "wd"):
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 72), "quote": u64(raw, 80)}
    if kind == "col":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "timestamp": struct.unpack_from("<q", raw, 8)[0],
                "creator": raw[16:48].hex(), "fee": u64(raw, 48),
                "vault_ata": raw[56:88].hex(), "dest": raw[88:120].hex()}
    if kind == "boost":
        if raw[:8].hex() != BST_DISC:
            return {"disc": raw[:8].hex(), "len": len(raw)}
        return {"disc": raw[:8].hex(), "len": len(raw),
                "requested": u64(raw, 144), "used": u64(raw, 152),
                "burned": u64(raw, 160),
                "vq": int.from_bytes(raw[168:184], "little", signed=True),
                "quote_after": u64(raw, 184), "base_after": u64(raw, 192),
                "remaining": u64(raw, 200)}
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


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def disc(name):
    return bytes(next(x for x in IDL["instructions"] if x["name"] == name)["discriminator"])


V2_KEYS = [pool, PAYER_KEY, CONFIG_KEY, base, quote, userbase, userquote,
           vaultbase, vaultquote, TOKEN, TOKEN, Pubkey.default(), volume, feeconfig,
           buyback, EVENT, PROGRAM]
LEG_REM = [AccountMeta(POOLV2, False, False), AccountMeta(_BB_OWNER, False, False),
           AccountMeta(BB22, False, True)]


def buy_keys(creator):
    v = vault_of(creator)
    return [pool, PAYER_KEY, CONFIG_KEY, base, quote, userbase, userquote, vaultbase, vaultquote,
            PROTOCOL, PROTO22, TOKEN, TOKEN22, Pubkey.default(), ATA_PROG, EVENT, PROGRAM,
            ata22_of(v), v, GVOL, volume, feeconfig, FEES]


def leg_keys(creator):
    v = vault_of(creator)
    return [pool, PAYER_KEY, CONFIG_KEY, base, quote, userbase, userquote, vaultbase, vaultquote,
            PROTOCOL, PROTO22, TOKEN, TOKEN22, Pubkey.default(), ATA_PROG, EVENT, PROGRAM,
            ata22_of(v), v, feeconfig, FEES]


def do_step(h, kind, args, routes):
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell3": "sell", "mhbuy3": "buy",
                        "mhsell5": "sell", "mhbuy5": "buy",
                        "mhsell4": "sell", "mhbuy4": "buy",
                        "mhsell1": "sell1", "mhbuy1": "buy1"}[kind]]
        data = bytes(ix["discriminator"]) + struct.pack("<QQ", args[0], args[1])
    elif kind in ("swp", "swc"):
        pool_k, mint_k, vq_k, proto_ata, creat_ata, _dest = POOLS[args]
        name = "sweep_protocol_fee" if kind == "swp" else "sweep_creator_fee"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [PAYER_KEY, CONFIG_KEY, pool_k, mint_k, TOKEN, vq_k,
                PROTOCOL if kind == "swp" else CREATOR_VAULT,
                proto_ata if kind == "swp" else creat_ata,
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name)
    elif kind in ("swp22", "swc22"):
        name = "sweep_protocol_fee" if kind == "swp22" else "sweep_creator_fee"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [PAYER_KEY, CONFIG_KEY, pool, quote, TOKEN22, vaultquote,
                PROTOCOL if kind == "swp22" else CREATOR_VAULT,
                PROTO22 if kind == "swp22" else CREAT22,
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name)
    elif kind == "col22":
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [quote, TOKEN22, CREATOR, CREATOR_VAULT, CREAT22, DEST22, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
    elif kind == "col":
        _pool_k, mint_k, _vq_k, _proto_ata, creat_ata, dest = POOLS[args]
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [mint_k, TOKEN, CREATOR, CREATOR_VAULT, creat_ata, dest, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
    elif kind in ("dep", "wd"):
        name = "deposit" if kind == "dep" else "withdraw"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(DEP_KEYS, ix["accounts"])]
        data = bytes(ix["discriminator"]) + struct.pack("<QQQ", *args)
    elif kind in ("boost", "boost3"):
        if kind == "boost":
            keys = [pool, PAYER_KEY, CONFIG_KEY, base, quote, vaultbase, vaultquote,
                    BOOST, BATA, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BATA
        else:
            keys = [P3, PAYER_KEY, CONFIG_KEY, BASE3, BASE2, VB3, VQ3,
                    BP3, BA3, TOKEN, TOKEN, EVENT, PROGRAM]
            bata = BA3
        ix = next(x for x in IDL["instructions"] if x["name"] == "boost_buy_and_burn")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        metas[8] = AccountMeta(bata, False, True)
        metas[10] = AccountMeta(TOKEN22, False, False)
        data = disc("boost_buy_and_burn") + struct.pack("<QQ", *args)
    elif kind == "tclaim":
        ix = next(x for x in IDL["instructions"] if x["name"] == "claim_token_incentives")
        metas = [AccountMeta(k, bool(at.get("signer")), bool(at.get("writable")))
                 for k, at in zip(TCLAIM_KEYS, ix["accounts"])]
        data = disc("claim_token_incentives")
    elif kind == "cclaim":
        ix = next(x for x in IDL["instructions"] if x["name"] == "claim_cashback")
        metas = [AccountMeta(k, bool(at.get("signer")), bool(at.get("writable")))
                 for k, at in zip(CLAIM_KEYS, ix["accounts"])]
        data = disc("claim_cashback")
    elif kind in ("close", "close_other", "close_unsigned"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "close_user_volume_accumulator")
        user_key = OUTSIDER_KEY if kind == "close_other" else PAYER_KEY
        fee_key = OUTSIDER if kind in ("close_other", "close_unsigned") else PAYER
        keys = [user_key, volume, EVENT, PROGRAM]
        metas = []
        for k, at in zip(keys, ix["accounts"]):
            signer = bool(at.get("signer"))
            if kind == "close_unsigned" and k == PAYER_KEY:
                signer = False
            metas.append(AccountMeta(k, signer, bool(at.get("writable"))))
        data = disc("close_user_volume_accumulator")
        h.vm.set_clock(Clock(100, 0, 0, 0, 10))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], fee_key.pubkey(), [fee_key], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind == "init":
        ix = next(x for x in IDL["instructions"] if x["name"] == "init_user_volume_accumulator")
        keys = [PAYER_KEY, PAYER_KEY, volume, Pubkey.default(), EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(at.get("signer")), bool(at.get("writable")))
                 for k, at in zip(keys, ix["accounts"])]
        data = disc("init_user_volume_accumulator")
        h.vm.set_clock(Clock(100, 0, 0, 0, 10))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], PAYER_KEY, [PAYER], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind == "sync":
        ix = next(x for x in IDL["instructions"] if x["name"] == "sync_user_volume_accumulator")
        keys = [PAYER_KEY, GVOL, volume, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(at.get("signer")), bool(at.get("writable")))
                 for k, at in zip(keys, ix["accounts"])]
        data = disc("sync_user_volume_accumulator")
        h.vm.set_clock(Clock(100, 0, 0, 0, 10))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], PAYER_KEY, [PAYER], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind in ("extend", "extend_unsigned", "extend_readonly"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "extend_account")
        metas = [AccountMeta(volume, False, kind != "extend_readonly"),
                 AccountMeta(PAYER_KEY, kind != "extend_unsigned", True),
                 AccountMeta(Pubkey.default(), False, False),
                 AccountMeta(EVENT, False, False),
                 AccountMeta(PROGRAM, False, False)]
        data = disc("extend_account")
        h.vm.set_clock(Clock(100, 0, 0, 0, 10))
        fee_key = OUTSIDER if kind == "extend_unsigned" else PAYER
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], fee_key.pubkey(), [fee_key], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind in ("ww", "harvest", "wfm"):
        if kind == "ww":
            dest_role, signer_mode, source_roles = args
            dest = ROLE_KEY[dest_role]
            if signer_mode == "payer":
                fee_key, auth_meta = PAYER, AccountMeta(PAYER_KEY, True, False)
            elif signer_mode == "outsider":
                fee_key, auth_meta = OUTSIDER, AccountMeta(OUTSIDER_KEY, True, False)
            elif signer_mode == "payer_unsigned":
                fee_key, auth_meta = OUTSIDER, AccountMeta(PAYER_KEY, False, False)
            else:
                raise ValueError(signer_mode)
            metas = ([AccountMeta(quote, False, False), AccountMeta(dest, False, True), auth_meta] +
                     [AccountMeta(ROLE_KEY[r], False, True) for r in source_roles])
            data = bytes([26, 3, len(source_roles)])
        elif kind == "harvest":
            source_roles = args[0]
            fee_key = PAYER
            metas = ([AccountMeta(quote, False, True)] +
                     [AccountMeta(ROLE_KEY[r], False, True) for r in source_roles])
            data = bytes([26, 4])
        else:  # wfm
            dest = ROLE_KEY[args[0]]
            fee_key = PAYER
            metas = [AccountMeta(quote, False, True), AccountMeta(dest, False, True),
                     AccountMeta(PAYER_KEY, True, False)]
            data = bytes([26, 2])
        h.vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
        tx = Transaction.new_signed_with_payer(
            [Instruction(TOKEN22, data, metas)], fee_key.pubkey(), [fee_key], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind in ("bbcfg", "ufc", "tog", "dis"):
        mode = args[-1]
        if mode == "payer":
            signer_key, signer_flag, fee_key = PAYER_KEY, True, PAYER
        elif mode == "outsider":
            signer_key, signer_flag, fee_key = OUTSIDER_KEY, True, OUTSIDER
        elif mode == "unsigned":
            signer_key, signer_flag, fee_key = PAYER_KEY, False, OUTSIDER
        else:
            raise ValueError(mode)
        if kind == "bbcfg":
            bps_opt, recips = args[0], args[1]
            payload = b"\x00" if bps_opt is None else b"\x01" + struct.pack("<Q", bps_opt)
            metas = [AccountMeta(signer_key, signer_flag, False),
                     AccountMeta(CONFIG_KEY, False, True),
                     AccountMeta(EVENT, False, False),
                     AccountMeta(PROGRAM, False, False)]
            for k in (recips or []):
                metas.append(AccountMeta(k, False, False))
            data = BB_DISC + payload
        elif kind == "ufc":
            lp_v, proto_v, recips, creator_v, auth = args[0], args[1], args[2], args[3], args[4]
            payload = struct.pack("<QQ", lp_v, proto_v) + b"".join(bytes(r) for r in recips) + struct.pack("<Q", creator_v) + bytes(auth)
            metas = [AccountMeta(signer_key, signer_flag, False),
                     AccountMeta(CONFIG_KEY, False, True),
                     AccountMeta(EVENT, False, False),
                     AccountMeta(PROGRAM, False, False)]
            data = UFC_DISC + payload
        elif kind == "tog":
            name, enabled = args[0], args[1]
            ix = next(x for x in IDL["instructions"] if x["name"] == name)
            keys = [signer_key, CONFIG_KEY] + ([EVENT, PROGRAM] if name != "toggle_boost" else [])
            metas = [AccountMeta(k, bool(a.get("signer")) if k != signer_key else signer_flag, bool(a.get("writable")))
                     for k, a in zip(keys, ix["accounts"])]
            data = bytes(ix["discriminator"]) + bytes([1 if enabled else 0])
        else:  # dis
            bools = args[0]
            metas = [AccountMeta(signer_key, signer_flag, False),
                     AccountMeta(CONFIG_KEY, False, True),
                     AccountMeta(EVENT, False, False),
                     AccountMeta(PROGRAM, False, False)]
            data = DISABLE_DISC + bytes(bools)
        h.vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], fee_key.pubkey(), [fee_key], h.vm.latest_blockhash())
        assert tx.verify_with_results() and all(tx.verify_with_results())
        before = snap(h.vm)
        r = h.vm.send_transaction(tx)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
                "error": str(r.err()) if failed else None, "logs": logs,
                "events": [l for l in logs if l.startswith("Program data: ")],
                "before": before, "after": snap(h.vm),
                "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}
    elif kind == "set":
        ix = next(x for x in IDL["instructions"] if x["name"] == "set_coin_creator")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(SET_KEYS, ix["accounts"])]
        data = disc("set_coin_creator")
    elif kind == "mig":
        ix = next(x for x in IDL["instructions"] if x["name"] == "migrate_pool_coin_creator")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(MIG_KEYS, ix["accounts"])]
        data = disc("migrate_pool_coin_creator")
    elif kind == "swc22c":
        creator = args
        v = vault_of(creator)
        ix = next(x for x in IDL["instructions"] if x["name"] == "sweep_creator_fee")
        keys = [PAYER_KEY, CONFIG_KEY, pool, quote, TOKEN22, vaultquote, v, ata22_of(v),
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("sweep_creator_fee")
    elif kind == "col22c":
        creator = args
        v = vault_of(creator)
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [quote, TOKEN22, creator, v, ata22_of(v), ata22_of(creator), EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
    elif kind == "buy2":
        ix = next(x for x in IDL["instructions"] if x["name"] == "buy_v2")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(V2_KEYS, ix["accounts"])]
        metas[10] = AccountMeta(TOKEN22, False, False)
        metas[14] = AccountMeta(BB22, False, True)
        data = disc("buy_v2") + struct.pack("<QQ", args[0], MX)
    elif kind == "sell2":
        ix = next(x for x in IDL["instructions"] if x["name"] == "sell_v2")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(V2_KEYS, ix["accounts"])]
        metas[10] = AccountMeta(TOKEN22, False, False)
        metas[14] = AccountMeta(BB22, False, True)
        data = disc("sell_v2") + struct.pack("<QQ", args[0], 0)
    elif kind == "legbuy":
        ix = next(x for x in IDL["instructions"] if x["name"] == "buy")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(buy_keys(args[2]), ix["accounts"])] + list(LEG_REM)
        data = disc("buy") + struct.pack("<QQ", args[0], args[1]) + b"\0"
    elif kind == "legsell":
        ix = next(x for x in IDL["instructions"] if x["name"] == "sell")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(leg_keys(args[2]), ix["accounts"])] + list(LEG_REM)
        data = disc("sell") + struct.pack("<QQ", args[0], args[1])
    else:
        raise ValueError(kind)
    if kind == "tclaim":
        h.vm.set_clock(Clock(100, 0, 0, 0, 21))
    else:
        h.vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    tx = Transaction.new_signed_with_payer(
        [Instruction(PROGRAM, data, metas)], PAYER_KEY, [PAYER], h.vm.latest_blockhash())
    assert tx.verify_with_results() and all(tx.verify_with_results())
    before = snap(h.vm)
    r = h.vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    logs = meta.logs()
    return {"transaction_base64": base64.b64encode(bytes(tx)).decode(),
            "error": str(r.err()) if failed else None, "logs": logs,
            "events": [l for l in logs if l.startswith("Program data: ")],
            "before": before, "after": snap(h.vm),
            "site": next((l for l in logs if "thrown in" in l or "caused by account" in l), None)}


BST_DISC = "3f451c16305cc2b9"
MHBUY_DISC = "67f4521f2cf57777"


def E(dPAYER, deltas, pools, volume, event=None, events=1, error=None,
      rollback=False, withheld=None, boost_event=None, **extra):
    d = {"dPAYER": dPAYER, "deltas": deltas, "pools": pools,
         "volume": volume, "event": event, "events": events, "error": error,
         "rollback": rollback, "withheld": withheld or {},
         "boost_event": boost_event}
    d.update(extra)
    return d


TCLAIM_DISC = hashlib.sha256(b"event:ClaimTokenIncentivesEvent").digest()[:8].hex()
CLAIM_DISC = hashlib.sha256(b"event:ClaimCashbackEvent").digest()[:8].hex()


def BST_EV(used, burned, vq, quote_after, base_after, remaining, requested=None):
    return {"disc": BST_DISC, "len": 208,
            "requested": used if requested is None else requested, "used": used,
            "burned": burned, "vq": vq, "quote_after": quote_after,
            "base_after": base_after, "remaining": remaining}


def P(vq, pf, cf, sup=S_ASIS):
    return [vq, pf, cf, sup]


INIT = P(-125882, 2488, 123394)
ZERO = P(0, 0, 0)
VOL = {"lamports": 1844400, "len": 137, "user": PAYER_HEX}


def SWP_EV(amount, bucket, recipient):
    return {"disc": SWP_DISC, "len": 185, "timestamp": 1234567890,
            "recipient": bytes(recipient).hex(), "amount": amount, "bucket": bucket}


def COL_EV(amount, vault_ata, dest):
    return {"disc": COL_DISC, "len": 120, "timestamp": 1234567890,
            "creator": bytes(CREATOR).hex(), "fee": amount,
            "vault_ata": bytes(vault_ata).hex(), "dest": bytes(dest).hex()}


MHBUY_EV = {"disc": "67f4521f2cf57777", "len": 508}
MHSELL_EV = {"disc": "3e2f370aa503dc2a", "len": 449}

D_BUY3_1E9 = {"userquote": -10**9, "vb1": -5385694844757, "vq1": 995392847,
              "vb2": -5356844515538, "vq2": 5385694844757,
              "vb3": -5315084721958, "vq3": 5356844515538,
              "u3": 5315084721958, "buyback": 4607153}
D_SELL3_1E9 = {"userquote": 180345, "vb1": 997498005, "vq1": -181191,
               "vb2": 997499001, "vq2": -997498005,
               "vb3": 10**9, "vq3": -997499001, "u3": -10**9, "buyback": 846}
D_BUY3_1E6 = {"userquote": -10**6, "vb1": -5429043355, "vq1": 995393,
              "vb2": -5429013880, "vq2": 5429043355,
              "vb3": -5415445863, "vq3": 5429013880,
              "u3": 5415445863, "buyback": 4607}
D_SELL3_1E6 = {"userquote": 180, "vb1": 997498, "vq1": -181,
               "vb2": 997499, "vq2": -997498,
               "vb3": 10**6, "vq3": -997499, "u3": -10**6, "buyback": 1}
D_BUY3_2ND = {"userquote": -10**9, "vb1": -5300268622007, "vq1": 995392847,
              "vb2": -5216136464071, "vq2": 5300268622007,
              "vb3": -5121405353567, "vq3": 5216136464071,
              "u3": 5121405353567, "buyback": 4607153}
D_SELL3_2ND = {"userquote": 180344, "vb1": 997494021, "vq1": -181190,
               "vb2": 997497007, "vq2": -997494021,
               "vb3": 10**9, "vq3": -997497007, "u3": -10**9, "buyback": 846}
D_CROSS_SELL = {"userquote": 187229, "vb1": 1019086346, "vq1": -188108,
                "vb2": 1008198438, "vq2": -1019086346,
                "vb3": 10**9, "vq3": -1008198438, "u3": -10**9, "buyback": 879}


def POOLS3(main, pool2, p3):
    return {"main": main, "pool2": pool2, "p3": p3}


def MH(dPAYER, deltas, pools, event, withheld=None):
    return E(dPAYER, deltas, pools, VOL, event=event, events=4, withheld=withheld)


def SWC(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "creatorata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 1, CREATOR_VAULT), withheld=withheld)


def SWP(pool_tag, amount, pools, volume=VOL, withheld=None):
    return E(-5000, {"vq" + {"main": "1", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: -amount,
                     "protoata" + {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]: amount},
             pools, volume, event=SWP_EV(amount, 0, PROTOCOL), withheld=withheld)


def COL(pool_tag, amount, pools, volume=VOL, withheld=None):
    suffix = {"main": "", "p2": "2", "p3": "3", "p4": "4", "p5": "5"}[pool_tag]
    vault_ata = {"main": CREATOR_ATA, "p2": CREATOR_ATA_P2, "p3": CREATOR_ATA_P3, "p4": CREATOR_ATA_P4, "p5": CREATOR_ATA_P5}[pool_tag]
    dest = {"main": DEST, "p2": DEST2, "p3": DEST3, "p4": DEST4, "p5": DEST5}[pool_tag]
    return E(-5000, {"creatorata" + suffix: -amount, "dest" + suffix: amount},
             pools, volume, event=COL_EV(amount, vault_ata, dest), withheld=withheld)


def NOOP(pools, volume=VOL):
    return E(-5000, {}, pools, volume, events=0)


def FAIL(code, events, pools, event, volume=None):
    return E(-5000, {}, pools, volume, event=event, events=events,
             error=code, rollback=True)


def MH1(dPAYER, deltas, pools, event):
    return E(dPAYER, deltas, pools, VOL, event=event, events=1)


# --- case expectations: claim composition on the TRUE 3-hop split route ---
SEED = (1, 111, 222, 333444, 20, 1, 555, 666)
SMALL = (1, 111, 222, 0, 20, 1, 0, 0)
FSEED = (1, 111, 222, 333444, 20, 1, 5475, 0)
UVA_ZERO = {"needs": 0, "unclaimed": 0, "claimed": 0, "volume": 0, "last": 0, "has": 0, "earned": 0, "cb_claimed": 0}
UVA_ZERO_CLAIMED = dict(UVA_ZERO, last=21)
UVA_SEED = {"needs": 1, "unclaimed": 111, "claimed": 222, "volume": 333444, "last": 20, "has": 1, "earned": 555, "cb_claimed": 666}
UVA_SEED_CLAIMED = {"needs": 0, "unclaimed": 0, "claimed": 3334773, "volume": 0, "last": 21, "has": 1, "earned": 555, "cb_claimed": 666}
UVA_SMALL = {"needs": 1, "unclaimed": 111, "claimed": 222, "volume": 0, "last": 20, "has": 1, "earned": 0, "cb_claimed": 0}
UVA_SMALL_CLAIMED = {"needs": 0, "unclaimed": 0, "claimed": 333, "volume": 0, "last": 21, "has": 1, "earned": 0, "cb_claimed": 0}
UVA_F = {"needs": 1, "unclaimed": 111, "claimed": 222, "volume": 333444, "last": 20, "has": 1, "earned": 5475, "cb_claimed": 0}
UVA_F_CB = dict(UVA_F, cb_claimed=5475)
UVA_F_TC = {"needs": 0, "unclaimed": 0, "claimed": 3334773, "volume": 0, "last": 21, "has": 1, "earned": 5475, "cb_claimed": 0}
UVA_F_CB_TC = {"needs": 0, "unclaimed": 0, "claimed": 3334773, "volume": 0, "last": 21, "has": 1, "earned": 5475, "cb_claimed": 5475}
VOL_SEED = {"lamports": 10**9, "len": 137, "user": PAYER_HEX}
A_TIER = (10, 111, 333)
B_TIER = (20, 222, 444)


def C(label, steps, **kw):
    d = {"label": label, "steps": steps, "expect": [{} for _ in steps]}
    d.update(kw)
    return d


FIXTURE_RECIPS = [Pubkey.from_bytes(bytes.fromhex(h)) for h in [
    '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6',
    '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535',
    '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110',
    '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb',
    '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb',
    'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161',
    'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846',
    'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9']]
FIXTURE_AUTH = bytes.fromhex('07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532')
UFC = (30, 40, NEW_SORTED, 100, AUTH_NEW, "payer")
UFC_SAME = (20, 5, FIXTURE_RECIPS, 5, FIXTURE_AUTH, "payer")
DUP_RECIPS = [NEW_SORTED[0], NEW_SORTED[0]] + NEW_SORTED[1:7]
ZERO_RECIPS = [Pubkey.default()] + NEW_SORTED[:7]
TIER0 = {"tiers_inplace": [(0, (50, 50, 50))]}
EXO = {"exotic": (50, 10, 777)}
FSEED = (1, 111, 222, 333444, 20, 1, 5475, 0)

CASES = [
    # Family A: anchors (tf100).
    {"label": "a-buy3", "bps": 100,
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "a-sell3", "bps": 100,
     "steps": [("mhsell3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': 178541, 'vb1': 997498005, 'vq1': -181191, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 837}, 'pools': {'main': [-126729, 3335, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'userquote': 1804, 'bb22': 9}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 180345, 'vq1': -181191, 'bb22': 846}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}]},
    {"label": "a-buy2", "bps": 100,
     "steps": [("buy2", (10**10,))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userbase': 10000000000, 'userquote': -1866375, 'vb1': -10000000000, 'vq1': 1839310, 'bb22': 8401}, 'pools': {'main': [-139844, 10975, 128869, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'vq1': 18579, 'bb22': 85}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1866375, 'vq1': 1857889, 'bb22': 8486}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 500, 'curve': 1824983, 'lp_bps': 2, 'lp_fee': 365, 'proto_bps': 93, 'proto_fee': 16973, 'qwlp': 1825348, 'uin': 1847796}}]},
    {"label": "a-sell2", "bps": 100,
     "steps": [("sell2", (10**10,))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userbase': -10000000000, 'userquote': 1784093, 'vb1': 10000000000, 'vq1': -1810601, 'bb22': 8401}, 'pools': {'main': [-139843, 10974, 128869, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'userquote': 18022, 'bb22': 85}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 1802115, 'vq1': -1810601, 'bb22': 8486}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449, 'curve': 1824927, 'lp_bps': 2, 'lp_fee': 365, 'proto_bps': 93, 'proto_fee': 16972, 'quote': 1824562, 'uout': 1802115}}]},
    # Family T: tier crossing on the split chain.
    {"label": "t-cross-up", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (182353153971, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5294316148526, 'vq1': 989752624, 'vb2': -5210861553130, 'vq2': 5294316148526, 'vb3': -5116788773158, 'vq3': 5210861553130, 'u3': 5116788773158, 'bb22': 244902}, 'pools': {'main': [-4934341, 4810947, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-5244436851, 2488, 5244434363, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "t-cross-exact", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (182350153971, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5378790190096, 'vq1': 989752624, 'vb2': -5350013590152, 'vq2': 5378790190096, 'vb3': -5308343025925, 'vq3': 5350013590152, 'u3': 5308343025925, 'bb22': 244902}, 'pools': {'main': [-373259, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "t-cross-down", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (184000000000, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("mhbuy3", (10**9, 1)),
               ("mhsell3", (10**13, 1)), ("mhsell3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5294316148526, 'vq1': 989752624, 'vb2': -5210861553130, 'vq2': 5294316148526, 'vb3': -5116788773158, 'vq3': 5210861553130, 'u3': 5116788773158, 'bb22': 244902}, 'pools': {'main': [-4934341, 4810947, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-5244436851, 2488, 5244434363, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': 1871757566, 'vb1': 10195212837458, 'vq1': -1891137112, 'vb2': 10083662007501, 'vq2': -10195212837458, 'vb3': 10000000000000, 'vq3': -10083662007501, 'u3': -10000000000000, 'bb22': 468173}, 'pools': {'main': [-5407244, 5283850, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-10298904023, 2488, 10298901535, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'userquote': 18906643, 'bb22': 4730}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 1890664209, 'vq1': -1891137112, 'bb22': 472903}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': 179068, 'vb1': 999158338, 'vq1': -181726, 'vb2': 998297884, 'vq2': -999158338, 'vb3': 1000000000, 'vq3': -998297884, 'u3': -1000000000, 'bb22': 840}, 'pools': {'main': [-5408093, 5284699, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-10299404423, 2488, 10299401935, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'userquote': 1809, 'bb22': 9}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 180877, 'vq1': -181726, 'bb22': 849}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}]},
    {"label": "t-tier1-all", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("mhsell3", (10**9, 1)),
               ("buy2", (10**10,)), ("sell2", (10**10,))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5378790190096, 'vq1': 989752624, 'vb2': -5350013590152, 'vq2': 5378790190096, 'vb3': -5308343025925, 'vq3': 5350013590152, 'u3': 5308343025925, 'bb22': 244902}, 'pools': {'main': [-373259, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': 186994, 'vb1': 1019058520, 'vq1': -188930, 'vb2': 1008184757, 'vq2': -1019058520, 'vb3': 1000000000, 'vq3': -1008184757, 'u3': -1000000000, 'bb22': 46}, 'pools': {'main': [-373307, 249913, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668967194, 2488, 2668964706, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'userquote': 1889, 'bb22': 1}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 188883, 'vq1': -188930, 'bb22': 47}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userbase': 10000000000, 'userquote': -1895679, 'vb1': -10000000000, 'vq1': 1876262, 'bb22': 459}, 'pools': {'main': [-391389, 250377, 141012, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668967194, 2488, 2668964706, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'vq1': 18953, 'bb22': 5}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1895679, 'vq1': 1895215, 'bb22': 464}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 500, 'curve': 1854471, 'lp_bps': 20, 'lp_fee': 3709, 'proto_bps': 5, 'proto_fee': 928, 'qwlp': 1858180, 'uin': 1876726}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userbase': -10000000000, 'userquote': 1813892, 'vb1': 10000000000, 'vq1': -1832679, 'bb22': 459}, 'pools': {'main': [-409471, 250841, 158630, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668967194, 2488, 2668964706, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'userquote': 18323, 'bb22': 5}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 1832215, 'vq1': -1832679, 'bb22': 464}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449, 'curve': 1854470, 'lp_bps': 20, 'lp_fee': 3709, 'proto_bps': 5, 'proto_fee': 928, 'quote': 1850761, 'uout': 1832215}}]},
    {"label": "t-shortcircuit", "bps": 100,
     "fee_patch": {"tiers_inplace": [(10**15, (2, 93, 30))]},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "t-unsorted", "bps": 100,
     "fee_patch": {"tiers_inplace": [(100, (10, 111, 333)), (50, (20, 222, 444))]},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5265497796824, 'vq1': 979249658, 'vb2': -5237917554141, 'vq2': 5265497796824, 'vb3': -5197698194693, 'vq3': 5237917554141, 'u3': 5197698194693, 'bb22': 10642838}, 'pools': {'main': [-10876225, 10752831, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2612553590, 2488, 2612551102, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 107504}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 989249658, 'bb22': 10750342}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    # Family X: exotic flat fees on the tail hop (tf100).
    {"label": "x-lp100", "bps": 100,
     "fee_patch": {"exotic": (100, 0, 0)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5224033425497, 'vq3': 5303981938022, 'u3': 5224033425497, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-creator100", "bps": 100,
     "fee_patch": {"exotic": (0, 0, 100)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5224033425497, 'vq3': 5303981938022, 'u3': 5224033425497, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-52514798536, 2488, 52514796048, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-proto20", "bps": 100,
     "fee_patch": {"exotic": (0, 20, 0)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'u3': 5275998139846, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-proto100", "bps": 100,
     "fee_patch": {"exotic": (0, 100, 0)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5275998139846, 'vq3': 5303981938022, 'u3': 5275998139846, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-zero", "bps": 100,
     "fee_patch": {"exotic": (0, 0, 0)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281903, 'vq3': 5303981938022, 'u3': 5262910281903, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-777", "bps": 100,
     "fee_patch": {"exotic": (50, 10, 777)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -4874965557788, 'vq3': 5303981938022, 'u3': 4874965557788, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-380640558675, 2488, 380640556187, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "x-sell777", "bps": 100,
     "fee_patch": {"exotic": (50, 10, 777)},
     "steps": [("mhsell3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': 164186, 'vb1': 917298239, 'vq1': -166623, 'vb2': 917299081, 'vq2': -917298239, 'vb3': 1000000000, 'vq3': -917299081, 'u3': -1000000000, 'bb22': 770}, 'pools': {'main': [-126661, 3267, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-77825805, 2488, 77823317, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'userquote': 1659, 'bb22': 8}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 165845, 'vq1': -166623, 'bb22': 778}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}]},
    # Family G: fee-table account validation.
    {"label": "g-count0-buy3", "bps": 100,
     "fee_patch": {"tiers_rebuild": []},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -5000, 'dOUT': 0, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'events': 0, 'withheld': {}, 'error': '6082', 'rollback': True, 'lam_deltas': {}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': None, 'event': None}]},
    {"label": "g-count0-buy2", "bps": 100,
     "fee_patch": {"tiers_rebuild": []},
     "steps": [("buy2", (10**10,))], "expect": [{'dPAYER': -5000, 'dOUT': 0, 'deltas': {}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'events': 0, 'withheld': {}, 'error': '6082', 'rollback': True, 'lam_deltas': {}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': None, 'event': None}]},
    {"label": "g-stable0-buy3", "bps": 100,
     "fee_patch": {"stable_count": 0},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5274948716226, 'vq3': 5303981938022, 'u3': 5274948716226, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-1060710153, 2488, 1060707665, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "g-count1-buy3", "bps": 100,
     "fee_patch": {"tiers_rebuild": [(0, (2, 93, 30))]},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281903, 'vq3': 5303981938022, 'u3': 5262910281903, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "g-zero-buy2", "bps": 100, "zero": True,
     "steps": [("buy2", (10**10,))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userbase': 10000000000, 'userquote': -1860845, 'vb1': -10000000000, 'vq1': 1833835, 'bb22': 8401}, 'pools': {'main': [-134369, 10975, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'vq1': 18524, 'bb22': 85}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1860845, 'vq1': 1852359, 'bb22': 8486}, 'mint_wh': 0, 'pool_creator': '0000000000000000000000000000000000000000000000000000000000000000', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 500, 'curve': 1824983, 'lp_bps': 2, 'lp_fee': 365, 'proto_bps': 93, 'proto_fee': 16973, 'qwlp': 1825348, 'uin': 1842321}}]},
    {"label": "g-zero-buy3", "bps": 100, "zero": True,
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5332264170203, 'vq1': 985438918, 'vb2': -5303981938022, 'vq2': 5332264170203, 'vb3': -5262910281902, 'vq3': 5303981938022, 'u3': 5262910281902, 'bb22': 4515471}, 'pools': {'main': [-4686964, 4563570, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2645503408, 2488, 2645500920, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 45611}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995438918, 'bb22': 4561082}, 'mint_wh': 0, 'pool_creator': '0000000000000000000000000000000000000000000000000000000000000000', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    # Family D: downstream legs under a tier-1 table (tf100).
    {"label": "d-tier1-swp22", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("swp22", None), ("swc22", None), ("col22", None)], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5378790190096, 'vq1': 989752624, 'vb2': -5350013590152, 'vq2': 5378790190096, 'vb3': -5308343025925, 'vq3': 5350013590152, 'u3': 5308343025925, 'bb22': 244902}, 'pools': {'main': [-373259, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'vq1': -249865, 'proto22': 247366}, 'pools': {'main': [-123394, 0, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'proto22': 2499}, 'error': None, 'rollback': False, 'lam_deltas': {'vq1': -249865, 'proto22': 249865}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', 'amount': 249865, 'bucket': 0}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'vq1': -123394, 'creat22': 122160}, 'pools': {'main': [0, 0, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'creat22': 1234}, 'error': None, 'rollback': False, 'lam_deltas': {'vq1': -123394, 'creat22': 123394}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '82a42461e48287a5', 'len': 185, 'timestamp': 1234567890, 'recipient': '318133f36894131b95112673435f729234e7b96e1b217e685594eb883dcf34dd', 'amount': 123394, 'bucket': 1}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'creat22': -122160, 'dest22': 120938}, 'pools': {'main': [0, 0, 0, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'dest22': 1222}, 'error': None, 'rollback': False, 'lam_deltas': {}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': 'e8f5c2eeeada3a59', 'len': 120, 'timestamp': 1234567890, 'creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'fee': 122160, 'vault_ata': 'f45038d386b6b4dfb1f3302293c6a3afff53e012aa95859d156a7701d0afdd4a', 'dest': '6262626262626262626262626262626262626262626262626262626262626262'}}]},
    {"label": "d-tier1-boost", "bps": 100, "vq_patch": 10**9,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("boost", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5335732473785, 'vq1': 989752624, 'vb2': -5307413535697, 'vq2': 5335732473785, 'vb3': -5266297374951, 'vq3': 5307413535697, 'u3': 5266297374951, 'bb22': 244902}, 'pools': {'main': [999752623, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2647214928, 2488, 2647212440, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'vb1': -5254483001415, 'vq1': 990000000, 'boostata': -1000000000}, 'pools': {'main': [999752623, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2647214928, 2488, 2647212440, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 2, 'withheld': {'vq1': 10000000}, 'error': None, 'rollback': False, 'lam_deltas': {'vq1': 1000000000, 'boostata': -1000000000}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'boost_event': {'disc': '3f451c16305cc2b9', 'len': 208, 'requested': 1000000000, 'used': 1000000000, 'burned': 5254483001415, 'vq': 999752623, 'quote_after': 124926443344, 'base_after': 663106180437545, 'remaining': 999000000000}, 'event': None}]},
    {"label": "d-tier1-tclaim", "bps": 100, "claim_bps": 100, "uva_seed": FSEED,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("tclaim", ())], "expect": [{'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5378790190096, 'vq1': 989752624, 'vb2': -5350013590152, 'vq2': 5378790190096, 'vb3': -5308343025925, 'vq3': 5350013590152, 'u3': 5308343025925, 'bb22': 244902}, 'pools': {'main': [-373259, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1000000000, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {'vq1': 10000000, 'bb22': 2474}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999752624, 'bb22': 247376}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 1, 'unclaimed': 111, 'claimed': 222, 'volume': 333444, 'last': 20, 'has': 1, 'earned': 5475, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'gata': -3334551, 'uata': 3301205}, 'pools': {'main': [-373259, 249865, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2668461838, 2488, 2668459350, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1000000000, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {'uata': 33346}, 'error': None, 'rollback': False, 'lam_deltas': {}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 3334773, 'volume': 0, 'last': 21, 'has': 1, 'earned': 5475, 'cb_claimed': 0}, 'event': {'disc': '4facf631cd5bcee8', 'len': 104, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'mint': 'e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2e2', 'amount': 3334551, 'ts': 21, 'total_claimed': 3334773, 'current_sol_volume': 0}}]},
    {"label": "d-tier1-cclaim", "bps": 100, "plain": True, "no_ww": True, "uva_seed": FSEED, "uvata_amt": 5475,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("cclaim", ())], "expect": [{'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': 5475, 'uvata': -5475}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1000000000, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 1, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 5475, 'uvata': -5475}, 'mint_wh': None, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 1, 'unclaimed': 111, 'claimed': 222, 'volume': 333444, 'last': 20, 'has': 1, 'earned': 5475, 'cb_claimed': 5475}, 'event': {'disc': 'e2d6f62107f293e5', 'len': 72, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'amount': 5475, 'ts': 1234567890, 'total_claimed': 5475, 'total_earned': 5475}}]},
    {"label": "d-tier1-depwd", "bps": 100,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("dep", (10**9, MX, MX)), ("wd", (10**9, 0, 0))], "expect": [{'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userbase': -160619895224, 'userquote': -29608495, 'userlp': 1000000000, 'vb1': 160619895224, 'vq1': 29312410}, 'pools': {'main': [-125882, 2488, 123394, 4195352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'events': 1, 'withheld': {'vq1': 296085}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -29608495, 'vq1': 29608495}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': None, 'event': {'disc': '78f83d531f8e6b90', 'len': 264, 'base': 160619895224, 'quote': 29312410}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userbase': 160619895223, 'userquote': 29019284, 'userlp': -1000000000, 'vb1': -160619895223, 'vq1': -29312409}, 'pools': {'main': [-125882, 2488, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-125882, 2488, 123394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': None, 'events': 1, 'withheld': {'userquote': 293125}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 29312409, 'vq1': -29312409}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': None, 'event': {'disc': '1609851aa02c47c0', 'len': 264, 'base': 160619895223, 'quote': 29312409}}]},
    # Family W: table change x transfer fee (tf0 baseline vs tf100).
    {"label": "w-tier1-tf0", "bps": 0,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5432683274973, 'vq1': 999750125, 'vb2': -5403328702182, 'vq2': 5432683274973, 'vb3': -5360959279511, 'vq3': 5403328702182, 'u3': 5360959279511, 'bb22': 249875}, 'pools': {'main': [-375758, 252364, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2695052916, 2488, 2695050428, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999750125, 'bb22': 249875}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "w-exo-tf0", "bps": 0,
     "fee_patch": {"exotic": (50, 10, 777)},
     "steps": [("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -4923313100054, 'vq3': 5356844515538, 'u3': 4923313100054, 'bb22': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-384434243235, 2488, 384434240747, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995392847, 'bb22': 4607153}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
    {"label": "w-tier1-sell-tf0", "bps": 0,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (0, (20, 5, 95))]},
     "steps": [("mhsell3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': 181946, 'vb1': 997498005, 'vq1': -181992, 'vb2': 997499001, 'vq2': -997498005, 'vb3': 1000000000, 'vq3': -997499001, 'u3': -1000000000, 'bb22': 46}, 'pools': {'main': [-125928, 2534, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-625882, 2488, 623394, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': 181946, 'vq1': -181992, 'bb22': 46}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '3e2f370aa503dc2a', 'len': 449}}]},
    {"label": "w-cross-tf0", "bps": 0,
     "fee_patch": {"tiers_inplace": [(0, (2, 93, 30)), (182353153971, (20, 5, 95))]},
     "steps": [("mhbuy3", (10**9, 1)), ("mhbuy3", (10**9, 1))], "expect": [{'dPAYER': -1849400, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5385694844757, 'vq1': 995392847, 'vb2': -5356844515538, 'vq2': 5385694844757, 'vb3': -5315084721958, 'vq3': 5356844515538, 'u3': 5315084721958, 'bb22': 4607153}, 'pools': {'main': [-4733036, 4609642, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-2671868783, 2488, 2671866295, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 995392847, 'bb22': 4607153}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}, {'dPAYER': -5000, 'dOUT': 0, 'deltas': {'userquote': -1000000000, 'vb1': -5346514717583, 'vq1': 999750125, 'vb2': -5261407739746, 'vq2': 5346514717583, 'vb3': -5165623615966, 'vq3': 5261407739746, 'u3': 5165623615966, 'bb22': 249875}, 'pools': {'main': [-4982912, 4859518, 123394, 4194352106721], 'pool2': [-125882, 2488, 123394, 4194352106721], 'p3': [-5296012295, 2488, 5296009807, 4194352106721], 'p4': [-125882, 2488, 123394, 4194352106721], 'p5': [-125882, 2488, 123394, 4194352106721]}, 'volume': {'lamports': 1844400, 'len': 137, 'user': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5'}, 'events': 3, 'withheld': {}, 'error': None, 'rollback': False, 'lam_deltas': {'userquote': -1000000000, 'vq1': 999750125, 'bb22': 249875}, 'mint_wh': 0, 'pool_creator': '4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae', 'cfg': {'disable': 0, 'lp': 20, 'proto': 5, 'recipients': ['4ac2f8d0dd5cbc97e3289c197cb5062a54f3d956b9ce6e5115f96567aa5cb3e6', '608ccc1dfce961b43b779c191505a6e2d3bf45d5a4db4618ad76c82d61754535', '638373000ea22cb264d34aff64a04b5efabfbb74ddcd048997b1981547d7d110', '838474292e675a94b436ecb0a9988942328a83ddc6233802961267c5cd6117cb', '8d181a0c849fa937a6f34aded3081ef95700aacb0c9bb3d909a4b9147527a4eb', 'd7aa8fb060d8291b4c4d475daff762c96bdc0daceb36c012ead12ed3a9484161', 'e004c87ceb98fa5ce47f803806fd2c7945d29524959aec00ded97814f38f7846', 'ff8383818ba8fa28c3cd3b6d5e93f9fab8f0979bc37215acc5b246877ba8c3c9'], 'creator_fee': 5, 'fee_auth': '07215d9940793694e116066ce459b818fdf9bba0c7b41b783fa3a120ca419532', 'bps': 5000, 'bb_recipients': ['439e6510c03d65fad931e89d04be0bb70d51971f51c415fb344c07db419f2122', '02235516a917134c67588c493820ae155ee96665577ac1b718da47ddcf2a050e', 'e6a7e22068bb88640aa57f909308c61fef711a0163f5a755c070bc860d1f6367', '207cecda5bcc6cb1eaf0f16d68404566b18d56d2481acb317032656e90551c78', '449641f84958dc73a76a85d8756f55c02cdaca89ba1932790c368ab157e92d73', 'c54b96b5c931941e46ea4be2e0e31127744fc6b74cfb455efeaf8bd571792ced', '44fc1f78f94a33d0909c5e6b5fb021570ad8dbad8de8fdb3d20ed1cd99eb8e4e', '8770157eebeb678a655db99b37f6b1326c7657db90cfb8a87abef8c7b6f2c869'], 'mayhem': 1, 'cashback': 1, 'boost_auth': 'ba3b611e2882c1b6aa4b2ae3ec78ea0736e3ad99238353450171507a4b9f15b5', 'boost_enabled': 1}, 'uva': {'needs': 0, 'unclaimed': 0, 'claimed': 0, 'volume': 0, 'last': 0, 'has': 0, 'earned': 0, 'cb_claimed': 0}, 'event': {'disc': '67f4521f2cf57777', 'len': 508}}]},
]

MEASURE = bool(os.environ.get("MEASURE"))

STEP_KIND = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "mhbuy5": "mhbuy5", "mhsell5": "mhsell5", "mhbuy4": "mhbuy4", "mhsell4": "mhsell4", "mhbuy1": "mhbuy1", "mhsell1": "mhsell1", "swp": "swp", "swc": "swc", "col": "col", "dep": "dep", "wd": "wd", "swp22": "swp", "swc22": "swc", "col22": "col", "boost": "boost", "boost3": "boost", "tclaim": "tclaim", "cclaim": "cclaim", "close": "close", "close_other": "close", "close_unsigned": "close", "init": "init", "sync": "sync", "extend": "extend", "extend_unsigned": "extend", "extend_readonly": "extend", "ww": "ww", "harvest": "ww", "wfm": "ww", "set": "set", "mig": "mig", "bbcfg": "bbcfg", "ufc": "ufc", "tog": "tog", "dis": "dis",
            "swc22c": "swc", "col22c": "col", "buy2": "buy2", "sell2": "sell2",
            "legbuy": "legbuy", "legsell": "legsell"}

def case_expect(case, image_name):
    exp = case["expect"]
    if isinstance(exp, dict):
        return exp["original" if image_name == "original" else "rebuilt"]
    return exp


def run_case(case, image_name, binary):
    h = setup_vm(binary, case)
    apply_fee_patch(h, case.get("fee_patch"))
    if case.get("vq_patch") is not None:
        a = h.vm.get_account(pool)
        d = bytearray(a.data)
        d[245:261] = case["vq_patch"].to_bytes(16, "little", signed=True)
        h.vm.set_account(pool, Account(a.lamports, bytes(d), a.owner))
    if case.get("onehop"):
        routes = {"buy1": build_route_1hop(h, False), "sell1": build_route_1hop(h, True)}
    else:
        routes = {"buy": build_route(h, False, case.get("plain", False)),
                  "sell": build_route(h, True, case.get("plain", False))}
    if case.get("zero"):
        a = h.vm.get_account(pool)
        d = bytearray(a.data)
        d[211:243] = bytes(32)
        h.vm.set_account(pool, Account(a.lamports, bytes(d), a.owner))
    for tag, mode in case.get("flags", {}).items():
        flag_pool(h, POOLKEYS[tag], mode)
    out = []
    exp_list = [None] * len(case["steps"]) if MEASURE else case_expect(case, image_name)
    for step, exp in zip(case["steps"], exp_list):
        kind = step[0]
        args = step[1] if len(step) > 1 else None
        rec = do_step(h, kind, args, routes)
        tag = f"{case['label']}/{image_name}/{kind}"
        if MEASURE:
            meas = {"label": case["label"], "image": image_name, "step": kind,
                    "dPAYER": lam_delta(rec, PAYER_KEY),
                    "deltas": {role: tok_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if tok_delta(rec, ROLE_KEY[role]) != 0},
                    "pools": {name: pool_state(rec["after"][str(key)]) for name, key in (("main", pool), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5))},
                    "volume": vol_state(rec["after"][str(volume)]),
                    "events": len(rec["events"]),
                    "decoded": [decode_event(STEP_KIND[kind], raw) for raw in ev_list(rec["logs"])],
                    "withheld": {role: wh_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if wh_delta(rec, ROLE_KEY[role]) != 0},
                    "error": rec["error"],
                    "uva": uva_fields(rec["after"][str(volume)]),
                    "logfrag": "No tokens to claim" in "\n".join(rec["logs"]),
                    "lam": {role: (rec["after"][str(ROLE_KEY[role])]["lamports"] if rec["after"][str(ROLE_KEY[role])] else None) for role in ("gata", "uata", "uvata")},
                    "lam_deltas": {role: lam_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if lam_delta(rec, ROLE_KEY[role]) != 0},
                    "wh_after": {role: wh_of(rec["after"][str(ROLE_KEY[role])]) for role in TOKEN_ROLES if wh_of(rec["after"][str(ROLE_KEY[role])]) is not None},
                    "mint_wh": mint_wh(rec["after"][str(quote)]),
                    "dOUT": lam_delta(rec, OUTSIDER_KEY),
                    "pool_creator": bytes(rec["after"][str(pool)]["data_hex"], "utf-8") if False else bytes.fromhex(rec["after"][str(pool)]["data_hex"])[211:243].hex() if rec["after"][str(pool)] else None,
                    "cfg": cfg_fields(rec["after"][str(CONFIG_KEY)]),
                    "site": rec["site"]}
            print("MEAS " + json.dumps(meas))
            rec["case"] = case["label"]
            rec["image"] = image_name
            rec["step"] = kind
            out.append(rec)
            continue
        if exp["error"] is None:
            check(rec["error"] is None, f"{tag}: unexpected error {rec['error']}")
        else:
            check(rec["error"] is not None and exp["error"] in rec["error"],
                  f"{tag}: expected error {exp['error']}, got {rec['error']}")
        check(len(rec["events"]) == exp["events"],
              f"{tag}: events {len(rec['events'])} != {exp['events']}")
        d_payer = lam_delta(rec, PAYER_KEY)
        check(d_payer == exp["dPAYER"], f"{tag}: dPAYER {d_payer} != {exp['dPAYER']}")
        d_out = lam_delta(rec, OUTSIDER_KEY)
        check(d_out == exp.get("dOUT", 0), f"{tag}: dOUT {d_out} != {exp.get('dOUT', 0)}")
        for role, want in exp.get("lam_deltas", {}).items():
            got_d = lam_delta(rec, ROLE_KEY[role])
            check(got_d == want, f"{tag}: lam_delta {role} {got_d} != {want}")
        for role in TOKEN_ROLES:
            if role in exp.get("lam_deltas", {}):
                continue
            got_d = lam_delta(rec, ROLE_KEY[role])
            check(got_d == 0, f"{tag}: unexpected lam_delta {role} {got_d}")
        if "mint_wh" in exp:
            got_mw = mint_wh(rec["after"][str(quote)])
            check(got_mw == exp["mint_wh"], f"{tag}: mint_wh {got_mw} != {exp['mint_wh']}")
        for role, want in exp["deltas"].items():
            got_d = tok_delta(rec, ROLE_KEY[role])
            check(got_d == want, f"{tag}: delta {role} {got_d} != {want}")
        for role in TOKEN_ROLES:
            if role in exp["deltas"]:
                continue
            got_d = tok_delta(rec, ROLE_KEY[role])
            check(got_d == 0, f"{tag}: unexpected delta {role} {got_d}")
        for role, want in exp.get("withheld", {}).items():
            got_w = wh_delta(rec, ROLE_KEY[role])
            check(got_w == want, f"{tag}: withheld {role} {got_w} != {want}")
        for role in TOKEN_ROLES:
            if role in exp.get("withheld", {}):
                continue
            got_w = wh_delta(rec, ROLE_KEY[role])
            check(got_w == 0, f"{tag}: unexpected withheld {role} {got_w}")
        for pool_name, pool_key in (("main", pool), ("pool2", POOL2), ("p3", P3), ("p4", P4), ("p5", P5)):
            got_pool = pool_state(rec["after"][str(pool_key)])
            check(got_pool == exp["pools"][pool_name],
                  f"{tag}: pool {pool_name} {got_pool} != {exp['pools'][pool_name]}")
        if "pool_creator" in exp:
            got_pc = bytes.fromhex(rec["after"][str(pool)]["data_hex"])[211:243].hex()
            check(got_pc == exp["pool_creator"],
                  f"{tag}: pool_creator {got_pc} != {exp['pool_creator']}")
        got_vol = vol_state(rec["after"][str(volume)])
        check(got_vol == exp["volume"], f"{tag}: volume {got_vol} != {exp['volume']}")
        if "cfg" in exp:
            got_cfg = cfg_fields(rec["after"][str(CONFIG_KEY)])
            check(got_cfg == exp["cfg"],
                  f"{tag}: cfg {got_cfg} != {exp['cfg']}")
        if exp.get("uva") is not None:
            got_uva = uva_fields(rec["after"][str(volume)])
            check(got_uva == exp["uva"], f"{tag}: uva {got_uva} != {exp['uva']}")
        if exp.get("uva_absent"):
            check(rec["after"][str(volume)] is None, f"{tag}: volume should stay absent")
        for role, want in exp.get("lam_after", {}).items():
            got = rec["after"][str(ROLE_KEY[role])]
            check(got is not None and got["lamports"] == want,
                  f"{tag}: lam_after {role} {None if got is None else got['lamports']} != {want}")
        check(rec["after"][str(GVOL)] == rec["before"][str(GVOL)],
              f"{tag}: global volume accumulator changed")
        if exp.get("log_fragment"):
            check(exp["log_fragment"] in "\n".join(rec["logs"]),
                  f"{tag}: log fragment missing")
        if exp.get("site_fragment"):
            check(exp["site_fragment"] in "\n".join(rec["logs"]),
                  f"{tag}: site fragment missing")
        if exp.get("rollback"):
            for k, b in rec["before"].items():
                if k in (str(PAYER_KEY), str(OUTSIDER_KEY)):
                    continue
                check(rec["after"][k] == b, f"{tag}: rollback violated for {k}")
        if exp.get("boost_event") is not None:
            raws = ev_list(rec["logs"])
            check(len(raws) == 2, f"{tag}: boost events {len(raws)} != 2")
            first = decode_event("boost", raws[0])
            check(first == {"disc": MHBUY_DISC, "len": 512},
                  f"{tag}: boost first event {first}")
            got = decode_event("boost", raws[1])
            check(got is not None, f"{tag}: boost event decode failed")
            for fkey, want in exp["boost_event"].items():
                check(got.get(fkey) == want,
                      f"{tag}: boost event {fkey} {got.get(fkey)} != {want}")
        elif exp.get("event") is not None:
            raws = ev_list(rec["logs"])
            check(len(raws) == exp["events"],
                  f"{tag}: decoded events {len(raws)} != {exp['events']}")
            for raw in raws:
                got = decode_event(STEP_KIND[kind], raw)
                check(got is not None, f"{tag}: event decode failed")
                for fkey, want in exp["event"].items():
                    check(got.get(fkey) == want,
                          f"{tag}: event {fkey} {got.get(fkey)} != {want}")
        rec["case"] = case["label"]
        rec["image"] = image_name
        rec["step"] = kind
        out.append(rec)
    return out


def main():
    if MEASURE:
        for case in CASES:
            for image_name, binary in IMAGES.items():
                run_case(case, image_name, binary)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "runtime").mkdir(exist_ok=True)
    receipts = []
    report_cases = []
    for case in CASES:
        per_image = {}
        for image_name, binary in IMAGES.items():
            per_image[image_name] = run_case(case, image_name, binary)
        for image_name in IMAGES:
            for rec in per_image[image_name]:
                receipts.append(rec)

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
                            "events": len(rec["events"]),
                            "before": strip(rec["before"]), "after": strip(rec["after"])})
            return out
        # This packet PINS a divergence on purpose: do not assert surface
        # equality. Record it instead; control must still equal candidate.
        base = surface(per_image["original"])
        divergent = (surface(per_image["control"]) != base
                     or surface(per_image["candidate"]) != base)
        check(surface(per_image["control"]) == surface(per_image["candidate"]),
              f"{case['label']}: control and candidate surfaces differ")
        report_cases.append({"label": case["label"],
                             "flags": case.get("flags", {}),
                             "onehop": bool(case.get("onehop")),
                             "divergent": divergent,
                             "steps": case["expect"],
                             "error_sites": {image_name: [r["site"] for r in per_image[image_name]] for image_name in IMAGES}})
        print(f"OK {case['label']} ({len(case['steps'])} steps x 3 images)")
    parts = []
    for i in range(0, len(receipts), 10):
        chunk = receipts[i:i + 10]
        name = f"raw-transactions-part{i // 10 + 1:02d}.jsonl.gz"
        path = OUT / "runtime" / name
        with gzip.open(path, "wt", encoding="utf-8") as fh:
            for rec in chunk:
                fh.write(json.dumps(rec) + "\n")
        parts.append({"file": f"runtime/{name}", "count": len(chunk),
                      "sha256": sha(path.read_bytes()), "bytes": path.stat().st_size})
    report = {"case_count": len(CASES), "receipt_count": len(receipts),
              "counts": {"cases": len(CASES), "receipts": len(receipts),
                         "parts": len(parts)},
              "mismatches": [],
              "input_sha256": {k: IMAGE_SHA[k] for k in IMAGES},
              "parts": parts, "cases": report_cases,
              "images": {k: IMAGE_SHA[k] for k in IMAGES}}
    with gzip.open(OUT / "runtime" / "report.json.gz", "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(report, indent=2))
    print(f"cases={len(CASES)} receipts={len(receipts)} parts={len(parts)}")
    for p in parts:
        print(f"  {p['file']} {p['count']} receipts {p['bytes']} bytes")
    print("NEXT: write verify.py and README.md, then regenerate MANIFEST.json")
    print("ADDRESSES for verify.py:")
    for name, key in [("POOL", pool), ("POOL2", POOL2), ("P3", P3), ("P4", P4), ("P5", P5),
                      ("BASE2", BASE2), ("BASE3", BASE3), ("BASE4", BASE4), ("BASE5", BASE5),
                      ("VB2", VB2), ("VQ2", VQ2), ("VB3", VB3), ("VQ3", VQ3),
                      ("VB4", VB4), ("VQ4", VQ4), ("VB5", VB5), ("VQ5", VQ5),
                      ("U3", U3), ("U4", U4), ("U5", U5),
                      ("CREATOR", CREATOR), ("CREATOR_VAULT", CREATOR_VAULT),
                      ("PROTOCOL", PROTOCOL),
                      ("PROTOCOL_ATA", PROTOCOL_ATA), ("CREATOR_ATA", CREATOR_ATA),
                      ("DEST", DEST),
                      ("PROTOCOL_ATA_P3", PROTOCOL_ATA_P3), ("CREATOR_ATA_P3", CREATOR_ATA_P3),
                      ("DEST3", DEST3),
                      ("PROTOCOL_ATA_P2", PROTOCOL_ATA_P2), ("CREATOR_ATA_P2", CREATOR_ATA_P2),
                      ("DEST2", DEST2),
                      ("PROTOCOL_ATA_P4", PROTOCOL_ATA_P4), ("CREATOR_ATA_P4", CREATOR_ATA_P4),
                      ("DEST4", DEST4),
                      ("PROTOCOL_ATA_P5", PROTOCOL_ATA_P5), ("CREATOR_ATA_P5", CREATOR_ATA_P5),
                      ("DEST5", DEST5),
                      ("BOOST", BOOST), ("BATA", BATA), ("BP3", BP3), ("BA3", BA3),
                      ("GVOL", GVOL), ("IMINT", IMINT), ("GA_ATA", GA_ATA), ("UA_ATA", UA_ATA), ("UVATA", uvata),
                      ("WDEST", WDEST), ("BASE22", BASE22), ("PLAIN", PLAIN),
                      ("CREATOR0", CREATOR0), ("BC_CREATOR", BC_CREATOR),
                      ("NEWVAULT", NEWVAULT), ("NEWVAULT22", NEWVAULT22), ("NEWDEST22", NEWDEST22),
                      ("BCVAULT", BCVAULT), ("BCVAULT22", BCVAULT22), ("BCDEST22", BCDEST22),
                      ("SHARING_PDA", SHARING_PDA), ("SHVAULT", SHVAULT), ("SHVAULT22", SHVAULT22),
                      ("SHDEST22", SHDEST22), ("ZEROVAULT", ZEROVAULT), ("ZEROVAULT22", ZEROVAULT22),
                      ("ZERODEST22", ZERODEST22), ("ORIGDEST22", ORIGDEST22),
                      ("META_PDA", META_PDA), ("BC_PDA", BC_PDA),
                      ("POOLV2", POOLV2)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
