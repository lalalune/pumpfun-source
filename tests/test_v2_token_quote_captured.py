"""Captured-program checks for `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2` on token quotes.

Every case runs on the captured `evidence/original/pump/deployed.so` with the
captured Pump Fees, SPL Token, Token-2022 and ATA programs (all sha256-pinned)
and through `programs/pump/recovered/v2_token_quote_host.rs`. Quotes: wSOL
(fee tiers), USDC (stable tiers), another SPL mint (flat fees) and Token-2022
with and without a `TransferFeeConfig`. State is synthetic: Global, curve, mints,
token accounts and a pump_fees-owned FeeConfig at its canonical address.

A case passes when the captured program and the model agree on the error and committed-state rollback (apart from the transaction fee), or on
the lamport movements, every quote and base token balance, the Token-2022
withheld amounts, the stored curve and accumulator bytes and the full TradeEvent
and CompleteEvent bytes in the log and in the `emit_cpi!` self-call. This pins
observed behavior on these inputs only; it is not a byte-identity claim.
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
from unittest.mock import patch

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
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v2_token_quote_host.rs'

_PROGRAM_BYTES = None


def admit_program_images(expected):
    images = {}
    for path, digest in expected.items():
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError(f'captured program hash mismatch: {path}')
        images[path] = raw
    return images


def program_images():
    global _PROGRAM_BYTES
    if _PROGRAM_BYTES is None:
        _PROGRAM_BYTES = admit_program_images(ELF_SHA256)
    return _PROGRAM_BYTES


def parse_model_output(text, count):
    lines = text.splitlines()
    if len(lines) != count:
        raise ValueError(f'model returned {len(lines)} answers for {count} cases')
    answers = []
    for line in lines:
        if line.startswith('error:'):
            answers.append(('error', int(line[6:])))
        elif line in ('panic', 'invalid-account-data'):
            answers.append(('error', line))
        elif line.startswith('ok '):
            fields = [word.split('=', 1) for word in line.split()[1:]]
            if any(len(field) != 2 for field in fields) or len({field[0] for field in fields}) != len(fields):
                raise ValueError('malformed or duplicate model answer field')
            answers.append(('ok', {key: int(value) for key, value in fields}))
        else:
            raise ValueError('unknown model answer: ' + line)
    return answers


def rollback_differences(before, after):
    expected = dict(before)
    payer = before[USER.pubkey()]
    if payer is not None:
        expected[USER.pubkey()] = (payer[0] - TX_FEE, *payer[1:])
    return [] if after == expected else ['failed transaction changed state beyond transaction fee']

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

USER = Keypair.from_seed(bytes([231]) * 32)
CREATOR = Pubkey.from_bytes(bytes([232]) * 32)
BASE = Pubkey.from_bytes(bytes([233]) * 32)
SPL_QUOTE = Pubkey.from_bytes(bytes([234]) * 32)
T22_QUOTE = Pubkey.from_bytes(bytes([235]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([236]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([237]) * 32)
RESERVED = Pubkey.from_bytes(bytes([238]) * 32)
OTHER = Pubkey.from_bytes(bytes([239]) * 32)

pda = lambda program, *seeds: Pubkey.find_program_address(list(seeds), program)[0]
ata = lambda owner, mint, program=TOKEN: pda(ATA, bytes(owner), bytes(program), bytes(mint))
GLOBAL = pda(PUMP, b'global')
CURVE = pda(PUMP, b'bonding-curve', bytes(BASE))
EVENT_AUTHORITY = pda(PUMP, b'__event_authority')
GLOBAL_VOLUME = pda(PUMP, b'global_volume_accumulator')
USER_VOLUME = pda(PUMP, b'user_volume_accumulator', bytes(USER.pubkey()))
FEE_CONFIG, FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)
SHARING = pda(FEES, b'sharing-config', bytes(BASE))

TX_FEE = 5_000
EPOCH = 5
TIMESTAMP = 1_700_000_000
U64 = 2**64 - 1
rent = lambda n: (n + 128) * 6960
TOKEN_RENT = 2_039_280
LIMIT = 10**15

# quote kind -> (quote mint, token program, fee table, decimals)
QUOTES = {
    'wsol': (WSOL, TOKEN, 'tiers', 9),
    'usdc': (USDC, TOKEN, 'stable', 6),
    'spl': (SPL_QUOTE, TOKEN, 'flat', 6),
    't22': (T22_QUOTE, TOKEN22, 'flat', 6),
}
OPS = ('sell', 'buy', 'exact')
IX_NAME = {'sell': 'sell_v2', 'buy': 'buy_v2', 'exact': 'buy_exact_quote_in_v2'}
EVENT_NAME = {'sell': b'sell', 'buy': b'buy', 'exact': b'buy_exact_quote_in'}


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
    # TransferFeeAmount, behind ImmutableOwner on an account the ATA program made
    at = 166
    while at + 4 <= len(data):
        kind, size = struct.unpack_from('<HH', data, at)
        if kind == 2:
            return struct.unpack_from('<Q', data, at + 4)[0]
        at += 4 + size
    return 0


def fee_config_bytes(c):
    def tiers(rows):
        return struct.pack('<I', len(rows)) + b''.join(t.to_bytes(16, 'little') + struct.pack('<QQQ', 0, p, cr) for t, p, cr in rows)
    data = (ACCOUNT_DISC['FeeConfig'] + bytes([FEE_BUMP]) + bytes(32) + struct.pack('<QQQ', 0, *c['flat'])
            + tiers(c['tiers']) + tiers(c['stable']) + struct.pack('<QQQ', *c['exotic']))
    if len(data) > c['fee_len']:
        raise ValueError('fee_len shorter than the serialized FeeConfig')
    return data.ljust(c['fee_len'], b'\0')


def global_bytes(c):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    if c['whitelisted']:
        data[451:483] = bytes(USER.pubkey())
    data[483:515] = bytes(RESERVED)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, c['buyback_bps'])
    data[1045] = c['configurable']
    struct.pack_into('<Q', data, 1046, 10_000)
    return bytes(data)


def curve_bytes(c, quote_mint):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<5Q', data, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['supply'])
    data[48] = c['complete']
    if c['creator']:
        data[49:81] = bytes(CREATOR)
    data[81] = c['mayhem']
    data[82] = c['cashback']
    data[83:115] = bytes(quote_mint)
    struct.pack_into('<Q', data, 115, c['curve_creator_bps'])
    data[124] = c['holder']
    struct.pack_into('<Q', data, 142, c['vqr'])
    return bytes(data)


def default_case(**over):
    c = dict(
        op='sell', amount=None, limit=None, partial=0, vtr=1_000_000_000_000_000, vqr=30_000_000_000,
        rtr=793_100_000_000_000, rqr=5_000_000_000, supply=10**15, complete=0, cashback=0, mayhem=0, creator=1,
        curve_creator_bps=0, holder=0, curve_lamports=rent(166), vault_lamports=0, quote='spl', tf=None,
        mint_supply=10**15, buyback_bps=5_000, configurable=0, whitelisted=0, fee_len=4104, flat=(95, 30),
        tiers=[(0, 95, 30)], stable=[(0, 20, 5)], exotic=(0, 0, 0), user_base=10**13, curve_base=10**15,
        user_quote=10**14, curve_quote=None, fee_recipient_ok=1, buyback_ok=1, bad='none', uva=1, missing=(),
    )
    c.update(over)
    if c['amount'] is None:
        c['amount'] = 10**8 if c['op'] == 'exact' else 10**12
    if c['limit'] is None:
        c['limit'] = {'sell': 0, 'buy': LIMIT, 'exact': 1}[c['op']]
    if c['curve_quote'] is None:
        c['curve_quote'] = c['rqr']
    return c


def host_line(c):
    tiers = lambda rows: '/'.join(f'{t}:{p}:{cr}' for t, p, cr in rows) or '-'
    tf = ':'.join(map(str, c['tf'])) if c['tf'] else '-'
    kv = dict(
        op=c['op'], amount=c['amount'], limit=c['limit'], partial=c['partial'], vtr=c['vtr'], vqr=c['vqr'],
        rtr=c['rtr'], rqr=c['rqr'], supply=c['supply'], complete=c['complete'], cashback=c['cashback'],
        mayhem=c['mayhem'], creator=c['creator'], curve_creator_bps=c['curve_creator_bps'],
        curve_lamports=c['curve_lamports'], vault_lamports=c['vault_lamports'], table=QUOTES[c['quote']][2], tf=tf,
        epoch=EPOCH, mint_supply=c['mint_supply'], buyback_bps=c['buyback_bps'], configurable=c['configurable'],
        whitelisted=c['whitelisted'], fee_len=c['fee_len'], flat=f"{c['flat'][0]}:{c['flat'][1]}",
        tiers=tiers(c['tiers']), stable=tiers(c['stable']), exotic=':'.join(map(str, c['exotic'])),
        user_base=c['user_base'], curve_base=c['curve_base'], user_quote=c['user_quote'],
        curve_quote=c['curve_quote'], fee_recipient_ok=c['fee_recipient_ok'], buyback_ok=c['buyback_ok'], bad=c['bad'],
    )
    return ' '.join(f'{k}={v}' for k, v in kv.items())


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'v2_token_quote_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(c) + '\n' for c in cases)
    out = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    return parse_model_output('\n'.join(out), len(cases))


def roles(c):
    quote_mint, program, _, decimals = QUOTES[c['quote']]
    user = USER.pubkey()
    vault = pda(PUMP, b'creator-vault', bytes(CREATOR if c['creator'] else SYSTEM))
    recipient = RESERVED if c['mayhem'] else FEE_RECIPIENT
    q = lambda owner: ata(owner, quote_mint, program)
    return dict(
        quote_mint=quote_mint, program=program, decimals=decimals, vault=vault, recipient=recipient,
        user_quote=q(user), curve_quote=q(CURVE), vault_quote=q(vault), uva_quote=q(USER_VOLUME),
        recipient_quote=q(recipient), buyback_quote=q(BUYBACK), user_base=ata(user, BASE), curve_base=ata(CURVE, BASE),
    )


_VM = None
_TOUCHED = set()


def fresh_vm():
    # Loading the five programs dominates a case, so they stay loaded and the
    # accounts of the previous case are wiped instead.
    global _VM
    if _VM is None:
        _VM = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((PUMP, PUMP_ELF), (FEES, FEES_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF)):
            _VM.add_program(key, program_images()[path])
        _VM.set_clock(Clock(100, TIMESTAMP, EPOCH, EPOCH, TIMESTAMP))
    for key in _TOUCHED:
        _VM.set_account(key, Account(0, b'', SYSTEM))
    _TOUCHED.clear()
    return _VM


def run_captured(c):
    r = roles(c)
    vm = fresh_vm()
    user = USER.pubkey()
    ext = c['tf'] is not None
    vm.set_account(GLOBAL, Account(10**9, global_bytes(c), PUMP))
    vm.set_account(FEE_CONFIG, Account(10**9, fee_config_bytes(c), FEES))
    vm.set_account(GLOBAL_VOLUME, Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP))
    vm.set_account(user, Account(10**13, b'', SYSTEM))
    vm.set_account(BASE, Account(10**9, mint_bytes(c['mint_supply'], 6), TOKEN))
    vm.set_account(r['quote_mint'], Account(10**9, mint_bytes(10**18, r['decimals'], c['tf']), r['program']))
    vm.set_account(CURVE, Account(c['curve_lamports'], curve_bytes(c, r['quote_mint']), PUMP))
    vm.set_account(r['curve_base'], Account(TOKEN_RENT, token_bytes(BASE, CURVE, c['curve_base']), TOKEN))
    vm.set_account(r['user_base'], Account(TOKEN_RENT, token_bytes(BASE, user, c['user_base']), TOKEN))
    if c['vault_lamports']:
        vm.set_account(r['vault'], Account(c['vault_lamports'], b'', SYSTEM))
    quote_accounts = {'curve': (r['curve_quote'], CURVE, c['curve_quote']), 'user': (r['user_quote'], user, c['user_quote']),
                      'vault': (r['vault_quote'], r['vault'], 0), 'uva': (r['uva_quote'], USER_VOLUME, 0),
                      'recipient': (r['recipient_quote'], r['recipient'], 0), 'buyback': (r['buyback_quote'], BUYBACK, 0)}
    if c['bad'] == 'curve_missing':
        del quote_accounts['curve']
    for name, (key, owner, amount) in quote_accounts.items():
        if name not in c['missing']:
            mint = BASE if name == 'user' and c['bad'] == 'user_mint' else r['quote_mint']
            vm.set_account(key, Account(TOKEN_RENT, token_bytes(mint, owner, amount, ext), r['program']))
    if c['uva']:
        uva = bytearray(137)
        uva[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
        uva[8:40] = bytes(user)
        vm.set_account(USER_VOLUME, Account(rent(137), bytes(uva), PUMP))
    stray = Pubkey.from_bytes(bytes([240]) * 32)
    wrong = lambda slot, key: stray if c['bad'] == slot else key
    recipient = r['recipient'] if c['fee_recipient_ok'] else OTHER
    buyback = BUYBACK if c['buyback_ok'] else OTHER
    names = {
        'global': GLOBAL, 'base_mint': BASE, 'quote_mint': r['quote_mint'], 'base_token_program': TOKEN,
        'quote_token_program': r['program'], 'associated_token_program': ATA, 'fee_recipient': recipient,
        'associated_quote_fee_recipient': wrong('recipient_key', ata(recipient, r['quote_mint'], r['program'])),
        'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': wrong('buyback_key', ata(buyback, r['quote_mint'], r['program'])),
        'bonding_curve': CURVE, 'associated_base_bonding_curve': r['curve_base'],
        'associated_quote_bonding_curve': wrong('curve_key', r['curve_quote']), 'user': user,
        'associated_base_user': r['user_base'], 'associated_quote_user': wrong('user_key', r['user_quote']),
        'creator_vault': r['vault'], 'associated_creator_vault': wrong('vault_key', r['vault_quote']),
        'sharing_config': SHARING, 'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
        'associated_user_volume_accumulator': wrong('accumulator_key', r['uva_quote']), 'fee_config': FEE_CONFIG,
        'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX[IX_NAME[c['op']]]
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', c['amount'], c['limit'])
    if c['op'] != 'sell':
        data += bytes([c['partial']])
    watched = sorted({user, CURVE, BUYBACK, r['vault'], r['recipient'], USER_VOLUME, GLOBAL, FEE_CONFIG, BASE,
                      r['quote_mint'], r['user_quote'], r['curve_quote'], r['vault_quote'], r['uva_quote'],
                      r['recipient_quote'], r['buyback_quote'], r['user_base'], r['curve_base']}, key=bytes)

    _TOUCHED.update(watched)

    def snap():
        out = {}
        for key in watched:
            a = vm.get_account(key)
            out[key] = None if a is None or a.lamports == 0 else (a.lamports, bytes(a.data), a.owner)
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
        if 'ProgramFailedToComplete' in text:
            error = 'panic'
        elif 'InvalidAccountData' in text:
            error = 'invalid-account-data'
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group
           if bytes(ix.instruction().data[:8]) == EMIT_CPI_TAG]
    return dict(error=error, before=before, after=snap(), events=events, cpi=cpi, roles=r, logs=meta.logs())


def trade_event(c, r, m):
    """TradeEvent bytes as the captured program writes them, from the model's numbers."""
    p = lambda fmt, *v: struct.pack('<' + fmt, *v)
    name = EVENT_NAME[c['op']]
    holder, cashback = c['holder'], c['cashback']
    recipient = r['recipient']
    bps, fee = m['creator_fee_bps'], m['creator_fee']
    return (EVENT_DISC['TradeEvent'] + bytes(BASE) + p('Q', 0) + p('Q', m['base_moved'])
            + bytes([c['op'] != 'sell']) + bytes(USER.pubkey()) + p('q', TIMESTAMP)
            + p('Q', 0) + p('Q', m['vtr']) + p('Q', 0) + p('Q', m['rtr'])
            + bytes(recipient) + p('QQ', m['protocol_fee_bps'], m['protocol_fee'])
            + (bytes(CREATOR) if c['creator'] else bytes(32)) + p('QQ', 0 if cashback else bps, 0 if cashback else fee)
            + bytes([0]) + p('QQQq', 0, 0, 0, 0) + p('I', len(name)) + name + bytes([c['mayhem']])
            + p('QQ', bps if cashback else 0, fee if cashback else 0)
            + p('QQ', m['buyback_fee_bps'], m['buyback_received']) + p('I', 0)
            + bytes(r['quote_mint']) + p('QQQ', m['quote'], m['vqr'], m['rqr'])
            + p('QQ', bps if holder else 0, fee if holder else 0)
            + p('Q', 0) + p('Q', m['quote_transfer_fee']))


