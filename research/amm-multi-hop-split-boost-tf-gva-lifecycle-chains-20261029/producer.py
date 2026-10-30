"""Build research/amm-multi-hop-split-boost-tf-gva-lifecycle-chains-20261029 receipts.

3rd run packet #110: the split x boost x tf chain at TRUE 3 hops
(three_amm only, final output U3) meets the GlobalVolumeAccumulator
lifecycle. There is NO init or close instruction for the GVA in the
program (only close_user_volume_accumulator exists, for the UVA):
the GVA is a PDA account that must pre-exist, and its lifecycle is
driven by admin_update_token_incentives plus claim/sync reads. This
packet measures: chain legs beside an absent / zeroed / truncated /
wrong-owner GVA (trades and boost ignore it; claim, sync and admin
do not); the admin gates (StartTimeInThePast 6030, EndTimeInThePast
6031, EndTimeBeforeStartTime 6032, TimeRangeTooLarge 6033,
SupplyUpdateForFinishedRange 6035, DayIndexAfterEndIndex 6036,
DayInActiveRange 6037, InvalidAdmin 6005); start-change wiping all
supplies and sol_volumes; mid-range admin zeroing future sol_volumes
only; supply-slot edits moving the next claim reward; mint rotation
breaking claims with InvalidIncentiveMint 6038 and restoration;
the claim/sync reset gates; and the UVA close arc (close strands
unclaimed tokens, breaks the next claim until re-init, while the
next chain buy recreates a fresh UVA and the boost stays anchor).
No GVA re-init path exists: admin_update on an absent GVA fails
instead of creating it.

Route check (read from this builder, not the packet name):
build_route calls three_amm only and appends NO g4/g5 hop group,
so the fixture route is main -> POOL2 -> P3, final output U3:
TRUE 3 hops. #61 appended g4 and was actually 4 hops; do NOT
re-add it. cpatch steps are harness field resets recorded with an
empty transaction, never presented as on-chain instructions.
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
OUT = ROOT / "research/amm-multi-hop-split-boost-tf-gva-lifecycle-chains-20261029"
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


ZEROPK = Pubkey.default()
EXTKEY = Pubkey.from_bytes(bytes([150]) * 32)
# Created pools (creator = payer, index 0 unless noted).
CPOOL, _ = Pubkey.find_program_address([b"pool", struct.pack("<H", 0), bytes(PAYER_KEY), bytes(base), bytes(quote)], PROGRAM)
CLP, _ = Pubkey.find_program_address([b"pool_lp_mint", bytes(CPOOL)], PROGRAM)
CVB = Pubkey.find_program_address([bytes(CPOOL), bytes(TOKEN), bytes(base)], ATA_PROG)[0]
CVQ = Pubkey.find_program_address([bytes(CPOOL), bytes(TOKEN), bytes(quote)], ATA_PROG)[0]
CULP = Pubkey.find_program_address([bytes(PAYER_KEY), bytes(TOKEN22), bytes(CLP)], ATA_PROG)[0]
CTAIL, _ = Pubkey.find_program_address([b"pool", struct.pack("<H", 0), bytes(PAYER_KEY), bytes(BASE3), bytes(BASE2)], PROGRAM)
CTLP, _ = Pubkey.find_program_address([b"pool_lp_mint", bytes(CTAIL)], PROGRAM)
CTVB = Pubkey.find_program_address([bytes(CTAIL), bytes(TOKEN), bytes(BASE3)], ATA_PROG)[0]
CTVQ = Pubkey.find_program_address([bytes(CTAIL), bytes(TOKEN), bytes(BASE2)], ATA_PROG)[0]
CTULP = Pubkey.find_program_address([bytes(PAYER_KEY), bytes(TOKEN22), bytes(CTLP)], ATA_PROG)[0]
CTAIL1, _ = Pubkey.find_program_address([b"pool", struct.pack("<H", 1), bytes(PAYER_KEY), bytes(BASE3), bytes(BASE2)], PROGRAM)
CT1LP, _ = Pubkey.find_program_address([b"pool_lp_mint", bytes(CTAIL1)], PROGRAM)
CT1VB = Pubkey.find_program_address([bytes(CTAIL1), bytes(TOKEN), bytes(BASE3)], ATA_PROG)[0]
CT1VQ = Pubkey.find_program_address([bytes(CTAIL1), bytes(TOKEN), bytes(BASE2)], ATA_PROG)[0]
CT1ULP = Pubkey.find_program_address([bytes(PAYER_KEY), bytes(TOKEN22), bytes(CT1LP)], ATA_PROG)[0]
CUB = Pubkey.from_bytes(bytes([60]) * 32)
CUQ = Pubkey.from_bytes(bytes([61]) * 32)
CUB3 = Pubkey.from_bytes(bytes([63]) * 32)
CUQ2 = Pubkey.from_bytes(bytes([64]) * 32)
ZVAULT, _ = Pubkey.find_program_address([b"creator_vault", bytes(ZEROPK)], PROGRAM)
ZATA = Pubkey.find_program_address([bytes(ZVAULT), bytes(TOKEN), bytes(quote)], ATA_PROG)[0]
ZDEST = Pubkey.from_bytes(bytes([62]) * 32)
CBV, _ = Pubkey.find_program_address([b"boost_vault", bytes(CPOOL)], PROGRAM)
CBA = Pubkey.find_program_address([bytes(CBV), bytes(TOKEN22), bytes(quote)], ATA_PROG)[0]


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
PUMPVAULT, _ = Pubkey.find_program_address([b'creator-vault', bytes(CREATOR)], PUMP)
DEST_T22 = Pubkey.find_program_address([bytes(PUMPVAULT), bytes(TOKEN22), bytes(quote)], ATA_PROG)[0]
DEST_SPL = Pubkey.find_program_address([bytes(PUMPVAULT), bytes(TOKEN), bytes(quote)], ATA_PROG)[0]
DEST_SPL_B2 = Pubkey.find_program_address([bytes(PUMPVAULT), bytes(TOKEN), bytes(BASE2)], ATA_PROG)[0]
DEST_SPL_BASE = Pubkey.find_program_address([bytes(PUMPVAULT), bytes(TOKEN), bytes(base)], ATA_PROG)[0]
DEST_T22_B2 = Pubkey.find_program_address([bytes(PUMPVAULT), bytes(TOKEN22), bytes(BASE2)], ATA_PROG)[0]
BATA, _ = Pubkey.find_program_address([bytes(BOOST), bytes(TOKEN22), bytes(quote)], ATA_PROG)
BP3, _ = Pubkey.find_program_address([b'boost_vault', bytes(P3)], PROGRAM)
BA3, _ = Pubkey.find_program_address([bytes(BP3), bytes(TOKEN22), bytes(BASE2)], ATA_PROG)

GVOL = Pubkey.find_program_address([b'global_volume_accumulator'], PROGRAM)[0]
GQATA, _ = Pubkey.find_program_address([bytes(GVOL), bytes(TOKEN22), bytes(quote)], ATA_PROG)
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
WATCH = [PAYER_KEY, OUTSIDER_KEY, pool, POOL2, P3, quote, P4, P5, base, quote, BASE2, BASE3, BASE4, BASE5, lp, userbase,
         userquote, userlp, vaultbase, vaultquote, VB2, VQ2, VB3, VQ3, VB4, VQ4, VB5, VQ5, U3, U4, U5,
         buyback, volume, feeconfig, CONFIG_KEY,
         PROTOCOL_ATA, CREATOR_ATA, DEST,
         PROTOCOL_ATA_P3, CREATOR_ATA_P3, DEST3,
         PROTOCOL_ATA_P2, CREATOR_ATA_P2, DEST2,
         PROTOCOL_ATA_P4, CREATOR_ATA_P4, DEST4,
         PROTOCOL_ATA_P5, CREATOR_ATA_P5, DEST5,
         PROTO22, CREAT22, DEST22, BB22, BOOST, BATA, BP3, BA3,
         GVOL, IMINT, GA_ATA, GQATA, UA_ATA, uvata, WDEST, BASE22, PLAIN,
         NEWVAULT22, NEWDEST22, BCVAULT22, BCDEST22, SHVAULT22, SHDEST22,
         ZEROVAULT22, ZERODEST22, ORIGDEST22, META_PDA, BC_PDA, SHARING_PDA,
         NEWVAULT, BCVAULT, SHVAULT, ZEROVAULT, POOLV2,
         CPOOL, CTAIL, CTAIL1, CLP, CTLP, CT1LP, CVB, CVQ, CULP,
         CTVB, CTVQ, CTULP, CT1VB, CT1VQ, CT1ULP, CUB, CUQ, CUB3, CUQ2,
         ZVAULT, ZATA, ZDEST, CBV, CBA, EXTKEY,
         PUMPVAULT, DEST_T22, DEST_SPL, DEST_SPL_B2, DEST_SPL_BASE, DEST_T22_B2]
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
            "gata": GA_ATA, "gqata": GQATA, "uata": UA_ATA, "uvata": uvata,
            "newvault": NEWVAULT22, "newdest": NEWDEST22,
            "bcvault": BCVAULT22, "bcdest": BCDEST22,
            "shvault": SHVAULT22, "shdest": SHDEST22,
            "zerovault": ZEROVAULT22, "zerodest": ZERODEST22,
            "origdest": ORIGDEST22,
            "cvb": CVB, "cvq": CVQ, "culp": CULP,
            "ctvb": CTVB, "ctvq": CTVQ, "ctulp": CTULP,
            "ct1vb": CT1VB, "ct1vq": CT1VQ, "ct1ulp": CT1ULP,
            "cub": CUB, "cuq": CUQ, "cub3": CUB3, "cuq2": CUQ2,
            "zata": ZATA, "zdest": ZDEST, "cba": CBA, "extacc": EXTKEY,
            "pvault": PUMPVAULT, "pdest": DEST_SPL, "pdest22": DEST_T22,
            "pdestb2": DEST_SPL_B2, "pdestbase": DEST_SPL_BASE, "pdestb2t22": DEST_T22_B2,
            "creat22": CREAT22, "proto22": PROTO22}
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
               "gata", "gqata", "uata", "uvata",
               "newvault", "newdest", "bcvault", "bcdest",
               "shvault", "shdest", "zerovault", "zerodest", "origdest",
               "cvb", "cvq", "culp", "ctvb", "ctvq", "ctulp",
               "ct1vb", "ct1vq", "ct1ulp", "cub", "cuq", "cub3", "cuq2",
               "zata", "zdest", "cba", "pvault", "pdest", "pdest22",
               "pdestb2", "pdestbase", "pdestb2t22", "creat22", "proto22"]
SWP_DISC = "82a42461e48287a5"
COL_DISC = "e8f5c2eeeada3a59"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def patch_mint_epochs(h, oe, ob, ne, nb, omax=2**64 - 1, nmax=2**64 - 1):
    m = h.vm.get_account(quote)
    d = bytearray(m.data)
    struct.pack_into("<QQH", d, 242, oe, omax, ob)
    struct.pack_into("<QQH", d, 260, ne, nmax, nb)
    h.vm.set_account(quote, Account(m.lamports, bytes(d), TOKEN22))


def setup_vm(binary, case):
    bps = case.get("bps", 0)
    h = Harness(binary)
    h._epoch = case.get("clock_epoch", 0)
    vm = h.vm
    vm.set_clock(Clock(100, 1234567890, case.get("clock_epoch", 0), 0, 1234567890))
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
        gs = case.get("gva_seed")
        if gs is None:
            start, end, sec, sup, vol, mintk = 20, 49, 1, 1000, 100, IMINT
        else:
            start, end, sec, sup, vol, mintk = gs
        sup_l = sup if isinstance(sup, (list, tuple)) else [sup] * 30
        vol_l = vol if isinstance(vol, (list, tuple)) else [vol] * 30
        g = GDISC + struct.pack('<qqq', start, end, sec) + bytes(mintk) \
            + struct.pack('<30Q', *sup_l) + struct.pack('<30Q', *vol_l)
        gowner = PROGRAM if case.get("gva_owner", "prog") == "prog" else Pubkey.default()
        vm.set_account(GVOL, Account(10**9, g.ljust(600, b'\0'), gowner))
    else:
        vm.set_account(GVOL, Account(0, b'', Pubkey.default()))
    base82 = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**12) + bytes([6, 1]) + bytes(36)
    vm.set_account(IMINT, Account(10**9, tf_mint_data(base82, case.get("claim_bps", 0), 2**64 - 1), TOKEN22))
    if case.get("gata", True):
        vm.set_account(GA_ATA, Account(10**9, t22acct_imint(IMINT, GVOL, case.get("gata_amt", 10**9)), TOKEN22))
    else:
        vm.set_account(GA_ATA, Account(0, b'', Pubkey.default()))
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
    if case.get("epochs") is not None and not case.get("plain"):
        oe, ob, ne, nb = case["epochs"]
        patch_mint_epochs(h, oe, ob, ne, nb, case.get("omax", 2**64 - 1), case.get("nmax", 2**64 - 1))
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
    if case.get("fund_create"):
        vm.set_account(CUB, Account(10**9, token(base, PAYER_KEY, 10**15, False), TOKEN))
        vm.set_account(CUQ, Account(10**15 + 2039280, token(quote, PAYER_KEY, 10**15, True), TOKEN))
        vm.set_account(CUB3, Account(10**9, token(BASE3, PAYER_KEY, 10**15, False), TOKEN))
        vm.set_account(CUQ2, Account(10**9, token(BASE2, PAYER_KEY, 10**15, False), TOKEN))
    vm.set_account(ZVAULT, Account(10**9, b"", Pubkey.default()))
    vm.set_account(ZATA, Account(2039280, token(quote, ZVAULT, 0, True), TOKEN))
    vm.set_account(ZDEST, Account(2039280, token(quote, ZEROPK, 0, True), TOKEN))
    vm.set_account(PUMPVAULT, Account(10**9, b"", Pubkey.default()))
    vm.set_account(CBV, Account(10**9, b"", Pubkey.default()))
    rawc = token(quote, CBV, 10**12, True)
    dc = bytes(rawc[:165]) + bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    vm.set_account(CBA, Account(10**12 + 10**9, dc, TOKEN22))
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
    if kind == "create":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "base": u64(raw, 116), "quote": u64(raw, 124),
                "pbase": u64(raw, 132), "pquote": u64(raw, 140),
                "minliq": u64(raw, 148), "initliq": u64(raw, 156),
                "lpout": u64(raw, 164)}
    if kind == "ww":
        return None
    if kind in ("mhbuy3", "mhsell3", "mhbuy5", "mhsell5", "mhbuy4", "mhsell4", "mhbuy1", "mhsell1"):
        return {"disc": raw[:8].hex(), "len": len(raw)}
    if kind == "admin":
        return {"disc": raw[:8].hex(), "len": len(raw),
                "start": struct.unpack_from("<q", raw, 8)[0],
                "end": struct.unpack_from("<q", raw, 16)[0],
                "day": u64(raw, 24), "supply": u64(raw, 32),
                "mint": raw[40:72].hex(),
                "sec": struct.unpack_from("<q", raw, 72)[0],
                "timestamp": struct.unpack_from("<q", raw, 80)[0]}
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
    if kind == "cpatch":
        # Harness field reset, NOT an instruction: patch pool/config/ATA
        # fields in place and record before/after snapshots. The receipt
        # carries an empty transaction; verify.py skips signature checks
        # for cpatch steps and asserts the recorded pool-state transition.
        before = snap(h.vm)
        target, spec = args
        if target == "cpool":
            a = h.vm.get_account(CPOOL)
            if a is None:
                raise AssertionError("cpatch cpool before create")
            d = bytearray(a.data)
            if "vq" in spec:
                d[245:261] = spec["vq"].to_bytes(16, "little", signed=True)
            if "proto" in spec:
                struct.pack_into("<Q", d, 271, spec["proto"])
            if "creator" in spec:
                struct.pack_into("<Q", d, 279, spec["creator"])
            h.vm.set_account(CPOOL, Account(a.lamports, bytes(d), a.owner))
        elif target == "config":
            a = h.vm.get_account(CONFIG_KEY)
            d = bytearray(a.data)
            if "boost_auth" in spec:
                d[907:939] = bytes(spec["boost_auth"])
            if "boost_enabled" in spec:
                d[939] = spec["boost_enabled"]
            h.vm.set_account(CONFIG_KEY, Account(a.lamports, bytes(d), a.owner))
        elif target == "mint_tf":
            # Post-create transfer-fee extension on the quote mint
            # (the same harness rewrite setup_vm applies at case start).
            # Direct create under a tf-configured quote mint fails
            # IncorrectProgramId at any bps (probed: 0/100/5000, with
            # and without the ww patch), so tf created-pool cases must
            # create plain first and bolt tf on afterwards. The created
            # pool's own accounts are untouched by the rewrite.
            transferfee(quote, spec["bps"], 2**64 - 1)(h, [])
        elif target == "conv_cvq":
            # Convert the created pool's quote vault to a Token-2022
            # account (owner + 178-byte extension form, exactly the
            # rewrite transferfee applies to fixture vaults). Direct
            # create always births SPL Token vaults; this rewrite is
            # what a created pool's quote leg needs for boost (see
            # README: mint must ALSO be Token-2022 via mint_tf).
            a = h.vm.get_account(CVQ)
            d = bytes(a.data[:165]) + bytes([2]) + struct.pack("<HHQ", 2, 8, 0)
            h.vm.set_account(CVQ, Account(a.lamports, d, TOKEN22))
        elif target == "cba":
            a = h.vm.get_account(CBA)
            d = bytearray(a.data)
            if "amount" in spec:
                struct.pack_into("<Q", d, 64, spec["amount"])
            h.vm.set_account(CBA, Account(a.lamports, bytes(d), a.owner))
        elif target == "pool":
            a = h.vm.get_account(pool)
            d = bytearray(a.data)
            if "vq" in spec:
                d[245:261] = spec["vq"].to_bytes(16, "little", signed=True)
            if "proto" in spec:
                struct.pack_into("<Q", d, 271, spec["proto"])
            if "creator" in spec:
                struct.pack_into("<Q", d, 279, spec["creator"])
            h.vm.set_account(pool, Account(a.lamports, bytes(d), a.owner))
        elif target == "flagpool":
            key = POOLKEYS[spec["pool"]]
            a = h.vm.get_account(key)
            d = bytearray(a.data)
            d[243] = 1 if spec["mode"] in ("mayhem", "both") else 0
            d[244] = 1 if spec["mode"] in ("cb", "both") else 0
            h.vm.set_account(key, Account(a.lamports, bytes(d), a.owner))
        elif target == "epoch":
            a = h.vm.get_account(quote)
            d = bytearray(a.data)
            cur = {"oe": struct.unpack_from("<Q", d, 242)[0],
                   "omax": struct.unpack_from("<Q", d, 250)[0],
                   "ob": struct.unpack_from("<H", d, 258)[0],
                   "ne": struct.unpack_from("<Q", d, 260)[0],
                   "nmax": struct.unpack_from("<Q", d, 268)[0],
                   "nb": struct.unpack_from("<H", d, 276)[0]}
            cur.update(spec)
            patch_mint_epochs(h, cur["oe"], cur["ob"], cur["ne"], cur["nb"], cur["omax"], cur["nmax"])
        elif target == "clock":
            h._epoch = spec["epoch"]
            h.vm.set_clock(Clock(100, 1234567890, spec["epoch"], 0, 1234567890))
        elif target == "freeze":
            a = h.vm.get_account(ROLE_KEY[spec["role"]])
            d = bytearray(a.data)
            d[108] = 2
            h.vm.set_account(ROLE_KEY[spec["role"]], Account(a.lamports, bytes(d), a.owner))
        elif target == "seedata":
            key = ROLE_KEY[spec["role"]]
            a = h.vm.get_account(key)
            d = bytearray(a.data)
            struct.pack_into("<Q", d, 64, spec["amount"])
            h.vm.set_account(key, Account(spec.get("lamports", a.lamports), bytes(d), a.owner))
        else:
            raise ValueError(target)
        return {"transaction_base64": "", "error": None, "logs": [],
                "events": [], "before": before, "after": snap(h.vm),
                "site": None}
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
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 10))
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
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 10))
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
    elif kind == "admin":
        start, end, sec, day, supply, ts, mint_role, mode = args
        mint_key = IMINT if mint_role == "imint" else quote
        gata_key = GA_ATA if mint_role == "imint" else GQATA
        if mode == "payer":
            signer_key, fee_key, signers, sflag = PAYER_KEY, PAYER, [PAYER], True
        elif mode == "outsider":
            signer_key, fee_key, signers, sflag = OUTSIDER_KEY, OUTSIDER, [OUTSIDER], True
        elif mode == "unsigned":
            signer_key, fee_key, signers, sflag = PAYER_KEY, OUTSIDER, [OUTSIDER], False
        else:
            raise ValueError(mode)
        ix = next(x for x in IDL["instructions"] if x["name"] == "admin_update_token_incentives")
        keys = [signer_key, CONFIG_KEY, GVOL, mint_key, gata_key, ATA_PROG,
                Pubkey.default(), TOKEN22, EVENT, PROGRAM]
        metas = []
        for k, at in zip(keys, ix["accounts"]):
            signer = bool(at.get("signer"))
            if k == signer_key:
                signer = sflag
            metas.append(AccountMeta(k, signer, bool(at.get("writable"))))
        data = disc("admin_update_token_incentives") + struct.pack("<qqqQQ", start, end, sec, day, supply)
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, ts))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], fee_key.pubkey(), signers, h.vm.latest_blockhash())
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
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 10))
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
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 10))
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
    elif kind == "ext":
        target_name, mode = args
        target = {"pool": pool, "cfg": CONFIG_KEY, "uva": volume, "gva": GVOL,
                  "fee": feeconfig, "vault": vaultquote, "extacc": EXTKEY}[target_name]
        if mode == "payer":
            ukey, fee_key, signers, usigner, uwritable, twritable = PAYER_KEY, PAYER, [PAYER], True, True, True
        elif mode == "out":
            ukey, fee_key, signers, usigner, uwritable, twritable = OUTSIDER_KEY, OUTSIDER, [OUTSIDER], True, True, True
        elif mode == "unsigned":
            ukey, fee_key, signers, usigner, uwritable, twritable = PAYER_KEY, OUTSIDER, [OUTSIDER], False, True, True
        elif mode == "ro_target":
            ukey, fee_key, signers, usigner, uwritable, twritable = PAYER_KEY, PAYER, [PAYER], True, True, False
        elif mode == "ro_user_out":
            ukey, fee_key, signers, usigner, uwritable, twritable = OUTSIDER_KEY, PAYER, [PAYER, OUTSIDER], True, False, True
        else:
            raise ValueError(mode)
        metas = [AccountMeta(target, False, twritable),
                 AccountMeta(ukey, usigner, uwritable),
                 AccountMeta(Pubkey.default(), False, False),
                 AccountMeta(EVENT, False, False),
                 AccountMeta(PROGRAM, False, False)]
        data = disc("extend_account")
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 10))
        tx = Transaction.new_signed_with_payer(
            [Instruction(PROGRAM, data, metas)], fee_key.pubkey(), signers, h.vm.latest_blockhash())
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
        h.vm.set_clock(Clock(100, 1234567890, getattr(h, "_epoch", 0), 0, 1234567890))
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
    elif kind in ("xfer2", "xfer1"):
        if kind == "xfer2":
            mint_role, prog_role, vault_role, dest_role, payer_mode = args
            mint_k = {"quote": quote, "base2": BASE2, "base": base}[mint_role]
            prog_k = TOKEN22 if prog_role == "t22" else TOKEN
            fee_key = OUTSIDER if payer_mode == "out" else PAYER
            ix = next(x for x in IDL["instructions"] if x["name"] == "transfer_creator_fees_to_pump_v2")
            keys = [fee_key.pubkey(), mint_k, prog_k, Pubkey.default(), ATA_PROG, CREATOR,
                    CREATOR_VAULT, ROLE_KEY[vault_role], PUMPVAULT, ROLE_KEY[dest_role],
                    EVENT, PROGRAM]
            data = disc("transfer_creator_fees_to_pump_v2")
        else:
            mint_role, prog_role, vault_role, payer_mode = args
            mint_k = {"quote": quote, "base2": BASE2, "base": base}[mint_role]
            prog_k = TOKEN22 if prog_role == "t22" else TOKEN
            fee_key = OUTSIDER if payer_mode == "out" else PAYER
            ix = next(x for x in IDL["instructions"] if x["name"] == "transfer_creator_fees_to_pump")
            keys = [mint_k, prog_k, Pubkey.default(), ATA_PROG, CREATOR,
                    CREATOR_VAULT, ROLE_KEY[vault_role], PUMPVAULT, EVENT, PROGRAM]
            data = disc("transfer_creator_fees_to_pump")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        if kind == "xfer2":
            metas[0] = AccountMeta(fee_key.pubkey(), True, True)
        h.vm.set_clock(Clock(100, 1234567890, getattr(h, "_epoch", 0), 0, 1234567890))
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
        h.vm.set_clock(Clock(100, 1234567890, getattr(h, "_epoch", 0), 0, 1234567890))
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
    elif kind == "create":
        pair, bamt, qamt, trailing, mayhem, index = args
        if pair == "std":
            pk, lp_k, vb_k, vq_k, ulp_k, ub_k, uq_k, bm, qm = CPOOL, CLP, CVB, CVQ, CULP, CUB, CUQ, base, quote
        elif pair == "tail":
            pk, lp_k, vb_k, vq_k, ulp_k, ub_k, uq_k, bm, qm = CTAIL, CTLP, CTVB, CTVQ, CTULP, CUB3, CUQ2, BASE3, BASE2
        elif pair == "tail1":
            pk, lp_k, vb_k, vq_k, ulp_k, ub_k, uq_k, bm, qm = CTAIL1, CT1LP, CT1VB, CT1VQ, CT1ULP, CUB3, CUQ2, BASE3, BASE2
        else:
            raise ValueError(pair)
        ix = next(x for x in IDL["instructions"] if x["name"] == "create_pool")
        keys = [pk, CONFIG_KEY, PAYER_KEY, bm, qm, lp_k, ub_k, uq_k, ulp_k, vb_k, vq_k,
                Pubkey.default(), TOKEN22, TOKEN, TOKEN, ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("create_pool") + struct.pack("<HQQ", index, bamt, qamt) + bytes(PAYER_KEY) + bytes([mayhem]) + trailing
    elif kind in ("mhbuy3c", "mhsell3c"):
        ix = next(x for x in IDL["instructions"] if x["name"] == "multi_hop_swap")
        metas = routes[{"mhsell3c": "sell_c", "mhbuy3c": "buy_c"}[kind]]
        data = bytes(ix["discriminator"]) + struct.pack("<QQ", args[0], args[1])
    elif kind == "lexact":
        ix = next(x for x in IDL["instructions"] if x["name"] == "buy_exact_quote_in")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(buy_keys(args[2]), ix["accounts"])] + list(LEG_REM)
        data = disc("buy_exact_quote_in") + struct.pack("<QQ", args[0], args[1]) + b"\0"
    elif kind == "bexact2":
        ix = next(x for x in IDL["instructions"] if x["name"] == "buy_exact_quote_in_v2")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(V2_KEYS, ix["accounts"])]
        metas[10] = AccountMeta(TOKEN22, False, False)
        metas[14] = AccountMeta(BB22, False, True)
        data = disc("buy_exact_quote_in_v2") + struct.pack("<QQ", args[0], args[1])
    elif kind == "buy2m":
        ix = next(x for x in IDL["instructions"] if x["name"] == "buy_v2")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(V2_KEYS, ix["accounts"])]
        metas[10] = AccountMeta(TOKEN22, False, False)
        metas[14] = AccountMeta(BB22, False, True)
        data = disc("buy_v2") + struct.pack("<QQ", args[0], args[1])
    elif kind == "sell2m":
        ix = next(x for x in IDL["instructions"] if x["name"] == "sell_v2")
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(V2_KEYS, ix["accounts"])]
        metas[10] = AccountMeta(TOKEN22, False, False)
        metas[14] = AccountMeta(BB22, False, True)
        data = disc("sell_v2") + struct.pack("<QQ", args[0], args[1])
    elif kind in ("buy2c", "sell2c"):
        name = "buy_v2" if kind == "buy2c" else "sell_v2"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [CPOOL, PAYER_KEY, CONFIG_KEY, base, quote, userbase, userquote, CVB, CVQ,
                TOKEN, TOKEN, Pubkey.default(), volume, feeconfig, buyback, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name) + struct.pack("<QQ", args[0], args[1])
    elif kind in ("swpc", "swcc"):
        name = "sweep_protocol_fee" if kind == "swpc" else "sweep_creator_fee"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [PAYER_KEY, CONFIG_KEY, CPOOL, quote, TOKEN, CVQ,
                PROTOCOL if kind == "swpc" else ZVAULT,
                PROTOCOL_ATA if kind == "swpc" else ZATA,
                Pubkey.default(), ATA_PROG, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name)
    elif kind == "colc":
        ix = next(x for x in IDL["instructions"] if x["name"] == "collect_coin_creator_fee")
        keys = [quote, TOKEN, ZEROPK, ZVAULT, ZATA, ZDEST, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc("collect_coin_creator_fee")
    elif kind == "boostc":
        ix = next(x for x in IDL["instructions"] if x["name"] == "boost_buy_and_burn")
        keys = [CPOOL, PAYER_KEY, CONFIG_KEY, base, quote, CVB, CVQ,
                CBV, CBA, TOKEN, TOKEN, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        metas[8] = AccountMeta(CBA, False, True)
        metas[10] = AccountMeta(TOKEN22, False, False)
        data = disc("boost_buy_and_burn") + struct.pack("<QQ", *args)
    elif kind in ("depc", "wdc"):
        name = "deposit" if kind == "depc" else "withdraw"
        ix = next(x for x in IDL["instructions"] if x["name"] == name)
        keys = [CPOOL, CONFIG_KEY, PAYER_KEY, base, quote, CLP, userbase, userquote, CULP, CVB, CVQ,
                TOKEN, TOKEN22, EVENT, PROGRAM]
        metas = [AccountMeta(k, bool(a.get("signer")), bool(a.get("writable")))
                 for k, a in zip(keys, ix["accounts"])]
        data = disc(name) + struct.pack("<QQQ", args[0], args[1], args[2])
    else:
        raise ValueError(kind)
    if kind == "tclaim":
        h.vm.set_clock(Clock(100, 0, getattr(h, "_epoch", 0), 0, 21))
    else:
        h.vm.set_clock(Clock(100, 1234567890, getattr(h, "_epoch", 0), 0, 1234567890))
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




# --- #106: transfer-fee epoch-schedule selection on the true-3-hop split x boost x tf chain ---

STEP_KIND105 = {"mhbuy3": "mhbuy3", "mhsell3": "mhsell3", "boost": "boost",
                "swp22": "swp", "swc22": "swc", "col22": "col", "dep": "dep", "wd": "wd",
                "tclaim": "tclaim", "cclaim": "cclaim", "sync": "sync",
                "admin": "admin", "close": "close", "close_other": "close", "close_unsigned": "close", "init": "init",
                "swp": "swp", "swc": "swc", "col": "col",
                "xfer2": None, "xfer1": None, "cpatch": None, "ww": None,
                "buy2m": "buy2", "sell2m": "sell2", "lexact": None, "bexact2": None,
                "harvest": None, "wfm": None}
TARGET_KEY = {"pool": pool, "cfg": CONFIG_KEY, "uva": volume, "gva": GVOL,
              "fee": feeconfig, "vault": vaultquote, "extacc": EXTKEY}
BST_DISC = "3f451c16305cc2b9"
MHBUY_DISC = "67f4521f2cf57777"


def gva_fields(entry):
    if entry is None:
        return None
    raw = bytes.fromhex(entry["data_hex"])
    if len(raw) < 64:
        return {"len": len(raw)}
    # GVA layout: disc 8, start 8, end 8, sec 8, mint 32,
    # total_token_supply[30] at 64, sol_volumes[30] at 304.
    sup = [struct.unpack_from("<Q", raw, 64 + i * 8)[0] for i in range(30)] if len(raw) >= 304 else None
    vol = [struct.unpack_from("<Q", raw, 304 + i * 8)[0] for i in range(30)] if len(raw) >= 544 else None
    return {"len": len(raw),
            "start": struct.unpack_from("<q", raw, 8)[0],
            "end": struct.unpack_from("<q", raw, 16)[0],
            "sec": struct.unpack_from("<q", raw, 24)[0],
            "mint": raw[32:64].hex(),
            "supply": sup, "vol": vol}


def safe_pool_state(entry):
    if entry is None:
        return None
    d = bytes.fromhex(entry["data_hex"])
    if len(d) < 287:
        return {"len": len(d)}
    return pool_state(entry)


def acct_len(entry):
    return None if entry is None else len(bytes.fromhex(entry["data_hex"]))


def acct_lam(entry):
    return None if entry is None else entry["lamports"]


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
            "wh": mint_wh(entry)}


def summarize(rec, kind):
    raws = ev_list(rec["logs"])
    dk = STEP_KIND105.get(kind)
    decoded = None
    if dk is not None:
        decoded = [decode_event(dk, raw) for raw in raws]
    if kind == "boost" and raws:
        decoded = [decode_event("boost", raw) for raw in raws]
    after = rec["after"]
    s = {"step": kind, "error": rec["error"], "events": len(rec["events"]),
         "decoded": decoded,
         "dPAYER": lam_delta(rec, PAYER_KEY), "dOUT": lam_delta(rec, OUTSIDER_KEY),
         "deltas": {role: tok_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if tok_delta(rec, ROLE_KEY[role]) != 0},
         "withheld": {role: wh_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if wh_delta(rec, ROLE_KEY[role]) != 0},
         "lam_deltas": {role: lam_delta(rec, ROLE_KEY[role]) for role in TOKEN_ROLES if lam_delta(rec, ROLE_KEY[role]) != 0},
         "pools": {name: safe_pool_state(after[str(key)]) for name, key in (("main", pool), ("pool2", POOL2), ("p3", P3))},
         "pool_creator": bytes.fromhex(after[str(pool)]["data_hex"])[211:243].hex() if after[str(pool)] else None,
         "cfg": cfg_fields(after[str(CONFIG_KEY)]),
         "uva": uva_fields(after[str(volume)]),
         "gva": gva_fields(after[str(GVOL)]),
         "mint": mint_fields(after[str(quote)]),
         "lens": {"pool": acct_len(after[str(pool)]), "cfg": acct_len(after[str(CONFIG_KEY)]),
                  "uva": acct_len(after[str(volume)]), "gva": acct_len(after[str(GVOL)]),
                  "fee": acct_len(after[str(feeconfig)]), "extacc": acct_len(after[str(EXTKEY)])},
         "site": rec["site"]}
    if kind == "cpatch":
        s["decoded"] = []
    return s


def C(label, steps, **kw):
    d = {"label": label, "steps": steps}
    d.update(kw)
    return d


SEED = (1, 111, 222, 333444, 20, 1, 555, 666)
SEED_LAST10 = (1, 111, 222, 333444, 10, 1, 555, 666)
FSEED = (1, 111, 222, 333444, 20, 1, 5475, 0)
MAXU = 2 ** 64 - 1
MH = (10 ** 9, 1)
MHSMALL = (10 ** 6, 1)
BST = (10 ** 9, 0)
DEP = (10 ** 6, MAXU, MAXU)
WD = (10 ** 6, 0, 0)
STD = (0, 100, 10, 5000)
VQ = ("cpatch", ("pool", {"vq": 10 ** 9}))


def CLK(ep):
    return ("cpatch", ("clock", {"epoch": ep}))


def EPO(ne=None, nb=None, oe=None, ob=None, omax=None, nmax=None):
    spec = {}
    if ne is not None:
        spec["ne"] = ne
    if nb is not None:
        spec["nb"] = nb
    if oe is not None:
        spec["oe"] = oe
    if ob is not None:
        spec["ob"] = ob
    if omax is not None:
        spec["omax"] = omax
    if nmax is not None:
        spec["nmax"] = nmax
    return ("cpatch", ("epoch", spec))


CASES = [
    # --- A: anchors on the fixture GVA (start 20, end 49, sec 1, supplies 1000, vols 100) ---
    C("A-mhbuy", [("mhbuy3", MH)], bps=100),
    C("A-mhsell", [("mhsell3", MH)], bps=100),
    C("A-boost", [VQ, ("boost", BST)], bps=100),
    C("A-tclaim", [("tclaim", None)], bps=100, uva_seed=SEED),
    C("A-sync-noop", [("sync", None)], bps=100, uva_seed=SEED),
    C("A-sync-reset", [("sync", None)], bps=100, uva_seed=SEED_LAST10),
    C("A-tclaim-twice", [("tclaim", None), ("tclaim", None)], bps=100, uva_seed=SEED),
    # --- B: GVA absent / zeroed / truncated / wrong-owner ---
    C("B-absent-mhbuy", [("mhbuy3", MH)], bps=100, gva=False),
    C("B-absent-boost", [VQ, ("boost", BST)], bps=100, gva=False),
    C("B-absent-tclaim", [("tclaim", None)], bps=100, gva=False, uva_seed=SEED),
    C("B-absent-sync", [("sync", None)], bps=100, gva=False, uva_seed=SEED_LAST10),
    C("B-absent-admin", [("admin", (20, 49, 1, 0, 0, 10, "imint", "payer"))], bps=100, gva=False),
    C("B-absent-swp-col-dep", [("swp22", None), ("swc22", None), ("col22", None), ("dep", DEP)], bps=100, gva=False),
    C("B-zeroed-tclaim", [("tclaim", None)], bps=100, gva_seed=(0, 0, 0, 0, 0, IMINT), uva_seed=SEED),
    C("B-zeroed-sync", [("sync", None)], bps=100, gva_seed=(0, 0, 0, 0, 0, IMINT), uva_seed=SEED_LAST10),
    C("B-zeroed-admin-tclaim", [("admin", (20, 49, 1, 0, 0, 10, "imint", "payer")), ("tclaim", None)], bps=100, gva_seed=(0, 0, 0, 0, 0, IMINT), uva_seed=SEED),
    C("B-trunc-mhbuy", [("mhbuy3", MH)], bps=100, gva_len=100),
    C("B-trunc-tclaim", [("tclaim", None)], bps=100, gva_len=100, uva_seed=SEED),
    C("B-trunc-admin", [("admin", (20, 49, 1, 0, 0, 10, "imint", "payer"))], bps=100, gva_len=100),
    C("B-owner-tclaim", [("tclaim", None)], bps=100, gva_owner="default", uva_seed=SEED),
    C("B-owner-mhbuy", [("mhbuy3", MH)], bps=100, gva_owner="default"),
    # --- C: admin gates and admin effects ---
    C("C-same-start", [("admin", (20, 49, 1, 0, 0, 10, "imint", "payer"))], bps=100),
    C("C-new-end-tclaim", [("admin", (20, 40, 1, 0, 0, 10, "imint", "payer")), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("C-start-wipe-tclaim-sync", [("admin", (30, 59, 1, 0, 0, 10, "imint", "payer")), ("tclaim", None), ("sync", None)], bps=100, uva_seed=SEED),
    C("C-supply-day0-tclaim", [("admin", (20, 49, 1, 0, 2000, 10, "imint", "payer")), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("C-supply-all-tclaim", [("admin", (20, 49, 1, 30, 500, 10, "imint", "payer")), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("C-midrange-zero-tclaim", [("admin", (20, 49, 1, 7, 777, 25, "imint", "payer")), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("C-start-past", [("admin", (5, 49, 1, 0, 0, 10, "imint", "payer"))], bps=100),
    C("C-end-past", [("admin", (20, 5, 1, 0, 0, 10, "imint", "payer"))], bps=100),
    C("C-end-before-start", [("admin", (25, 22, 1, 0, 0, 10, "imint", "payer"))], bps=100),
    C("C-range-large", [("admin", (25, 55, 1, 0, 0, 10, "imint", "payer"))], bps=100),
    C("C-supply-finished", [("admin", (0, 0, 1, 0, 100, 60, "imint", "payer"))], bps=100),
    C("C-day-after-end", [("admin", (20, 25, 1, 7, 100, 10, "imint", "payer"))], bps=100),
    C("C-day-active", [("admin", (20, 49, 1, 3, 100, 25, "imint", "payer"))], bps=100),
    C("C-outsider", [("admin", (20, 49, 1, 0, 0, 10, "imint", "outsider"))], bps=100),
    C("C-unsigned", [("admin", (20, 49, 1, 0, 0, 10, "imint", "unsigned"))], bps=100),
    C("C-mint-rotate", [("admin", (20, 49, 1, 0, 0, 10, "quote", "payer")), ("tclaim", None), ("admin", (20, 49, 1, 0, 0, 10, "imint", "payer")), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("C-admin-boost", [("admin", (20, 49, 1, 0, 2000, 10, "imint", "payer")), VQ, ("boost", BST)], bps=100),
    C("C-admin-mhbuy", [("admin", (20, 49, 1, 0, 2000, 10, "imint", "payer")), ("mhbuy3", MH)], bps=100),
    # --- D: claim lifecycle ---
    C("D-claim-after-mhbuy", [("mhbuy3", MH), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("D-claim-after-boost", [VQ, ("boost", BST), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("D-claim-after-swp", [("swp22", None), ("swc22", None), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("D-claim-ga-absent", [("tclaim", None)], bps=100, gata=False, uva_seed=SEED),
    C("D-claim-ga-empty", [("tclaim", None)], bps=100, gata_amt=0, uva_seed=SEED),
    C("D-claim-uata-absent", [("tclaim", None)], bps=100, uata=False, uva_seed=SEED),
    C("D-claim-mint-mismatch", [("tclaim", None)], bps=100, gva_seed=(20, 49, 1, 1000, 100, ZEROPK), uva_seed=SEED),
    # --- E: sync lifecycle ---
    C("E-sync-after-claim-admin", [("tclaim", None), ("admin", (30, 59, 1, 0, 0, 10, "imint", "payer")), ("sync", None)], bps=100, uva_seed=SEED),
    C("E-sync-absent-gva", [("sync", None)], bps=100, gva=False, uva_seed=SEED_LAST10),
    C("E-sync-zeroed-gva", [("sync", None)], bps=100, gva_seed=(0, 0, 0, 0, 0, IMINT), uva_seed=SEED_LAST10),
    # --- F: UVA close lifecycle ---
    C("F-close-seeded", [("close", None)], bps=100, uva_seed=SEED),
    C("F-close-then-tclaim", [("close", None), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("F-close-then-mhbuy", [("close", None), ("mhbuy3", MH)], bps=100, uva_seed=SEED),
    C("F-close-mhbuy-tclaim", [("close", None), ("mhbuy3", MH), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("F-close-init-tclaim", [("close", None), ("init", None), ("tclaim", None)], bps=100, uva_seed=SEED),
    C("F-close-other", [("close_other", None)], bps=100, uva_seed=SEED),
    C("F-close-unsigned", [("close_unsigned", None)], bps=100, uva_seed=SEED),
    C("F-close-boost", [("close", None), VQ, ("boost", BST)], bps=100, uva_seed=SEED),
    # --- G: GVA-blind chain legs ---
    C("G-absent-dep-wd", [("dep", DEP), ("wd", WD)], bps=100, gva=False),
    C("G-admin-mhbuy-boost", [("admin", (20, 49, 1, 0, 2000, 10, "imint", "payer")), ("mhbuy3", MH), VQ, ("boost", BST)], bps=100),
    C("G-zeroed-mhsell", [("mhsell3", MH)], bps=100, gva_seed=(0, 0, 0, 0, 0, IMINT)),
]


def apply_setup(h, case):
    if case.get("flags"):
        for name, mode in case["flags"].items():
            if mode:
                flag_pool(h, POOLKEYS[name], mode)
    if case.get("gmayhem") is not None or case.get("gcashback") is not None:
        a = h.vm.get_account(CONFIG_KEY)
        d = bytearray(a.data)
        if case.get("gmayhem") is not None:
            d[417] = case["gmayhem"]
        if case.get("gcashback") is not None:
            d[642] = case["gcashback"]
        h.vm.set_account(CONFIG_KEY, Account(a.lamports, bytes(d), a.owner))
    if case.get("pool_len") is not None:
        n = case["pool_len"]
        a = h.vm.get_account(pool)
        d = bytes(a.data)
        nd = d[:n].ljust(n, b"\0") if n > len(d) else d[:n]
        h.vm.set_account(pool, Account(a.lamports, nd, a.owner))
    if case.get("cfg_len") is not None:
        n = case["cfg_len"]
        a = h.vm.get_account(CONFIG_KEY)
        h.vm.set_account(CONFIG_KEY, Account(a.lamports, bytes(a.data)[:n], a.owner))
    if case.get("gva_len") is not None:
        n = case["gva_len"]
        a = h.vm.get_account(GVOL)
        if a is not None:
            h.vm.set_account(GVOL, Account(a.lamports, bytes(a.data)[:n], a.owner))
    if case.get("destb2_seed") is not None:
        h.vm.set_account(DEST_SPL_B2, Account(2039280, token(BASE2, PUMPVAULT, case["destb2_seed"], False), TOKEN))
    if case.get("seed_creator_ata") is not None:
        amt, lamp = case["seed_creator_ata"]
        h.vm.set_account(CREATOR_ATA, Account(lamp, token(quote, CREATOR_VAULT, amt, True), TOKEN))
    if case.get("pool_disc0"):
        a = h.vm.get_account(pool)
        d = bytearray(a.data)
        d[0:8] = bytes(8)
        h.vm.set_account(pool, Account(a.lamports, bytes(d), a.owner))
    if case.get("extacc") == "random":
        h.vm.set_account(EXTKEY, Account(10 ** 9, bytes([7]) * 100, PROGRAM))
    if case.get("out_lamports") is not None:
        h.vm.set_account(OUTSIDER_KEY, Account(case["out_lamports"], b"", Pubkey.default()))


def run_case(case, image_name, binary):
    h = setup_vm(binary, case)
    routes = {"buy": build_route(h, False, case.get("plain", False)),
              "sell": build_route(h, True, case.get("plain", False))}
    apply_setup(h, case)
    out = []
    for step in case["steps"]:
        kind = step[0]
        args = step[1] if len(step) > 1 else None
        if kind == "cpatch":
            target, spec = args
            spec = dict(spec)
            if target == "config" and spec.get("boost_auth") == "PAYER":
                spec["boost_auth"] = PAYER_KEY
            args = (target, spec)
        rec = do_step(h, kind, args, routes)
        rec["case"] = case["label"]
        rec["image"] = image_name
        rec["step"] = kind
        out.append(rec)
    return out


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


def main():
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
        base = surface(per_image["original"])
        divergent = (surface(per_image["control"]) != base
                     or surface(per_image["candidate"]) != base)
        check(surface(per_image["control"]) == surface(per_image["candidate"]),
              f"{case['label']}: control and candidate surfaces differ")
        for image_name in IMAGES:
            for rec in per_image[image_name]:
                if rec["error"] is not None:
                    for k, b in rec["before"].items():
                        if k in (str(PAYER_KEY), str(OUTSIDER_KEY)):
                            continue
                        check(rec["after"][k] == b, f"{case['label']}/{image_name}: rollback violated for {k}")
        report_cases.append({"label": case["label"],
                             "divergent": divergent,
                             "steps": [s[0] for s in case["steps"]],
                             "summaries": {image_name: [summarize(rec, rec["step"]) for rec in per_image[image_name]]
                                           for image_name in IMAGES},
                             "error_sites": {image_name: [r["site"] for r in per_image[image_name]] for image_name in IMAGES}})
        print(f"OK {case['label']} ({len(case['steps'])} steps x 3 images, divergent={divergent})")
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
              "input_sha256": {k: IMAGE_SHA[k] for k, v in IMAGES.items()},
              "parts": parts, "cases": report_cases,
              "images": {k: IMAGE_SHA[k] for k, v in IMAGES.items()}}
    with gzip.open(OUT / "runtime" / "report.json.gz", "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(report, indent=2))
    print(f"cases={len(CASES)} receipts={len(receipts)} parts={len(parts)}")
    for p in parts:
        print(f"  {p['file']} {p['count']} receipts {p['bytes']} bytes")
    print("NEXT: write verify.py and README.md, then regenerate MANIFEST.json")
    print("ADDRESSES for verify.py:")
    for name, key in [("POOL", pool), ("POOL2", POOL2), ("P3", P3),
                      ("CONFIG_KEY", CONFIG_KEY), ("FEECONFIG", feeconfig),
                      ("VOLUME", volume), ("GVOL", GVOL), ("EXTKEY", EXTKEY),
                      ("VAULTQUOTE", vaultquote), ("U3", U3),
                      ("USERQUOTE", userquote), ("USERBASE", userbase),
                      ("PROTO22", PROTO22), ("CREAT22", CREAT22),
                      ("QUOTE", quote), ("BB22", BB22), ("WDEST", WDEST)]:
        print(f"  {name} = {key}")


if __name__ == "__main__":
    main()
