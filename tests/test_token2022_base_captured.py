"""Captured-program checks for Token-2022 base mints on the legacy and v2 native trades.

Every case runs on the captured `evidence/original/pump/deployed.so` with the
captured Pump Fees, SPL Token, Token-2022 and ATA programs and through
`programs/pump/recovered/token2022_base_host.rs`. State is synthetic.

A case passes when the captured program and the model agree on the error and committed-state rollback (apart from the transaction fee), or on
the lamports of the user, curve, fee recipient, buyback recipient and creator
vault, the base balances and withheld transfer fees, the stored curve bytes and
the TradeEvent fields the model names. This pins observed behavior on these inputs only; it is not a
byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/token2022_base_host.rs'

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
        elif line in ('panic', 'missing'):
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
TRADE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'TradeEvent'))

PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([241]) * 32)
CREATOR = Pubkey.from_bytes(bytes([242]) * 32)
MINT = Pubkey.from_bytes(bytes([243]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([244]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([245]) * 32)
RESERVED = Pubkey.from_bytes(bytes([246]) * 32)
OTHER = Pubkey.from_bytes(bytes([247]) * 32)

pda = lambda program, *seeds: Pubkey.find_program_address(list(seeds), program)[0]
ata = lambda owner, mint=MINT, program=TOKEN: pda(ATA, bytes(owner), bytes(program), bytes(mint))
GLOBAL = pda(PUMP, b'global')
CURVE = pda(PUMP, b'bonding-curve', bytes(MINT))
CURVE_V2 = pda(PUMP, b'bonding-curve-v2', bytes(MINT))
SHARING = pda(FEES, b'sharing-config', bytes(MINT))
EVENT_AUTHORITY = pda(PUMP, b'__event_authority')
GLOBAL_VOLUME = pda(PUMP, b'global_volume_accumulator')
USER_VOLUME = pda(PUMP, b'user_volume_accumulator', bytes(USER.pubkey()))
FEE_CONFIG, FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)
CREATOR_KEY = lambda c: CREATOR if c['creator'] else SYSTEM
VAULT = lambda c: pda(PUMP, b'creator-vault', bytes(CREATOR_KEY(c)))
LIST0 = Pubkey.from_bytes(bytes([248]) * 32)
LIST6 = Pubkey.from_bytes(bytes([249]) * 32)
RECIPIENT = {'regular': FEE_RECIPIENT, 'reserved': RESERVED, 'list0': LIST0, 'list6': LIST6, 'other': OTHER}

TX_FEE = 5_000
TIMESTAMP = 1_700_000_000
TOKEN_RENT = 2_039_280
CURVE_RENT = (166 + 128) * 6960
U64 = 2**64 - 1
OPS = ('sell', 'buy', 'exact')
IX_NAME = {'sell': 'sell_v2', 'buy': 'buy_v2', 'exact': 'buy_exact_quote_in_v2'}
LEGACY_NAME = {'sell': 'sell', 'buy': 'buy', 'exact': 'buy_exact_sol_in'}


def mint_bytes(supply, decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_bytes(owner, amount, exts=b''):
    data = (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))
    return data + bytes([2]) + exts if exts else data


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint22_bytes(c):
    exts = {'plain': b'', 'meta': tlv(18, bytes(64)), 'hook': tlv(14, bytes(32) + bytes(OTHER)),
            'hook0': tlv(14, bytes(64)), 'nontransfer': tlv(9), 'pause': tlv(26, bytes(33)), 'pause1': tlv(26, bytes(32) + b'\1'),
            'delegate': tlv(12, bytes(OTHER))}.get(c['ext'])
    if c['ext'] == 'fee':
        exts = tlv(1, bytes(72) + struct.pack('<QQH', 0, c['fee_max'], c['fee_bps']) + struct.pack('<QQH', 0, c['fee_max'], c['fee_bps']))
    raw = mint_bytes(c['mint_supply'], 6)
    return raw.ljust(165, b'\0') + bytes([1]) + exts if exts else raw


def base_account(c, owner, amount):
    if c['ext'] in ('fee',):
        exts = tlv(7) + tlv(2, bytes(8))
    elif c['ext'] in ('hook', 'hook0'):
        exts = tlv(7) + tlv(15, bytes(1))
    elif c['ext'] == 'nontransfer':
        exts = tlv(7) + tlv(13)
    elif c['ext'] == 'pause' or c['ext'] == 'pause1':
        exts = tlv(7) + tlv(27)
    elif c['ext'] in ('meta', 'delegate'):
        exts = tlv(7)
    else:
        exts = b''
    return token_bytes(owner, amount, exts)


def global_bytes(c):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[451:483] = bytes(OTHER)
    data[483:515] = bytes(RESERVED)
    data[516:548] = bytes(LIST0)
    data[708:740] = bytes(LIST6)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, c['buyback_bps'])
    data[1045] = c['configurable']
    struct.pack_into('<Q', data, 1046, 10_000)
    return bytes(data)


def fee_config_bytes(c):
    tiers = () if c['tiers'] == '-' else [tuple(int(n) for n in entry.split(':')) for entry in c['tiers'].split(';')]
    data = bytearray(ACCOUNT_DISC['FeeConfig']) + bytes([FEE_BUMP]) + bytes(32) + bytes(24)
    data += struct.pack('<I', len(tiers))
    for threshold, protocol, creator in tiers:
        data += threshold.to_bytes(16, 'little') + struct.pack('<QQQ', 0, protocol, creator)
    data += struct.pack('<I', 0) + bytes(24)
    return bytes(data).ljust(4104, b'\0')


def curve_bytes(c):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<5Q', data, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['supply'])
    data[48] = c['complete']
    data[49:81] = bytes(CREATOR_KEY(c))
    struct.pack_into('<Q', data, 115, c['creator_bps'])
    struct.pack_into('<Q', data, 142, c['vqr'])
    return bytes(data)


def base_key(owner, c):
    return ata(owner, MINT, TOKEN if c['ata'] == 'spl' else TOKEN22)


def default_case(**over):
    c = dict(op='sell', amount=None, limit=None, trailing='-', vtr=10**15, vqr=30_000_000_000, rtr=793_100_000_000_000,
             rqr=5_000_000_000, supply=2 * 10**15, complete=0, creator=1, creator_bps=0,
             configurable=0, mint_supply=10**15, tiers='0:95:30', buyback_bps=5_000, vault=0, user_base=10**13, curve_base=10**15,
             recipient='regular', buyback_ok=1, family='v2', ext='plain', fee_bps=0,
             fee_max=0, program='t22', mint_owner='t22', ata='t22')
    c.update(over)
    if c['amount'] is None:
        c['amount'] = 10**8 if c['op'] == 'exact' else 10**12
    if c['limit'] is None:
        c['limit'] = {'sell': 0, 'buy': 10**15, 'exact': 1}[c['op']]
    return c


def host_line(c):
    return ' '.join(f'{k}={v}' for k, v in c.items())


_HOST = None


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'token2022_base_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(cases):
    text = ''.join(host_line(c) + '\n' for c in cases)
    out = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    return parse_model_output('\n'.join(out), len(cases))


_VM = None


def vm_for(c):
    global _VM
    if _VM is None:
        _VM = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((PUMP, PUMP_ELF), (FEES, FEES_ELF), (TOKEN, TOKEN_ELF), (TOKEN22, TOKEN22_ELF), (ATA, ATA_ELF)):
            _VM.add_program(key, program_images()[path])
        _VM.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    user = USER.pubkey()
    accounts = {
        user: Account(10**16, b'', SYSTEM),
        GLOBAL: Account(10**9, global_bytes(c), PUMP),
        MINT: Account(10**9, mint22_bytes(c), TOKEN22 if c['mint_owner'] == 't22' else TOKEN),
        WSOL: Account(10**9, mint_bytes(0, 9), TOKEN),
        CURVE: Account(CURVE_RENT + c['rqr'] % 10**15, curve_bytes(c), PUMP),
        base_key(CURVE, c): Account(TOKEN_RENT, base_account(c, CURVE, c['curve_base']), TOKEN22 if c['mint_owner'] == 't22' else TOKEN),
        base_key(user, c): Account(TOKEN_RENT, base_account(c, user, c['user_base']), TOKEN22 if c['mint_owner'] == 't22' else TOKEN),
        CURVE_V2: Account(10**7, b'', SYSTEM),
        FEE_CONFIG: Account(10**9, fee_config_bytes(c), FEES),
        GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
        USER_VOLUME: Account(10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(user) + bytes(97), PUMP),
        VAULT(c): Account(c['vault'], b'', SYSTEM),
    }
    for key, account in accounts.items():
        _VM.set_account(key, account)
    return _VM


def run_captured(c):
    vm = vm_for(c)
    user = USER.pubkey()
    recipient = RECIPIENT[c['recipient']]
    buyback = BUYBACK if c['buyback_ok'] else OTHER
    program = TOKEN22 if c['program'] == 't22' else TOKEN
    names = {
        'global': GLOBAL, 'base_mint': MINT, 'quote_mint': WSOL, 'base_token_program': program,
        'mint': MINT, 'token_program': program, 'associated_bonding_curve': base_key(CURVE, c), 'associated_user': base_key(user, c),
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'fee_recipient': recipient,
        'associated_quote_fee_recipient': ata(recipient, WSOL), 'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
        'associated_base_bonding_curve': base_key(CURVE, c), 'associated_quote_bonding_curve': ata(CURVE, WSOL),
        'user': user, 'associated_base_user': base_key(user, c), 'associated_quote_user': ata(user, WSOL),
        'creator_vault': VAULT(c), 'associated_creator_vault': ata(VAULT(c), WSOL), 'sharing_config': SHARING,
        'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
        'associated_user_volume_accumulator': ata(USER_VOLUME, WSOL), 'fee_config': FEE_CONFIG,
        'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX[(LEGACY_NAME if c['family'] == 'legacy' else IX_NAME)[c['op']]]
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
    if c['family'] == 'legacy':
        metas += [AccountMeta(CURVE_V2, False, False), AccountMeta(buyback, False, True)]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', c['amount'], c['limit'])
    if c['trailing'] != '-':
        data += bytes.fromhex(c['trailing'])
    lamports = lambda key: vm.get_account(key).lamports
    watched = sorted({user, *(meta.pubkey for meta in metas)}, key=bytes)
    def snap():
        result = {}
        for key in watched:
            account = vm.get_account(key)
            if account is None or account.lamports == 0:
                result[key] = None
            elif not account.executable:
                result[key] = (account.lamports, bytes(account.data), account.owner)
        return result
    before_state = snap()
    money = (user, CURVE, RECIPIENT[c['recipient']], BUYBACK, VAULT(c))
    balance = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [balance(key) for key in money]
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], user, [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        if code:
            error = int(code.group(1))
        else:
            error = 'panic' if 'ProgramFailedToComplete' in text else 'missing' if 'MissingAccount' in text else text
        return dict(error=error, before=before_state, after=snap())
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0]
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    trade = next(e for e in events if e[:8] == TRADE_EVENT)
    return dict(error=None, before=before_state, after=snap(), delta=[balance(key) - was for key, was in zip(money, before)],
                stored=bytes(vm.get_account(CURVE).data), user_base=tokens(base_key(user, c)), curve_base=tokens(base_key(CURVE, c)),
                withheld=(withheld(vm.get_account(base_key(user, c)).data), withheld(vm.get_account(base_key(CURVE, c)).data)),
                event=decode_trade(trade))


def withheld(data):
    at = 166
    while at + 4 <= len(data):
        kind, size = struct.unpack_from('<HH', data, at)
        if kind == 2:
            return struct.unpack_from('<Q', data, at + 4)[0]
        at += 4 + size
    return 0


def decode_trade(data):
    offset = 8 + 32
    def take(fmt='<Q'):
        nonlocal offset
        value = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)
        return value
    event = {'sol_amount': take(), 'tokens': take()}
    offset += 1 + 32 + 8
    event['vqr'], event['vtr'], event['rqr'], event['rtr'] = take(), take(), take(), take()
    offset += 32
    event['protocol_bps'], event['protocol_fee'] = take(), take()
    offset += 32
    event['creator_bps'], event['creator_fee'] = take(), take()
    offset += 1 + 32
    name_len = take('<I')
    offset += name_len
    offset += 1 + 16
    event['buyback_bps'], event['buyback_fee'] = take(), take()
    return event


def check(c, got, answer):
    kind, m = answer
    if kind == 'error':
        bad = [] if got['error'] == m else [f"error {got['error']!r} != {m}"]
        return bad + rollback_differences(got['before'], got['after'])
    if got['error'] is not None:
        return [f"captured failed with {got['error']!r}"]
    bad = []
    sell = c['op'] == 'sell'
    curve_delta = -m['sol_amount'] if sell else m['sol_amount']
    expected = [m['user_delta'] - TX_FEE, curve_delta, m['protocol_fee'] - m['buyback_fee'], m['buyback_fee'], m['vault_credit']]
    if got['delta'] != expected:
        bad.append(f"lamports {got['delta']} != {expected}")
    # The source loses the whole amount; the destination holds the fee as withheld.
    if sell:
        balances = (c['user_base'] - m['tokens'], c['curve_base'] + m['tokens'] - m['withheld'])
        kept = (0, m['withheld'])
    else:
        balances = (c['user_base'] + m['tokens'] - m['withheld'], c['curve_base'] - m['tokens'])
        kept = (m['withheld'], 0)
    if (got['user_base'], got['curve_base']) != balances:
        bad.append('base balances')
    if got['withheld'] != kept:
        bad.append(f"withheld {got['withheld']} != {kept}")
    curve = bytearray(curve_bytes(c))
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    curve[48] = m['completes']
    if got['stored'] != bytes(curve):
        bad.append('curve bytes')
    for field, value in got['event'].items():
        if value != m[field]:
            bad.append(f'event {field} {value} != {m[field]}')
    return bad


def fixed_cases():
    out = []
    big = lambda op: 10**12 if op != 'exact' else 10**15
    extensions = (dict(ext='plain'), dict(ext='meta'), dict(ext='delegate'), dict(ext='hook0'), dict(ext='pause'),
                  dict(ext='fee'), dict(ext='fee', fee_bps=100, fee_max=10**12), dict(ext='fee', fee_bps=100, fee_max=1_000),
                  dict(ext='fee', fee_bps=1, fee_max=U64), dict(ext='fee', fee_bps=10_000, fee_max=U64),
                  dict(ext='fee', fee_bps=10_000, fee_max=0), dict(ext='hook'), dict(ext='nontransfer'), dict(ext='pause1'))
    for family in ('legacy', 'v2'):
        for op in OPS:
            tag = f'{family}-{op}'
            k = dict(family=family, op=op)
            add = lambda label, **more: out.append((f'{tag}-{label}', default_case(**k, **more)))
            for index, extension in enumerate(extensions):
                x = f"{extension['ext']}{index}"
                add(f'{x}-plain', **extension)
                add(f'{x}-no-creator', **extension, creator=0)
                add(f'{x}-vault-short', **extension, vault=890_879)
                add(f'{x}-vault-funded', **extension, vault=10**9)
                add(f'{x}-override', **extension, configurable=1, creator_bps=500)
                add(f'{x}-small', **extension, amount=1_000 if op != 'exact' else 10**6)
                add(f'{x}-rounded', **extension, amount=10_001 if op != 'exact' else 10_001_000)
                add(f'{x}-complete', **extension, complete=1)
                add(f'{x}-zero', **extension, amount=0)
                add(f'{x}-no-tiers', **extension, tiers='-')
                add(f'{x}-vtr-zero', **extension, vtr=0)
                add(f'{x}-buyback-above-fee', **extension, buyback_bps=20_000)
                add(f'{x}-huge-protocol', **extension, tiers=f'0:{U64}:30', vqr=10**15, amount=big(op))
                add(f'{x}-spl-program', **extension, program='spl')
                add(f'{x}-spl-ata', **extension, ata='spl')
                add(f'{x}-spl-both', **extension, ata='spl', program='spl')
                add(f'{x}-spl-owner', **extension, mint_owner='spl')
                add(f'{x}-spl-owner-ata', **extension, mint_owner='spl', ata='spl')
                add(f'{x}-spl-owner-program', **extension, mint_owner='spl', program='spl')
                if extension['ext'] == 'plain':
                    add(f'{x}-spl-route', **extension, mint_owner='spl', program='spl', ata='spl')
                add(f'{x}-mismatch-complete', **extension, program='spl', complete=1)
                add(f'{x}-mismatch-zero', **extension, ata='spl', amount=0)
                add(f'{x}-mismatch-no-tiers', **extension, program='spl', tiers='-')
                if family == 'v2':
                    add(f'{x}-other-recipient', **extension, recipient='other')
                if family == 'v2' or op == 'sell':
                    add(f'{x}-bad-buyback', **extension, buyback_ok=0)
                if op == 'sell':
                    add(f'{x}-bad-buyback-limit-short', **extension, buyback_ok=0, limit=U64)
                if op == 'sell':
                    add(f'{x}-too-many', **extension, amount=10**13 + 1)
                    add(f'{x}-limit-short', **extension, limit=U64)
                    add(f'{x}-over-real-quote', **extension, amount=10**14, rqr=1_000)
                    add(f'{x}-all-tokens', **extension, amount=10**13)
                elif op == 'buy':
                    add(f'{x}-limit-short', **extension, limit=1)
                    add(f'{x}-over-real', **extension, amount=10**13, rtr=10**12)
                    add(f'{x}-partial', **extension, trailing='0101' if family == 'legacy' else '01', amount=10**13, rtr=10**12)
                    add(f'{x}-completes', **extension, amount=10**12, rtr=10**12)
                    add(f'{x}-bad-option', **extension, trailing='02', program='spl')
                    add(f'{x}-second-option', **extension, trailing='0002', program='spl')
                    add(f'{x}-first-flag-over-real', **extension, trailing='01', amount=10**13, rtr=10**12)
                    add(f'{x}-second-flag-over-real', **extension, trailing='0001', amount=10**13, rtr=10**12)
                else:
                    add(f'{x}-limit-high', **extension, limit=U64)
                    add(f'{x}-partial', **extension, trailing='0101' if family == 'legacy' else '01', amount=10**10, rtr=10**12)
                    add(f'{x}-over-real', **extension, amount=10**10, rtr=10**12)
                    add(f'{x}-dust', **extension, amount=1, limit=1)
                    add(f'{x}-bad-option', **extension, trailing='02', ata='spl')
                    add(f'{x}-second-option', **extension, trailing='0002', ata='spl')
                    add(f'{x}-first-flag-over-real', **extension, trailing='01', amount=10**10, rtr=10**12)
                    add(f'{x}-second-flag-over-real', **extension, trailing='0001', amount=10**10, rtr=10**12)
    return out


def random_cases(n=300, seed=20261030):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        op = rng.choice(OPS)
        family = rng.choice(('legacy', 'v2'))
        vtr = rng.randrange(10**12, 2 * 10**15)
        rtr = rng.randrange(1, vtr)
        amount = rng.choice([rng.randrange(1, 10**13), rng.randrange(1, 10**6), rng.randrange(1, 10**10)])
        extension = rng.choice([dict(ext='plain'), dict(ext='meta'), dict(ext='hook0'), dict(ext='hook'), dict(ext='nontransfer'),
                                dict(ext='pause1'), dict(ext='fee', fee_bps=rng.choice([0, 1, 50, 100, 9_999, 10_000]),
                                                         fee_max=rng.choice([0, 1, 1_000, 10**9, U64])),
                                dict(ext='fee', fee_bps=rng.randrange(1, 10_001), fee_max=rng.randrange(1, 10**12))])
        program, owner, derived = rng.choice([('t22',) * 3] * 6 + [('spl', 't22', 't22'), ('t22', 't22', 'spl'), ('t22', 'spl', 't22'), ('spl',) * 3])
        if owner == 'spl' and program == 'spl':
            extension = dict(ext='plain')
        tiers = rng.choice(['0:95:30', '0:0:0', '0:95:30;1000000:50:20', f'0:300:100;{10**9}:50:25', '0:10000:10000'])
        trailing = rng.choice(['-', '00', '01', '0100', '0101']) if op != 'sell' else '-'
        c = default_case(family=family, op=op, amount=amount, vtr=vtr, vqr=rng.randrange(10**8, 10**12), rtr=rtr, trailing=trailing,
                         rqr=rng.randrange(0, 10**13), creator=int(rng.random() < .8), tiers=tiers, configurable=rng.randrange(2),
                         creator_bps=rng.choice([0, 50, 500]), buyback_bps=rng.choice([0, 1, 3_333, 5_000, 10_000]),
                         vault=rng.choice([0, 1, 890_879, 890_880, 10**9]), user_base=rng.choice([10**13, amount, max(0, amount - 1), 10**15]),
                         program=program, mint_owner=owner, ata=derived, **extension)
        c['curve_base'] = rng.randrange(max(amount, rtr), 2 * 10**15)
        if family == 'v2' or op == 'sell':
            c['buyback_ok'] = int(rng.random() < .9)
        kind, ans = model([c])[0]
        if kind == 'ok':
            if op == 'sell':
                output = ans['user_delta'] + ans['vault_credit'] - ans['creator_fee']
                c['limit'] = rng.choice([0, output, output + 1])
            elif op == 'buy':
                cost = ans['sol_amount'] + ans['protocol_fee'] + ans['creator_fee']
                c['limit'] = rng.choice([U64, cost, cost - 1])
            else:
                c['limit'] = rng.choice([1, ans['tokens'], ans['tokens'] + 1])
        out.append((f'random-{len(out)}', c))
    return out


class Token2022BaseCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        program_images()

    def run_all(self, labelled):
        answers = model([c for _, c in labelled])
        results = []
        for (label, c), answer in zip(labelled, answers, strict=True):
            with self.subTest(label):
                self.assertEqual(check(c, run_captured(c), answer), [], label)
            results.append(answer)
        return results

    def test_fixed_cases(self):
        results = self.run_all(fixed_cases())
        outcomes = {a[1] if a[0] == 'error' else a[0] for a in results}
        for want in ('ok', 'panic', 'missing', 37, 67, 102, 2009, 2023, 6000, 6002, 6003, 6005, 6020, 6021, 6022, 6023, 6024, 6025, 6026,
                     6041, 6042, 6057):
            self.assertIn(want, outcomes)
        self.assertTrue(any(a[0] == 'ok' and a[1]['completes'] for a in results))
        self.assertTrue(any(a[0] == 'ok' and a[1]['withheld'] for a in results))

    def test_random_cases(self):
        self.assertGreaterEqual(sum(a[0] == 'ok' for a in self.run_all(random_cases())), 60)

    def test_checker_rejects_tampered_outcomes(self):
        for op in OPS:
            c = default_case(op=op)
            answer = model([c])[0]
            got = run_captured(c)
            self.assertEqual(check(c, got, answer), [])
            for field in answer[1]:
                self.assertNotEqual(check(c, got, ('ok', dict(answer[1], **{field: answer[1][field] + 1}))), [], field)
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
        with tempfile.TemporaryDirectory(prefix='pinned-token2022-model-') as temporary:
            image = Path(temporary) / 'pump.so'
            image.write_bytes(PUMP_ELF.read_bytes())
            expected = {path: digest for path, digest in ELF_SHA256.items() if path != PUMP_ELF}
            expected[image] = ELF_SHA256[PUMP_ELF]
            images = admit_program_images(expected)
            image.write_bytes(b'replaced after admission')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                admit_program_images(expected)
            with patch.dict(globals(), {'PUMP_ELF': image, '_PROGRAM_BYTES': images, '_VM': None}):
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
