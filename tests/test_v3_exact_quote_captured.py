"""Captured-program checks for the recovered Pump `buy_exact_quote_in_v3` and crossing `buy_v3`.

Every case runs on the captured `evidence/original/pump/deployed.so` (with the
captured SPL Token, Token-2022 and ATA programs, all sha256-pinned) and through
`programs/pump/recovered/v3_exact_quote_host.rs`. Quotes: native SOL, SPL Token
(flat fees), wSOL and USDC (tier tables) and Token-2022 with and without a
`TransferFeeConfig`. State is synthetic: Global, curve, mints, token accounts
and a pump_fees-owned FeeConfig at its canonical address.

A case passes when the captured program and the model agree on the error, or on
the signed lamport and token deltas of the user, curve, buyback recipient and
all their token accounts, the Token-2022 withheld amounts, every byte of the
curve account, and the TradeEvent, CompleteEvent and PostCompleteBuyEvent bytes
in the log and in the `emit_cpi!` self-call. Whitelisted users on mayhem curves
are not generated (the model answers `unmodelled`). This pins observed behaviour
on these inputs; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_exact_quote_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
IX = {'exact': next(ix for ix in IDL['instructions'] if ix['name'] == 'buy_exact_quote_in_v3'),
      'buy': next(ix for ix in IDL['instructions'] if ix['name'] == 'buy_v3')}
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}
EMIT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')

PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([231]) * 32)
CREATOR = Pubkey.from_bytes(bytes([232]) * 32)
BASE = Pubkey.from_bytes(bytes([233]) * 32)
SPL_QUOTE = Pubkey.from_bytes(bytes([234]) * 32)
T22_QUOTE = Pubkey.from_bytes(bytes([235]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([236]) * 32)

pda = lambda program, *seeds: Pubkey.find_program_address(list(seeds), program)[0]
ata = lambda owner, mint, program=TOKEN: pda(ATA, bytes(owner), bytes(program), bytes(mint))
GLOBAL = pda(PUMP, b'global')
CURVE = pda(PUMP, b'bonding-curve', bytes(BASE))
EVENT_AUTHORITY = pda(PUMP, b'__event_authority')
USER_VOLUME = pda(PUMP, b'user_volume_accumulator', bytes(USER.pubkey()))
FEE_CONFIG, FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)

TX_FEE = 5_000
EPOCH = 5
TIMESTAMP = 1_700_000_000
USER_LAMPORTS = 10**15
U64 = 2**64 - 1
rent = lambda n: (n + 128) * 6960
TOKEN_RENT = 2_039_280
TF_250 = (0, 0, 0, 250, 10**18)

# quote kind -> (curve.quote_mint, quote mint account, token program, fee table)
QUOTES = {
    'sol': (SYSTEM, WSOL, TOKEN, 'tiers'),
    'wsol': (WSOL, WSOL, TOKEN, 'tiers'),
    'usdc': (USDC, USDC, TOKEN, 'stable'),
    'spl': (SPL_QUOTE, SPL_QUOTE, TOKEN, 'flat'),
    't22': (T22_QUOTE, T22_QUOTE, TOKEN22, 'flat'),
}


def mint_bytes(supply, decimals, transfer_fee=None):
    base = struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)
    if transfer_fee is None:
        return base
    older_bps, older_max, newer_epoch, newer_bps, newer_max = transfer_fee
    ext = (bytes(32) + bytes(32) + struct.pack('<Q', 0) + struct.pack('<QQH', 0, older_max, older_bps)
           + struct.pack('<QQH', newer_epoch, newer_max, newer_bps))
    return base.ljust(165, b'\0') + bytes([1]) + struct.pack('<HH', 1, len(ext)) + ext


def token_bytes(mint_key, owner, amount, with_fee_ext=False):
    data = (bytes(mint_key) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(8) + struct.pack('<Q', 0) + struct.pack('<I', 0) + bytes(32))
    if with_fee_ext:
        data += bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    return data


def token_amount(data):
    return struct.unpack_from('<Q', data, 64)[0]


def withheld(data):
    return struct.unpack_from('<Q', data, 170)[0] if len(data) >= 178 else 0


def fee_config_bytes(c):
    def tiers(rows):
        return struct.pack('<I', len(rows)) + b''.join(t.to_bytes(16, 'little') + struct.pack('<QQQ', 0, p, cr) for t, p, cr in rows)
    data = (ACCOUNT_DISC['FeeConfig'] + bytes([FEE_BUMP]) + bytes(32) + struct.pack('<QQQ', 0, *c['flat'])
            + tiers(c['tiers']) + tiers(c['stable']) + struct.pack('<QQQ', *c['exotic']))
    assert len(data) <= c['fee_len'], 'fee_len shorter than the serialized FeeConfig'
    return data.ljust(c['fee_len'], b'\0')


def global_bytes(c):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<Q', data, 146, c['pool_fee'])
    if c['whitelisted']:
        data[451:483] = bytes(USER.pubkey())
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, c['buyback_bps'])
    data[1045] = c['configurable']
    struct.pack_into('<Q', data, 1046, 10_000)
    return bytes(data)


def curve_bytes(c, quote_mint_field):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<5Q', data, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['supply'])
    data[48] = c['complete']
    if c['creator']:
        data[49:81] = bytes(CREATOR)
    data[81] = c['mayhem']
    data[82] = c['cashback']
    data[83:115] = bytes(quote_mint_field)
    struct.pack_into('<Q', data, 115, c['curve_creator_bps'])
    data[124] = c['holder']
    struct.pack_into('<QQ', data, 125, c['creator_fee'], c['protocol_fees'])
    struct.pack_into('<Q', data, 142, c['vqr'])
    return bytes(data)


def default_case(**over):
    c = dict(
        mode='exact', spendable=10**9, min_tokens=1, partial=0, vtr=10**15, vqr=30_000_000_000,
        rtr=793_100_000_000_000, rqr=5_000_000_000, supply=10**15, complete=0, cashback=0, mayhem=0, creator=1,
        curve_creator_bps=0, holder=0, creator_fee=0, protocol_fees=0, curve_lamports=None, quote='sol',
        tf=None, mint_supply=10**15, buyback_bps=5_000, configurable=0, whitelisted=0,
        fee_len=4104, flat=(95, 30), tiers=[(0, 95, 30)], stable=[(0, 20, 5)], exotic=(0, 0, 0),
        curve_base=10**15, user_quote=10**14, uva=1, pool_fee=0,
    )
    c.update(over)
    if c['curve_lamports'] is None:
        reserved = c['rqr'] + c['creator_fee'] + c['protocol_fees'] if c['quote'] == 'sol' else 0
        c['curve_lamports'] = rent(166) + reserved
    return c


def crossing(**over):
    """A curve with 10**12 tokens left, which the default budget fills and passes."""
    return default_case(**dict(dict(rtr=10**12), **over))


def host_line(c):
    tiers = lambda rows: '/'.join(f'{t}:{p}:{cr}' for t, p, cr in rows) or '-'
    tf = ':'.join(map(str, c['tf'])) if c['tf'] else '-'
    kv = dict(
        mode=c.get('mode', 'exact'), spendable=c['spendable'], min_tokens=c['min_tokens'], partial=c['partial'], vtr=c['vtr'], vqr=c['vqr'],
        rtr=c['rtr'], rqr=c['rqr'], supply=c['supply'], complete=c['complete'], cashback=c['cashback'],
        mayhem=c['mayhem'], creator=c['creator'], curve_creator_bps=c['curve_creator_bps'],
        creator_fee=c['creator_fee'], protocol_fees=c['protocol_fees'], curve_lamports=c['curve_lamports'],
        native=int(c['quote'] == 'sol'), table=QUOTES[c['quote']][3], tf=tf, epoch=EPOCH,
        mint_supply=c['mint_supply'], buyback_bps=c['buyback_bps'], configurable=c['configurable'],
        whitelisted=c['whitelisted'], fee_len=c['fee_len'], flat=f"{c['flat'][0]}:{c['flat'][1]}",
        tiers=tiers(c['tiers']), stable=tiers(c['stable']), exotic=':'.join(map(str, c['exotic'])),
        curve_base=c['curve_base'], user_quote=c['user_quote'], pool_fee=c['pool_fee'],
    )
    return ' '.join(f'{k}={v}' for k, v in kv.items())


_HOST = None
_PROGRAM_IMAGES = None


def program_images():
    """Use exactly the captured bytes that passed the digest checks in every VM."""
    global _PROGRAM_IMAGES
    if _PROGRAM_IMAGES is None:
        images = {}
        for path, expected in ELF_SHA256.items():
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'captured program digest mismatch: {path}')
            images[path] = data
        _PROGRAM_IMAGES = images
    return _PROGRAM_IMAGES


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'v3_exact_quote_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(c) + '\n' for c in cases)
    out = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(out) != len(cases):
        raise ValueError(f'model returned {len(out)} answers for {len(cases)} cases')
    answers = []
    for line in out:
        if line == 'unmodelled':
            answers.append(('unmodelled', None))
        elif line.startswith('error:'):
            answers.append(('error', int(line[6:])))
        else:
            answers.append(('ok', {k: int(v) for k, v in (kv.split('=') for kv in line.split()[1:])}))
    return answers


def roles(c):
    curve_field, quote_mint, program, _ = QUOTES[c['quote']]
    native = c['quote'] == 'sol'
    user = USER.pubkey()
    return dict(
        native=native, curve_field=curve_field, quote_mint=quote_mint, program=program,
        user_quote=ata(user, quote_mint, program), curve_quote=ata(CURVE, quote_mint, program),
        recipient=BUYBACK if native else ata(BUYBACK, quote_mint, program),
        user_base=ata(user, BASE), curve_base=ata(CURVE, BASE),
    )


def run_captured(c):
    r = roles(c)
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    for key, path in ((PUMP, PUMP_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF)):
        vm.add_program(key, program_images()[path])
    vm.set_clock(Clock(100, TIMESTAMP, EPOCH, EPOCH, TIMESTAMP))
    user = USER.pubkey()
    ext = c['tf'] is not None
    vm.set_account(GLOBAL, Account(10**9, global_bytes(c), PUMP))
    vm.set_account(FEE_CONFIG, Account(10**9, fee_config_bytes(c), FEES))
    vm.set_account(user, Account(USER_LAMPORTS, b'', SYSTEM))
    vm.set_account(BUYBACK, Account(10**9, b'', SYSTEM))
    vm.set_account(BASE, Account(10**9, mint_bytes(c['mint_supply'], 6), TOKEN))
    vm.set_account(r['quote_mint'], Account(10**9, mint_bytes(10**18, 9 if r['native'] else 6, c['tf']), r['program']))
    vm.set_account(CURVE, Account(c['curve_lamports'], curve_bytes(c, r['curve_field']), PUMP))
    vm.set_account(r['curve_base'], Account(TOKEN_RENT, token_bytes(BASE, CURVE, c['curve_base']), TOKEN))
    vm.set_account(r['user_base'], Account(TOKEN_RENT, token_bytes(BASE, user, 0), TOKEN))
    if not r['native']:
        curve_quote = min(U64, c['rqr'] + c['creator_fee'] + c['protocol_fees'])
        for key, owner, amount in ((r['curve_quote'], CURVE, curve_quote), (r['user_quote'], user, c['user_quote']),
                                   (r['recipient'], BUYBACK, 0)):
            vm.set_account(key, Account(TOKEN_RENT, token_bytes(r['quote_mint'], owner, amount, ext), r['program']))
    if c['uva']:
        uva = bytearray(137)
        uva[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
        uva[8:40] = bytes(user)
        vm.set_account(USER_VOLUME, Account(rent(137), bytes(uva), PUMP))
    names = {
        'global': GLOBAL, 'base_mint': BASE, 'quote_mint': r['quote_mint'], 'base_token_program': TOKEN,
        'quote_token_program': r['program'], 'bonding_curve': CURVE, 'associated_base_bonding_curve': r['curve_base'],
        'associated_quote_bonding_curve': r['curve_quote'], 'user': user, 'associated_base_user': r['user_base'],
        'associated_quote_user': r['user_quote'], 'user_volume_accumulator': USER_VOLUME, 'fee_config': FEE_CONFIG,
        'buyback_fee_recipient': r['recipient'], 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY,
        'program': PUMP,
    }
    ix = IX[c['mode']]
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', c['spendable'], c['min_tokens']) + bytes([c['partial']])
    watched = sorted({user, CURVE, BUYBACK, r['curve_quote'], r['user_quote'], r['recipient'], r['user_base'],
                      r['curve_base'], USER_VOLUME, GLOBAL, FEE_CONFIG, BASE, r['quote_mint']}, key=bytes)

    def snap():
        out = {}
        for key in watched:
            a = vm.get_account(key)
            out[key] = None if a is None else (a.lamports, bytes(a.data), a.owner)
        return out

    before = snap()
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)], user, [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    error = None
    if failed:
        text = str(result.err())
        m = re.search(r'Custom\((\d+)\)', text)
        error = int(m.group(1)) if m else text
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group
           if bytes(ix.instruction().data[:8]) == EMIT_CPI_TAG]
    return dict(error=error, before=before, after=snap(), events=events, cpi=cpi, roles=r)


def trade_event(c, r, m):
    """TradeEvent bytes as the captured program writes them, from the model's numbers."""
    native = r['native']
    p = lambda fmt, *v: struct.pack('<' + fmt, *v)
    name = b'buy_exact_quote_in' if c.get('mode', 'exact') == 'exact' else b'buy'
    holder = c['holder']
    return (EVENT_DISC['TradeEvent'] + bytes(BASE) + p('Q', m['quote'] if native else 0) + p('Q', m['base_moved'])
            + bytes([1]) + bytes(USER.pubkey()) + p('q', TIMESTAMP)
            + p('Q', m['vqr'] if native else 0) + p('Q', m['vtr']) + p('Q', m['rqr'] if native else 0) + p('Q', m['rtr'])
            + bytes(32) + p('QQ', m['protocol_fee_bps'], m['protocol_fee'])
            + (bytes(CREATOR) if c['creator'] else bytes(32)) + p('QQ', m['creator_fee_bps'], m['trade_creator_fee'])
            + bytes([0]) + p('QQQq', 0, 0, 0, 0) + p('I', len(name)) + name + bytes([c['mayhem']])
            + p('QQ', 0, 0) + p('QQ', m['buyback_fee_bps'], m['event_buyback_fee']) + p('I', 0)
            + bytes(r['curve_field']) + p('QQQ', m['quote'], m['vqr'], m['rqr'])
            + p('QQ', m['creator_fee_bps'] if holder else 0, m['trade_creator_fee'] if holder else 0)
            + p('Q', m['creator_fee']) + p('Q', m['quote_transfer_fee']))


