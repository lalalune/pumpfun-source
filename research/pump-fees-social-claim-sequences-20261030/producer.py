#!/usr/bin/env python3
"""Pump Fees social-fee PDA lifecycle sequences on persistent state.

Every case runs a chain of transactions (create_social_fee_pda, lamport
deposits, claim_social_fee_pda, global setters, clock moves) on ONE persistent
LiteSVM per image, so a later step sees the state left by an earlier one. The
existing scripts/fees_social_*_differential.py suites run each claim or create
once on freshly synthesized state.

usage: producer.py --root <repo> --images '{"original": p, "candidate": p}' --out <packet dir>
Deterministic: fixed key seeds, fixed clock values, no paths in the output.
"""
import argparse, gzip, hashlib, json, pathlib, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
SYSTEM = Pubkey.default()
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b'fee-program-global'], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
NOW = 1700000000
SEEDS = {'AUTH': 223, 'OTHER': 224, 'PAYER': 225, 'THIRD': 226}
KP = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in SEEDS.items()}
A, O, T = KP['AUTH'].pubkey(), KP['OTHER'].pubkey(), KP['THIRD'].pubkey()
ZERO = Pubkey.default()
USERS = {'U1': ('12345', 0), 'U2': ('12345', 1), 'U3': ('67890', 0)}


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


GLOBAL_DISC = disc('FeeProgramGlobal', 'account')
SOCIAL_DISC = disc('SocialFeePda', 'account')


def social(u):
    uid, platform = USERS[u]
    return Pubkey.find_program_address([b'social-fee-pda', uid.encode(), bytes([platform])], PROGRAM)[0]


def global_data(authority, flags=0, social_authority=None, rate=60):
    sa = social_authority if social_authority is not None else authority
    return GLOBAL_DISC + bytes([GLOBAL_BUMP]) + bytes(authority) + bytes([flags]) + bytes(sa) + rate.to_bytes(8, 'little') + bytes(256)


def decode_social(d):
    # SocialFeePda: disc, bump, version, user_id (string), platform, total_claimed, last_claimed, total_stable_claimed, reserved
    if len(d) < 14 or d[:8] != SOCIAL_DISC:
        return None
    n = struct.unpack_from('<I', d, 10)[0]
    o = 14 + n
    if o + 25 > len(d):
        return {'fits': False}
    total, last, stable = struct.unpack_from('<QQQ', d, o + 1)
    return {'bump': d[8], 'version': d[9], 'user_id': d[14:o].decode('utf-8', 'replace'), 'platform': d[o],
            'total_claimed': total, 'last_claimed': last, 'total_stable_claimed': stable,
            'nonzero_reserved': sum(1 for b in d[o + 25:] if b)}


def m(key, signer, writable):
    return [str(key), signer, writable]


