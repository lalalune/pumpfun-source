#!/usr/bin/env python3
"""Pump Fees authority-transition and state-transition sequences.

Every case runs a chain of transactions on ONE persistent LiteSVM per image,
so a later step observes the state left by an earlier step (the existing
scripts/fees_*_differential.py suites rebuild fresh state for every case).

usage: producer.py --root <repo> --images '{"original": p, "candidate": p}' --out <packet dir>
Deterministic: fixed key seeds, no clock, no paths in the output.
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
CONFIG_PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b'fee-program-global'], PROGRAM)
CONFIG, CONFIG_BUMP = Pubkey.find_program_address([b'fee_config', bytes(CONFIG_PROGRAM)], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
OTHER_NORMAL = Pubkey.from_bytes(bytes([131, 13, 252, 159, 222, 95, 230, 184, 170, 124, 4, 164, 118, 233, 30, 138, 198, 187, 38, 74, 173, 144, 250, 25, 201, 223, 73, 216, 92, 62, 91, 94]))
MINT77 = Pubkey.from_bytes(bytes([77]) * 32)
VAULT0 = Pubkey.find_program_address([b'buyback-vault', bytes([0])], PROGRAM)[0]
VAULT1 = Pubkey.find_program_address([b'buyback-vault', bytes([1])], PROGRAM)[0]
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
NOW = 1700000000
TOKEN_RESERVE = 2039280  # rent-exempt minimum for a 165-byte account


def ata(owner, mint=WSOL):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA_PROGRAM)[0]


def native_token_data(owner, amount):
    td = bytearray(165)
    td[:32] = bytes(WSOL); td[32:64] = bytes(owner); td[64:72] = amount.to_bytes(8, 'little'); td[108] = 1
    td[109:113] = (1).to_bytes(4, 'little'); td[113:121] = TOKEN_RESERVE.to_bytes(8, 'little')
    return bytes(td)
# signer labels -> fixed seeds
SEEDS = {'AUTH': 213, 'OTHER': 214, 'PAYER': 215, 'THIRD': 216}
KP = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in SEEDS.items()}
ZERO = Pubkey.default()


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


GLOBAL_DISC = disc('FeeProgramGlobal', 'account')
CONFIG_DISC = disc('FeeConfig', 'account')


def fees(f):
    return struct.pack('<QQQ', *f)


def tiers(xs):
    return struct.pack('<I', len(xs)) + b''.join(t.to_bytes(16, 'little') + fees(f) for t, f in xs)


def global_data(authority, flags=0, social=bytes([44]) * 32, rate=123):
    return GLOBAL_DISC + bytes([GLOBAL_BUMP]) + bytes(authority) + bytes([flags]) + social + rate.to_bytes(8, 'little') + bytes(256)


def config_data(admin, normal, stable, flat=(11, 22, 33), exotic=(44, 55, 66), allocation=4097):
    d = CONFIG_DISC + bytes([CONFIG_BUMP]) + bytes(admin) + fees(flat) + tiers(normal) + tiers(stable) + fees(exotic)
    return d.ljust(allocation, b'\0')


def decode_config(d):
    # raw decode at the full-layout positions; fields that do not fit are None
    if len(d) < 69 or d[:8] != CONFIG_DISC:
        return None
    out = {'admin': str(Pubkey.from_bytes(d[9:41])), 'flat': list(struct.unpack_from('<QQQ', d, 41))}
    o = 65
    for name in ['normal', 'stable']:
        if o + 4 > len(d):
            out[name] = None
            return out
        n = struct.unpack_from('<I', d, o)[0]
        if o + 4 + n * 40 > len(d):
            out[name] = {'count': n, 'fits': False}
            return out
        out[name] = {'count': n, 'tiers': [[int.from_bytes(d[o + 4 + i * 40:o + 20 + i * 40], 'little')] + list(struct.unpack_from('<QQQ', d, o + 20 + i * 40)) for i in range(n)]}
        o += 4 + n * 40
    out['exotic'] = list(struct.unpack_from('<QQQ', d, o)) if o + 24 <= len(d) else None
    out['end'] = o + 24
    out['nonzero_after_end'] = sum(1 for b in d[o + 24:] if b)
    return out


def vault_data(authority, rate=60, last=0, total=0):
    return disc('BuybackVault', 'account') + bytes(authority) + total.to_bytes(8, 'little') + bytes(16) + last.to_bytes(8, 'little', signed=True) + rate.to_bytes(8, 'little', signed=True) + bytes(128)


def m(key, signer, writable):
    return [str(key), signer, writable]


# ---- instruction builders (return (ix dict, signer labels)) ----
def g_setter(name, signer, arg):
    return {'data_hex': (disc(name) + arg).hex(),
            'accounts': [m(KP[signer].pubkey(), True, True), m(GLOBAL, False, True), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def set_authority(signer, new):
    return g_setter('set_authority', signer, bytes(new))


def set_flags(signer, v):
    return g_setter('set_disable_flags', signer, bytes([v]))


def set_rate(signer, v):
    return g_setter('set_claim_rate_limit', signer, v.to_bytes(8, 'little'))


def set_social(signer, new):
    return g_setter('set_social_claim_authority', signer, bytes(new))


def c_admin_ix(name, signer, arg, system=False):
    accs = [m(CONFIG, False, True), m(KP[signer].pubkey(), True, system), m(CONFIG_PROGRAM, False, False)]
    if system:
        accs.append(m(ZERO, False, False))
    accs += [m(EVENT, False, False), m(PROGRAM, False, False)]
    return {'data_hex': (disc(name) + arg).hex(), 'accounts': accs}, [signer]


def update_fee_config(signer, ts, flat):
    return c_admin_ix('update_fee_config', signer, tiers(ts) + fees(flat))


def update_stable(signer, ts):
    return c_admin_ix('update_stable_fee_config', signer, tiers(ts))


def upsert(signer, ts, offset, stable=False):
    return c_admin_ix('upsert_stable_fee_tiers' if stable else 'upsert_fee_tiers', signer, tiers(ts) + bytes([offset]))


def set_exotic(signer, f):
    return c_admin_ix('set_exotic_flat_fees', signer, fees(f), system=True)


def update_admin(signer, new):
    return {'data_hex': disc('update_admin').hex(),
            'accounts': [m(KP[signer].pubkey(), True, False), m(CONFIG, False, True), m(new, False, False),
                         m(CONFIG_PROGRAM, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def extend(signer):
    return {'data_hex': disc('extend_fee_config').hex(),
            'accounts': [m(CONFIG, False, True), m(KP[signer].pubkey(), True, True), m(CONFIG_PROGRAM, False, False),
                         m(ZERO, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def query(pool, cap, quote):
    return {'data_hex': (disc('get_fees_with_quote_mint') + bytes([pool]) + cap.to_bytes(16, 'little') + bytes(quote)).hex(),
            'accounts': [m(CONFIG, False, False), m(CONFIG_PROGRAM, False, False)]}, []


def b_ix(name, signer, index, arg, vault=None):
    v = vault if vault is not None else (VAULT0 if index == 0 else VAULT1)
    return {'data_hex': (disc(name) + bytes([index]) + arg).hex(),
            'accounts': [m(KP[signer].pubkey(), True, True), m(GLOBAL, False, True), m(v, False, True), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def vault_auth(signer, index, new, vault=None):
    return b_ix('update_buyback_authority', signer, index, bytes(new), vault)


def vault_rate(signer, index, rate, vault=None):
    return b_ix('update_buyback_claim_rate_limit', signer, index, rate.to_bytes(8, 'little', signed=True), vault)


def sweep(signer, dest, index=0):
    v = VAULT0 if index == 0 else VAULT1
    return {'data_hex': (disc('sweep_buyback') + bytes([index])).hex(),
            'accounts': [m(dest, False, True), m(KP[signer].pubkey(), True, True), m(v, False, True), m(ata(v), False, True), m(ata(dest), False, True),
                         m(ZERO, False, False), m(ATA_PROGRAM, False, False), m(WSOL, False, False), m(TOKEN, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def tx(label, *ixs):
    signers = []
    for _, s in ixs:
        for x in s:
            if x not in signers:
                signers.append(x)
    return {'label': label, 'instructions': [i for i, _ in ixs], 'signers': signers}


def acct(key, data, owner=PROGRAM, lamports=10**9):
    return {'pubkey': str(key), 'lamports': lamports, 'owner': str(owner), 'data_hex': data.hex()}


A, O, T = KP['AUTH'].pubkey(), KP['OTHER'].pubkey(), KP['THIRD'].pubkey()
N0 = [(0, (1, 2, 3)), (100, (4, 5, 6))]
S0 = [(0, (7, 8, 9))]


def cases():
    out = []

    def G(name, steps, flags=0):
        out.append({'name': name, 'family': 'global', 'initial': [acct(GLOBAL, global_data(A, flags))], 'steps': steps})

    def C(name, steps, normal=N0, stable=S0, allocation=4097, lamports=10**9):
        out.append({'name': name, 'family': 'config', 'initial': [acct(GLOBAL, global_data(A)), acct(CONFIG, config_data(A, normal, stable, allocation=allocation), lamports=lamports)], 'steps': steps})

    # ---- FeeProgramGlobal authority transitions ----
    G('g-transfer-old-rejected-new-accepted', [tx('auth->other', set_authority('AUTH', O)), tx('auth flags', set_flags('AUTH', 1)), tx('other flags', set_flags('OTHER', 2))])
    G('g-transfer-old-cannot-reclaim', [tx('auth->other', set_authority('AUTH', O)), tx('auth->auth', set_authority('AUTH', A)), tx('other rate', set_rate('OTHER', 7))])
    G('g-round-trip', [tx('auth->other', set_authority('AUTH', O)), tx('other->auth', set_authority('OTHER', A)), tx('other social', set_social('OTHER', T)), tx('auth social', set_social('AUTH', T))])
    G('g-self-transfer', [tx('auth->auth', set_authority('AUTH', A)), tx('auth flags', set_flags('AUTH', 3))])
    G('g-zero-authority-rejected', [tx('auth->zero', set_authority('AUTH', ZERO)), tx('auth flags', set_flags('AUTH', 1)), tx('auth rate', set_rate('AUTH', 1)), tx('auth social', set_social('AUTH', O)), tx('auth->auth', set_authority('AUTH', A))])
    G('g-chain-three-holders', [tx('auth->other', set_authority('AUTH', O)), tx('other->third', set_authority('OTHER', T)), tx('other flags', set_flags('OTHER', 1)), tx('auth flags', set_flags('AUTH', 1)), tx('third flags', set_flags('THIRD', 9))])
    G('g-same-tx-transfer-then-new-acts', [tx('auth->other + other flags', set_authority('AUTH', O), set_flags('OTHER', 5))])
    G('g-same-tx-transfer-then-old-acts-rollback', [tx('auth->other + auth flags', set_authority('AUTH', O), set_flags('AUTH', 5)), tx('auth flags after rollback', set_flags('AUTH', 6))])
    G('g-same-tx-double-transfer', [tx('auth->other + other->third', set_authority('AUTH', O), set_authority('OTHER', T)), tx('third rate', set_rate('THIRD', 99))])
    G('g-same-tx-new-acts-before-transfer', [tx('other flags + auth->other', set_flags('OTHER', 5), set_authority('AUTH', O)), tx('auth still holds', set_flags('AUTH', 4))])
    G('g-social-authority-is-not-admin', [tx('social=other', set_social('AUTH', O)), tx('other flags', set_flags('OTHER', 1)), tx('other social', set_social('OTHER', T)), tx('other->other', set_authority('OTHER', O))])
    G('g-all-flags-then-admin-still-works', [tx('flags 255', set_flags('AUTH', 255)), tx('rate', set_rate('AUTH', 2**64 - 1)), tx('social', set_social('AUTH', T)), tx('auth->other', set_authority('AUTH', O)), tx('other flags 0', set_flags('OTHER', 0))])
    G('g-initial-flags-255', [tx('rate', set_rate('AUTH', 5)), tx('flags 0', set_flags('AUTH', 0))], flags=255)
    G('g-rate-sequence', [tx('rate 0', set_rate('AUTH', 0)), tx('rate max', set_rate('AUTH', 2**64 - 1)), tx('rate 1', set_rate('AUTH', 1)), tx('rate 1 again', set_rate('AUTH', 1))])
    G('g-repeat-identical-setter', [tx('flags 7', set_flags('AUTH', 7)), tx('flags 7 again', set_flags('AUTH', 7)), tx('flags 7 + flags 8', set_flags('AUTH', 7), set_flags('AUTH', 8))])
    G('g-failing-tail-rolls-back-head', [tx('rate 9 + other flags', set_rate('AUTH', 9), set_flags('OTHER', 1)), tx('flags 1', set_flags('AUTH', 1))])

    # ---- FeeConfig admin transitions ----
    C('c-update-admin-old-rejected-new-accepted', [tx('auth->other', update_admin('AUTH', O)), tx('auth update', update_fee_config('AUTH', [(0, (9, 9, 9))], (1, 1, 1))), tx('other update', update_fee_config('OTHER', [(0, (9, 9, 9))], (1, 1, 1)))])
    C('c-update-admin-zero-lockout', [tx('auth->zero', update_admin('AUTH', ZERO)), tx('auth exotic', set_exotic('AUTH', (1, 2, 3))), tx('auth upsert', upsert('AUTH', [(0, (1, 1, 1))], 0)), tx('auth->auth', update_admin('AUTH', A))])
    C('c-update-admin-round-trip', [tx('auth->other', update_admin('AUTH', O)), tx('other->auth', update_admin('OTHER', A)), tx('other stable', update_stable('OTHER', [(0, (1, 1, 1))])), tx('auth stable', update_stable('AUTH', [(0, (1, 1, 1))]))])
    C('c-update-admin-to-program-and-config-keys', [tx('auth->config pda', update_admin('AUTH', CONFIG)), tx('auth exotic', set_exotic('AUTH', (1, 1, 1)))])
    C('c-same-tx-admin-then-new-upserts', [tx('auth->other + other upsert', update_admin('AUTH', O), upsert('OTHER', [(100, (5, 5, 5))], 1))])
    C('c-same-tx-admin-then-old-upserts-rollback', [tx('auth->other + auth upsert', update_admin('AUTH', O), upsert('AUTH', [(100, (5, 5, 5))], 1)), tx('auth upsert after rollback', upsert('AUTH', [(100, (6, 6, 6))], 1))])
    C('c-global-authority-change-does-not-move-config-admin', [tx('global auth->other', set_authority('AUTH', O)), tx('other upsert', upsert('OTHER', [(0, (1, 1, 1))], 0)), tx('auth upsert', upsert('AUTH', [(0, (1, 1, 1))], 0))])
    C('c-config-admin-change-does-not-move-global-authority', [tx('config auth->other', update_admin('AUTH', O)), tx('other global flags', set_flags('OTHER', 1)), tx('auth global flags', set_flags('AUTH', 1))])
    # ---- FeeConfig layout transitions (vec growth/shrink moves later fields) ----
    q = lambda label, pool, cap, quote: tx(label, query(pool, cap, quote))
    C('c-grow-normal-shifts-stable-and-exotic', [q('q before', 1, 50, ZERO), tx('upsert normal +3 at 2', upsert('AUTH', [(200, (7, 7, 7)), (300, (8, 8, 8)), (400, (9, 9, 9))], 2)), q('q zero-key mint', 1, 50, ZERO), q('q wsol cap 399', 1, 399, WSOL), q('q wsol cap 400', 1, 400, WSOL), q('q usdc', 1, 400, USDC)])
    C('c-shrink-normal-tail-bytes', [tx('update normal 1 tier', update_fee_config('AUTH', [(0, (3, 3, 3))], (12, 12, 12))), q('q wsol', 1, 1000, WSOL), q('q usdc', 1, 1000, USDC), q('q zero', 1, 1000, ZERO)], normal=[(i * 10, (1, 2, 3)) for i in range(30)], stable=[(i * 10, (4, 5, 6)) for i in range(30)])
    C('c-grow-stable-then-normal', [tx('stable 20', update_stable('AUTH', [(i * 5, (1, 1, i)) for i in range(20)])), tx('normal upsert 10 at 2', upsert('AUTH', [(200 + i, (2, 2, i)) for i in range(10)], 2)), q('q usdc 104', 1, 104, USDC), q('q usdc 105', 1, 105, USDC), q('q wsol 205', 1, 205, WSOL), q('q zero', 0, 0, ZERO)])
    C('c-upsert-replace-middle-truncates', [tx('upsert 1 at 1', upsert('AUTH', [(50, (6, 6, 6))], 1)), q('q wsol 49', 1, 49, WSOL), q('q wsol 50', 1, 50, WSOL), q('q wsol 100', 1, 100, WSOL)], normal=[(0, (1, 1, 1)), (100, (2, 2, 2)), (200, (3, 3, 3))])
    C('c-upsert-offset-equal-len-appends', [tx('upsert at 2', upsert('AUTH', [(150, (6, 6, 6))], 2)), tx('upsert at 4 (gap)', upsert('AUTH', [(160, (6, 6, 6))], 4)), tx('upsert at 3', upsert('AUTH', [(160, (7, 7, 7))], 3))])
    C('c-upsert-unsorted-against-prefix', [tx('upsert at 1 below prefix', upsert('AUTH', [(0, (6, 6, 6))], 1)), tx('upsert at 1 equal prefix', upsert('AUTH', [(0, (6, 6, 6))], 1)), tx('upsert at 0 empty', upsert('AUTH', [], 0))], normal=[(10, (1, 1, 1)), (100, (2, 2, 2))])
    C('c-exotic-survives-update-fee-config', [tx('exotic 100,200,300', set_exotic('AUTH', (100, 200, 300))), tx('update normal', update_fee_config('AUTH', [(0, (1, 1, 1))], (2, 2, 2))), tx('update stable', update_stable('AUTH', [(0, (3, 3, 3)), (1, (4, 4, 4))])), q('q zero', 1, 5, ZERO)])
    C('c-grow-past-allocation-then-extend', [tx('upsert 40 normal', upsert('AUTH', [(i, (1, 1, 1)) for i in range(40)], 0)), tx('upsert 40 stable', upsert('AUTH', [(i, (2, 2, 2)) for i in range(40)], 0, stable=True)), tx('extend', extend('PAYER')), tx('upsert 40 stable after extend', upsert('AUTH', [(i, (2, 2, 2)) for i in range(40)], 0, stable=True))], allocation=2512)
    C('c-extend-then-fill-max', [tx('extend', extend('PAYER')), tx('extend again', extend('PAYER')), tx('normal 50', update_fee_config('AUTH', [(i, (1, 1, 1)) for i in range(50)], (1, 1, 1))), tx('stable 50', update_stable('AUTH', [(i, (2, 2, 2)) for i in range(50)])), tx('normal 51 via upsert at 50', upsert('AUTH', [(50, (1, 1, 1))], 50)), tx('normal replace last via upsert at 49', upsert('AUTH', [(49, (3, 3, 3))], 49)), tx('normal 51 via update', update_fee_config('AUTH', [(i, (1, 1, 1)) for i in range(51)], (1, 1, 1)))], allocation=2512)
    C('c-same-tx-double-admin-transfer', [tx('auth->other + other->third', update_admin('AUTH', O), update_admin('OTHER', T)), tx('other exotic', set_exotic('OTHER', (1, 1, 1))), tx('third exotic', set_exotic('THIRD', (1, 1, 1)))])
    C('c-new-admin-extends-and-upserts', [tx('auth->other', update_admin('AUTH', O)), tx('extend by other', extend('OTHER')), tx('other normal 50', update_fee_config('OTHER', [(i, (1, 1, 1)) for i in range(50)], (1, 1, 1)))], allocation=2512)
    C('c-failing-update-keeps-previous', [tx('valid update', update_fee_config('AUTH', [(0, (5, 5, 5)), (10, (6, 6, 6))], (7, 7, 7))), tx('fee total 10001', update_fee_config('AUTH', [(0, (10001, 0, 0))], (7, 7, 7))), tx('unsorted', update_fee_config('AUTH', [(10, (1, 1, 1)), (0, (1, 1, 1))], (7, 7, 7))), q('q wsol 10', 1, 10, WSOL)])
    # ---- FeeConfig size/version boundaries (account length selects the layout that is read) ----
    seq = lambda: [q('q usdc', 1, 500, USDC), q('q mint77', 1, 500, MINT77), q('q other-normal', 1, 500, OTHER_NORMAL), tx('update stable', update_stable('AUTH', [(0, (13, 14, 15))])), q('q usdc after stable', 1, 500, USDC),
                   tx('exotic 100,200,300', set_exotic('AUTH', (100, 200, 300))), q('q usdc after exotic', 1, 500, USDC), q('q mint77 after exotic', 1, 500, MINT77), tx('update stable again', update_stable('AUTH', [(0, (16, 17, 18))])), q('q usdc final', 1, 500, USDC)]
    for allocation in [2512, 4072, 4073, 4096, 4097]:
        C(f'v-size-{allocation}-stable-then-exotic', seq(), allocation=allocation)
    C('v-size-4072-underfunded-exotic-resize', seq(), allocation=4072, lamports=1)
    def B(name, steps, vault_authority=A, flags=0):
        out.append({'name': name, 'family': 'buyback', 'initial': [acct(GLOBAL, global_data(A, flags)), acct(VAULT0, vault_data(vault_authority)), acct(VAULT1, vault_data(vault_authority, rate=5))], 'steps': steps})

    B('b-vault-authority-transfer', [tx('auth vault0->other', vault_auth('AUTH', 0, O)), tx('auth rate vault0', vault_rate('AUTH', 0, 9)), tx('other rate vault0', vault_rate('OTHER', 0, 9)), tx('other vault0->third', vault_auth('OTHER', 0, T))])
    B('b-global-transfer-then-vault-setters', [tx('global auth->other', set_authority('AUTH', O)), tx('auth rate vault0', vault_rate('AUTH', 0, 9)), tx('other rate vault0', vault_rate('OTHER', 0, 9)), tx('other vault1->third', vault_auth('OTHER', 1, T))])
    B('b-vault-authority-differs-from-global', [tx('other rate vault0', vault_rate('OTHER', 0, 9)), tx('auth rate vault0', vault_rate('AUTH', 0, 10))], vault_authority=O)
    B('b-rate-limit-sequence', [tx('rate 0', vault_rate('AUTH', 0, 0)), tx('rate -1', vault_rate('AUTH', 0, -1)), tx('rate i64 max', vault_rate('AUTH', 0, 2**63 - 1)), tx('rate i64 min', vault_rate('AUTH', 0, -2**63)), tx('rate 60', vault_rate('AUTH', 0, 60))])
    B('b-index-vault-mismatch', [tx('index 1 with vault0', vault_rate('AUTH', 1, 9, vault=VAULT0)), tx('index 0 with vault1', vault_auth('AUTH', 0, O, vault=VAULT1)), tx('index 1 with vault1', vault_rate('AUTH', 1, 9))])
    B('b-vault-authority-zero', [tx('vault0->zero', vault_auth('AUTH', 0, ZERO)), tx('auth rate vault0', vault_rate('AUTH', 0, 1))])
    B('b-same-tx-global-transfer-then-vault', [tx('global auth->other + other rate vault0', set_authority('AUTH', O), vault_rate('OTHER', 0, 11)), tx('auth rate vault0', vault_rate('AUTH', 0, 12))])
    B('b-flags-255-vault-setters', [tx('rate vault0', vault_rate('AUTH', 0, 13)), tx('vault0->other', vault_auth('AUTH', 0, O))], flags=255)
    def S(name, steps, vault_authority=A, rate=60, last=0, tokens=1000000):
        md = bytearray(82); md[44] = 9; md[45] = 1
        initial = [acct(GLOBAL, global_data(A)), acct(VAULT0, vault_data(vault_authority, rate=rate, last=last), lamports=10**9),
                   acct(ata(VAULT0), native_token_data(VAULT0, tokens), owner=TOKEN, lamports=TOKEN_RESERVE + tokens),
                   acct(ata(T), native_token_data(T, 0), owner=TOKEN, lamports=TOKEN_RESERVE),
                   acct(WSOL, bytes(md), owner=TOKEN)]
        out.append({'name': name, 'family': 'sweep', 'clock_unix': NOW, 'initial': initial, 'watch': [str(ata(VAULT0)), str(ata(T))], 'steps': steps})

    S('s-sweep-by-stored-vault-authority-after-transfer', [tx('vault0->other', vault_auth('AUTH', 0, O)), tx('sweep by auth', sweep('AUTH', T)), tx('sweep by other', sweep('OTHER', T))])
    S('s-sweep-by-stored-authority-not-global', [tx('sweep by auth (global)', sweep('AUTH', T)), tx('sweep by other (stored)', sweep('OTHER', T))], vault_authority=O)
    S('s-sweep-after-global-transfer', [tx('global auth->other', set_authority('AUTH', O)), tx('sweep by other', sweep('OTHER', T)), tx('sweep by auth', sweep('AUTH', T))])
    S('s-sweep-twice-rate-limited', [tx('sweep 1', sweep('AUTH', T)), tx('sweep 2 same second', sweep('AUTH', T)),
                                     {**tx('', sweep('AUTH', T)), 'label': 'sweep 3 at +59s', 'clock_unix': NOW + 59}, {**tx('', sweep('AUTH', T)), 'label': 'sweep 4 at +60s', 'clock_unix': NOW + 60}, {**tx('', sweep('AUTH', T)), 'label': 'sweep 5 at +61s', 'clock_unix': NOW + 61}, {**tx('', sweep('AUTH', T)), 'label': 'sweep 6 at +120s', 'clock_unix': NOW + 120}, {**tx('', sweep('AUTH', T)), 'label': 'sweep 7 at +121s', 'clock_unix': NOW + 121}])
    S('s-sweep-rate-reset-to-zero', [tx('sweep 1', sweep('AUTH', T)), tx('rate 0', vault_rate('AUTH', 0, 0)), tx('sweep 2 same second', sweep('AUTH', T))])
    S('s-sweep-negative-rate', [tx('sweep 1', sweep('AUTH', T)), tx('sweep 2 same second', sweep('AUTH', T))], rate=-1)
    S('s-same-tx-transfer-vault-authority-then-sweep', [tx('vault0->other + other sweep', vault_auth('AUTH', 0, O), sweep('OTHER', T)), tx('auth sweep', sweep('AUTH', T))])
    C('v-empty-normal-tiers-queries', [q('q wsol', 1, 500, WSOL), q('q zero', 1, 500, ZERO), q('q usdc', 1, 500, USDC), q('q mint77', 1, 500, MINT77), q('q wsol non-pump', 0, 500, WSOL),
                                        tx('update normal empty', update_fee_config('AUTH', [], (1, 1, 1))), tx('upsert normal 1', upsert('AUTH', [(0, (2, 2, 2))], 0)), q('q wsol after upsert', 1, 500, WSOL)], normal=[])
    C('v-size-2512-underfunded-extend', [tx('extend', extend('PAYER')), q('q usdc', 1, 500, USDC), q('q mint77', 1, 500, MINT77)], allocation=2512, lamports=1)
    return out


class Runner:
    def __init__(self, binary):
        self.binary = binary

    def run(self, case):
        vm = LiteSVM().with_transaction_history(0)
        vm.add_program_from_file(PROGRAM, self.binary)
        for k in KP.values():
            vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
        vm.set_account(CONFIG_PROGRAM, Account(10**9, b'', ZERO))
        if 'clock_unix' in case:
            vm.set_clock(Clock(1000, 0, 0, 0, case['clock_unix']))
        for a in case['initial']:
            vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
        watched = [GLOBAL, CONFIG, VAULT0, VAULT1] + [Pubkey.from_string(k) for k in case.get('watch', [])]
        results = []
        for st in case['steps']:
            if 'clock_unix' in st:
                vm.set_clock(Clock(1000, 0, 0, 0, st['clock_unix']))
            ixs = [Instruction(PROGRAM, bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
            signers = [KP['PAYER']] + [KP[s] for s in st['signers'] if s != 'PAYER']
            t = Transaction.new_signed_with_payer(ixs, KP['PAYER'].pubkey(), signers, vm.latest_blockhash())
            r = vm.send_transaction(t)
            failed = isinstance(r, FailedTransactionMetadata)
            meta = r.meta() if failed else r
            state = {}
            for k in watched:
                a = vm.get_account(k)
                state[str(k)] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(a.data), 'sha256': hashlib.sha256(bytes(a.data)).hexdigest()}
                if a is not None and k == CONFIG:
                    state[str(k)]['decoded'] = decode_config(bytes(a.data))
            rd = meta.return_data()
            logs = meta.logs()
            results.append({
                'error': str(r.err()) if failed else None,
                'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
                'error_number': next((int(l.split('Error Number: ')[1].split('.')[0]) for l in logs if 'Error Number: ' in l), None),
                'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
                'events': [l for l in logs if l.startswith('Program data:')],
                'program_logs': [l for l in logs if l.startswith('Program log:')],
                'state': state,
                'compute_units': meta.compute_units_consumed() if callable(meta.compute_units_consumed) else meta.compute_units_consumed,
            })
        final = {}
        for k in watched:
            a = vm.get_account(k)
            final[str(k)] = None if a is None else bytes(a.data).hex()
        return results, final


COMPARED = ['error', 'custom_error', 'error_number', 'return_hex', 'events', 'program_logs', 'state']


def produce(images, cases_list):
    shas = {n: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for n, p in images.items()}
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
                        'cu_original': [s['original']['compute_units'] for s in step_rows],
                        'cu_candidate': [s['candidate']['compute_units'] for s in step_rows]})
    report = {'program_id': str(PROGRAM), 'signer_seeds': SEEDS, 'compared_fields': COMPARED,
              'scope': 'Pump Fees authority-transition and FeeConfig layout-transition sequences on persistent LiteSVM state; compared per step: error, custom error, return data, events, watched account lamports/owner/len/sha256; final account bytes. Compute units recorded, not compared.',
              'image_sha256': shas, 'case_count': len(summary), 'step_count': sum(s['steps'] for s in summary),
              'mismatched_cases': [s['name'] for s in summary if not s['match']], 'cases': summary}
    return receipts, report


def gz(obj_bytes):
    return gzip.compress(obj_bytes, compresslevel=9, mtime=0)


def check_idl(root):
    # discriminators are derived locally; confirm them against the repository IDL
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: bytes(i['discriminator']) for i in idl['instructions']}
    for n in ['set_authority', 'set_disable_flags', 'set_claim_rate_limit', 'set_social_claim_authority', 'update_fee_config',
              'update_stable_fee_config', 'upsert_fee_tiers', 'upsert_stable_fee_tiers', 'set_exotic_flat_fees', 'update_admin',
              'extend_fee_config', 'get_fees_with_quote_mint', 'update_buyback_authority', 'update_buyback_claim_rate_limit']:
        assert ixs[n] == disc(n), n
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['FeeConfig'] == CONFIG_DISC and accs['FeeProgramGlobal'] == GLOBAL_DISC and accs['BuybackVault'] == disc('BuybackVault', 'account')


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