def post_event(r, m):
    """PostCompleteBuyEvent bytes: the pool reserves after are before minus and plus the fill."""
    p = lambda fmt, *v: struct.pack('<' + fmt, *v)
    return (EVENT_DISC['PostCompleteBuyEvent'] + bytes(USER.pubkey()) + bytes(BASE) + bytes(CURVE) + bytes(r['curve_field'])
            + p('q', TIMESTAMP) + p('QQ', m['post_base_out'], m['post_quote_in'])
            + p('QQ', m['protocol_fee_bps'], m['post_protocol_fee']) + p('QQ', m['creator_fee_bps'], m['post_creator_fee'])
            + p('Q', m['post_buyback_fee']) + p('QQ', m['post_pool_base'], m['post_pool_quote'])
            + p('QQ', m['post_pool_base'] - m['post_base_out'], m['post_pool_quote'] + m['post_quote_in']))


def lamports(snap, key):
    return snap[key][0] if snap[key] else 0


def check(case, got, answer):
    """List of mismatches between a captured run and the model's answer."""
    kind, m = answer
    bad = []
    if kind == 'unmodelled':
        return ['case is outside the model']
    if kind == 'error':
        if got['error'] != m:
            bad.append(f"error {got['error']!r} != {m}")
        return bad
    if got['error'] is not None:
        return [f"captured failed with {got['error']!r}"]
    r, b, a = got['roles'], got['before'], got['after']
    user = USER.pubkey()
    uva_rent = 0 if case['uva'] else rent(137)
    native = r['native']
    expect_lamports = {
        user: -TX_FEE - m['rent_top_up'] - uva_rent + (m['user_quote'] if native else 0),
        CURVE: m['rent_top_up'] + (m['curve_quote'] if native else 0),
        BUYBACK: m['buyback_recipient'] if native else 0,
        USER_VOLUME: uva_rent,
    }
    for key in a:
        delta = lamports(a, key) - lamports(b, key)
        if delta != expect_lamports.get(key, 0):
            bad.append(f'lamports {key}: {delta} != {expect_lamports.get(key, 0)}')
    delivered = m['base_moved'] + m.get('post_base_out', 0)
    tokens = {r['user_base']: delivered, r['curve_base']: -delivered}
    if not native:
        tokens.update({r['user_quote']: m['user_quote'], r['curve_quote']: m['curve_quote'], r['recipient']: m['buyback_recipient']})
    for key, want in tokens.items():
        delta = token_amount(a[key][1]) - token_amount(b[key][1])
        if delta != want:
            bad.append(f'tokens {key}: {delta} != {want}')
    if not native:
        held = sum(withheld(a[k][1]) - withheld(b[k][1]) for k in (r['user_quote'], r['curve_quote'], r['recipient']))
        if held != -m['user_quote'] - m['curve_quote'] - m['buyback_recipient']:
            bad.append(f'withheld {held}')
    curve = bytearray(b[CURVE][1])
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    struct.pack_into('<QQ', curve, 125, m['creator_fee'], m['protocol_fees'])
    curve[48] |= m['completes']
    if 'post_base_out' in m:
        struct.pack_into('<QQ', curve, 150, m['post_base_out'], m['post_quote_in'])
    if a[CURVE][1] != bytes(curve):
        bad.append('curve bytes')
    for key in a:
        if key not in (CURVE, USER_VOLUME, *tokens) and a[key] and b[key] and a[key][1] != b[key][1]:
            bad.append(f'data changed {key}')
    if case['uva'] and a[USER_VOLUME][1] != b[USER_VOLUME][1]:
        bad.append('user volume accumulator changed')
    events = [trade_event(case, r, m)]
    if m['completes']:
        events.append(EVENT_DISC['CompleteEvent'] + bytes(user) + bytes(BASE) + bytes(CURVE)
                      + struct.pack('<q', TIMESTAMP) + bytes(r['curve_field']))
    if 'post_base_out' in m:
        events.append(post_event(r, m))
    if got['events'] != events:
        bad.append('log event')
    if got['cpi'] != [EMIT_CPI_TAG + e for e in events]:
        bad.append('emit_cpi event')
    return bad