def lamports(snap, key):
    return snap[key][0] if snap[key] else 0


def check(case, got, answer):
    """List of mismatches between a captured run and the model's answer."""
    kind, m = answer
    bad = []
    if kind == 'error':
        if got['error'] != m:
            bad.append(f"error {got['error']!r} != {m}")
        return bad + rollback_differences(got['before'], got['after'])
    if got['error'] is not None:
        return [f"captured failed with {got['error']!r}"]
    r, b, a = got['roles'], got['before'], got['after']
    user = USER.pubkey()
    uva_rent = 0 if case['uva'] else rent(137)
    creator_key = r['uva_quote'] if case['cashback'] else r['vault_quote']
    created = {r[k] for k in ('user_quote', 'curve_quote', 'vault_quote', 'uva_quote', 'recipient_quote', 'buyback_quote')
               if b[r[k]] is None}
    ata_rent = sum(lamports(a, k) for k in created)
    expect = {user: -TX_FEE - m['vault_rent'] - m['curve_rent'] - uva_rent - ata_rent, CURVE: m['curve_rent'],
              r['vault']: m['vault_rent'], USER_VOLUME: uva_rent}
    for key in created:
        expect[key] = lamports(a, key)
    for key in a:
        delta = lamports(a, key) - lamports(b, key)
        if delta != expect.get(key, 0):
            bad.append(f'lamports {key}: {delta} != {expect.get(key, 0)}')
    balance = lambda s, key: token_amount(s[key][1]) if s[key] else 0
    sell = case['op'] == 'sell'
    quote_moves = {
        r['user_quote']: (m['user_received'] if sell else -m['user_sent'], m['user_sent'] - m['user_received'] if sell else 0),
        r['curve_quote']: (-m['curve_sent'] if sell else m['curve_received'], 0 if sell else m['curve_sent'] - m['curve_received']),
        r['recipient_quote']: (m['recipient_received'], m['recipient_sent'] - m['recipient_received']),
        r['buyback_quote']: (m['buyback_received'], m['buyback_sent'] - m['buyback_received']),
    }
    moved = (m['creator_received'], m['creator_sent'] - m['creator_received'])
    quote_moves[creator_key] = moved
    other = r['vault_quote'] if case['cashback'] else r['uva_quote']
    quote_moves[other] = (0, 0)
    for key, (amount, fee) in quote_moves.items():
        delta = balance(a, key) - balance(b, key)
        if delta != amount:
            bad.append(f'tokens {key}: {delta} != {amount}')
        kept = (withheld(a[key][1]) if a[key] else 0) - (withheld(b[key][1]) if b[key] else 0)
        if kept != fee:
            bad.append(f'withheld {key}: {kept} != {fee}')
    base = -m['base_moved'] if sell else m['base_moved']
    if balance(a, r['user_base']) - balance(b, r['user_base']) != base:
        bad.append('user base')
    if balance(a, r['curve_base']) - balance(b, r['curve_base']) != -base:
        bad.append('curve base')
    curve = bytearray(b[CURVE][1])
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    curve[48] |= m['completes']
    if a[CURVE][1] != bytes(curve):
        bad.append('curve bytes')
    if case['uva']:
        uva = bytearray(b[USER_VOLUME][1])
    else:
        uva = bytearray(137)
        uva[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
        uva[8:40] = bytes(user)
        uva[136] = a[USER_VOLUME][1][136]
    if case['cashback']:
        struct.pack_into('<Q', uva, 90, m['creator_fee'])
    if a[USER_VOLUME][1] != bytes(uva):
        bad.append('user volume accumulator bytes')
    events = [trade_event(case, r, m)]
    if m['completes']:
        events.append(EVENT_DISC['CompleteEvent'] + bytes(user) + bytes(BASE) + bytes(CURVE)
                      + struct.pack('<q', TIMESTAMP) + bytes(r['quote_mint']))
    if got['events'] != events:
        bad.append('log event')
    if got['cpi'] != [EMIT_CPI_TAG + e for e in events]:
        bad.append('emit_cpi event')
    return bad


def fixed_cases():
    out = []
    add = lambda label, **k: out.append((label, default_case(**k)))
    for quote in QUOTES:
        for op in OPS:
            tag = f'{quote}-{op}'
            for bb in (0, 3_333, 10_000):
                add(f'{tag}-bb{bb}', quote=quote, op=op, buyback_bps=bb)
            add(f'{tag}-mayhem', quote=quote, op=op, mayhem=1)
            add(f'{tag}-no-creator', quote=quote, op=op, creator=0)
            add(f'{tag}-configurable', quote=quote, op=op, configurable=1, curve_creator_bps=250)
            add(f'{tag}-whitelisted', quote=quote, op=op, whitelisted=1)
            add(f'{tag}-holder', quote=quote, op=op, holder=1)
            add(f'{tag}-cashback', quote=quote, op=op, cashback=1)
            add(f'{tag}-no-uva', quote=quote, op=op, uva=0)
            add(f'{tag}-rent-short', quote=quote, op=op, curve_lamports=rent(166) - 1_000)
            add(f'{tag}-rent-over', quote=quote, op=op, curve_lamports=rent(166) + 1_000)
            for vault in (1, 890_879, 890_880):
                add(f'{tag}-vault{vault}', quote=quote, op=op, vault_lamports=vault)
            add(f'{tag}-zero', quote=quote, op=op, amount=0)
            add(f'{tag}-complete', quote=quote, op=op, complete=1)
            add(f'{tag}-bad-recipient', quote=quote, op=op, fee_recipient_ok=0)
            add(f'{tag}-bad-buyback', quote=quote, op=op, buyback_ok=0)
            add(f'{tag}-fee-len-2511', quote=quote, op=op, fee_len=2511)
            add(f'{tag}-fee-len-2512', quote=quote, op=op, fee_len=2512)
            add(f'{tag}-fee-len-4097-exotic', quote=quote, op=op, fee_len=4097, exotic=(0, 50, 10))
            add(f'{tag}-empty-tiers', quote=quote, op=op, tiers=[], stable=[])
            add(f'{tag}-truncation', quote=quote, op=op, flat=(U64, 30), tiers=[(0, U64, 30)], stable=[(0, U64, 30)])
            for slot in ('curve_key', 'user_key', 'vault_key', 'accumulator_key', 'recipient_key', 'buyback_key',
                         'curve_missing'):
                add(f'{tag}-{slot}', quote=quote, op=op, bad=slot)
            add(f'{tag}-user-mint', quote=quote, op=op, bad='user_mint')
            add(f'{tag}-curve-base-short', quote=quote, op=op, curve_base=10)
            add(f'{tag}-user-quote-short', quote=quote, op=op, user_quote=10)
        add(f'{quote}-sell-too-many', quote=quote, amount=10**13 + 1)
        add(f'{quote}-sell-over-real-quote', quote=quote, amount=10**14, rqr=1_000)
        add(f'{quote}-sell-curve-account-short', quote=quote, curve_quote=1_000)
        add(f'{quote}-sell-fee-over-quote', quote=quote, flat=(9_000, 2_000), tiers=[(0, 9_000, 2_000)], stable=[(0, 9_000, 2_000)])
        add(f'{quote}-sell-vtr-zero', quote=quote, vtr=0)
        add(f'{quote}-buy-over-real', quote=quote, op='buy', amount=10**13, rtr=10**12)
        add(f'{quote}-buy-partial', quote=quote, op='buy', partial=1, amount=10**13, rtr=10**12)
        add(f'{quote}-buy-partial-zero', quote=quote, op='buy', partial=1, rtr=0)
        add(f'{quote}-buy-complete-fill', quote=quote, op='buy', amount=10**12, rtr=10**12)
        add(f'{quote}-buy-vtr-equals-amount', quote=quote, op='buy', vtr=10**12, rtr=10**12)
        add(f'{quote}-exact-over-real', quote=quote, op='exact', amount=10**10, rtr=10**12)
        add(f'{quote}-exact-partial', quote=quote, op='exact', partial=1, amount=10**10, rtr=10**12)
        add(f'{quote}-exact-partial-short', quote=quote, op='exact', partial=1, amount=30_100_000, rtr=10**12, limit=1)
        add(f'{quote}-exact-dust', quote=quote, op='exact', amount=1)
        add(f'{quote}-exact-two', quote=quote, op='exact', amount=2)
        add(f'{quote}-exact-three', quote=quote, op='exact', amount=3)
        add(f'{quote}-exact-min-high', quote=quote, op='exact', limit=U64)
        add(f'{quote}-exact-zero-limit', quote=quote, op='exact', limit=0)
    # exact-quote fees are sized on the budget first, so 6025 comes before the 6024 bps sum and 6041
    for quote, tf in (('spl', None), ('t22', (0, 0, 0, 250, 10**18))):
        for amount in (159_999, 160_000, 164_102, 164_103, 10**8):
            for flat in ((2**60, 0), (0, 2**60), (2**63, 2**63), (U64 - 30, 30)):
                for creator in (0, 1):
                    add(f'{quote}-exact-budget-fee-{amount}-{flat}-{creator}', quote=quote, op='exact', tf=tf, amount=amount,
                        flat=flat, creator=creator)
    # guards that fail together: the first one in the handler's order names the error
    for op in OPS:
        add(f'{op}-both-recipients', op=op, fee_recipient_ok=0, buyback_ok=0)
        add(f'{op}-complete-zero', op=op, complete=1, amount=0)
        add(f'{op}-complete-recipient', op=op, complete=1, fee_recipient_ok=0)
        add(f'{op}-zero-recipient', op=op, amount=0, fee_recipient_ok=0)
        for slot in ('curve_key', 'user_key', 'vault_key', 'accumulator_key', 'recipient_key', 'buyback_key',
                     'curve_missing', 'user_mint'):
            add(f'{op}-{slot}-recipient', op=op, bad=slot, fee_recipient_ok=0)
            add(f'{op}-{slot}-buyback', op=op, bad=slot, buyback_ok=0)
            add(f'{op}-{slot}-fee-config', op=op, bad=slot, fee_len=2511)
            add(f'{op}-{slot}-complete', op=op, bad=slot, complete=1)
            add(f'{op}-{slot}-zero', op=op, bad=slot, amount=0)
        add(f'{op}-recipient-vtr-zero', op=op, vtr=0, fee_recipient_ok=0)
        add(f'{op}-fee-config-vtr-zero', op=op, vtr=0, fee_len=2511)
    add('exact-zero-both', op='exact', amount=0, limit=0)
    add('exact-zero-limit-recipient', op='exact', limit=0, fee_recipient_ok=0)
    add('sell-short-recipient', amount=10**13 + 1, fee_recipient_ok=0)
    add('sell-slippage-over-real-quote', amount=10**12, limit=10**12, rqr=1_000)
    add('sell-slippage-curve-short', amount=10**12, limit=10**12, curve_quote=1_000)
    add('sell-over-real-curve-short', amount=10**12, rqr=1_000, curve_quote=1_000)
    add('buy-over-real-recipient', op='buy', amount=10**13, rtr=10**12, fee_recipient_ok=0)
    add('buy-curve-base-user-short', op='buy', curve_base=10, user_quote=10)
    add('buy-slippage-user-short', op='buy', limit=1, user_quote=10)
    # the gross-up stops at the mint's maximum fee, one below, on and above it
    for op in ('buy', 'sell', 'exact'):
        c = default_case(op=op, quote='t22', tf=(0, 0, 0, 250, 10**18))
        kept = model([c])[0][1]['quote_transfer_fee']
        for cap in (1, kept - 1, kept, kept + 1, kept + 2):
            add(f't22-{op}-cap-{cap}', op=op, quote='t22', tf=(0, 0, 0, 250, cap))
    # a whitelisted trade on a mayhem curve ends with the virtual quote resync
    wl = dict(whitelisted=1, mayhem=1, supply=2 * 10**15)
    for quote in QUOTES:
        for op in OPS:
            tag = f'{quote}-{op}-resync'
            add(f'{tag}', quote=quote, op=op, **wl)
            add(f'{tag}-not-mayhem', quote=quote, op=op, whitelisted=1)
            add(f'{tag}-not-whitelisted', quote=quote, op=op, mayhem=1, supply=2 * 10**15)
            add(f'{tag}-cap', quote=quote, op=op, rqr=2 * 10**11, **wl)
            add(f'{tag}-no-supply', quote=quote, op=op, whitelisted=1, mayhem=1, supply=0)
            add(f'{tag}-huge-supply', quote=quote, op=op, whitelisted=1, mayhem=1, supply=U64)
            # the real-quote threshold reads the reserve after the trade
            small = 10**5 if op == 'exact' else 10**10
            moved = model([default_case(quote=quote, op=op, amount=small, **wl)])[0][1]['quote']
            for real in (999_999, 1_000_000):
                add(f'{tag}-real-{real}', quote=quote, op=op, amount=small, rqr=real + (moved if op == 'sell' else -moved),
                    curve_quote=10**12, **wl)
            # the denominator is 2 * supply less the two balances after the trade
            for gap in (-1, 0, 1):
                add(f'{tag}-denominator{gap}', quote=quote, op=op, whitelisted=1, mayhem=1, supply=10**15,
                    curve_base=2 * 10**15 - 10**12 - gap - 10**13)
        add(f'{quote}-resync-complete', quote=quote, op='buy', amount=10**12, rtr=10**12, **wl)
        add(f'{quote}-resync-conversion', quote=quote, op='buy', whitelisted=1, mayhem=1, supply=10**15, rqr=2**62,
            curve_base=2 * 10**15 - 10**12 - 10**13)
    # tier selection by market cap for wSOL, stable tiers for USDC, curve bps override
    mc = 10**15 * 30_000_000_000 // 1_000_000_000_000_000
    for quote in ('wsol', 'usdc'):
        for rows in ([(mc + 1, 100, 10), (mc + 2, 200, 20)], [(0, 100, 10), (mc, 200, 20), (mc + 1, 300, 30)],
                     [(0, 100, 10), (mc + 1, 300, 30), (5, 200, 20)]):
            for op in OPS:
                add(f'{quote}-{op}-tiers-{rows[0][0]}', quote=quote, op=op, tiers=rows, stable=rows)
        add(f'{quote}-tiers-mayhem-supply', quote=quote, mayhem=1, supply=2 * 10**15, tiers=[(0, 100, 10), (mc + 1, 300, 30)], stable=[(0, 100, 10), (mc + 1, 300, 30)])
    add('usdc-len-4072-no-stable', quote='usdc', fee_len=4072)
    add('usdc-len-4073-stable', quote='usdc', fee_len=4073)
    add('spl-len-4096-no-exotic', quote='spl', fee_len=4096, exotic=(0, 50, 10))
    add('spl-exotic-lp-only', quote='spl', fee_len=4104, exotic=(7, 0, 0))
    # Token-2022 transfer fees: epoch choice, cap, 100 %, every direction
    for op in OPS:
        for tf in ((100, 10**18, 0, 250, 10**18), (100, 10**18, EPOCH, 250, 10**18), (100, 10**18, EPOCH + 1, 250, 10**18),
                   (0, 0, 0, 1, 1), (500, 1_000, 0, 500, 1_000), (0, 0, 0, 10_000, 5_000), (0, 0, 0, 9_999, 10**18),
                   (0, 0, 0, 0, 10**18), (0, 0, 0, 3, 10**18)):
            add(f't22-{op}-tf-{tf}', quote='t22', op=op, tf=tf)
        tf = (0, 0, 0, 250, 10**18)
        add(f't22-{op}-tf-bb0', quote='t22', op=op, tf=tf, buyback_bps=0)
        add(f't22-{op}-tf-mayhem', quote='t22', op=op, tf=tf, mayhem=1)
        add(f't22-{op}-tf-cashback', quote='t22', op=op, tf=tf, cashback=1)
        add(f't22-{op}-tf-whitelisted', quote='t22', op=op, tf=tf, whitelisted=1)
        add(f't22-{op}-tf-small', quote='t22', op=op, tf=tf, amount=12_345)
        add(f't22-{op}-tf-user-short', quote='t22', op=op, tf=tf, user_quote=10)
    # a recipient's or vault's quote ATA is created through the ATA program, at the user's cost
    for quote, tf in (('spl', None), ('t22', None), ('t22', (0, 0, 0, 250, 10**18))):
        for op in OPS:
            for missing in ('vault', 'uva', 'recipient', 'buyback'):
                add(f'{quote}-{op}-create-{missing}-{bool(tf)}', quote=quote, op=op, tf=tf, missing=(missing,))
            add(f'{quote}-{op}-create-all-{bool(tf)}', quote=quote, op=op, tf=tf, missing=('vault', 'uva', 'recipient', 'buyback'))
    for quote, tf in (('spl', None), ('t22', (0, 0, 0, 250, 10**18))):
        c = default_case(quote=quote, tf=tf)
        net = model([c])[0][1]['user_received']
        add(f'{quote}-sell-min-exact', quote=quote, tf=tf, limit=net)
        add(f'{quote}-sell-min-short', quote=quote, tf=tf, limit=net + 1)
        c = default_case(quote=quote, tf=tf, op='buy')
        cost = model([c])[0][1]['user_sent']
        add(f'{quote}-buy-max-exact', quote=quote, tf=tf, op='buy', limit=cost)
        add(f'{quote}-buy-max-short', quote=quote, tf=tf, op='buy', limit=cost - 1)
        add(f'{quote}-buy-user-exact', quote=quote, tf=tf, op='buy', user_quote=cost)
        add(f'{quote}-buy-user-one-short', quote=quote, tf=tf, op='buy', user_quote=cost - 1)
        c = default_case(quote=quote, tf=tf, op='exact')
        tokens = model([c])[0][1]['base_moved']
        add(f'{quote}-exact-min-exact', quote=quote, tf=tf, op='exact', limit=tokens)
        add(f'{quote}-exact-min-short', quote=quote, tf=tf, op='exact', limit=tokens + 1)
    return out


def random_cases(n=240, seed=20261030):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        quote = rng.choice(list(QUOTES) + ['t22', 't22'])
        op = rng.choice(OPS)
        vtr = rng.choice([rng.randrange(10**14, 2 * 10**15), rng.randrange(1, 10**9)])
        rtr = rng.randrange(1, vtr) if op != 'sell' and vtr > 1 else rng.randrange(0, 10**15)
        amount = rng.choice([rng.randrange(1, max(2, rtr)), rng.randrange(0, 10**13), 1, rng.randrange(1, 10**6)])
        partial = int(rng.random() < 0.4)
        c = default_case(
            quote=quote, op=op, amount=amount, partial=partial, vtr=vtr, vqr=rng.randrange(10**6, 10**12), rtr=rtr,
            rqr=rng.randrange(0, 10**11), mayhem=int(rng.random() < 0.15), creator=int(rng.random() < 0.85),
            curve_creator_bps=rng.choice([0, 0, rng.randrange(0, 2_000)]), configurable=int(rng.random() < 0.3),
            holder=int(rng.random() < 0.2), cashback=int(rng.random() < 0.15),
            buyback_bps=rng.choice([0, 10_000, rng.randrange(0, 10_001)]), whitelisted=int(rng.random() < 0.1),
            flat=(rng.randrange(0, 3_000), rng.randrange(0, 3_000)),
            tiers=sorted([(rng.randrange(0, 10**12), rng.randrange(0, 3_000), rng.randrange(0, 3_000)) for _ in range(rng.randrange(1, 4))]),
            stable=[(0, rng.randrange(0, 3_000), rng.randrange(0, 3_000))],
            fee_len=rng.choice([4104, 4104, 4072, 4200]), exotic=rng.choice([(0, 0, 0), (0, rng.randrange(0, 500), rng.randrange(0, 500))]),
            tf=(rng.randrange(0, 10_001), rng.randrange(0, 10**9), rng.randrange(0, 10), rng.randrange(0, 10_001),
                rng.choice([U64, rng.randrange(0, 10**9)])) if quote == 't22' and rng.random() < 0.8 else None,
            user_base=rng.choice([10**13, amount, max(0, amount - 1)]), vault_lamports=rng.choice([0, 0, 890_880]),
        )
        c['curve_quote'] = max(c['rqr'], rng.choice([0, 10**12]))
        kind, ans = model([c])[0]
        if kind == 'ok':
            if op == 'sell':
                c['limit'] = rng.choice([0, ans['user_received'], ans['user_received'] + 1])
            elif op == 'buy':
                c['limit'] = rng.choice([U64, ans['user_sent'], max(0, ans['user_sent'] - 1)])
            else:
                c['limit'] = rng.choice([1, ans['base_moved'], ans['base_moved'] + 1])
        out.append((f'random-{len(out)}', c))
    return out


class V2TokenQuoteCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program_images()

    def run_all(self, labelled):
        answers = model([c for _, c in labelled])
        results = []
        for (label, c), answer in zip(labelled, answers, strict=True):
            got = run_captured(c)
            with self.subTest(label):
                self.assertEqual(check(c, got, answer), [], label)
            results.append((label, c, got, answer))
        return results

    def test_fixed_cases(self):
        results = self.run_all(fixed_cases())
        outcomes = {a[1] if a[0] == 'error' else a[0] for *_, a in results}
        for want in ('ok', 'panic', 'invalid-account-data', 1, 2006, 3012, 6000, 6002, 6003, 6004, 6005, 6010, 6020,
                     6021, 6022, 6023, 6024, 6025, 6026, 6041, 6042, 6057, 4102):
            self.assertIn(want, outcomes)
        oks = [(c, a[1]) for _, c, _, a in results if a[0] == 'ok']
        self.assertTrue(any(c['tf'] and a['quote_transfer_fee'] > 0 for c, a in oks))
        self.assertTrue(any(a['curve_rent'] > 0 for _, a in oks))
        self.assertTrue(any(a['completes'] for _, a in oks))
        self.assertEqual({c['quote'] for c, _ in oks}, set(QUOTES))

    def test_random_cases(self):
        results = self.run_all(random_cases())
        self.assertGreaterEqual(sum(a[0] == 'ok' for *_, a in results), 60)

    def test_an_unknown_bad_slot_is_refused(self):
        # The driver's catchall read a misspelt slot name as "no bad slot", so a
        # case labelled as a wrong account ran the happy path on both sides.
        line = host_line(default_case(bad='curve_kee'))
        run = subprocess.run([str(host_binary())], input=line + '\n', capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_checker_rejects_tampered_outcomes(self):
        tf = (0, 0, 0, 250, 10**18)
        picks = [default_case(quote='t22', tf=tf, op=op, vault_lamports=0, curve_lamports=rent(166) - 1) for op in OPS]
        for c, answer in zip(picks, model(picks)):
            got = run_captured(c)
            self.assertEqual(check(c, got, answer), [])
            for field in answer[1]:
                if field == 'completes' or (field in ('curve_received', 'user_received') and answer[1][field] == 0):
                    continue
                bent = dict(answer[1])
                bent[field] += 1
                self.assertNotEqual(check(c, got, ('ok', bent)), [], field)
            self.assertNotEqual(check(c, got, ('error', 6024)), [])


    def test_model_response_count_and_format_are_strict(self):
        case = default_case()
        raw = subprocess.run([str(host_binary())], input=host_line(case) + '\n', capture_output=True,
                             text=True, check=True).stdout
        self.assertEqual(len(parse_model_output(raw, 1)), 1)
        for output in ('', raw + raw, 'unexpected field=1\n', 'ok field=1 field=2\n'):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    parse_model_output(output, 1)
        with patch.dict(globals(), {'model': lambda cases: []}):
            with self.assertRaises(ValueError):
                self.run_all([('missing-response', case)])

    def test_captured_bytes_remain_pinned_after_path_replacement(self):
        with tempfile.TemporaryDirectory(prefix='pinned-v2-model-') as temporary:
            image = Path(temporary) / 'pump.so'
            image.write_bytes(PUMP_ELF.read_bytes())
            expected = {path: digest for path, digest in ELF_SHA256.items() if path != PUMP_ELF}
            expected[image] = ELF_SHA256[PUMP_ELF]
            images = admit_program_images(expected)
            image.write_bytes(b'replaced after admission')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                admit_program_images(expected)
            changes = {'PUMP_ELF': image, '_PROGRAM_BYTES': images, '_VM': None}
            if '_TOUCHED' in globals():
                changes['_TOUCHED'] = set()
            with patch.dict(globals(), changes):
                case = default_case()
                self.assertEqual(check(case, run_captured(case), model([case])[0]), [])

    def test_error_checker_rejects_committed_state_mutation(self):
        case = default_case(complete=1)
        answer = model([case])[0]
        self.assertEqual(answer, ('error', 6005))
        got = run_captured(case)
        self.assertEqual(check(case, got, answer), [])
        changed = dict(got)
        changed['after'] = dict(got['after'])
        lamports, data, owner = changed['after'][CURVE]
        changed['after'][CURVE] = (lamports, bytes([data[0] ^ 1]) + data[1:], owner)
        self.assertNotEqual(check(case, changed, answer), [])



if __name__ == '__main__':
    unittest.main()