def create(u, payer='AUTH'):
    uid, platform = USERS[u]
    arg = len(uid).to_bytes(4, 'little') + uid.encode() + bytes([platform])
    return {'data_hex': (disc('create_social_fee_pda') + arg).hex(),
            'accounts': [m(KP[payer].pubkey(), True, True), m(social(u), False, True), m(SYSTEM, False, False),
                         m(GLOBAL, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [payer]


def claim(u, authority='AUTH', recipient=None):
    uid, platform = USERS[u]
    arg = len(uid).to_bytes(4, 'little') + uid.encode() + bytes([platform])
    r = recipient if recipient is not None else T
    return {'data_hex': (disc('claim_social_fee_pda') + arg).hex(),
            'accounts': [m(r, False, True), m(social(u), False, True), m(GLOBAL, False, False),
                         m(KP[authority].pubkey(), True, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [authority]


def fund(u, lamports):
    # System Program transfer from the fee payer into the social PDA
    return {'program_id': str(SYSTEM), 'data_hex': (struct.pack('<I', 2) + lamports.to_bytes(8, 'little')).hex(),
            'accounts': [m(KP['PAYER'].pubkey(), True, True), m(social(u), False, True)]}, []


TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
COMPUTE_BUDGET = Pubkey.from_string('ComputeBudget111111111111111111111111111111')
TOKEN_RESERVE = 2039280  # rent-exempt minimum for a 165-byte account


def ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA_PROGRAM)[0]


def token_data(mint, owner, amount):
    td = bytearray(165)
    td[:32] = bytes(mint); td[32:64] = bytes(owner); td[64:72] = amount.to_bytes(8, 'little'); td[108] = 1
    if mint == WSOL:
        td[109:113] = (1).to_bytes(4, 'little'); td[113:121] = TOKEN_RESERVE.to_bytes(8, 'little')
    return bytes(td)


def mint_data(decimals):
    md = bytearray(82); md[44] = decimals; md[45] = 1
    return bytes(md)


def claim_v2(u, quote, authority='AUTH', recipient=None):
    uid, platform = USERS[u]
    arg = len(uid).to_bytes(4, 'little') + uid.encode() + bytes([platform])
    r = recipient if recipient is not None else T
    cb = {'program_id': str(COMPUTE_BUDGET), 'data_hex': (bytes([2]) + (1400000).to_bytes(4, 'little')).hex(), 'accounts': []}
    ix = {'data_hex': (disc('claim_social_fee_pda_v2') + arg).hex(),
          'accounts': [m(r, False, True), m(social(u), False, True), m(quote, False, True), m(ata(social(u), quote), False, True), m(ata(r, quote), False, True),
                       m(TOKEN, False, False), m(ATA_PROGRAM, False, False), m(GLOBAL, False, False), m(KP[authority].pubkey(), True, False),
                       m(SYSTEM, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}
    return [cb, ix], [authority]


def g_setter(name, signer, arg):
    return {'data_hex': (disc(name) + arg).hex(),
            'accounts': [m(KP[signer].pubkey(), True, True), m(GLOBAL, False, True), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def set_social(signer, new):
    return g_setter('set_social_claim_authority', signer, bytes(new))


def set_authority(signer, new):
    return g_setter('set_authority', signer, bytes(new))


def set_flags(signer, v):
    return g_setter('set_disable_flags', signer, bytes([v]))


def set_rate(signer, v):
    return g_setter('set_claim_rate_limit', signer, v.to_bytes(8, 'little'))


def tx(label, *ixs, at=None):
    signers = []
    for _, s in ixs:
        for x in s:
            if x not in signers:
                signers.append(x)
    flat = []
    for i, _ in ixs:
        flat += i if isinstance(i, list) else [i]
    out = {'label': label, 'instructions': flat, 'signers': signers}
    if at is not None:
        out['clock_unix'] = at
    return out


def acct(key, data, owner=PROGRAM, lamports=10**9):
    return {'pubkey': str(key), 'lamports': lamports, 'owner': str(owner), 'data_hex': data.hex()}


F = 1000000  # deposit size used by most steps


def cases():
    out = []

    def S(name, steps, flags=0, rate=60, social_authority=None, prefund=None, tokens=None):
        initial = [acct(GLOBAL, global_data(A, flags, social_authority, rate))]
        for u, lam in (prefund or {}).items():
            initial.append(acct(social(u), b'', owner=SYSTEM, lamports=lam))
        case = {'name': name, 'family': name.split('-')[0], 'clock_unix': NOW, 'initial': initial, 'steps': steps}
        if tokens:
            # tokens: {mint: amount held by U1's social PDA ATA}; recipient THIRD's ATA exists with 0
            watch = []
            for mint, amount in tokens.items():
                initial.append(acct(mint, mint_data(9 if mint == WSOL else 6), owner=TOKEN))
                src, dst = ata(social('U1'), mint), ata(T, mint)
                initial.append(acct(src, token_data(mint, social('U1'), amount), owner=TOKEN, lamports=TOKEN_RESERVE + (amount if mint == WSOL else 0)))
                initial.append(acct(dst, token_data(mint, T, 0), owner=TOKEN, lamports=TOKEN_RESERVE))
                watch += [str(src), str(dst)]
            case['watch'] = watch
        out.append(case)

    # ---- l: lifecycle and rate-limit windows ----
    S('l-create-then-claim-empty', [tx('create U1', create('U1')), tx('claim U1 empty', claim('U1')), tx('claim U1 empty +61', claim('U1'), at=NOW + 61)])
    S('l-claim-before-create', [tx('claim U1 missing', claim('U1')), tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim U1', claim('U1'))])
    S('l-rate-window-60', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim 1', claim('U1')),
                           tx('fund', fund('U1', F)), tx('claim +0', claim('U1')), tx('claim +59', claim('U1'), at=NOW + 59),
                           tx('claim +60', claim('U1'), at=NOW + 60), tx('claim +61', claim('U1'), at=NOW + 61),
                           tx('fund', fund('U1', F)), tx('claim +120', claim('U1'), at=NOW + 120), tx('claim +121', claim('U1'), at=NOW + 121), tx('claim +122', claim('U1'), at=NOW + 122)])
    S('l-total-accumulates', [tx('create U1', create('U1')), tx('fund 1', fund('U1', 1)), tx('claim 1', claim('U1')),
                              tx('fund 2', fund('U1', 2 * F)), tx('claim 2', claim('U1'), at=NOW + 100),
                              tx('fund 3', fund('U1', 3 * F)), tx('claim 3', claim('U1'), at=NOW + 200),
                              tx('claim nothing', claim('U1'), at=NOW + 300)])
    S('l-empty-claim-does-not-start-window', [tx('create U1', create('U1')), tx('claim empty', claim('U1')), tx('fund', fund('U1', F)),
                                        tx('claim +30', claim('U1'), at=NOW + 30), tx('claim +61', claim('U1'), at=NOW + 61)])
    S('l-failed-claim-keeps-last', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim t', claim('U1')),
                                    tx('fund', fund('U1', F)), tx('claim +10 rate-limited', claim('U1'), at=NOW + 10), tx('claim +61', claim('U1'), at=NOW + 61)])
    S('l-create-twice', [tx('create U1', create('U1')), tx('create U1 again', create('U1')), tx('fund', fund('U1', F)),
                         tx('claim', claim('U1')), tx('create U1 after claim', create('U1', payer='OTHER'))])
    S('l-prefunded-address', [tx('create U1 on prefunded', create('U1')), tx('claim', claim('U1')), tx('claim +61', claim('U1'), at=NOW + 61)], prefund={'U1': 5 * F})
    S('l-prefunded-address-1-lamport', [tx('create U1 on 1 lamport', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1'))], prefund={'U1': 1})
    S('l-fund-1-lamport', [tx('create U1', create('U1')), tx('fund 1', fund('U1', 1)), tx('claim 1 lamport', claim('U1'))])

    # ---- p: independence across users / platforms ----
    S('p-platforms-independent', [tx('create U1', create('U1')), tx('create U2', create('U2')), tx('fund U1', fund('U1', F)), tx('fund U2', fund('U2', 2 * F)),
                                  tx('claim U1', claim('U1')), tx('claim U2 same second', claim('U2')), tx('claim U1 again', claim('U1')), tx('claim U2 +61', claim('U2'), at=NOW + 61)])
    S('p-users-independent-same-tx', [tx('create U1', create('U1')), tx('create U3', create('U3')), tx('fund U1+U3', fund('U1', F), fund('U3', F)),
                                      tx('claim U1 + claim U3', claim('U1'), claim('U3')), tx('claim U3', claim('U3'))])
    S('p-same-tx-create-two', [tx('create U1 + U2 + U3', create('U1'), create('U2'), create('U3')), tx('fund U2', fund('U2', F)), tx('claim U2', claim('U2'))])

    # ---- t: same-transaction ordering ----
    S('t-same-tx-create-fund-claim', [tx('create + fund + claim', create('U1'), fund('U1', F), claim('U1'))])
    S('t-same-tx-fund-then-claim', [tx('create U1', create('U1')), tx('fund + claim', fund('U1', F), claim('U1'))])
    S('t-same-tx-claim-then-fund', [tx('create U1', create('U1')), tx('claim + fund', claim('U1'), fund('U1', F)), tx('claim +61', claim('U1'), at=NOW + 61)])
    S('t-same-tx-double-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim + claim', claim('U1'), claim('U1')), tx('claim again', claim('U1'))])
    S('t-same-tx-claim-then-recipient-funds-pda', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim to PAYER + fund', claim('U1', recipient=KP['PAYER'].pubkey()), fund('U1', 7))])

    # ---- a: social claim authority transitions ----
    S('a-rotate-social-authority', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim by AUTH', claim('U1')),
                                    tx('social AUTH->OTHER', set_social('AUTH', O)), tx('fund', fund('U1', F)),
                                    tx('claim by AUTH +61', claim('U1'), at=NOW + 61), tx('claim by OTHER +61', claim('U1', 'OTHER'), at=NOW + 61)])
    S('a-same-tx-rotate-then-new-claims', [tx('create U1', create('U1')), tx('fund', fund('U1', F)),
                                           tx('social AUTH->OTHER + OTHER claims', set_social('AUTH', O), claim('U1', 'OTHER')), tx('AUTH claims +61', claim('U1'), at=NOW + 61)])
    S('a-same-tx-rotate-then-old-claims', [tx('create U1', create('U1')), tx('fund', fund('U1', F)),
                                           tx('social AUTH->OTHER + AUTH claims', set_social('AUTH', O), claim('U1')), tx('AUTH claims after rollback', claim('U1'))])
    S('a-same-tx-old-claims-then-rotate', [tx('create U1', create('U1')), tx('fund', fund('U1', F)),
                                           tx('AUTH claims + social AUTH->OTHER', claim('U1'), set_social('AUTH', O)), tx('fund', fund('U1', F)), tx('OTHER claims +61', claim('U1', 'OTHER'), at=NOW + 61)])
    S('a-global-authority-move-keeps-social', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('global AUTH->OTHER', set_authority('AUTH', O)),
                                               tx('OTHER claims', claim('U1', 'OTHER')), tx('AUTH claims', claim('U1'))])
    S('a-social-authority-distinct-from-admin', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('AUTH claims', claim('U1')),
                                                 tx('fund', fund('U1', F)), tx('THIRD claims +61', claim('U1', 'THIRD'), at=NOW + 61), tx('THIRD sets rate', set_rate('THIRD', 0))], social_authority=T)
    S('a-social-authority-zero', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('social -> zero', set_social('AUTH', ZERO)),
                                  tx('AUTH claims', claim('U1')), tx('social -> AUTH', set_social('AUTH', A)), tx('AUTH claims', claim('U1'))])
    S('a-authority-as-recipient', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim to AUTH (authority as recipient)', claim('U1', recipient=A))])

    # ---- r: global rate limit changes between claims ----
    S('r-rate-zero-same-second', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1')), tx('rate 0', set_rate('AUTH', 0)),
                                  tx('fund', fund('U1', F)), tx('claim same second', claim('U1')), tx('claim same second again', claim('U1'))])
    S('r-rate-raised-after-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1')), tx('rate 1000', set_rate('AUTH', 1000)),
                                    tx('fund', fund('U1', F)), tx('claim +61', claim('U1'), at=NOW + 61), tx('claim +1000', claim('U1'), at=NOW + 1000), tx('claim +1001', claim('U1'), at=NOW + 1001)])
    S('r-rate-lowered-after-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1')), tx('rate 1', set_rate('AUTH', 1)),
                                     tx('fund', fund('U1', F)), tx('claim +1', claim('U1'), at=NOW + 1), tx('claim +2', claim('U1'), at=NOW + 2)])
    S('r-rate-u64-max-after-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1')), tx('rate u64 max', set_rate('AUTH', 2**64 - 1)),
                                     tx('fund', fund('U1', F)), tx('claim +10^9', claim('U1'), at=NOW + 10**9)])
    S('r-rate-u64-max-first-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim first', claim('U1'))], rate=2**64 - 1)
    S('r-rate-i64-boundary', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim first', claim('U1')), tx('fund', fund('U1', F)),
                              tx('claim +2^31', claim('U1'), at=NOW + 2**31)], rate=2**63)

    # ---- c: clock moves ----
    S('c-clock-backwards', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim t', claim('U1')), tx('fund', fund('U1', F)),
                            tx('claim t-100', claim('U1'), at=NOW - 100), tx('claim t+61', claim('U1'), at=NOW + 61)])
    S('c-clock-negative-then-forward', [tx('create U1', create('U1'), at=-5), tx('fund', fund('U1', F)), tx('claim at -5', claim('U1')),
                                        tx('fund', fund('U1', F)), tx('claim at 54', claim('U1'), at=54), tx('claim at 56', claim('U1'), at=56)])
    S('c-clock-zero', [tx('create U1', create('U1'), at=0), tx('fund', fund('U1', F)), tx('claim at 0', claim('U1')), tx('fund', fund('U1', F)), tx('claim at 61', claim('U1'), at=61)])
    S('c-clock-zero-reclaim-in-window', [tx('create U1', create('U1'), at=0), tx('fund', fund('U1', F)), tx('claim at 0', claim('U1')), tx('fund', fund('U1', F)),
                                         tx('claim at 0 again', claim('U1')), tx('fund', fund('U1', F)), tx('claim at 10', claim('U1'), at=10), tx('fund', fund('U1', F)), tx('claim at 20', claim('U1'), at=20)])
    S('c-clock-negative-later-clocks', [tx('create U1', create('U1'), at=-5), tx('fund', fund('U1', F)), tx('claim at -5', claim('U1')), tx('fund', fund('U1', F)),
                                        tx('claim at 1700000000', claim('U1'), at=NOW), tx('claim at 2^62', claim('U1'), at=2**62), tx('claim at -1', claim('U1'), at=-1), tx('claim at 55', claim('U1'), at=55)])
    S('c-clock-negative-rate-zero', [tx('create U1', create('U1'), at=-5), tx('fund', fund('U1', F)), tx('claim at -5', claim('U1')), tx('rate 0', set_rate('AUTH', 0)), tx('fund', fund('U1', F)),
                                     tx('claim at 100', claim('U1'), at=100)])
    S('r-rate-max-then-reset', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim', claim('U1')), tx('rate u64 max', set_rate('AUTH', 2**64 - 1)), tx('fund', fund('U1', F)),
                                tx('claim +10', claim('U1'), at=NOW + 10), tx('rate 60', set_rate('AUTH', 60)), tx('claim +61', claim('U1'), at=NOW + 61)])

    # ---- f: disable flags toggled mid-sequence ----
    for bit in [1, 2, 4, 8, 16, 128]:
        S(f'f-flag-{bit}-toggle', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx(f'flags {bit}', set_flags('AUTH', bit)),
                                   tx('create U3 under flag', create('U3')), tx('claim U1 under flag', claim('U1')),
                                   tx('flags 0', set_flags('AUTH', 0)), tx('create U3', create('U3')), tx('claim U1', claim('U1'))])
    S('f-same-tx-disable-then-claim', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('flags 255 + claim', set_flags('AUTH', 255), claim('U1')), tx('claim', claim('U1'))])
    S('f-same-tx-claim-then-disable', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('claim + flags 255', claim('U1'), set_flags('AUTH', 255)), tx('fund', fund('U1', F)), tx('claim +61', claim('U1'), at=NOW + 61)])

    # ---- v: claim_social_fee_pda (v1, lamports) and claim_social_fee_pda_v2 (token path) on the same PDA ----
    UT = {USDC: 5000000}
    S('v-v2-stable-twice-window', [tx('create U1', create('U1')), tx('v2 usdc', claim_v2('U1', USDC)), tx('v2 usdc +59', claim_v2('U1', USDC), at=NOW + 59),
                                   tx('v2 usdc +60', claim_v2('U1', USDC), at=NOW + 60)], tokens=UT)
    S('v-v1-then-v2-stable-same-second', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('v1 claim', claim('U1')), tx('v2 usdc same second', claim_v2('U1', USDC)),
                                          tx('v2 usdc +60', claim_v2('U1', USDC), at=NOW + 60)], tokens=UT)
    S('v-v2-stable-then-v1-same-second', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('v2 usdc', claim_v2('U1', USDC)), tx('v1 same second', claim('U1')),
                                          tx('v1 +60', claim('U1'), at=NOW + 60)], tokens=UT)
    S('v-same-tx-v1-and-v2-stable', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('v1 + v2 usdc', claim('U1'), claim_v2('U1', USDC))], tokens=UT)
    S('v-v2-native-then-v1', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('v2 wsol', claim_v2('U1', WSOL)), tx('fund', fund('U1', F)),
                              tx('v1 same second', claim('U1')), tx('v1 +60', claim('U1'), at=NOW + 60)], tokens={WSOL: 3000000})
    S('v-v2-stable-empty-then-v1', [tx('create U1', create('U1')), tx('fund', fund('U1', F)), tx('v2 usdc empty', claim_v2('U1', USDC)), tx('v1 same second', claim('U1'))], tokens={USDC: 0})
    S('v-v2-stable-rotated-authority', [tx('create U1', create('U1')), tx('social AUTH->OTHER', set_social('AUTH', O)), tx('v2 usdc by AUTH', claim_v2('U1', USDC)),
                                        tx('v2 usdc by OTHER', claim_v2('U1', USDC, 'OTHER'))], tokens=UT)
    S('v-v2-stable-flag-2', [tx('create U1', create('U1')), tx('flags 2', set_flags('AUTH', 2)), tx('v2 usdc under flag 2', claim_v2('U1', USDC)),
                             tx('flags 0', set_flags('AUTH', 0)), tx('v2 usdc', claim_v2('U1', USDC))], tokens=UT)
    return out