def fixed_cases():
    out = []
    add = lambda label, **k: out.append((label, default_case(**k)))
    cross = lambda label, **k: out.append((label, crossing(**k)))
    for quote in QUOTES:
        q = dict(quote=quote)
        for bb in (0, 3_333, 10_000):
            add(f'{quote}-bb{bb}', buyback_bps=bb, **q)
        add(f'{quote}-mayhem', mayhem=1, **q)
        add(f'{quote}-no-creator', creator=0, **q)
        add(f'{quote}-configurable', configurable=1, curve_creator_bps=250, **q)
        add(f'{quote}-whitelisted', whitelisted=1, **q)
        add(f'{quote}-holder', holder=1, creator_fee=7, protocol_fees=11, **q)
        add(f'{quote}-no-uva', uva=0, **q)
        add(f'{quote}-rent-short', curve_lamports=rent(166) - 1_000 + (5_000_000_000 if quote == 'sol' else 0), **q)
        add(f'{quote}-zero-spend', spendable=0, **q)
        add(f'{quote}-zero-min', min_tokens=0, **q)
        add(f'{quote}-zero-both', spendable=0, min_tokens=0, **q)
        add(f'{quote}-complete', complete=1, **q)
        add(f'{quote}-cashback', cashback=1, **q)
        add(f'{quote}-complete-cashback', complete=1, cashback=1, **q)
        for dust in (1, 2, 3, 4, 5, 9_999, 10_000, 10_125, 10_126, 10_127):
            add(f'{quote}-dust-{dust}', spendable=dust, **q)
            add(f'{quote}-dust-wl-{dust}', spendable=dust, whitelisted=1, **q)
        add(f'{quote}-fee-len-2511', fee_len=2511, **q)
        add(f'{quote}-fee-len-2512', fee_len=2512, **q)
        add(f'{quote}-fee-len-4097-exotic', fee_len=4097, exotic=(0, 50, 10), **q)
        add(f'{quote}-empty-tiers', tiers=[], stable=[], **q)
        add(f'{quote}-empty-tiers-wl', tiers=[], stable=[], whitelisted=1, **q)
        huge = dict(flat=(U64, 30), tiers=[(0, U64, 30)], stable=[(0, U64, 30)])
        add(f'{quote}-truncation', spendable=10**15, **huge, **q)
        add(f'{quote}-bps-overflow', spendable=1, **huge, **q)
        add(f'{quote}-high-bps', flat=(9_000, 2_000), tiers=[(0, 9_000, 2_000)], stable=[(0, 9_000, 2_000)], **q)
        add(f'{quote}-vtr-zero', vtr=0, **q)
        add(f'{quote}-vqr-zero', vqr=0, **q)
        add(f'{quote}-vqr-zero-wl', spendable=1, vqr=0, whitelisted=1, **q)
        add(f'{quote}-accrue-overflow', protocol_fees=U64 - 5, curve_lamports=10**12, **q)
        add(f'{quote}-creator-accrue-overflow', creator_fee=U64 - 5, curve_lamports=10**12, **q)
        add(f'{quote}-curve-base-short', curve_base=10, **q)
        s = model([default_case(**q)])[0][1]
        tokens = s['base_moved']
        add(f'{quote}-min-exact', min_tokens=tokens, **q)
        add(f'{quote}-min-short', min_tokens=tokens + 1, **q)
        add(f'{quote}-user-exact', user_quote=-s['user_quote'], **q)
        add(f'{quote}-user-short', user_quote=-s['user_quote'] - 1, **q)

        cross(f'{quote}-cross', **q)
        cross(f'{quote}-cross-partial', partial=1, **q)
        cross(f'{quote}-cross-bb0', buyback_bps=0, **q)
        cross(f'{quote}-cross-bb10000', buyback_bps=10_000, **q)
        cross(f'{quote}-cross-no-creator', creator=0, **q)
        cross(f'{quote}-cross-configurable', configurable=1, curve_creator_bps=250, **q)
        cross(f'{quote}-cross-holder', holder=1, creator_fee=7, protocol_fees=11, **q)
        cross(f'{quote}-cross-pool-fee', pool_fee=3 * 10**9, **q)
        cross(f'{quote}-cross-pool-fee-over', pool_fee=10**11, **q)
        cross(f'{quote}-cross-pool-base-zero', curve_base=10**12, **q)
        cross(f'{quote}-cross-pool-base-short', curve_base=10**12 - 1, **q)
        cross(f'{quote}-cross-rqr-max', spendable=10**8, rqr=U64, curve_lamports=10**12, **q)
        cross(f'{quote}-cross-mayhem', mayhem=1, **q)
        cross(f'{quote}-cross-mayhem-partial', mayhem=1, partial=1, **q)
        cross(f'{quote}-cross-mayhem-partial-big-min', mayhem=1, partial=1, min_tokens=U64, **q)
        cross(f'{quote}-cross-wl', whitelisted=1, **q)
        cross(f'{quote}-cross-wl-partial', whitelisted=1, partial=1, **q)
        cross(f'{quote}-cross-wl-partial-big-min', whitelisted=1, partial=1, min_tokens=U64, **q)
        cross(f'{quote}-cross-big-min', min_tokens=U64, **q)
        add(f'{quote}-cross-rtr-zero', rtr=0, **q)
        add(f'{quote}-cross-rtr-zero-mayhem', rtr=0, mayhem=1, partial=1, **q)
        add(f'{quote}-cross-all-vtr', vtr=10**12, rtr=10**12, **q)
        cost = -model([crossing(mode='buy', spendable=10**12, min_tokens=U64, **q)])[0][1]['user_quote']
        cross(f'{quote}-cross-curve-only-min', spendable=cost, min_tokens=10**12, **q)
        cross(f'{quote}-cross-curve-only-short', spendable=cost, min_tokens=10**12 + 1, **q)
        for d in (-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11):
            cross(f'{quote}-cross-near-cost-{d}', spendable=cost + d, **q)
        for d in (-1, 0, 1, 2, 3, 4, 200):
            cross(f'{quote}-cross-near-cost-m{d}', spendable=cost + d, mayhem=1, partial=1, **q)
        s = model([crossing(**q)])[0][1]
        delivered = s['base_moved'] + s['post_base_out']
        cross(f'{quote}-cross-min-exact', min_tokens=delivered, **q)
        cross(f'{quote}-cross-min-short', min_tokens=delivered + 1, **q)
        cross(f'{quote}-cross-user-exact', user_quote=-s['user_quote'], **q)
        cross(f'{quote}-cross-user-short', user_quote=-s['user_quote'] - 1, **q)
    for i, tf in enumerate(((100, 10**18, 0, 250, 10**18), (100, 10**18, EPOCH, 250, 10**18), (100, 10**18, EPOCH + 1, 250, 10**18),
                            (0, 0, 0, 1, 1), (500, 1_000, 0, 500, 1_000), (0, 0, 0, 10_000, 5_000), (0, 0, 0, 9_999, 10**18),
                            (0, 0, 0, 0, 10**18), (0, 0, 0, 3, 10**18))):
        q = dict(quote='t22', tf=tf)
        add(f't22-tf-{i}', **q)
        add(f't22-tf-{i}-bb0', buyback_bps=0, **q)
        cross(f't22-tf-{i}-cross', **q)
        cross(f't22-tf-{i}-cross-bb0', buyback_bps=0, **q)
    add('t22-all-withheld', quote='t22', tf=(0, 0, 0, 10_000, U64))
    # The rent top-up reads the reserved quote before the curve flags are checked.
    add('sol-complete-reserved-overflow', complete=1, rqr=U64, protocol_fees=1, curve_lamports=10**12)
    add('sol-cashback-reserved-overflow', cashback=1, rqr=U64, protocol_fees=1, curve_lamports=10**12)
    # No creator: the creator share stays out of the divisor of both nets, not just the curve one.
    for i, (spend, vtr, vqr, rtr, flat) in enumerate(((6, 10**15, 10**6, 1, (9_999, 95)), (6, 10**15, 3 * 10**10, 1, (5_000, 30)),
                                                      (5, 439_128, 410_648, 1, (5_000, 5_000)), (988_231, 10**9, 3 * 10**10, 1, (9_999, 95)))):
        for creator in (0, 1):
            add(f'spl-creator{creator}-share-{i}', quote='spl', spendable=spend, vtr=vtr, vqr=vqr, rtr=rtr, rqr=0, flat=flat, creator=creator,
                buyback_bps=0, partial=1)
    return out + buy_crossing_cases()


