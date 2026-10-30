"""Captured-program checks for the quote accounting of `sell_v3` and on-curve `buy_v3`.

Every case runs on the captured `evidence/original/pump/deployed.so` (with the
captured SPL Token, Token-2022 and ATA programs, all sha256-pinned) and through
`programs/pump/recovered/v3_trade_accounting_host.rs`. Quotes: native SOL,
SPL Token (flat fees), wSOL and USDC (tier tables) and Token-2022 with and
without a `TransferFeeConfig`. State is synthetic: Global, curve, mints, token
accounts and a pump_fees-owned FeeConfig at its canonical address.

A case passes when the captured program and the model agree on the error, or on
the signed lamport and token deltas of the user, curve, buyback recipient and
all their token accounts, the Token-2022 withheld amounts, every byte of the
curve account, and the full TradeEvent bytes in the log and in the
`emit_cpi!` self-call. Buys that would cross into the post-complete pool are
not generated (the model answers `unmodelled`). This pins observed behaviour on
these inputs; it is not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest

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
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_trade_accounting_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
IX = {ix['name']: ix for ix in IDL['instructions']}
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

USER = Keypair.from_seed(bytes([241]) * 32)
CREATOR = Pubkey.from_bytes(bytes([242]) * 32)
BASE = Pubkey.from_bytes(bytes([243]) * 32)
SPL_QUOTE = Pubkey.from_bytes(bytes([244]) * 32)
T22_QUOTE = Pubkey.from_bytes(bytes([245]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([246]) * 32)

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
U64 = 2**64 - 1
rent = lambda n: (n + 128) * 6960
TOKEN_RENT = 2_039_280

# quote kind -> (curve.quote_mint, quote mint account, token program, fee table, transfer fee allowed)
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
        buy=0, amount=10**12, limit=0, partial=0, vtr=1_000_000_000_000_000, vqr=30_000_000_000,
        rtr=793_100_000_000_000, rqr=5_000_000_000, supply=10**15, complete=0, cashback=0, mayhem=0, creator=1,
        curve_creator_bps=0, holder=0, creator_fee=0, protocol_fees=0, curve_lamports=None, quote='sol',
        tf=None, mint_supply=10**15, buyback_bps=5_000, configurable=0, whitelisted=0,
        fee_len=4104, flat=(95, 30), tiers=[(0, 95, 30)], stable=[(0, 20, 5)], exotic=(0, 0, 0),
        user_base=10**13, curve_base=10**15, user_quote=10**14, uva=1,
    )
    c.update(over)
    if c['curve_lamports'] is None:
        reserved = c['rqr'] + c['creator_fee'] + c['protocol_fees'] if c['quote'] == 'sol' else 0
        c['curve_lamports'] = rent(166) + reserved
    return c


def host_line(c):
    tiers = lambda rows: '/'.join(f'{t}:{p}:{cr}' for t, p, cr in rows) or '-'
    tf = ':'.join(map(str, c['tf'])) if c['tf'] else '-'
    kv = dict(
        buy=c['buy'], amount=c['amount'], limit=c['limit'], partial=c['partial'], vtr=c['vtr'], vqr=c['vqr'],
        rtr=c['rtr'], rqr=c['rqr'], supply=c['supply'], complete=c['complete'], cashback=c['cashback'],
        mayhem=c['mayhem'], creator=c['creator'], curve_creator_bps=c['curve_creator_bps'],
        creator_fee=c['creator_fee'], protocol_fees=c['protocol_fees'], curve_lamports=c['curve_lamports'],
        native=int(c['quote'] == 'sol'), table=QUOTES[c['quote']][3], tf=tf, epoch=EPOCH,
        mint_supply=c['mint_supply'], buyback_bps=c['buyback_bps'], configurable=c['configurable'],
        whitelisted=c['whitelisted'], fee_len=c['fee_len'], flat=f"{c['flat'][0]}:{c['flat'][1]}",
        tiers=tiers(c['tiers']), stable=tiers(c['stable']), exotic=':'.join(map(str, c['exotic'])),
        user_base=c['user_base'], curve_base=c['curve_base'], user_quote=c['user_quote'],
    )
    return ' '.join(f'{k}={v}' for k, v in kv.items())


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'v3_trade_accounting_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(c) + '\n' for c in cases)
    out = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
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
        vm.add_program_from_file(key, path)
    vm.set_clock(Clock(100, TIMESTAMP, EPOCH, EPOCH, TIMESTAMP))
    user = USER.pubkey()
    ext = c['tf'] is not None
    vm.set_account(GLOBAL, Account(10**9, global_bytes(c), PUMP))
    vm.set_account(FEE_CONFIG, Account(10**9, fee_config_bytes(c), FEES))
    vm.set_account(user, Account(10**12, b'', SYSTEM))
    vm.set_account(BUYBACK, Account(10**9, b'', SYSTEM))
    vm.set_account(BASE, Account(10**9, mint_bytes(c['mint_supply'], 6), TOKEN))
    vm.set_account(r['quote_mint'], Account(10**9, mint_bytes(10**18, 9 if r['native'] else 6, c['tf']), r['program']))
    vm.set_account(CURVE, Account(c['curve_lamports'], curve_bytes(c, r['curve_field']), PUMP))
    vm.set_account(r['curve_base'], Account(TOKEN_RENT, token_bytes(BASE, CURVE, c['curve_base']), TOKEN))
    vm.set_account(r['user_base'], Account(TOKEN_RENT, token_bytes(BASE, user, c['user_base']), TOKEN))
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
    ix = IX['buy_v3' if c['buy'] else 'sell_v3']
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', c['amount'], c['limit'])
    if c['buy']:
        data += bytes([c['partial']])
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
    name = b'buy' if c['buy'] else b'sell'
    holder = c['holder']
    return (EVENT_DISC['TradeEvent'] + bytes(BASE) + p('Q', m['quote'] if native else 0) + p('Q', m['base_moved'])
            + bytes([c['buy']]) + bytes(USER.pubkey()) + p('q', TIMESTAMP)
            + p('Q', m['vqr'] if native else 0) + p('Q', m['vtr']) + p('Q', m['rqr'] if native else 0) + p('Q', m['rtr'])
            + bytes(32) + p('QQ', m['protocol_fee_bps'], m['protocol_fee'])
            + (bytes(CREATOR) if c['creator'] else bytes(32)) + p('QQ', m['creator_fee_bps'], m['trade_creator_fee'])
            + bytes([0]) + p('QQQq', 0, 0, 0, 0) + p('I', len(name)) + name + bytes([c['mayhem']])
            + p('QQ', 0, 0) + p('QQ', m['buyback_fee_bps'], m['event_buyback_fee']) + p('I', 0)
            + bytes(r['curve_field']) + p('QQQ', m['quote'], m['vqr'], m['rqr'])
            + p('QQ', m['creator_fee_bps'] if holder else 0, m['trade_creator_fee'] if holder else 0)
            + p('Q', m['creator_fee']) + p('Q', m['quote_transfer_fee']))


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
    tokens = {r['user_base']: -m['base_moved'] if not case['buy'] else m['base_moved'],
              r['curve_base']: m['base_moved'] if not case['buy'] else -m['base_moved']}
    if not native:
        tokens.update({r['user_quote']: m['user_quote'], r['curve_quote']: m['curve_quote'], r['recipient']: m['buyback_recipient']})
    for key, want in tokens.items():
        delta = token_amount(a[key][1]) - token_amount(b[key][1])
        if delta != want:
            bad.append(f'tokens {key}: {delta} != {want}')
    if not native:
        sent = -m['curve_quote'] - m['user_quote'] - m['buyback_recipient'] if not case['buy'] else -m['user_quote'] - m['curve_quote'] - m['buyback_recipient']
        held = sum(withheld(a[k][1]) - withheld(b[k][1]) for k in (r['user_quote'], r['curve_quote'], r['recipient']))
        if held != sent:
            bad.append(f'withheld {held} != {sent}')
    curve = bytearray(b[CURVE][1])
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    struct.pack_into('<QQ', curve, 125, m['creator_fee'], m['protocol_fees'])
    curve[48] |= m['completes']
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
    if got['events'] != events:
        bad.append('log event')
    if got['cpi'] != [EMIT_CPI_TAG + e for e in events]:
        bad.append('emit_cpi event')
    return bad


def fixed_cases():
    out = []
    add = lambda label, **k: out.append((label, default_case(**k)))
    for quote in QUOTES:
        for buy in (0, 1):
            for bb in (0, 3_333, 10_000):
                add(f'{quote}-{buy}-bb{bb}', quote=quote, buy=buy, buyback_bps=bb, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-mayhem', quote=quote, buy=buy, mayhem=1, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-no-creator', quote=quote, buy=buy, creator=0, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-configurable', quote=quote, buy=buy, configurable=1, curve_creator_bps=250, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-whitelisted', quote=quote, buy=buy, whitelisted=1, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-holder', quote=quote, buy=buy, holder=1, creator_fee=7, protocol_fees=11, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-no-uva', quote=quote, buy=buy, uva=0, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-rent-short', quote=quote, buy=buy, curve_lamports=rent(166) - 1_000 + (5_000_000_000 if quote == 'sol' else 0), limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-zero', quote=quote, buy=buy, amount=0, limit=10**15)
            add(f'{quote}-{buy}-complete', quote=quote, buy=buy, complete=1, limit=10**15)
            add(f'{quote}-{buy}-cashback', quote=quote, buy=buy, cashback=1, limit=10**15)
            add(f'{quote}-{buy}-fee-len-2511', quote=quote, buy=buy, fee_len=2511, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-fee-len-2512', quote=quote, buy=buy, fee_len=2512, limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-fee-len-4097-exotic', quote=quote, buy=buy, fee_len=4097, exotic=(0, 50, 10), limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-empty-tiers', quote=quote, buy=buy, tiers=[], stable=[], limit=10**15 if buy else 0)
            add(f'{quote}-{buy}-truncation', quote=quote, buy=buy, flat=(U64, 30), tiers=[(0, U64, 30)], stable=[(0, U64, 30)], limit=10**15 if buy else 0)
        # sell slippage at the exact boundary and one above
        base = default_case(quote=quote)
        ok = model([base])[0]
        if ok[0] == 'ok':
            net = ok[1]['user_quote']
            add(f'{quote}-sell-min-exact', quote=quote, limit=net)
            add(f'{quote}-sell-min-short', quote=quote, limit=net + 1)
        buy = default_case(quote=quote, buy=1, limit=10**15)
        ok = model([buy])[0]
        if ok[0] == 'ok':
            cost = -ok[1]['user_quote']
            add(f'{quote}-buy-max-exact', quote=quote, buy=1, limit=cost)
            add(f'{quote}-buy-max-short', quote=quote, buy=1, limit=cost - 1)
        add(f'{quote}-sell-too-many', quote=quote, amount=10**13 + 1)
        add(f'{quote}-sell-over-real-quote', quote=quote, amount=10**14, rqr=1_000)
        add(f'{quote}-sell-fee-over-quote', quote=quote, flat=(9_000, 2_000), tiers=[(0, 9_000, 2_000)], stable=[(0, 9_000, 2_000)])
        add(f'{quote}-sell-vtr-zero', quote=quote, vtr=0)
        add(f'{quote}-accrue-overflow', quote=quote, protocol_fees=U64 - 5, curve_lamports=10**12)
        add(f'{quote}-buy-mayhem-over-real', quote=quote, buy=1, mayhem=1, amount=10**15, rtr=10**12, limit=10**15)
        add(f'{quote}-buy-mayhem-partial', quote=quote, buy=1, mayhem=1, partial=1, amount=10**15, rtr=10**12, limit=10**15)
        add(f'{quote}-buy-vtr-equals-amount', quote=quote, buy=1, vtr=10**12, rtr=10**12, limit=10**15)
        add(f'{quote}-buy-curve-base-short', quote=quote, buy=1, curve_base=10, limit=10**15)
    # tier selection by market cap (unsorted tiers too) for SOL / wSOL, stable tiers for USDC
    mc = 10**15 * 30_000_000_000 // 1_000_000_000_000_000
    for quote in ('sol', 'wsol', 'usdc'):
        for rows in ([(mc + 1, 100, 10), (mc + 2, 200, 20)], [(0, 100, 10), (mc, 200, 20), (mc + 1, 300, 30)],
                     [(0, 100, 10), (mc + 1, 300, 30), (5, 200, 20)]):
            add(f'{quote}-tiers-{rows[0][0]}', quote=quote, tiers=rows, stable=rows)
        add(f'{quote}-tiers-mayhem-supply', quote=quote, mayhem=1, supply=2 * 10**15, tiers=[(0, 100, 10), (mc + 1, 300, 30)], stable=[(0, 100, 10), (mc + 1, 300, 30)])
    add('usdc-len-4072-no-stable', quote='usdc', fee_len=4072)
    for quote in ('sol', 'usdc'):
        # market cap equal to the first threshold: the reverse search picks the last tier at or below it
        add(f'{quote}-tier-tie-first', quote=quote, tiers=[(mc, 100, 10), (5, 200, 20)], stable=[(mc, 100, 10), (5, 200, 20)])
    for quote in ('sol', 'spl'):
        add(f'{quote}-buy-complete-over-real', quote=quote, buy=1, complete=1, amount=10**15, rtr=10**12, limit=10**15)
        add(f'{quote}-buy-cashback-over-real', quote=quote, buy=1, cashback=1, amount=10**15, rtr=10**12, limit=10**15)
    for quote, tf in (('spl', None), ('t22', (0, 0, 0, 250, 10**18))):
        s = model([default_case(quote=quote, buy=1, tf=tf, limit=10**15)])[0][1]
        cost = -s['user_quote']
        buyback = s['protocol_fee'] * 5_000 // 10_000
        add(f'{quote}-buy-user-covers-pool-not-buyback', quote=quote, buy=1, tf=tf, user_quote=cost - buyback, limit=10**15)
        add(f'{quote}-buy-user-exact', quote=quote, buy=1, tf=tf, user_quote=cost, limit=10**15)
    add('usdc-len-4073-stable', quote='usdc', fee_len=4073)
    add('spl-len-4096-no-exotic', quote='spl', fee_len=4096, exotic=(0, 50, 10))
    add('spl-exotic-lp-only', quote='spl', fee_len=4104, exotic=(7, 0, 0))
    # Token-2022 transfer fees: epoch choice, cap, 100 %, both directions
    for buy in (0, 1):
        lim = 10**15 if buy else 0
        for tf in ((100, 10**18, 0, 250, 10**18), (100, 10**18, EPOCH, 250, 10**18), (100, 10**18, EPOCH + 1, 250, 10**18),
                   (0, 0, 0, 1, 1), (500, 1_000, 0, 500, 1_000), (0, 0, 0, 10_000, 5_000), (0, 0, 0, 9_999, 10**18),
                   (0, 0, 0, 0, 10**18), (0, 0, 0, 3, 10**18)):
            add(f't22-tf-{buy}-{tf}', quote='t22', buy=buy, tf=tf, limit=lim)
        add(f't22-tf-{buy}-bb0', quote='t22', buy=buy, tf=(0, 0, 0, 250, 10**18), buyback_bps=0, limit=lim)
        add(f't22-tf-{buy}-mayhem', quote='t22', buy=buy, tf=(0, 0, 0, 250, 10**18), mayhem=1, limit=lim)
        add(f't22-tf-{buy}-small', quote='t22', buy=buy, tf=(0, 0, 0, 250, 10**18), amount=12_345, limit=lim)
    s = model([default_case(quote='t22', tf=(0, 0, 0, 250, 10**18))])[0][1]
    add('t22-tf-sell-min-exact', quote='t22', tf=(0, 0, 0, 250, 10**18), limit=s['user_quote'])
    add('t22-tf-sell-min-short', quote='t22', tf=(0, 0, 0, 250, 10**18), limit=s['user_quote'] + 1)
    s = model([default_case(quote='t22', buy=1, tf=(0, 0, 0, 250, 10**18), limit=10**15)])[0][1]
    add('t22-tf-buy-max-exact', quote='t22', buy=1, tf=(0, 0, 0, 250, 10**18), limit=-s['user_quote'])
    add('t22-tf-buy-max-short', quote='t22', buy=1, tf=(0, 0, 0, 250, 10**18), limit=-s['user_quote'] - 1)
    add('t22-tf-buy-user-short', quote='t22', buy=1, tf=(0, 0, 0, 250, 10**18), user_quote=10, limit=10**15)
    add('spl-buy-user-short', quote='spl', buy=1, user_quote=10, limit=10**15)
    return out


def random_cases(n=160, seed=20261029):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        quote = rng.choice(list(QUOTES) + ['t22', 't22'])
        buy = rng.random() < 0.5
        vtr = rng.choice([rng.randrange(10**14, 2 * 10**15), rng.randrange(1, 10**9)])
        rtr = rng.randrange(1, vtr) if buy and vtr > 1 else rng.randrange(0, 10**15)
        amount = rng.choice([rng.randrange(1, max(2, rtr)), rng.randrange(0, 10**13), 1])
        c = default_case(
            quote=quote, buy=int(buy), amount=amount, vtr=vtr, vqr=rng.randrange(10**6, 10**12), rtr=rtr,
            rqr=rng.randrange(0, 10**11), mayhem=int(rng.random() < 0.15), creator=int(rng.random() < 0.85),
            curve_creator_bps=rng.choice([0, 0, rng.randrange(0, 2_000)]), configurable=int(rng.random() < 0.3),
            holder=int(rng.random() < 0.2), creator_fee=rng.randrange(0, 10**6), protocol_fees=rng.randrange(0, 10**6),
            buyback_bps=rng.choice([0, 10_000, rng.randrange(0, 10_001)]), whitelisted=int(rng.random() < 0.1),
            flat=(rng.randrange(0, 3_000), rng.randrange(0, 3_000)),
            tiers=sorted([(rng.randrange(0, 10**12), rng.randrange(0, 3_000), rng.randrange(0, 3_000)) for _ in range(rng.randrange(1, 4))]),
            stable=[(0, rng.randrange(0, 3_000), rng.randrange(0, 3_000))],
            fee_len=rng.choice([4104, 4104, 4072, 4200]), exotic=rng.choice([(0, 0, 0), (0, rng.randrange(0, 500), rng.randrange(0, 500))]),
            tf=(rng.randrange(0, 10_001), rng.randrange(0, 10**9), rng.randrange(0, 10), rng.randrange(0, 10_001),
                rng.choice([U64, rng.randrange(0, 10**9)])) if quote == 't22' and rng.random() < 0.8 else None,
            limit=0, user_base=rng.choice([10**13, amount, max(0, amount - 1)]),
        )
        if c['whitelisted'] and c['mayhem']:
            continue  # whitelisted mayhem trades resync virtual reserves (see mayhem_virtual_params)
        ans = model([c])[0]
        if ans[0] == 'unmodelled':
            continue
        if ans[0] == 'ok':
            if buy:
                cost = -ans[1]['user_quote']
                c['limit'] = rng.choice([U64, cost, max(0, cost - 1)])
            else:
                net = ans[1]['user_quote']
                c['limit'] = rng.choice([0, net, net + 1])
        else:
            c['limit'] = U64 if buy else 0
        out.append((f'random-{len(out)}', c))
    return out


class V3TradeAccountingCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path

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
        outcomes = {a[1] if a[0] == 'error' else a[0] for _, _, _, a in results}
        for want in ('ok', 6002, 6003, 6005, 6094, 6020, 6021, 6022, 6023, 6024, 6025, 6026, 6096, 6097, 1):
            self.assertIn(want, outcomes)
        oks = [(c, a[1]) for _, c, _, a in results if a[0] == 'ok']
        self.assertTrue(any(c['tf'] and a['quote_transfer_fee'] > 0 for c, a in oks))
        self.assertTrue(any(a['rent_top_up'] > 0 for _, a in oks))
        self.assertGreaterEqual(len({c['quote'] for c, _ in oks}), 5)

    def test_random_cases(self):
        results = self.run_all(random_cases())
        self.assertGreaterEqual(sum(a[0] == 'ok' for *_, a in results), 60)

    def test_checker_rejects_tampered_outcomes(self):
        picks = [default_case(quote='sol'), default_case(quote='t22', tf=(0, 0, 0, 250, 10**18)),
                 default_case(quote='t22', buy=1, tf=(0, 0, 0, 250, 10**18), limit=10**15)]
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