def watched_keys(case):
    keys = [GLOBAL] + [social(u) for u in USERS] + [A, O, T, KP['PAYER'].pubkey()]
    return keys + [Pubkey.from_string(k) for k in case.get('watch', [])]


class Runner:
    def __init__(self, binary):
        self.binary = binary

    def run(self, case):
        vm = LiteSVM().with_transaction_history(0)
        vm.add_program_from_file(PROGRAM, self.binary)
        for k in KP.values():
            vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
        vm.set_clock(Clock(1000, 0, 0, 0, case['clock_unix']))
        for a in case['initial']:
            vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
        watched = watched_keys(case)
        results = []
        for st in case['steps']:
            if 'clock_unix' in st:
                vm.set_clock(Clock(1000, 0, 0, 0, st['clock_unix']))
            ixs = [Instruction(Pubkey.from_string(i.get('program_id', str(PROGRAM))), bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
            signers = [KP['PAYER']] + [KP[s] for s in st['signers'] if s != 'PAYER']
            t = Transaction.new_signed_with_payer(ixs, KP['PAYER'].pubkey(), signers, vm.latest_blockhash())
            r = vm.send_transaction(t)
            failed = isinstance(r, FailedTransactionMetadata)
            meta = r.meta() if failed else r
            state = {}
            for k in watched:
                a = vm.get_account(k)
                state[str(k)] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(a.data), 'sha256': hashlib.sha256(bytes(a.data)).hexdigest()}
                if a is not None and len(a.data) == 165 and str(a.owner) == 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA':
                    state[str(k)]['token_amount'] = int.from_bytes(bytes(a.data)[64:72], 'little')
                if a is not None and len(a.data) and bytes(a.data)[:8] == SOCIAL_DISC:
                    state[str(k)]['decoded'] = decode_social(bytes(a.data))
            rd = meta.return_data()
            logs = meta.logs()
            cu = meta.compute_units_consumed
            results.append({
                'error': str(r.err()) if failed else None,
                'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
                'error_number': next((int(l.split('Error Number: ')[1].split('.')[0]) for l in logs if 'Error Number: ' in l), None),
                'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
                'events': [l for l in logs if l.startswith('Program data:')],
                'program_logs': [l for l in logs if l.startswith('Program log:')],
                'state': state,
                'compute_units': cu() if callable(cu) else cu,
            })
        final = {}
        for k in watched:
            a = vm.get_account(k)
            final[str(k)] = None if a is None else {'lamports': a.lamports, 'data_hex': bytes(a.data).hex()}
        return results, final


COMPARED = ['error', 'custom_error', 'error_number', 'return_hex', 'events', 'program_logs', 'state']


def produce(images, cases_list):
    shas = {n: hashlib.sha256(pathlib.Path(images[n]).read_bytes()).hexdigest() for n in ['original', 'candidate']}
    runners = {n: Runner(images[n]) for n in ['original', 'candidate']}
    receipts, summary = [], []
    for c in cases_list:
        per = {n: runners[n].run(c) for n in runners}
        step_rows = []
        for i, st in enumerate(c['steps']):
            o, k = per['original'][0][i], per['candidate'][0][i]
            step_rows.append({'label': st['label'], 'match': all(o[f] == k[f] for f in COMPARED), 'original': o, 'candidate': k})
        final_match = per['original'][1] == per['candidate'][1]
        receipts.append({'case': c, 'steps': step_rows, 'final_state': {n: per[n][1] for n in per}, 'final_match': final_match})
        summary.append({'name': c['name'], 'family': c['family'], 'steps': len(c['steps']),
                        'match': final_match and all(s['match'] for s in step_rows),
                        'outcomes': [('ok' if s['original']['error'] is None else (s['original']['custom_error'] or s['original']['error'])) for s in step_rows],
                        'outcomes_candidate': [('ok' if s['candidate']['error'] is None else (s['candidate']['custom_error'] or s['candidate']['error'])) for s in step_rows],
                        'cu_original': [s['original']['compute_units'] for s in step_rows],
                        'cu_candidate': [s['candidate']['compute_units'] for s in step_rows]})
    report = {'program_id': str(PROGRAM), 'signer_seeds': SEEDS, 'compared_fields': COMPARED,
              'users': {k: {'user_id': v[0], 'platform': v[1], 'address': str(social(k))} for k, v in USERS.items()},
              'scope': 'Pump Fees social-fee PDA lifecycle sequences (create_social_fee_pda, System transfers into the PDA, claim_social_fee_pda, global setters, clock moves) on persistent LiteSVM state; compared per step: error, custom error, return data, events, program logs, watched account lamports/owner/len/sha256/decoded; final account lamports and bytes. Compute units recorded, not compared.',
              'image_sha256': shas, 'case_count': len(summary), 'step_count': sum(s['steps'] for s in summary),
              'mismatched_cases': [s['name'] for s in summary if not s['match']], 'cases': summary}
    return receipts, report


def gz(obj_bytes):
    return gzip.compress(obj_bytes, compresslevel=9, mtime=0)


def check_idl(root):
    # discriminators are derived locally; confirm them against the repository IDL
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: i for i in idl['instructions']}
    for n in ['create_social_fee_pda', 'claim_social_fee_pda', 'set_authority', 'set_disable_flags', 'set_claim_rate_limit', 'set_social_claim_authority']:
        assert bytes(ixs[n]['discriminator']) == disc(n), n
    # account order / signer / writable flags used by create() and claim()
    assert [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs['create_social_fee_pda']['accounts']] == [
        ('payer', True, True), ('social_fee_pda', False, True), ('system_program', False, False), ('fee_program_global', False, False), ('event_authority', False, False), ('program', False, False)]
    assert [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs['claim_social_fee_pda']['accounts']] == [
        ('recipient', False, True), ('social_fee_pda', False, True), ('fee_program_global', False, False), ('social_claim_authority', True, False), ('event_authority', False, False), ('program', False, False)]
    assert bytes(ixs['claim_social_fee_pda_v2']['discriminator']) == disc('claim_social_fee_pda_v2')
    assert [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs['claim_social_fee_pda_v2']['accounts']] == [
        ('recipient', False, True), ('social_fee_pda', False, True), ('quote_mint', False, True), ('associated_social_fee_pda', False, True),
        ('associated_recipient', False, True), ('quote_token_program', False, False), ('associated_token_program', False, False),
        ('fee_program_global', False, False), ('social_claim_authority', True, False), ('system_program', False, False),
        ('event_authority', False, False), ('program', False, False)], [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs['claim_social_fee_pda_v2']['accounts']]
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['SocialFeePda'] == SOCIAL_DISC and accs['FeeProgramGlobal'] == GLOBAL_DISC


def load_images(arg):
    # JSON object string, or a path to a file holding that JSON object
    arg = arg.strip()
    return json.loads(arg if arg.startswith('{') else pathlib.Path(arg).read_text())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--images', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    images = load_images(a.images)
    check_idl(pathlib.Path(a.root))
    receipts, report = produce(images, cases())
    rt = pathlib.Path(a.out) / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'receipts.jsonl.gz').write_bytes(gz(b''.join(json.dumps(r, sort_keys=True, separators=(',', ':')).encode() + b'\n' for r in receipts)))
    (rt / 'report.json.gz').write_bytes(gz(json.dumps(report, sort_keys=True, indent=1).encode() + b'\n'))
    print(json.dumps({'cases': report['case_count'], 'steps': report['step_count'], 'mismatched': report['mismatched_cases']}))


if __name__ == '__main__':
    main()