def buy_crossing_cases():
    """`buy_v3` past the curve: `spendable` is the token amount, `min_tokens` the cost limit."""
    out = []
    buy = lambda **over: crossing(**dict(dict(mode='buy', spendable=2 * 10**12, min_tokens=10**15), **over))
    add = lambda label, **k: out.append((f'buy-{label}', buy(**k)))
    for quote in QUOTES:
        add(f'{quote}', quote=quote)
        add(f'{quote}-partial', quote=quote, partial=1)
        for bb in (0, 3_333, 10_000):
            add(f'{quote}-bb{bb}', quote=quote, buyback_bps=bb)
        add(f'{quote}-no-creator', quote=quote, creator=0)
        add(f'{quote}-configurable', quote=quote, configurable=1, curve_creator_bps=250)
        add(f'{quote}-holder', quote=quote, holder=1, creator_fee=7, protocol_fees=11)
        add(f'{quote}-no-uva', quote=quote, uva=0)
        add(f'{quote}-rent-short', quote=quote, curve_lamports=rent(166) - 1_000 + (5_000_000_000 if quote == 'sol' else 0))
        add(f'{quote}-one-over', quote=quote, spendable=10**12 + 1)
        add(f'{quote}-at-curve', quote=quote, spendable=10**12)
        add(f'{quote}-complete', quote=quote, complete=1)
        add(f'{quote}-cashback', quote=quote, cashback=1)
        add(f'{quote}-rtr-zero', quote=quote, rtr=0)
        add(f'{quote}-mayhem', quote=quote, mayhem=1)
        add(f'{quote}-mayhem-partial', quote=quote, mayhem=1, partial=1)
        add(f'{quote}-wl', quote=quote, whitelisted=1)
        add(f'{quote}-wl-partial', quote=quote, whitelisted=1, partial=1)
        add(f'{quote}-pool-fee', quote=quote, pool_fee=3 * 10**9)
        add(f'{quote}-pool-fee-over', quote=quote, pool_fee=10**11)
        add(f'{quote}-rqr-max', quote=quote, rqr=U64, curve_lamports=10**12)
        add(f'{quote}-vtr-all', quote=quote, vtr=10**12)
        add(f'{quote}-vtr-under', quote=quote, vtr=10**12 - 1)
        add(f'{quote}-vtr-zero', quote=quote, vtr=0)
        add(f'{quote}-fee-len-2511', quote=quote, fee_len=2511)
        add(f'{quote}-empty-tiers', quote=quote, tiers=[], stable=[])
        add(f'{quote}-truncation', quote=quote, flat=(U64, 30), tiers=[(0, U64, 30)], stable=[(0, U64, 30)])
        add(f'{quote}-accrue-overflow', quote=quote, protocol_fees=U64 - 5, curve_lamports=10**12)
        # The pool must keep tokens after the excess.
        for extra in (-1, 0, 1, 2):
            add(f'{quote}-pool-base{extra}', quote=quote, curve_base=2 * 10**12 + extra)
        add(f'{quote}-curve-base-under-fill', quote=quote, curve_base=10**12 - 1)
        s = model([buy(quote=quote)])[0][1]
        cost = -s['user_quote']
        add(f'{quote}-max-exact', quote=quote, min_tokens=cost)
        add(f'{quote}-max-short', quote=quote, min_tokens=cost - 1)
        add(f'{quote}-pool-quote-one', quote=quote, pool_fee=5 * 10**9 + s['quote'] - 1)
        add(f'{quote}-pool-quote-zero', quote=quote, pool_fee=5 * 10**9 + s['quote'])
    for quote, tf in (('spl', None), ('t22', TF_250)):
        cost = -model([buy(quote=quote, tf=tf)])[0][1]['user_quote']
        add(f'{quote}-user-exact', quote=quote, tf=tf, user_quote=cost)
        add(f'{quote}-user-short', quote=quote, tf=tf, user_quote=cost - 1)
    for i, tf in enumerate(((100, 10**18, 0, 250, 10**18), (100, 10**18, EPOCH, 250, 10**18), (100, 10**18, EPOCH + 1, 250, 10**18),
                            (0, 0, 0, 1, 1), (500, 1_000, 0, 500, 1_000), (0, 0, 0, 10_000, 5_000), (0, 0, 0, 9_999, 10**18),
                            (0, 0, 0, 0, 10**18), (0, 0, 0, 3, 10**18))):
        add(f't22-tf-{i}', quote='t22', tf=tf)
        add(f't22-tf-{i}-bb0', quote='t22', tf=tf, buyback_bps=0)
    return out


