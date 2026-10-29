#!/usr/bin/env python3
"""Pump Fees buyback-vault initialization and referral withdraw sequences.

Every case runs a chain of transactions on ONE persistent LiteSVM per image:
initialize_buyback, real SPL / Token-2022 transfers into the vault ATA,
System transfers into the vault PDA, update_buyback_authority, sweep_buyback,
withdraw (native and token mode) and clock moves. A later step sees the state
left by an earlier one. scripts/fees_buyback_differential.py and
scripts/fees_withdraw_differential.py run single instructions on directly
written state, and #1907 (pump-fees-authority-transition-sequences-20261029)
sweeps only a pre-written native vault; none of them runs initialize_buyback,
a non-native or Token-2022 sweep, or withdraw sequences.

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
ZERO = Pubkey.default()
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b'fee-program-global'], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
NOW = 1700000000
SEEDS = {'AUTH': 211, 'OTHER': 212, 'PAYER': 213, 'USER': 214, 'THIRD': 215}
KP = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in SEEDS.items()}
A, O, P, U, T = (KP[k].pubkey() for k in ['AUTH', 'OTHER', 'PAYER', 'USER', 'THIRD'])
LEG = Pubkey.from_bytes(bytes([61]) * 32)   # legacy SPL Token mint, 6 decimals
T22 = Pubkey.from_bytes(bytes([62]) * 32)   # Token-2022 mint (base layout, no extensions), 6 decimals
TFM = Pubkey.from_bytes(bytes([63]) * 32)  # Token-2022 mint with a TransferFeeConfig extension, 6 decimals
MINTS = {'LEG': (LEG, TOKEN, 6), 'WSOL': (WSOL, TOKEN, 9), 'T22': (T22, TOKEN22, 6), 'TF': (TFM, TOKEN22, 6)}
TOKEN_RESERVE = 2039280  # rent-exempt minimum for a 165-byte account
TF_BPS, TF_MAX = 100, 5000  # transfer fee: 1% capped at 5,000 base units (same in older and newer slots)


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


GLOBAL_DISC = disc('FeeProgramGlobal', 'account')
VAULT_DISC = disc('BuybackVault', 'account')


def global_data(authority):
    return GLOBAL_DISC + bytes([GLOBAL_BUMP]) + bytes(authority) + bytes([0]) + bytes(authority) + (60).to_bytes(8, 'little') + bytes(256)


def bvault(i):
    return Pubkey.find_program_address([b'buyback-vault', bytes([i])], PROGRAM)[0]


def rvault(user):
    return Pubkey.find_program_address([b'referral-vault', bytes(user)], PROGRAM)[0]


def ata(owner, mk):
    mint, prog, _ = MINTS[mk]
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(mint)], ATA_PROGRAM)[0]


def decode_vault(d):
    # BuybackVault: disc, authority, total_claimed, total_claimed_token1, total_claimed_token2, last_claimed, claim_rate_limit, reserved[128]
    if len(d) < 88 or d[:8] != VAULT_DISC:
        return None
    tc, t1, t2, last, rate = struct.unpack_from('<QQQqq', d, 40)
    return {'authority': str(Pubkey.from_bytes(d[8:40])), 'total_claimed': tc, 'total_claimed_token1': t1, 'total_claimed_token2': t2,
            'last_claimed': last, 'claim_rate_limit': rate, 'nonzero_reserved': sum(1 for b in d[88:] if b)}


def m(key, signer, writable):
    return [str(key), signer, writable]


def init_bb(i, mk, payer='AUTH', token_program=None):
    mint, prog, _ = MINTS[mk]
    prog = token_program or prog
    v = bvault(i)
    vata = Pubkey.find_program_address([bytes(v), bytes(prog), bytes(mint)], ATA_PROGRAM)[0]
    return {'data_hex': (disc('initialize_buyback') + bytes([i])).hex(),
            'accounts': [m(KP[payer].pubkey(), True, True), m(v, False, True), m(vata, False, True), m(SYSTEM, False, False), m(ATA_PROGRAM, False, False),
                         m(mint, False, False), m(prog, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [payer]


def sweep(i, mk, authority='OTHER', destination=None):
    mint, prog, _ = MINTS[mk]
    d = destination if destination is not None else T
    v = bvault(i)
    return {'data_hex': (disc('sweep_buyback') + bytes([i])).hex(),
            'accounts': [m(d, False, True), m(KP[authority].pubkey(), True, True), m(v, False, True), m(ata(v, mk), False, True), m(ata(d, mk), False, True),
                         m(SYSTEM, False, False), m(ATA_PROGRAM, False, False), m(mint, False, False), m(prog, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [authority]


def bb_setter(name, i, signer, arg):
    return {'data_hex': (disc(name) + bytes([i]) + arg).hex(),
            'accounts': [m(KP[signer].pubkey(), True, True), m(GLOBAL, False, True), m(bvault(i), False, True), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def bb_auth(i, new, signer='AUTH'):
    return bb_setter('update_buyback_authority', i, signer, bytes(new))


def bb_rate(i, v, signer='AUTH'):
    return bb_setter('update_buyback_claim_rate_limit', i, signer, struct.pack('<q', v))


def set_authority(signer, new):
    return {'data_hex': (disc('set_authority') + bytes(new)).hex(),
            'accounts': [m(KP[signer].pubkey(), True, True), m(GLOBAL, False, True), m(EVENT, False, False), m(PROGRAM, False, False)]}, [signer]


def lamports_to(key, n):
    # System Program transfer from the fee payer
    return {'program_id': str(SYSTEM), 'data_hex': (struct.pack('<I', 2) + n.to_bytes(8, 'little')).hex(),
            'accounts': [m(P, True, True), m(key, False, True)]}, []


def tokens_to(dest, mk, n):
    # SPL / Token-2022 TransferChecked from PAYER's funded token account
    mint, prog, dec = MINTS[mk]
    return {'program_id': str(prog), 'data_hex': (bytes([12]) + n.to_bytes(8, 'little') + bytes([dec])).hex(),
            'accounts': [m(ata(P, mk), False, True), m(mint, False, False), m(dest, False, True), m(P, True, False)]}, []


def withdraw(user='USER', mk=None, vault_ata=True, user_ata_owner=None, token_program=True, mint_override=None, vault_user=None):
    u = KP[user].pubkey()
    vu = KP[vault_user].pubkey() if vault_user else u
    none = m(PROGRAM, False, False)   # Anchor encodes an absent Option account as the program id
    if mk is None:
        metas = [none, none, none, none]
    else:
        mint, prog, _ = MINTS[mk]
        metas = [m(mint_override or mint, False, False),
                 m(ata(rvault(vu), mk), False, True) if vault_ata else none,
                 m(ata(user_ata_owner or u, mk), False, True),
                 m(prog, False, False) if token_program else none]
    return {'data_hex': disc('withdraw').hex(),
            'accounts': [m(u, True, True), m(rvault(u), False, True)] + metas + [m(SYSTEM, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, [user]


def tx(label, *ixs, at=None):
    signers = []
    for _, s in ixs:
        for x in s:
            if x not in signers:
                signers.append(x)
    out = {'label': label, 'instructions': [i for i, _ in ixs], 'signers': signers}
    if at is not None:
        out['clock_unix'] = at
    return out


def acct(key, data, owner, lamports):
    return {'pubkey': str(key), 'lamports': lamports, 'owner': str(owner), 'data_hex': data.hex()}


def mint_data(dec, transfer_fee=False):
    md = bytearray(82); md[36:44] = (10**15).to_bytes(8, 'little'); md[44] = dec; md[45] = 1
    if transfer_fee:
        # Token-2022 extension layout: base mint, zero padding to 165, account type 1 (Mint), TLV TransferFeeConfig (type 1, 108 bytes)
        fee = (0).to_bytes(8, 'little') + TF_MAX.to_bytes(8, 'little') + TF_BPS.to_bytes(2, 'little')
        md += bytes(165 - 82) + bytes([1]) + struct.pack('<HH', 1, 108) + bytes(64) + (0).to_bytes(8, 'little') + fee + fee
    return bytes(md)


def token_data(mk, owner, amount):
    mint = MINTS[mk][0]
    td = bytearray(165)
    td[:32] = bytes(mint); td[32:64] = bytes(owner); td[64:72] = amount.to_bytes(8, 'little'); td[108] = 1
    if mint == WSOL:
        td[109:113] = (1).to_bytes(4, 'little'); td[113:121] = TOKEN_RESERVE.to_bytes(8, 'little')
    if mk == 'TF':
        # account type 2 (Account), TLV TransferFeeAmount (type 2, withheld u64)
        td += bytes([2]) + struct.pack('<HH', 2, 8) + (0).to_bytes(8, 'little')
    return bytes(td)


def token_acct(owner, mk, amount, key=None):
    lam = TOKEN_RESERVE + (amount if mk == 'WSOL' else 0) + (3 * 10**6 if mk == 'TF' else 0)
    return acct(key or ata(owner, mk), token_data(mk, owner, amount), MINTS[mk][1], lam)


E = 1000000  # token deposit size used by most steps


def cases():
    out = []

    def S(name, steps, extra=(), watch=()):
        initial = [acct(GLOBAL, global_data(A), PROGRAM, 10**9)]
        for mk, (mint, prog, dec) in MINTS.items():
            initial.append(acct(mint, mint_data(dec, mk == 'TF'), prog, 10**9))
            initial.append(token_acct(P, mk, 10**12))   # PAYER's funding account
            initial.append(token_acct(T, mk, 0))        # default sweep destination ATA
        initial += list(extra)
        out.append({'name': name, 'family': name.split('-')[0], 'clock_unix': NOW, 'initial': initial, 'steps': steps, 'watch': [str(k) for k in watch]})

    def BW(i, mk):
        return [bvault(i), ata(bvault(i), mk), T, ata(T, mk)]

    # ---- i: initialize_buyback ----
    S('i-index-0-then-again', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('init 0 LEG again', init_bb(0, 'LEG')), tx('init 0 WSOL', init_bb(0, 'WSOL'))], watch=BW(0, 'LEG') + [ata(bvault(0), 'WSOL')])
    S('i-index-boundary', [tx('init 8', init_bb(8, 'LEG')), tx('init 255', init_bb(255, 'LEG')), tx('init 7', init_bb(7, 'LEG')), tx('init 8 again', init_bb(8, 'LEG'))],
      watch=[bvault(7), bvault(8), bvault(255), ata(bvault(8), 'LEG')])
    S('i-same-tx-two-indices', [tx('init 1 LEG + init 2 WSOL', init_bb(1, 'LEG'), init_bb(2, 'WSOL')), tx('init 3 T22 + init 8 LEG', init_bb(3, 'T22'), init_bb(8, 'LEG'))],
      watch=[bvault(1), bvault(2), bvault(3), ata(bvault(3), 'T22')])
    S('i-prefunded-vault-address', [tx('init 0 LEG on prefunded address', init_bb(0, 'LEG'))], extra=[acct(bvault(0), b'', SYSTEM, 5 * E)], watch=BW(0, 'LEG'))
    S('i-prefunded-vault-1-lamport', [tx('init 0 LEG on 1 lamport', init_bb(0, 'LEG'))], extra=[acct(bvault(0), b'', SYSTEM, 1)], watch=BW(0, 'LEG'))
    S('i-vault-ata-preexists-with-tokens', [tx('init 0 LEG', init_bb(0, 'LEG'))], extra=[token_acct(bvault(0), 'LEG', 777)], watch=BW(0, 'LEG'))
    S('i-token2022-mint', [tx('init 4 T22', init_bb(4, 'T22')), tx('init 5 LEG', init_bb(5, 'LEG'))], watch=[bvault(4), ata(bvault(4), 'T22'), bvault(5)])
    S('i-mint-program-mismatch', [tx('init 0 LEG with Token-2022', init_bb(0, 'LEG', token_program=TOKEN22)), tx('init 0 T22 with Token', init_bb(0, 'T22', token_program=TOKEN)),
                                  tx('init 0 LEG', init_bb(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('i-payer-other', [tx('init 6 LEG paid by OTHER', init_bb(6, 'LEG', payer='OTHER')), tx('OTHER sweeps 6', sweep(6, 'LEG'))], watch=BW(6, 'LEG') + [O])

    # ---- s: init -> authority -> sweep chains ----
    for mk in ['LEG', 'WSOL', 'T22']:
        S(f's-{mk.lower()}-zero-authority-rotate-sweep', [
            tx('init 0', init_bb(0, mk)), tx('deposit 1e6', tokens_to(ata(bvault(0), mk), mk, E)),
            tx('AUTH sweeps (zero authority)', sweep(0, mk, 'AUTH')), tx('OTHER sweeps (zero authority)', sweep(0, mk, 'OTHER')),
            tx('authority -> OTHER', bb_auth(0, O)), tx('AUTH sweeps', sweep(0, mk, 'AUTH')), tx('OTHER sweeps', sweep(0, mk)),
            tx('OTHER sweeps empty same second', sweep(0, mk)), tx('deposit 7', tokens_to(ata(bvault(0), mk), mk, 7)), tx('OTHER sweeps 7', sweep(0, mk))], watch=BW(0, mk))
    S('s-vault-lamports-swept', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('authority -> OTHER', bb_auth(0, O)), tx('3e6 lamports to vault', lamports_to(bvault(0), 3 * E)),
                                 tx('sweep', sweep(0, 'LEG')), tx('1 lamport to vault', lamports_to(bvault(0), 1)), tx('sweep 1 lamport', sweep(0, 'LEG')), tx('sweep nothing', sweep(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('s-wsol-lamports-and-tokens', [tx('init 0 WSOL', init_bb(0, 'WSOL')), tx('authority -> OTHER', bb_auth(0, O)), tx('2e6 lamports to vault', lamports_to(bvault(0), 2 * E)),
                                     tx('deposit 5e6 WSOL', tokens_to(ata(bvault(0), 'WSOL'), 'WSOL', 5 * E)), tx('sweep', sweep(0, 'WSOL'))], watch=BW(0, 'WSOL'))
    S('s-rate-after-init', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('authority -> OTHER', bb_auth(0, O)), tx('rate 60', bb_rate(0, 60)),
                            tx('sweep', sweep(0, 'LEG')), tx('sweep +0', sweep(0, 'LEG')), tx('sweep +60', sweep(0, 'LEG'), at=NOW + 60), tx('sweep +61', sweep(0, 'LEG'), at=NOW + 61)], watch=BW(0, 'LEG'))
    S('s-destination-ata-missing', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('authority -> OTHER', bb_auth(0, O)), tx('deposit', tokens_to(ata(bvault(0), 'LEG'), 'LEG', E)),
                                    tx('sweep to USER (no ATA)', sweep(0, 'LEG', destination=U)), tx('sweep to THIRD', sweep(0, 'LEG'))], watch=BW(0, 'LEG') + [U, ata(U, 'LEG')])
    S('s-mint-not-initialized-for-vault', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('authority -> OTHER', bb_auth(0, O)), tx('sweep 0 with WSOL', sweep(0, 'WSOL')),
                                           tx('sweep 0 with T22', sweep(0, 'T22')), tx('sweep 0 LEG', sweep(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('s-rotate-back-to-zero', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('authority -> OTHER', bb_auth(0, O)), tx('OTHER sweeps', sweep(0, 'LEG')),
                                tx('authority -> zero', bb_auth(0, ZERO)), tx('OTHER sweeps', sweep(0, 'LEG')), tx('authority -> THIRD', bb_auth(0, T)), tx('THIRD sweeps', sweep(0, 'LEG', 'THIRD'))], watch=BW(0, 'LEG'))
    S('s-uninitialized-index', [tx('sweep 8', sweep(8, 'LEG')), tx('sweep 1', sweep(1, 'LEG')), tx('authority 8 -> OTHER', bb_auth(8, O)), tx('rate 8', bb_rate(8, 1))], watch=[bvault(1), bvault(8)])
    S('s-same-tx-init-rotate-sweep', [tx('init + rotate + deposit + sweep', init_bb(0, 'LEG'), bb_auth(0, O), tokens_to(ata(bvault(0), 'LEG'), 'LEG', E), sweep(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('s-same-tx-init-sweep-zero', [tx('init + AUTH sweep', init_bb(0, 'LEG'), sweep(0, 'LEG', 'AUTH')), tx('init again', init_bb(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('s-global-authority-moved', [tx('init 0 LEG', init_bb(0, 'LEG')), tx('global AUTH -> OTHER', set_authority('AUTH', O)), tx('AUTH sets vault authority', bb_auth(0, A)),
                                   tx('OTHER sets vault authority', bb_auth(0, O, 'OTHER')), tx('OTHER sweeps', sweep(0, 'LEG'))], watch=BW(0, 'LEG'))
    S('s-two-vaults-independent', [tx('init 0 LEG + init 1 LEG', init_bb(0, 'LEG'), init_bb(1, 'LEG')), tx('authority 1 -> OTHER', bb_auth(1, O)),
                                   tx('deposit both', tokens_to(ata(bvault(0), 'LEG'), 'LEG', E), tokens_to(ata(bvault(1), 'LEG'), 'LEG', 2 * E)),
                                   tx('OTHER sweeps 0', sweep(0, 'LEG')), tx('OTHER sweeps 1', sweep(1, 'LEG'))], watch=BW(0, 'LEG') + [bvault(1), ata(bvault(1), 'LEG')])

    # ---- w: referral withdraw ----
    UW = [rvault(U), U]
    S('w-native-ladder', [tx('withdraw (no vault account)', withdraw()), tx('fund 5', lamports_to(rvault(U), 5)), tx('withdraw 5 (below rent floor)', withdraw()),
                          tx('fund 890875', lamports_to(rvault(U), 890875)), tx('withdraw at floor', withdraw()), tx('fund 1', lamports_to(rvault(U), 1)),
                          tx('withdraw floor+1', withdraw()), tx('withdraw again', withdraw())], watch=UW)
    S('w-native-same-tx', [tx('fund + withdraw', lamports_to(rvault(U), E), withdraw()), tx('withdraw + fund', withdraw(), lamports_to(rvault(U), E)),
                           tx('withdraw + withdraw', withdraw(), withdraw()), tx('withdraw', withdraw())], extra=[acct(rvault(U), b'', SYSTEM, E)], watch=UW)
    S('w-native-users-independent', [tx('OTHER withdraws own empty vault', withdraw('OTHER')), tx('USER withdraws', withdraw()), tx('OTHER withdraws', withdraw('OTHER'))],
      extra=[acct(rvault(U), b'', SYSTEM, 3 * E)], watch=UW + [rvault(O), O])
    S('w-native-vault-owned-by-program', [tx('withdraw (vault owned by pump_fees)', withdraw())], extra=[acct(rvault(U), b'', PROGRAM, 3 * E)], watch=UW)
    S('w-native-vault-with-data', [tx('withdraw (vault holds 8 bytes)', withdraw())], extra=[acct(rvault(U), bytes(8), SYSTEM, 3 * E)], watch=UW)
    for mk in ['LEG', 'WSOL', 'T22']:
        S(f'w-{mk.lower()}-token-ladder', [tx('withdraw 12345', withdraw(mk=mk)), tx('withdraw again', withdraw(mk=mk)), tx('deposit 7', tokens_to(ata(rvault(U), mk), mk, 7)),
                                          tx('withdraw 7', withdraw(mk=mk)), tx('1e6 lamports to vault PDA', lamports_to(rvault(U), E)), tx('token withdraw with lamports only', withdraw(mk=mk)),
                                          tx('native withdraw', withdraw())],
          extra=[token_acct(rvault(U), mk, 12345), token_acct(U, mk, 0)], watch=UW + [ata(rvault(U), mk), ata(U, mk)])
    S('w-token-incomplete-accounts', [tx('mint only (no vault ata)', withdraw(mk='LEG', vault_ata=False)), tx('no token program', withdraw(mk='LEG', token_program=False)),
                                      tx('complete', withdraw(mk='LEG'))], extra=[token_acct(rvault(U), 'LEG', 500), token_acct(U, 'LEG', 0)], watch=UW + [ata(rvault(U), 'LEG'), ata(U, 'LEG')])
    S('w-token-user-ata-other-owner', [tx('user_ata owned by OTHER', withdraw(mk='LEG', user_ata_owner=O)), tx('own user_ata', withdraw(mk='LEG'))],
      extra=[token_acct(rvault(U), 'LEG', 500), token_acct(U, 'LEG', 0), token_acct(O, 'LEG', 0)], watch=UW + [ata(rvault(U), 'LEG'), ata(U, 'LEG'), ata(O, 'LEG')])
    S('w-token-mint-mismatch', [tx('quote_mint WSOL with LEG accounts', withdraw(mk='LEG', mint_override=WSOL)), tx('quote_mint T22 with LEG accounts', withdraw(mk='LEG', mint_override=T22)),
                                tx('matching', withdraw(mk='LEG'))], extra=[token_acct(rvault(U), 'LEG', 500), token_acct(U, 'LEG', 0)], watch=UW + [ata(rvault(U), 'LEG'), ata(U, 'LEG')])
    S('w-token-other-user-vault', [tx('OTHER withdraws own missing vault ata', withdraw('OTHER', mk='LEG')), tx('OTHER withdraws with USER vault ata', withdraw('OTHER', mk='LEG', vault_user='USER')),
                                   tx('USER withdraws', withdraw(mk='LEG'))],
      extra=[token_acct(rvault(U), 'LEG', 500), token_acct(U, 'LEG', 0), token_acct(O, 'LEG', 0)], watch=UW + [ata(rvault(U), 'LEG'), ata(U, 'LEG'), ata(O, 'LEG')])
    S('w-same-tx-native-and-token', [tx('native + token withdraw', withdraw(), withdraw(mk='T22')), tx('token + native again', withdraw(mk='T22'), withdraw())],
      extra=[acct(rvault(U), b'', SYSTEM, 2 * E), token_acct(rvault(U), 'T22', 900), token_acct(U, 'T22', 0)], watch=UW + [ata(rvault(U), 'T22'), ata(U, 'T22')])
    S('w-clock-in-event', [tx('withdraw at 0', withdraw(), at=0), tx('fund', lamports_to(rvault(U), E)), tx('withdraw at -1', withdraw(), at=-1),
                           tx('fund', lamports_to(rvault(U), E)), tx('withdraw at 2^62', withdraw(), at=2**62)], extra=[acct(rvault(U), b'', SYSTEM, 2 * E)], watch=UW)

    # ---- x: Token-2022 mint with a transfer fee (1%, max 5,000) ----
    S('x-tf-init-deposit-sweep', [tx('init 0 TF', init_bb(0, 'TF')), tx('deposit 1e6', tokens_to(ata(bvault(0), 'TF'), 'TF', E)), tx('authority -> OTHER', bb_auth(0, O)),
                                  tx('sweep', sweep(0, 'TF')), tx('deposit 100', tokens_to(ata(bvault(0), 'TF'), 'TF', 100)), tx('sweep', sweep(0, 'TF')),
                                  tx('deposit 1', tokens_to(ata(bvault(0), 'TF'), 'TF', 1)), tx('sweep', sweep(0, 'TF'))], watch=BW(0, 'TF'))
    S('x-tf-withdraw-ladder', [tx('withdraw 12345', withdraw(mk='TF')), tx('deposit 7', tokens_to(ata(rvault(U), 'TF'), 'TF', 7)), tx('withdraw', withdraw(mk='TF')),
                               tx('withdraw again', withdraw(mk='TF'))],
      extra=[token_acct(rvault(U), 'TF', 12345), token_acct(U, 'TF', 0)], watch=UW + [ata(rvault(U), 'TF'), ata(U, 'TF')])
    S('x-tf-withdraw-1-and-max-fee', [tx('withdraw 1', withdraw(mk='TF')), tx('deposit 10^7', tokens_to(ata(rvault(U), 'TF'), 'TF', 10**7)), tx('withdraw', withdraw(mk='TF'))],
      extra=[token_acct(rvault(U), 'TF', 1), token_acct(U, 'TF', 0)], watch=UW + [ata(rvault(U), 'TF'), ata(U, 'TF')])
    return out


def watched_keys(case):
    return [GLOBAL, A, O, P] + [Pubkey.from_string(k) for k in case['watch']]


def snap(a):
    if a is None:
        return None
    d = bytes(a.data)
    s = {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(d), 'sha256': hashlib.sha256(d).hexdigest()}
    if str(a.owner) in (str(TOKEN), str(TOKEN22)) and len(d) >= 165:
        s['token_amount'] = int.from_bytes(d[64:72], 'little')
        s['token_owner'] = str(Pubkey.from_bytes(d[32:64]))
        if len(d) > 165 and d[165] == 2:
            # Token-2022 account TLV: report the TransferFeeAmount.withheld_amount extension if present
            o = 166
            while o + 4 <= len(d):
                t, n = struct.unpack_from('<HH', d, o)
                if t == 2 and n == 8:
                    s['withheld'] = int.from_bytes(d[o + 4:o + 12], 'little')
                o += 4 + n
    if d[:8] == VAULT_DISC:
        s['decoded'] = decode_vault(d)
    return s


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
            vm.expire_blockhash()
            ixs = [Instruction(Pubkey.from_string(i.get('program_id', str(PROGRAM))), bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
            signers = [KP['PAYER']] + [KP[s] for s in st['signers'] if s != 'PAYER']
            t = Transaction.new_signed_with_payer(ixs, P, signers, vm.latest_blockhash())
            r = vm.send_transaction(t)
            failed = isinstance(r, FailedTransactionMetadata)
            meta = r.meta() if failed else r
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
                'state': {str(k): snap(vm.get_account(k)) for k in watched},
                'compute_units': cu() if callable(cu) else cu,
            })
        final = {}
        for k in watched:
            a = vm.get_account(k)
            final[str(k)] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'data_hex': bytes(a.data).hex()}
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

        def outcome(s):
            return 'ok' if s['error'] is None else (s['custom_error'] or s['error'])
        summary.append({'name': c['name'], 'family': c['family'], 'steps': len(c['steps']),
                        'match': final_match and all(s['match'] for s in step_rows),
                        'labels': [s['label'] for s in step_rows],
                        'outcomes': [outcome(s['original']) for s in step_rows],
                        'outcomes_candidate': [outcome(s['candidate']) for s in step_rows],
                        'cu_original': [s['original']['compute_units'] for s in step_rows],
                        'cu_candidate': [s['candidate']['compute_units'] for s in step_rows]})
    report = {'program_id': str(PROGRAM), 'signer_seeds': SEEDS, 'compared_fields': COMPARED,
              'addresses': {'buyback_vault_0': str(bvault(0)), 'referral_vault_USER': str(rvault(U)), 'mint_LEG': str(LEG), 'mint_T22': str(T22)},
              'scope': 'Pump Fees initialize_buyback / update_buyback_* / sweep_buyback chains (legacy SPL, WSOL, Token-2022 without extensions and with a 1% / max 5,000 transfer fee) and referral withdraw (native and token mode) on persistent LiteSVM state; compared per step: error, custom error, return data, events, program logs, watched account lamports/owner/len/sha256/token amount/decoded vault; final account lamports, owner and bytes. Compute units recorded, not compared.',
              'image_sha256': shas, 'case_count': len(summary), 'step_count': sum(s['steps'] for s in summary),
              'mismatched_cases': [s['name'] for s in summary if not s['match']], 'cases': summary}
    return receipts, report


def gz(obj_bytes):
    return gzip.compress(obj_bytes, compresslevel=9, mtime=0)


def check_idl(root):
    # discriminators and account orders are built locally; confirm them against the repository IDL
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: i for i in idl['instructions']}
    for n in ['initialize_buyback', 'sweep_buyback', 'update_buyback_authority', 'update_buyback_claim_rate_limit', 'withdraw', 'set_authority']:
        assert bytes(ixs[n]['discriminator']) == disc(n), n

    def shape(n):
        return [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs[n]['accounts']]
    assert shape('initialize_buyback') == [('payer', True, True), ('buyback_vault', False, True), ('buyback_vault_ata', False, True), ('system_program', False, False),
                                           ('associated_token_program', False, False), ('mint', False, False), ('token_program', False, False), ('event_authority', False, False), ('program', False, False)]
    assert shape('sweep_buyback') == [('destination', False, True), ('authority', True, True), ('buyback_vault', False, True), ('buyback_vault_ata', False, True), ('destination_ata', False, True),
                                      ('system_program', False, False), ('associated_token_program', False, False), ('mint', False, False), ('token_program', False, False),
                                      ('event_authority', False, False), ('program', False, False)]
    for n in ['update_buyback_authority', 'update_buyback_claim_rate_limit']:
        assert shape(n) == [('authority', True, True), ('fee_program_global', False, True), ('buyback_vault', False, True), ('event_authority', False, False), ('program', False, False)], n
    assert shape('withdraw') == [('user', True, True), ('referral_vault', False, True), ('quote_mint', False, False), ('vault_ata', False, True), ('user_ata', False, True),
                                 ('token_program', False, False), ('system_program', False, False), ('event_authority', False, False), ('program', False, False)]
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['BuybackVault'] == VAULT_DISC and accs['FeeProgramGlobal'] == GLOBAL_DISC


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
