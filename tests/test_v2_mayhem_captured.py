"""Captured-program checks for native Mayhem and holder-reward coins on `sell_v2`, `buy_v2` and `buy_exact_quote_in_v2`.

Every case runs on the captured `evidence/original/pump/deployed.so` with the
captured Pump Fees, SPL Token and ATA programs and through
`programs/pump/recovered/v2_mayhem_host.rs`. State is synthetic.

A case passes when the captured program and the model agree on the error and committed-state rollback (apart from the transaction fee), or on
the lamports of the user, curve, fee recipient, buyback recipient and creator
vault, the user's base balance, the stored curve bytes and the TradeEvent fields
the model names. This pins observed behavior on these inputs only; it is not a
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
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v2_mayhem_host.rs'

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
        elif line == 'panic':
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
ata = lambda owner, mint=MINT: pda(ATA, bytes(owner), bytes(TOKEN), bytes(mint))
GLOBAL = pda(PUMP, b'global')
CURVE = pda(PUMP, b'bonding-curve', bytes(MINT))
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
UVA_RENT = 1_844_400
TIMESTAMP = 1_700_000_000
TOKEN_RENT = 2_039_280
CURVE_RENT = (166 + 128) * 6960
U64 = 2**64 - 1
OPS = ('sell', 'buy', 'exact')
IX_NAME = {'sell': 'sell_v2', 'buy': 'buy_v2', 'exact': 'buy_exact_quote_in_v2'}


def mint_bytes(supply, decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_bytes(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_bytes(c):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[451:483] = bytes(OTHER)
    data[483:515] = bytes(RESERVED)
    data[515] = c['mayhem_enabled']
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
    data[81] = c['mayhem']
    data[124] = c['holder_reward']
    struct.pack_into('<Q', data, 115, c['creator_bps'])
    struct.pack_into('<Q', data, 142, c['vqr'])
    return bytes(data)


def default_case(**over):
    c = dict(op='sell', amount=None, limit=None, trailing='-', vtr=10**15, vqr=30_000_000_000, rtr=793_100_000_000_000,
             rqr=5_000_000_000, supply=2 * 10**15, complete=0, mayhem=1, mayhem_enabled=1, holder_reward=0, creator=1, creator_bps=0,
             configurable=0, mint_supply=10**15, tiers='0:95:30', buyback_bps=5_000, vault=0, user_base=10**13, curve_base=10**15,
             recipient=None, buyback_ok=1)
    c.update(over)
    if c['recipient'] is None:
        c['recipient'] = 'reserved' if c['mayhem'] else 'regular'
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
        out = Path(tempfile.mkdtemp()) / 'v2_mayhem_host'
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
        for key, path in ((PUMP, PUMP_ELF), (FEES, FEES_ELF), (TOKEN, TOKEN_ELF), (ATA, ATA_ELF)):
            _VM.add_program(key, program_images()[path])
        _VM.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    user = USER.pubkey()
    accounts = {
        user: Account(10**16, b'', SYSTEM),
        GLOBAL: Account(10**9, global_bytes(c), PUMP),
        MINT: Account(10**9, mint_bytes(c['mint_supply'], 6), TOKEN),
        WSOL: Account(10**9, mint_bytes(0, 9), TOKEN),
        CURVE: Account(CURVE_RENT + c['rqr'] % 10**15, curve_bytes(c), PUMP),
        ata(CURVE): Account(TOKEN_RENT, token_bytes(CURVE, c['curve_base']), TOKEN),
        ata(user): Account(TOKEN_RENT, token_bytes(user, c['user_base']), TOKEN),
        FEE_CONFIG: Account(10**9, fee_config_bytes(c), FEES),
        GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
        # `sell_v2` creates the user's accumulator; the buys read it.
        USER_VOLUME: (Account(0, b'', SYSTEM) if c['op'] == 'sell' else
                      Account(10**9, ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(user) + bytes(97), PUMP)),
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
    names = {
        'global': GLOBAL, 'base_mint': MINT, 'quote_mint': WSOL, 'base_token_program': TOKEN,
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'fee_recipient': recipient,
        'associated_quote_fee_recipient': ata(recipient, WSOL), 'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
        'associated_base_bonding_curve': ata(CURVE), 'associated_quote_bonding_curve': ata(CURVE, WSOL),
        'user': user, 'associated_base_user': ata(user), 'associated_quote_user': ata(user, WSOL),
        'creator_vault': VAULT(c), 'associated_creator_vault': ata(VAULT(c), WSOL), 'sharing_config': SHARING,
        'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
        'associated_user_volume_accumulator': ata(USER_VOLUME, WSOL), 'fee_config': FEE_CONFIG,
        'fee_program': FEES, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    ix = IX[IX_NAME[c['op']]]
    metas = [AccountMeta(names[a['name']], bool(a.get('signer')), bool(a.get('writable'))) for a in ix['accounts']]
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
            error = 'panic' if 'ProgramFailedToComplete' in text else text
        return dict(error=error, before=before_state, after=snap())
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0]
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    trade = next(e for e in events if e[:8] == TRADE_EVENT)
    return dict(error=None, before=before_state, after=snap(), delta=[balance(key) - was for key, was in zip(money, before)],
                stored=bytes(vm.get_account(CURVE).data), user_base=tokens(ata(user)), curve_base=tokens(ata(CURVE)),
                event=decode_trade(trade))


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
    event['mayhem_mode'] = data[offset]
    offset += 1 + 16
    event['buyback_bps'], event['buyback_fee'] = take(), take()
    shareholders = take('<I')
    offset += shareholders * 34 + 32 + 24
    event['holder_rewards_bps'], event['holder_rewards'] = take(), take()
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
    base = -m['tokens'] if sell else m['tokens']
    if (got['user_base'], got['curve_base']) != (c['user_base'] + base, c['curve_base'] - base):
        bad.append('base balances')
    curve = bytearray(curve_bytes(c))
    struct.pack_into('<4Q', curve, 8, m['vtr'], m['vqr'], m['rtr'], m['rqr'])
    curve[48] = m['completes']
    if got['stored'] != bytes(curve):
        bad.append('curve bytes')
    for field, value in got['event'].items():
        want = c['mayhem'] if field == 'mayhem_mode' else m[field]
        if value != want:
            bad.append(f'event {field} {value} != {want}')
    return bad


def fixed_cases():
    out = []
    add = lambda label, **k: out.append((label, default_case(**k)))
    big = lambda op: 10**12 if op != 'exact' else 10**15
    for op in OPS:
        for mayhem in (0, 1):
            tag = f'{op}-mayhem{mayhem}'
            add(f'{tag}-plain', op=op, mayhem=mayhem)
            add(f'{tag}-no-buyback-bps', op=op, mayhem=mayhem, buyback_bps=0)
            add(f'{tag}-full-buyback-bps', op=op, mayhem=mayhem, buyback_bps=10_000)
            add(f'{tag}-buyback-above-fee', op=op, mayhem=mayhem, buyback_bps=20_000)
            add(f'{tag}-no-creator', op=op, mayhem=mayhem, creator=0)
            add(f'{tag}-holder', op=op, mayhem=mayhem, holder_reward=1)
            add(f'{tag}-holder-no-creator', op=op, mayhem=mayhem, holder_reward=1, creator=0)
            add(f'{tag}-holder-override', op=op, mayhem=mayhem, holder_reward=1, configurable=1, creator_bps=500)
            add(f'{tag}-disabled', op=op, mayhem=mayhem, mayhem_enabled=0)
            add(f'{tag}-regular-recipient', op=op, mayhem=mayhem, recipient='regular')
            add(f'{tag}-reserved-recipient', op=op, mayhem=mayhem, recipient='reserved')
            add(f'{tag}-reserved-list-first', op=op, mayhem=mayhem, recipient='list0')
            add(f'{tag}-reserved-list-last', op=op, mayhem=mayhem, recipient='list6')
            add(f'{tag}-other-recipient', op=op, mayhem=mayhem, recipient='other')
            add(f'{tag}-other-recipient-complete', op=op, mayhem=mayhem, recipient='other', complete=1)
            add(f'{tag}-complete', op=op, mayhem=mayhem, complete=1)
            add(f'{tag}-zero', op=op, mayhem=mayhem, amount=0)
            add(f'{tag}-no-tiers', op=op, mayhem=mayhem, tiers='-')
            add(f'{tag}-vtr-zero', op=op, mayhem=mayhem, vtr=0)
            add(f'{tag}-huge-protocol', op=op, mayhem=mayhem, tiers=f'0:{U64}:30', vqr=10**15, amount=big(op))
            add(f'{tag}-vault-just-short', op=op, mayhem=mayhem, vault=890_879)
            add(f'{tag}-vault-at-minimum', op=op, mayhem=mayhem, vault=890_880)
            add(f'{tag}-bad-buyback', op=op, mayhem=mayhem, buyback_ok=0)
            add(f'{tag}-bad-buyback-recipient', op=op, mayhem=mayhem, buyback_ok=0, recipient='other')
            add(f'{tag}-bad-buyback-complete', op=op, mayhem=mayhem, buyback_ok=0, complete=1)
            add(f'{tag}-bad-buyback-zero', op=op, mayhem=mayhem, buyback_ok=0, amount=0)
            add(f'{tag}-bad-recipient-zero', op=op, mayhem=mayhem, recipient='other', amount=0)
            add(f'{tag}-bad-buyback-no-tiers', op=op, mayhem=mayhem, buyback_ok=0, tiers='-')
            for supply in (10**15, 10**15 - 1):
                for mint_supply in (10**15, 10**15 - 1):
                    add(f'{tag}-tier-supply{supply}-mint{mint_supply}', op=op, mayhem=mayhem, tiers=f'{10**15}:95:30;0:50:20',
                        supply=supply, mint_supply=mint_supply, vqr=10**15, amount=big(op))
            add(f'{tag}-rounded-fee', op=op, mayhem=mayhem, tiers='0:1:1', amount=10**11 if op != 'exact' else 10**5)
    for mayhem in (0, 1):
        add(f'sell-too-many-{mayhem}', mayhem=mayhem, amount=10**13 + 1)
        add(f'sell-limit-short-{mayhem}', mayhem=mayhem, limit=U64)
        add(f'sell-over-real-quote-{mayhem}', mayhem=mayhem, amount=10**14, rqr=1_000)
        add(f'sell-one-lamport-{mayhem}', mayhem=mayhem, amount=1, vqr=10**9)
        add(f'buy-limit-short-{mayhem}', mayhem=mayhem, op='buy', limit=1)
        add(f'buy-over-real-{mayhem}', mayhem=mayhem, op='buy', amount=10**13, rtr=10**12)
        add(f'buy-partial-{mayhem}', mayhem=mayhem, op='buy', trailing='01', amount=10**13, rtr=10**12)
        add(f'buy-completes-{mayhem}', mayhem=mayhem, op='buy', amount=10**12, rtr=10**12)
        add(f'buy-bad-option-{mayhem}', mayhem=mayhem, op='buy', trailing='02', recipient='other')
        add(f'buy-vtr-equals-amount-{mayhem}', mayhem=mayhem, op='buy', vtr=10**12, rtr=10**12)
        add(f'exact-limit-high-{mayhem}', mayhem=mayhem, op='exact', limit=U64)
        add(f'exact-partial-{mayhem}', mayhem=mayhem, op='exact', trailing='01', amount=10**10, rtr=10**12)
        add(f'exact-over-real-{mayhem}', mayhem=mayhem, op='exact', amount=10**10, rtr=10**12)
        add(f'exact-dust-{mayhem}', mayhem=mayhem, op='exact', amount=1, limit=1)
        add(f'exact-zero-limit-{mayhem}', mayhem=mayhem, op='exact', limit=0)
    return out


def random_cases(n=300, seed=20261030):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        op = rng.choice(OPS)
        vtr = rng.randrange(10**12, 2 * 10**15)
        rtr = rng.randrange(1, vtr)
        amount = rng.choice([rng.randrange(1, 10**13), rng.randrange(1, 10**6), rng.randrange(1, 10**10)])
        mayhem = rng.randrange(2)
        tiers = rng.choice(['0:95:30', '0:0:0', '0:95:30;1000000:50:20', f'0:300:100;{10**9}:50:25', '0:10000:10000'])
        c = default_case(op=op, amount=amount, vtr=vtr, vqr=rng.randrange(10**8, 10**12), rtr=rtr, mayhem=mayhem,
                         trailing=rng.choice(['-', '00', '01', '0100']) if op != 'sell' else '-',
                         rqr=rng.randrange(0, 10**13), supply=rng.randrange(5 * 10**14, 2 * 10**15), holder_reward=rng.randrange(2),
                         creator=int(rng.random() < .8), tiers=tiers, configurable=rng.randrange(2), creator_bps=rng.choice([0, 50, 500]),
                         buyback_bps=rng.choice([0, 1, 3_333, 5_000, 10_000]), vault=rng.choice([0, 1, 890_879, 890_880, 10**9]),
                         user_base=rng.choice([10**13, amount, max(0, amount - 1), 10**15]))
        c['curve_base'] = rng.randrange(max(amount, rtr), 2 * 10**15)
        kind, ans = model([c])[0]
        if kind == 'ok':
            if op == 'sell':
                c['limit'] = rng.choice([0, ans['user_delta'] + ans['vault_credit'] - ans['creator_fee'] + UVA_RENT, 1])
            elif op == 'buy':
                c['limit'] = rng.choice([U64, -ans['user_delta'], -ans['user_delta'] - 1])
            else:
                c['limit'] = rng.choice([1, ans['tokens'], ans['tokens'] + 1])
        out.append((f'random-{len(out)}', c))
    return out


class V2MayhemCaptured(unittest.TestCase):
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
        for want in ('ok', 'panic', 102, 6000, 6002, 6003, 6005, 6020, 6021, 6022, 6023, 6024, 6025, 6026, 6041, 6042, 6057):
            self.assertIn(want, outcomes)
        self.assertTrue(any(a[0] == 'ok' and a[1]['completes'] for a in results))
        self.assertTrue(any(a[0] == 'ok' and a[1]['holder_rewards'] for a in results))

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
        with tempfile.TemporaryDirectory(prefix='pinned-v2-model-') as temporary:
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