def random_cases(n=240, seed=20261030):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        small = lambda: rng.choice([rng.randrange(0, 40), rng.randrange(0, 3000), rng.randrange(0, 10**6), 10**4, 9_999, 10**4 + 1])
        wide = lambda: rng.choice([small(), rng.randrange(0, 10**12), rng.randrange(0, 10**13)])
        bps = lambda: rng.choice([0, 1, 100, 5_000, 9_999, 10_000, 20_000, rng.randrange(0, 10**5)])
        quote = rng.choice(['sol', 'spl', 't22', 't22', 'usdc', 'wsol'])
        vtr = rng.choice([wide(), 10**15])
        rtr = rng.choice([wide(), rng.randrange(0, vtr + 1)])
        tf = (rng.randrange(0, 10_001), wide(), 0, rng.choice([1, 100, 9_999, 10_000, rng.randrange(0, 10_001)]), wide()) if quote == 't22' else None
        c = default_case(
            quote=quote, spendable=wide(), min_tokens=rng.choice([1, 1, wide()]), partial=rng.randrange(2), vtr=vtr, vqr=wide(), rtr=rtr,
            rqr=rng.randrange(0, 10**12), mayhem=int(rng.random() < .2), whitelisted=int(rng.random() < .15),
            creator=rng.randrange(2), buyback_bps=rng.choice([0, 10_000, 5_000]), tf=tf, flat=(bps(), bps()),
            tiers=[(0, bps(), bps())], stable=[(0, bps(), bps())], pool_fee=rng.choice([0, rng.randrange(0, 10**12)]),
            curve_base=rng.choice([10**15, 10**13, rtr + rng.randrange(0, 10**10)]), user_quote=rng.choice([10**14, wide()]))
        if c['whitelisted'] and c['mayhem']:
            continue  # whitelisted mayhem trades resync virtual reserves (see mayhem_virtual_params)
        if rng.random() < 0.3:
            c.update(mode='buy', spendable=rng.randrange(1, 2 * max(rtr, 1) + 1), min_tokens=U64)
            ans = model([c])[0]
            if ans[0] == 'ok':
                cost = -ans[1]['user_quote']
                c['min_tokens'] = rng.choice([U64, cost, max(0, cost - 1)])
        out.append((f'random-{len(out)}', c))
    return out


