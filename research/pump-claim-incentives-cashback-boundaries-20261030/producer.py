#!/usr/bin/env python3
"""Pump Main claim handlers: claim_token_incentives, claim_cashback and claim_cashback_v2,
original vs rebuild.

claim_token_incentives runs the shared volume-accumulator worker with zero new volume
(roll-over of the user's last active day into total_unclaimed_tokens), then moves
total_unclaimed_tokens from the GlobalVolumeAccumulator's incentive ATA to the user's ATA
(created with init_if_needed) with a transfer_checked signed by the accumulator PDA, then
record_claim. claim_cashback (v1) pays the UserVolumeAccumulator's lamports above
rent(data_len) to `user`; claim_cashback_v2 does the same for the native quote mint and, for an
SPL / Token-2022 quote, moves the whole balance of the accumulator's quote ATA to a token
account owned by `user`.

The repository harnesses for these handlers (scripts/pump_claim_token_incentives_differential.py,
pump_claim_boundary_differential.py, pump_claim_panic_differential.py,
pump_cashback_differential.py) load `research/imported-lab/...curve-fresh-trades-v3-signed-
surfpool.json`, which is not in the git tree, so they cannot be rerun. This packet builds every
account synthetically from the IDL layout. scripts/pump_volume_sync_differential.py already
varies the worker's day arithmetic through sync_user_volume_accumulator; here the cases target
what only the claim handlers do: the token transfer and its account constraints, record_claim,
the overflow/truncation/panic exits reached from a claim, the cashback rent floor and the
v2 token branch's checks.

Only the Pump image is loaded (upgradeable loader layout). System, SPL Token, Token-2022 and
ATA are LiteSVM built-ins. All state is synthetic, keys come from fixed seeds, the clock is
fixed per case, and there is no network. The full initial account set and instruction list of
every case is written to runtime/plan.json.gz, so verify.py replays without the repository.

Usage:
  python3 producer.py --root <repo> --images '{"original": "...", "candidate": "..."}' --out <packet dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
PAYER_SEED = bytes([233]) * 32
PAYER = Keypair.from_seed(PAYER_SEED).pubkey()
USER = Pubkey(bytes([70]) * 32)
USER_B = Pubkey(bytes([71]) * 32)
INCENTIVE = Keypair.from_seed(bytes([72]) * 32).pubkey()
OTHER_MINT = Keypair.from_seed(bytes([73]) * 32).pubkey()
QUOTE = Keypair.from_seed(bytes([74]) * 32).pubkey()
DAY = 86_400
START = 1_800_000_000
U64 = 2**64 - 1
GVA_LEN = 600
UVA_LEN = 137

IX = {'claim_token_incentives': bytes.fromhex('1004471ccc01281b'),
      'claim_cashback': bytes.fromhex('253a237ebe35e4c5'),
      'claim_cashback_v2': bytes.fromhex('7af3cc415e741d37')}
IX_ACCOUNTS = {'claim_token_incentives': 12, 'claim_cashback': 5, 'claim_cashback_v2': 10}
GVA_DISC = bytes.fromhex('ca2af62b8ebe1eff')
UVA_DISC = bytes.fromhex('56ff700e66359afa')

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
EVENT_AUTHORITY = pda([b'__event_authority'])
GVA = pda([b'global_volume_accumulator'])


def rent(n):
    return (128 + n) * 6960


def uva_of(user):
    return pda([b'user_volume_accumulator', bytes(user)])


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


def mint_data(decimals):
    d = bytearray(82)
    struct.pack_into('<Q', d, 36, 10**15)
    d[44] = decimals
    d[45] = 1
    return bytes(d)


def token_data(mint, owner, amount, state=1):
    d = bytearray(165)
    d[:32] = bytes(mint)
    d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount)
    d[108] = state
    return bytes(d)


def gva_data(start=START, end=START + 10 * DAY, secs=DAY, mint=INCENTIVE, supply=None, volumes=None, length=GVA_LEN):
    d = bytearray(GVA_DISC + struct.pack('<qqq', start, end, secs) + bytes(mint))
    d += struct.pack('<30Q', *(supply or [0] * 30)) + struct.pack('<30Q', *(volumes or [0] * 30))
    return bytes(d + bytes(max(0, length - len(d))))[:length]


def uva_data(user=USER, needs_claim=1, unclaimed=0, claimed=0, volume=0, last=0, has_claimed=0,
             cashback=0, cashback_claimed=0, stable=0, stable_claimed=0, length=UVA_LEN):
    d = UVA_DISC + bytes(user) + struct.pack('<BQQQqBQQQQ', needs_claim, unclaimed, claimed, volume, last,
                                             has_claimed, cashback, cashback_claimed, stable, stable_claimed)
    return bytes(d + bytes(max(0, length - len(d))))[:length]


UVA_FIELDS = ('needs_claim', 'total_unclaimed_tokens', 'total_claimed_tokens', 'current_sol_volume',
              'last_update_timestamp', 'has_total_claimed_tokens', 'cashback_earned', 'total_cashback_claimed',
              'stable_cashback_earned', 'total_stable_cashback_claimed')


def decode_uva(hexdata):
    d = bytes.fromhex(hexdata)
    if len(d) < 106 or d[:8] != UVA_DISC:
        return None
    return dict(zip(UVA_FIELDS, struct.unpack_from('<BQQQqBQQQQ', d, 40)))


# ---- plan: cases are pure data (accounts + instruction list) ----

def acct(key, lamports, owner=SYSTEM, data=b''):
    return [str(key), lamports, str(owner), data.hex()]


def ix(kind, keys):
    return {'program': str(PROGRAM), 'data_hex': IX[kind].hex(),
            'metas': [[str(k), k == PAYER, w] for k, w in keys]}


def claim_ti(user=USER, mint=INCENTIVE, tprog=TOKEN, sub=None):
    keys = [(user, False), (ata(user, mint, tprog), True), (GVA, False), (ata(GVA, mint, tprog), True),
            (uva_of(user), True), (mint, False), (tprog, False), (SYSTEM, False), (ATA_PROGRAM, False),
            (EVENT_AUTHORITY, False), (PROGRAM, False), (PAYER, True)]
    for i, k in (sub or {}).items():
        keys[i] = (k, keys[i][1])
    return ix('claim_token_incentives', keys)


def claim_cb(user=USER, sub=None):
    keys = [(user, True), (uva_of(user), True), (SYSTEM, False), (EVENT_AUTHORITY, False), (PROGRAM, False)]
    for i, k in (sub or {}).items():
        keys[i] = (k, keys[i][1])
    return ix('claim_cashback', keys)


def claim_cb2(user=USER, mint=WSOL, tprog=TOKEN, dest=None, sub=None):
    keys = [(user, True), (uva_of(user), True), (mint, False), (tprog, False), (ATA_PROGRAM, False),
            (ata(uva_of(user), mint, tprog), True), (dest or ata(user, mint, tprog), True), (SYSTEM, False),
            (EVENT_AUTHORITY, False), (PROGRAM, False)]
    for i, k in (sub or {}).items():
        keys[i] = (k, keys[i][1])
    return ix('claim_cashback_v2', keys)


def plan():
    cases = []

    def add(name, note, accounts, ixs, ts):
        cases.append({'case': name, 'note': note, 'accounts': [acct(PAYER, 10**12)] + accounts,
                      'instructions': ixs, 'unix_timestamp': ts})

    # ---------------- claim_token_incentives ----------------
    def ti_state(tprog=TOKEN, gva=None, uva=None, pool=10**12, user_ata=False, decimals=6, extra=()):
        out = [acct(INCENTIVE, 10**9, tprog, mint_data(decimals)),
               acct(GVA, rent(GVA_LEN), PROGRAM, gva if gva is not None else gva_data()),
               acct(ata(GVA, INCENTIVE, tprog), rent(165), tprog, token_data(INCENTIVE, GVA, pool)),
               acct(USER, 10**9)]
        if uva is not None:
            out.append(acct(uva_of(USER), rent(UVA_LEN), PROGRAM, uva))
        if user_ata:
            out.append(acct(ata(USER, INCENTIVE, tprog), rent(165), tprog, token_data(INCENTIVE, USER, 7)))
        return out + list(extra)

    sup = [1_000_000] * 30
    vol = [100] * 30
    day0, day1 = START + 10, START + DAY + 10
    g = gva_data(supply=sup, volumes=vol)
    for tag, tp in (('spl', TOKEN), ('t22', TOKEN22)):
        add(f'ti-{tag}-rollover-50pct', 'last on day 0 with 50/100 of day volume, now day 1: 500,000 units; user ATA created',
            ti_state(tp, g, uva_data(volume=50, last=day0)), [claim_ti(tprog=tp)], day1)
        add(f'ti-{tag}-rollover-existing-ata', 'as rollover-50pct, user ATA already holds 7 units',
            ti_state(tp, g, uva_data(volume=50, last=day0), user_ata=True), [claim_ti(tprog=tp)], day1)
        add(f'ti-{tag}-pool-short-by-1', 'owed 500,000; incentive ATA holds 499,999',
            ti_state(tp, g, uva_data(volume=50, last=day0), pool=499_999), [claim_ti(tprog=tp)], day1)
    add('ti-pool-exact', 'owed 500,000; incentive ATA holds exactly 500,000',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0), pool=500_000), [claim_ti()], day1)
    add('ti-same-day-no-rollover', 'last and now both on day 0: nothing owed, "No tokens to claim"',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0)), [claim_ti()], day0 + 100)
    add('ti-before-start', 'now before start_time; stored claimed 9 / has_claimed 1 with last before start are reset',
        ti_state(TOKEN, g, uva_data(volume=50, last=START - 500, claimed=9, has_claimed=1)), [claim_ti()], START - 100)
    add('ti-before-start-with-unclaimed', 'now before start_time; stored unclaimed 1,234 is still paid',
        ti_state(TOKEN, g, uva_data(unclaimed=1_234, last=START - 500)), [claim_ti()], START - 100)
    add('ti-day-volume-zero', 'global volume of the last day is 0: no roll-over, stored volume kept',
        ti_state(TOKEN, gva_data(supply=sup), uva_data(volume=50, last=day0)), [claim_ti()], day1)
    add('ti-user-volume-zero', 'user volume 0, day volume 100: returns before roll-over',
        ti_state(TOKEN, g, uva_data(volume=0, last=day0)), [claim_ti()], day1)
    add('ti-rounding-down', 'user 1 / day 3 of supply 1,000,000: floor 333,333',
        ti_state(TOKEN, gva_data(supply=sup, volumes=[3] * 30), uva_data(volume=1, last=day0)), [claim_ti()], day1)
    add('ti-result-u64max', 'user volume u64::MAX, supply u64::MAX, day volume u64::MAX: exactly u64::MAX units',
        ti_state(TOKEN, gva_data(supply=[U64] * 30, volumes=[U64] * 30), uva_data(volume=U64, last=day0), pool=U64),
        [claim_ti()], day1)
    add('ti-truncation', 'user volume 2, day volume 1, supply u64::MAX: product/volume > u64 -> Truncation',
        ti_state(TOKEN, gva_data(supply=[U64] * 30, volumes=[1] * 30), uva_data(volume=2, last=day0)), [claim_ti()], day1)
    add('ti-unclaimed-add-overflow', 'stored unclaimed u64::MAX plus a roll-over of 500,000',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0, unclaimed=U64)), [claim_ti()], day1)
    add('ti-claimed-add-overflow', 'stored claimed u64::MAX - 10, owed 500,000: transfer then record_claim unwrap',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0, claimed=U64 - 10, has_claimed=1)), [claim_ti()], day1)
    add('ti-claimed-add-max', 'stored claimed u64::MAX - 500,000, owed 500,000: claimed reaches u64::MAX',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0, claimed=U64 - 500_000, has_claimed=1)), [claim_ti()], day1)
    add('ti-last-after-end-day', 'end = start + 2 days; last on day 3 (> end_day): no roll-over, stored unclaimed 77 paid',
        ti_state(TOKEN, gva_data(end=START + 2 * DAY, supply=sup, volumes=vol),
                 uva_data(volume=50, last=START + 3 * DAY + 5, unclaimed=77)), [claim_ti()], START + 4 * DAY)
    add('ti-now-after-end', 'end = start + 2 days, now day 5: roll-over of day 0 still paid',
        ti_state(TOKEN, gva_data(end=START + 2 * DAY, supply=sup, volumes=vol), uva_data(volume=50, last=day0)),
        [claim_ti()], START + 5 * DAY)
    add('ti-secs-zero', 'seconds_in_a_day 0: day_index None, stored unclaimed 55 paid',
        ti_state(TOKEN, gva_data(secs=0, supply=sup, volumes=vol), uva_data(volume=50, last=day0, unclaimed=55)),
        [claim_ti()], day1)
    add('ti-current-day-30', 'synthetic range of 40 days (setter caps at 30); now on day 30 within range',
        ti_state(TOKEN, gva_data(end=START + 40 * DAY, supply=sup, volumes=vol), uva_data(volume=50, last=day0)),
        [claim_ti()], START + 30 * DAY + 10)
    add('ti-last-day-30', 'synthetic range of 40 days; last on day 30, now day 31 (roll-over reads index 30)',
        ti_state(TOKEN, gva_data(end=START + 40 * DAY, supply=sup, volumes=vol),
                 uva_data(volume=50, last=START + 30 * DAY + 10)), [claim_ti()], START + 31 * DAY + 10)
    add('ti-negative-now', 'clock unix_timestamp -1 with start_time > 0',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0, unclaimed=5)), [claim_ti()], -1)
    add('ti-negative-last', 'stored last_update_timestamp -1, now day 1',
        ti_state(TOKEN, g, uva_data(volume=50, last=-1, unclaimed=5)), [claim_ti()], day1)
    add('ti-stored-user-differs', 'stored user field is USER_B: overwritten with USER, claim proceeds',
        ti_state(TOKEN, g, uva_data(user=USER_B, volume=50, last=day0)), [claim_ti()], day1)
    add('ti-uva-absent', 'user volume accumulator does not exist',
        ti_state(TOKEN, g, None), [claim_ti()], day1)
    add('ti-uva-of-other-user', 'accumulator slot holds USER_B\'s PDA',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0),
                 extra=[acct(uva_of(USER_B), rent(UVA_LEN), PROGRAM, uva_data(user=USER_B, volume=50, last=day0))]),
        [claim_ti(sub={4: uva_of(USER_B)})], day1)
    add('ti-gva-mint-mismatch', 'mint account is OTHER_MINT while GlobalVolumeAccumulator.mint = INCENTIVE',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0),
                 extra=[acct(OTHER_MINT, 10**9, TOKEN, mint_data(6)),
                        acct(ata(GVA, OTHER_MINT), rent(165), TOKEN, token_data(OTHER_MINT, GVA, 10**12))]),
        [claim_ti(mint=OTHER_MINT)], day1)
    add('ti-token-program-mismatch', 'SPL mint passed with the Token-2022 program',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0)),
        [claim_ti(sub={1: ata(USER, INCENTIVE, TOKEN22), 3: ata(GVA, INCENTIVE), 6: TOKEN22})], day1)
    add('ti-user-ata-not-canonical', 'user_ata slot holds a non-ATA token account owned by USER',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0),
                 extra=[acct(USER_B, rent(165), TOKEN, token_data(INCENTIVE, USER, 0))]),
        [claim_ti(sub={1: USER_B})], day1)
    add('ti-pool-not-canonical', 'incentive slot holds a non-ATA token account owned by the accumulator PDA',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0),
                 extra=[acct(USER_B, rent(165), TOKEN, token_data(INCENTIVE, GVA, 10**12))]),
        [claim_ti(sub={3: USER_B})], day1)
    add('ti-pool-frozen', 'incentive ATA frozen',
        [a if a[0] != str(ata(GVA, INCENTIVE)) else acct(ata(GVA, INCENTIVE), rent(165), TOKEN,
                                                        token_data(INCENTIVE, GVA, 10**12, state=2))
         for a in ti_state(TOKEN, g, uva_data(volume=50, last=day0))], [claim_ti()], day1)
    add('ti-decimals-0', 'incentive mint with 0 decimals',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0), decimals=0), [claim_ti()], day1)
    add('ti-user-is-payer', 'user = fee payer (signer)',
        [acct(INCENTIVE, 10**9, TOKEN, mint_data(6)), acct(GVA, rent(GVA_LEN), PROGRAM, g),
         acct(ata(GVA, INCENTIVE), rent(165), TOKEN, token_data(INCENTIVE, GVA, 10**12)),
         acct(uva_of(PAYER), rent(UVA_LEN), PROGRAM, uva_data(user=PAYER, volume=50, last=day0))],
        [claim_ti(user=PAYER)], day1)
    add('ti-claim-twice', 'claim, claim in one transaction (second logs "No tokens to claim")',
        ti_state(TOKEN, g, uva_data(volume=50, last=day0)), [claim_ti(), claim_ti()], day1)
    add('ti-gva-short-543', 'GlobalVolumeAccumulator data 543 bytes (one short of the struct)',
        ti_state(TOKEN, gva_data(supply=sup, volumes=vol, length=543), uva_data(volume=50, last=day0)), [claim_ti()], day1)

    # ---------------- claim_cashback (v1) and v2 native ----------------
    R = rent(UVA_LEN)

    def cb_state(lamports, length=UVA_LEN, user_lamports=10**9, **kw):
        out = [acct(uva_of(USER), lamports, PROGRAM, uva_data(length=length, **kw))]
        if user_lamports:
            out.append(acct(USER, user_lamports))
        return out

    for tag, build in (('v1', lambda **k: claim_cb(**k)), ('v2n', lambda **k: claim_cb2(**k))):
        add(f'cb-{tag}-exact-rent', 'accumulator holds exactly rent(137): "No cashback to claim"',
            cb_state(R, cashback=5), [build()], START)
        add(f'cb-{tag}-rent-plus-1', 'accumulator holds rent(137) + 1: 1 lamport paid',
            cb_state(R + 1, cashback=5), [build()], START)
        add(f'cb-{tag}-below-rent', 'accumulator holds rent(137) - 1 (synthetic): saturates to 0',
            cb_state(R - 1, cashback=5), [build()], START)
        add(f'cb-{tag}-claimed-overflow', 'total_cashback_claimed u64::MAX - 1, amount 2',
            cb_state(R + 2, cashback=5, cashback_claimed=U64 - 1), [build()], START)
        add(f'cb-{tag}-claimed-reaches-max', 'total_cashback_claimed u64::MAX - 2, amount 2',
            cb_state(R + 2, cashback=5, cashback_claimed=U64 - 2), [build()], START)
        add(f'cb-{tag}-user-absent-below-rent', 'user account absent; amount rent(0) - 1',
            cb_state(R + rent(0) - 1, user_lamports=0), [build()], START)
        add(f'cb-{tag}-user-absent-exact-rent', 'user account absent; amount rent(0)',
            cb_state(R + rent(0), user_lamports=0), [build()], START)
        add(f'cb-{tag}-length-106', 'accumulator data 106 bytes (struct size), rent(106) + 1,000',
            cb_state(rent(106) + 1_000, length=106), [build()], START)
        add(f'cb-{tag}-length-105', 'accumulator data 105 bytes (one short)',
            cb_state(rent(105) + 1_000, length=105), [build()], START)
        add(f'cb-{tag}-twice', 'claim, claim in one transaction',
            cb_state(R + 9_999), [build(), build()], START)
    add('cb-v1-other-user-pda', 'v1: accumulator slot holds USER_B\'s PDA',
        cb_state(R + 1_000) + [acct(uva_of(USER_B), R + 1_000, PROGRAM, uva_data(user=USER_B))],
        [claim_cb(sub={1: uva_of(USER_B)})], START)
    add('cb-v2n-mint-is-wsol-t22-program', 'v2 native branch with quote_token_program = Token-2022 (unchecked)',
        cb_state(R + 1_000), [claim_cb2(tprog=TOKEN22)], START)

    # ---------------- claim_cashback_v2 token branch ----------------
    def tq_state(tprog=TOKEN, pool=5_000, dest=True, dest_owner=USER, pool_present=True, mint_owner=None, **kw):
        U = uva_of(USER)
        out = [acct(QUOTE, 10**9, mint_owner or tprog, mint_data(6)),
               acct(U, R, PROGRAM, uva_data(**kw)), acct(USER, 10**9)]
        if pool_present:
            out.append(acct(ata(U, QUOTE, tprog), rent(165), tprog, token_data(QUOTE, U, pool)))
        if dest:
            out.append(acct(ata(USER, QUOTE, tprog), rent(165), tprog, token_data(QUOTE, dest_owner, 1)))
        return out

    for tag, tp in (('spl', TOKEN), ('t22', TOKEN22)):
        add(f'cb-v2-{tag}-pays-balance', 'token quote: accumulator quote ATA 5,000 units moved to the user ATA',
            tq_state(tp, stable=5_000), [claim_cb2(mint=QUOTE, tprog=tp)], START)
        add(f'cb-v2-{tag}-pool-zero', 'token quote: accumulator quote ATA empty',
            tq_state(tp, pool=0), [claim_cb2(mint=QUOTE, tprog=tp)], START)
    add('cb-v2-spl-pool-absent', 'token quote: accumulator quote ATA does not exist',
        tq_state(pool_present=False), [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-spl-pool-u64max', 'token quote: pool holds u64::MAX (stable earned 0)',
        tq_state(pool=U64), [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-spl-stable-claimed-overflow', 'token quote: total_stable_cashback_claimed u64::MAX - 4,999, pays 5,000',
        tq_state(stable_claimed=U64 - 4_999), [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-bad-token-program', 'quote_token_program = System program (accumulator quote ATA derived with it)',
        tq_state(), [claim_cb2(mint=QUOTE, sub={3: SYSTEM, 5: ata(uva_of(USER), QUOTE, SYSTEM)})], START)
    add('cb-v2-bad-token-program-seeds', 'quote_token_program = System program, accumulator quote ATA of SPL Token',
        tq_state(), [claim_cb2(mint=QUOTE, sub={3: SYSTEM})], START)
    add('cb-v2-mint-owner-mismatch', 'SPL mint with quote_token_program = Token-2022',
        tq_state(TOKEN22, mint_owner=TOKEN), [claim_cb2(mint=QUOTE, tprog=TOKEN22)], START)
    add('cb-v2-recipient-other-owner', 'destination token account owned (token-level) by USER_B',
        tq_state(dest_owner=USER_B), [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-dest-absent', 'destination account does not exist (system-owned, empty)',
        tq_state(dest=False), [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-dest-non-ata', 'destination is a non-ATA token account owned by USER',
        tq_state(dest=False) + [acct(USER_B, rent(165), TOKEN, token_data(QUOTE, USER, 0))],
        [claim_cb2(mint=QUOTE, dest=USER_B)], START)
    add('cb-v2-pool-garbage', 'accumulator quote ATA slot holds 10 bytes of SPL-owned data',
        [a if a[0] != str(ata(uva_of(USER), QUOTE)) else acct(ata(uva_of(USER), QUOTE), rent(10), TOKEN, bytes(10))
         for a in tq_state()], [claim_cb2(mint=QUOTE)], START)
    add('cb-v2-native-then-token', 'v2 native claim then v2 token claim in one transaction',
        [a if a[0] != str(uva_of(USER)) else acct(uva_of(USER), R + 3_000, PROGRAM, uva_data(cashback=3_000, stable=5_000))
         for a in tq_state()], [claim_cb2(), claim_cb2(mint=QUOTE)], START)
    return [c for c in cases if c['case'] not in DROPPED]


# Variants trimmed to keep the packet at 60 cases (each repeats a path another case covers).
DROPPED = {'ti-t22-pool-short-by-1', 'ti-t22-rollover-existing-ata', 'ti-pool-exact', 'ti-decimals-0',
           'ti-user-volume-zero', 'ti-day-volume-zero', 'cb-v2n-length-105', 'cb-v2n-twice', 'cb-v2n-below-rent',
           'cb-v2n-user-absent-below-rent', 'cb-v2n-claimed-reaches-max', 'cb-v2n-length-106', 'cb-v2n-rent-plus-1',
           'cb-v2-t22-pool-zero'}


# ---- execution (verify.py imports this from the packet copy) ----

LOADERS = ('upgradeable',)


def load_vm(image):
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf, UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    return vm


FIXED = {PROGRAM, TOKEN, TOKEN22, ATA_PROGRAM, SYSTEM}
PANIC = 'Program log: panicked at '


def pump_messages(logs):
    """`msg!` lines logged while the Pump program itself is on top of the invoke stack."""
    stack, out = [], []
    for l in logs:
        parts = l.split(' ')
        if len(parts) == 4 and parts[0] == 'Program' and parts[2] == 'invoke':
            stack.append(parts[1])
        elif len(parts) >= 3 and parts[0] == 'Program' and parts[2] in ('success', 'failed:') and stack:
            stack.pop()
        elif (stack and stack[-1] == str(PROGRAM) and l.startswith('Program log: ')
              and not l.startswith('Program log: Instruction: ') and not l.startswith('Program log: AnchorError')
              and not l.startswith(PANIC)):
            out.append(l[13:])
    return out


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, START, 0, 0, c['unix_timestamp']))
    keys = set()
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.add(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    ixs = []
    for i in c['instructions']:
        metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['metas']]
        keys |= {m.pubkey for m in metas}
        ixs.append(Instruction(Pubkey.from_string(i['program']), bytes.fromhex(i['data_hex']), metas))
    payer = Keypair.from_seed(PAYER_SEED)
    tx = Transaction.new_signed_with_payer(ixs, payer.pubkey(), [payer], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = list(meta.logs())
    after = {}
    for key in sorted(keys - FIXED, key=str):
        a = vm.get_account(key)
        if a is not None and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), a.executable, bytes(a.data).hex()]
    for key in keys - FIXED:  # reset so the next case starts from its own state only
        vm.set_account(key, Account(0, b'', SYSTEM))
    return {'case': c['case'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'handler_messages': pump_messages(logs),
            'panic_messages': [l[len(PANIC):].split(':', 3)[-1] for l in logs if l.startswith(PANIC)],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader == 'upgradeable'
    vm = load_vm(image)
    return [run_case(vm, i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'events', 'handler_messages', 'panic_messages', 'inner_instructions',
            'accounts_after')
SITE = 'Program log: AnchorError thrown in '


def classify_logs(original, candidate):
    if len(original) != len(candidate):
        return [{'kind': 'line-count', 'original': len(original), 'candidate': len(candidate)}]
    out = []
    for a, b in zip(original, candidate):
        if a == b:
            continue
        if a.startswith(SITE) and b.startswith(SITE) and a.split('. ', 1)[1:] == b.split('. ', 1)[1:]:
            out.append({'kind': 'anchor-error-site', 'original': a[len(SITE):].split('. ')[0],
                        'candidate': b[len(SITE):].split('. ')[0]})
        elif a.startswith(PANIC) and b.startswith(PANIC):
            out.append({'kind': 'panic-site', 'original': a[len(PANIC):], 'candidate': b[len(PANIC):]})
        elif ' consumed ' in a and ' consumed ' in b:
            out.append({'kind': 'consumed', 'original': a, 'candidate': b})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


def outcome(r):
    if r['error']:
        for line in r['logs']:
            if 'Error Code: ' in line:
                return 'error:' + line.split('Error Code: ', 1)[1].split('.', 1)[0]
        if r['panic_messages']:
            return 'panic:' + r['panic_messages'][0].strip()
        return 'error:' + r['error']
    return 'ok:' + ('|'.join(r['handler_messages']) or 'paid')


def before_of(c, key):
    return next((a for a in c['accounts'] if a[0] == key), None)


def lamport_delta(c, r, key):
    b = before_of(c, key)
    return r['accounts_after'].get(key, [0])[0] - (b[1] if b else 0)


def token_amount(hexdata):
    d = bytes.fromhex(hexdata)
    return struct.unpack_from('<Q', d, 64)[0] if len(d) >= 165 else None


def token_delta(c, r, key):
    b = before_of(c, key)
    before = token_amount(b[3]) if b and len(b[3]) >= 330 else 0
    a = r['accounts_after'].get(key)
    after = token_amount(a[3]) if a and len(a[3]) >= 330 else 0
    return (after or 0) - (before or 0)


def watched(c):
    """(user, user volume accumulator, token destination) of the first instruction."""
    m = [k for k, _, _ in c['instructions'][0]['metas']]
    kind = next(n for n, d in IX.items() if d.hex() == c['instructions'][0]['data_hex'])
    if kind == 'claim_token_incentives':
        return m[0], m[4], m[1]
    if kind == 'claim_cashback':
        return m[0], m[1], None
    return m[0], m[1], m[6]


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        user, uva, dest = watched(c)
        row = {'case': c['case'], 'note': c['note'],
               'outcome': {'original': outcome(ro), 'candidate': outcome(rc)},
               'claim_events': {'original': len(ro['events']), 'candidate': len(rc['events'])},
               'user_lamport_delta': {'original': lamport_delta(c, ro, user), 'candidate': lamport_delta(c, rc, user)},
               'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                 'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
               'logs_equal': ro['logs'] == rc['logs'],
               'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
               'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]}
        if dest:
            row['destination_token_delta'] = {'original': token_delta(c, ro, dest), 'candidate': token_delta(c, rc, dest)}
        for name, r in (('original', ro), ('candidate', rc)):
            a = r['accounts_after'].get(uva)
            row.setdefault('user_volume_accumulator_after', {})[name] = decode_uva(a[3]) if a else None
        rows.append(row)
    outcomes, deltas, kinds = {}, {}, {}
    for r in rows:
        o = r['outcome']['original']
        outcomes[o] = outcomes.get(o, 0) + 1
        dk = str(r['compute_units']['original_minus_candidate'])
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    return {'case_count': len(rows),
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'outcome_mismatches': [r['case'] for r in rows if r['outcome']['original'] != r['outcome']['candidate']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_outcome': dict(sorted(outcomes.items())),
            'compute_unit_delta_counts': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'cases': rows}


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl_path = args.root / 'evidence/upstream/pump.json'
    idl = json.loads(idl_path.read_text())
    assert idl['address'] == str(PROGRAM)
    for name, disc in IX.items():  # discriminators and account counts must match the upstream IDL
        i = next(i for i in idl['instructions'] if i['name'] == name)
        assert bytes(i['discriminator']) == disc and len(i['accounts']) == IX_ACCOUNTS[name], name
    acc = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert acc['GlobalVolumeAccumulator'] == GVA_DISC and acc['UserVolumeAccumulator'] == UVA_DISC
    cases = plan()
    assert len(cases) <= 60 and len({c['case'] for c in cases}) == len(cases)
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main claim_token_incentives / claim_cashback / claim_cashback_v2: transfer and account '
                       'constraints, record_claim, overflow/truncation/panic exits, cashback rent floor, v2 token '
                       'branch; original vs rebuild; upgradeable loader; synthetic state; no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {},
              'idl_sha256': hashlib.sha256(idl_path.read_bytes()).hexdigest()}
    for loader in LOADERS:
        original = run_plan(images['original'], loader, cases)
        candidate = run_plan(images['candidate'], loader, cases)
        lines = []
        for ro, rc in zip(original, candidate):
            lines += [json.dumps({'loader': loader, 'image': 'original', **ro}, sort_keys=True, separators=(',', ':')),
                      json.dumps({'loader': loader, 'image': 'candidate', **rc}, sort_keys=True, separators=(',', ':'))]
        name = f'receipts-{loader}.jsonl.gz'
        write_gz(runtime / name, '\n'.join(lines) + '\n')
        report['receipts'][name] = {'count': len(lines),
                                    'sha256': hashlib.sha256((runtime / name).read_bytes()).hexdigest()}
        report['loaders'][loader] = summarize(cases, original, candidate)
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    for loader, s in report['loaders'].items():
        print(loader, json.dumps({k: s[k] for k in ('case_count', 'behavior_mismatches', 'outcome_mismatches',
                                                    'compute_units_equal_cases', 'logs_equal_cases',
                                                    'cases_by_outcome', 'compute_unit_delta_counts',
                                                    'log_difference_kinds')}, indent=1))


if __name__ == '__main__':
    main()