class V3ExactQuoteCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program_images()

    def test_model_requires_one_answer_per_case(self):
        case = default_case()
        for output in ('', 'error:6020\nerror:6020\n'):
            with self.subTest(output=output), mock.patch(__name__ + '.host_binary', return_value=Path('unused')), \
                    mock.patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, output)):
                with self.assertRaisesRegex(ValueError, 'answers for 1 cases'):
                    model([case])

    def test_every_vm_uses_the_verified_program_images(self):
        # Mutate private copies, never the retained evidence. Both VMs must
        # still execute the bytes admitted before the concurrent replacement.
        with tempfile.TemporaryDirectory() as temporary:
            copies = {}
            for index, (original, digest) in enumerate(ELF_SHA256.items()):
                path = Path(temporary) / f'{index}.so'
                path.write_bytes(program_images()[original])
                copies[original] = path
            pins = {copies[path]: digest for path, digest in ELF_SHA256.items()}
            with mock.patch.multiple(sys.modules[__name__],
                                     PUMP_ELF=copies[PUMP_ELF], TOKEN_ELF=copies[TOKEN_ELF],
                                     TOKEN22_ELF=copies[TOKEN22_ELF], ATA_ELF=copies[ATA_ELF],
                                     ELF_SHA256=pins, _PROGRAM_IMAGES=None):
                before = run_captured(default_case())
                PUMP_ELF.write_bytes(b'concurrently replaced program')
                after = run_captured(default_case())
            self.assertEqual(before, after)

    def run_all(self, labelled):
        answers = model([c for _, c in labelled])
        results = []
        for (label, c), answer in zip(labelled, answers):
            got = run_captured(c)
            with self.subTest(label):
                self.assertEqual(check(c, got, answer), [], label)
            results.append((label, c, got, answer))
        return results

    def test_fixed_cases(self):
        results = self.run_all(fixed_cases())
        self.assertGreaterEqual(len(results), 30)
        self.assertTrue(any(c['mode'] == 'buy' and a[0] == 'ok' and 'post_base_out' in a[1] for _, c, _, a in results))
        self.assertTrue(any(c['mode'] == 'exact' and a[0] == 'ok' and 'post_base_out' in a[1] for _, c, _, a in results))
        outcomes = {a[1] if a[0] == 'error' else a[0] for _, _, _, a in results}
        for want in ('ok', 1, 6002, 6005, 6020, 6021, 6024, 6025, 6026, 6041, 6042, 6094, 6096, 6097):
            self.assertIn(want, outcomes)
        oks = [(c, a[1]) for _, c, _, a in results if a[0] == 'ok']
        self.assertTrue(any(c['tf'] and a['quote_transfer_fee'] > 0 for c, a in oks))
        self.assertTrue(any(a['rent_top_up'] > 0 for _, a in oks))
        self.assertGreaterEqual(len({c['quote'] for c, _ in oks}), 5)

    def test_random_cases(self):
        results = self.run_all(random_cases())
        self.assertGreaterEqual(sum(a[0] == 'ok' for *_, a in results), 60)

    def test_checker_rejects_tampered_outcomes(self):
        picks = [default_case(quote='sol'), crossing(quote='sol'), crossing(quote='t22', tf=TF_250),
                 crossing(mode='buy', quote='sol', spendable=2 * 10**12, min_tokens=10**15)]
        for c, answer in zip(picks, model(picks)):
            got = run_captured(c)
            self.assertEqual(check(c, got, answer), [])
            for field in answer[1]:
                bent = dict(answer[1])
                bent[field] += 1
                self.assertNotEqual(check(c, got, ('ok', bent)), [], field)
            self.assertNotEqual(check(c, got, ('error', 6024)), [])


if __name__ == '__main__':
    unittest.main()
