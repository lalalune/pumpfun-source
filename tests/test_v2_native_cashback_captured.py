"""Captured-program checks for native-SOL cashback on the v2 trades.

`sell_v2.rs` and `buy_v2.rs` price a regular coin and pay the creator fee into
the creator vault. They leave out cashback coins. Every case here runs
`sell_v2`, `buy_v2`, or `buy_exact_quote_in_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, against a native curve. The same
inputs go to `programs/pump/recovered/v2_native_cashback_host.rs`. Error
codes, lamport movements, accumulator bytes, reserves, and TradeEvent fee
fields must agree. Mayhem, holder-reward, whitelist, and token-quote curves
are not covered. This is not a byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/v2_native_cashback_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
TRADE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'TradeEvent'))

USER = Keypair.from_seed(bytes([214]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([14]) * 32)
MINT = Pubkey.from_bytes(bytes([15]) * 32)
OTHER = Pubkey.from_bytes(bytes([16]) * 32)


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)


GLOBAL = pda(b'global')[0]
CURVE = pda(b'bonding-curve', bytes(MINT))[0]
EVENT_AUTHORITY = pda(b'__event_authority')[0]
FEE_CONFIG, FEE_CONFIG_BUMP = pda(b'fee_config', bytes(PUMP), program=FEES)
VAULT = pda(b'creator-vault', bytes(CREATOR))[0]
DEFAULT_VAULT = pda(b'creator-vault', bytes(32))[0]
UVA = pda(b'user_volume_accumulator', bytes(USER.pubkey()))[0]
GLOBAL_VOLUME = pda(b'global_volume_accumulator')[0]
SHARING = pda(b'sharing-config', bytes(MINT), program=FEES)[0]

TX_FEE = 5000
USER_LAMPORTS = 10**12
CURVE_RENT = 2_046_960
TOKEN_RENT = 2_039_280
UVA_RENT = 1_844_400
UVA_SIZE = 137
CLAIMED_STAMP = 55
VT, VS = 873_000_000_000_000, 36_872_852_233
RT, RS, SUPPLY = 593_100_000_000_000, 6_872_852_233, 10**15
U64 = 2**64 - 1


def ata(owner, mint=MINT):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)[0]


def mint_data(supply, decimals=6):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token_data(owner, amount):
    return (bytes(MINT) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def global_data(buyback_bps, configurable):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    data[41:73] = bytes(FEE_RECIPIENT)
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<Q', data, 997, buyback_bps)
    data[1045] = int(configurable)
    return bytes(data)


def fee_config_data(tiers):
    data = bytearray(ACCOUNT_DISC['FeeConfig']) + bytes([FEE_CONFIG_BUMP]) + bytes(32) + bytes(24)
    data += struct.pack('<I', len(tiers))
    for threshold, protocol, creator in tiers:
        data += threshold.to_bytes(16, 'little') + struct.pack('<QQQ', 0, protocol, creator)
    data += struct.pack('<I', 0) + bytes(24)
    return bytes(data).ljust(4104, b'\0')


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, item['vt'], item['vs'], item['rt'], item['rs'], item['supply'])
    data[48] = int(item['complete'])
    data[49:81] = bytes(CREATOR if item['creator'] else SYSTEM)
    data[82] = item['cashback']
    struct.pack_into('<Q', data, 115, item['creator_bps'])
    return bytes(data)


def uva_data(item):
    data = bytearray(UVA_SIZE)
    data[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
    if item['prior'] == 'self':
        data[8:40] = bytes(USER.pubkey())
    elif item['prior'] == 'other':
        data[8:40] = bytes(OTHER)
    data[40] = 1 if item['unclaimed'] else 0
    struct.pack_into('<Q', data, 41, item['unclaimed'])
    struct.pack_into('<Q', data, 49, item['claimed'])
    struct.pack_into('<Q', data, 57, item['volume'])
    struct.pack_into('<q', data, 65, item['last'])
    data[73] = 1 if item['claimed'] else 0
    struct.pack_into('<Q', data, 74, item['earned'])
    struct.pack_into('<Q', data, 82, CLAIMED_STAMP)
    if item['hold'] == 'baddisc':
        data[0] ^= 1
    return bytes(data)


DEFAULTS = dict(
    op='sell', cashback=1, hold='valid', lamports=UVA_RENT, earned=0, writable=True, prior='self',
    unclaimed=0, claimed=0, volume=0, last=0, vault=0, vt=VT, vs=VS, rt=RT, rs=RS, complete=False,
    creator=True, creator_bps=0, supply=SUPPLY, configurable=False, buyback=0, user_tokens=10**13,
    fee_ok=True, buyback_ok=True, trailing=b'', tiers=((0, 95, 30),), overflow=False,
)


def case(amount, limit, **changes):
    item = dict(DEFAULTS, **changes)
    item['amount'], item['limit'] = amount, limit
    return item


def decode_trade(data):
    offset = 8 + 32

    def take(fmt):
        nonlocal offset
        value = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)
        return value

    event = {'sol_amount': take('<Q'), 'token_amount': take('<Q')}
    event['is_buy'] = data[offset]
    offset += 1 + 32 + 8
    event['virtual_sol'], event['virtual_token'] = take('<Q'), take('<Q')
    event['real_sol'], event['real_token'] = take('<Q'), take('<Q')
    offset += 32
    event['fee_bps'], event['fee'] = take('<Q'), take('<Q')
    offset += 32
    event['creator_bps'], event['creator_fee'] = take('<Q'), take('<Q')
    event['track_volume'] = data[offset]
    offset += 1
    event['unclaimed'], event['claimed'], event['volume'] = take('<Q'), take('<Q'), take('<Q')
    event['last'] = take('<q')
    name_len = take('<I')
    event['ix_name'] = data[offset:offset + name_len].decode()
    offset += name_len + 1
    event['cashback_bps'], event['cashback'] = take('<Q'), take('<Q')
    event['buyback_bps'], event['buyback_fee'] = take('<Q'), take('<Q')
    return event


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(FEES, FEES_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
    vault = VAULT if item['creator'] else DEFAULT_VAULT
    uva_key = OTHER if item['hold'] == 'wrong' else UVA
    accounts = {
        USER.pubkey(): Account(USER_LAMPORTS, b'', SYSTEM),
        GLOBAL: Account(10**9, global_data(item['buyback'], item['configurable']), PUMP),
        MINT: Account(10**9, mint_data(item['supply']), TOKEN),
        WSOL: Account(10**9, mint_data(0, 9), TOKEN),
        CURVE: Account(CURVE_RENT + item['rs'], curve_data(item), PUMP),
        ata(CURVE): Account(TOKEN_RENT, token_data(CURVE, item['rt']), TOKEN),
        ata(USER.pubkey()): Account(TOKEN_RENT, token_data(USER.pubkey(), item['user_tokens'] if item['op'] == 'sell' else 0), TOKEN),
        FEE_CONFIG: Account(10**9, fee_config_data(item['tiers']), FEES),
    }
    if item['op'] != 'sell':
        accounts[GLOBAL_VOLUME] = Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP)
    if item['hold'] == 'funded':
        accounts[uva_key] = Account(item['lamports'], b'', SYSTEM)
    elif item['hold'] == 'sysdata':
        accounts[uva_key] = Account(item['lamports'], b'\x11' * 10, SYSTEM)
    elif item['hold'] != 'missing':
        accounts[uva_key] = Account(item['lamports'], uva_data(item), OTHER if item['hold'] == 'foreign' else PUMP)
    if item['vault']:
        accounts[vault] = Account(item['vault'], b'', SYSTEM)
    for key, account in accounts.items():
        vm.set_account(key, account)
    fee_recipient = FEE_RECIPIENT if item['fee_ok'] else OTHER
    buyback = BUYBACK if item['buyback_ok'] else OTHER
    names = {
        'global': GLOBAL, 'base_mint': MINT, 'quote_mint': WSOL, 'base_token_program': TOKEN,
        'quote_token_program': TOKEN, 'associated_token_program': ATA, 'fee_recipient': fee_recipient,
        'associated_quote_fee_recipient': ata(fee_recipient, WSOL), 'buyback_fee_recipient': buyback,
        'associated_quote_buyback_fee_recipient': ata(buyback, WSOL), 'bonding_curve': CURVE,
        'associated_base_bonding_curve': ata(CURVE), 'associated_quote_bonding_curve': ata(CURVE, WSOL),
        'user': USER.pubkey(), 'associated_base_user': ata(USER.pubkey()),
        'associated_quote_user': ata(USER.pubkey(), WSOL), 'creator_vault': vault,
        'associated_creator_vault': ata(vault, WSOL), 'sharing_config': SHARING,
        'user_volume_accumulator': uva_key, 'associated_user_volume_accumulator': ata(uva_key, WSOL),
        'fee_config': FEE_CONFIG, 'fee_program': FEES, 'system_program': SYSTEM,
        'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    if item['op'] != 'sell':
        names['global_volume_accumulator'] = GLOBAL_VOLUME
    ix = IX['sell_v2' if item['op'] == 'sell' else ('buy_v2' if item['op'] == 'buy' else 'buy_exact_quote_in_v2')]
    metas = []
    for account in ix['accounts']:
        writable = account.get('writable', False)
        if account['name'] == 'user_volume_accumulator' and not item['writable']:
            writable = False
        metas.append(AccountMeta(names[account['name']], account.get('signer', False), writable))
    watched = (USER.pubkey(), CURVE, FEE_RECIPIENT, BUYBACK, vault, uva_key)
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', item['amount'], item['limit']) + item['trailing']
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], USER.pubkey(), [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        logs = result.meta().logs()
        if 'PrivilegeEscalation' in text:
            kind = 'privilege'
        elif 'BorshIoError' in text or any('BorshIoError' in line for line in logs):
            kind = 'borsh'
        elif 'ProgramFailedToComplete' in text or any('panicked' in line for line in logs):
            kind = 'panic'
        else:
            code = re.search(r'Custom\((\d+)\)', text)
            kind = int(code.group(1)) if code else text
        return {'error': kind, 'logs': logs}
    delta = dict(zip(('user', 'curve', 'recipient', 'buyback', 'vault', 'uva'),
                     (lamports(key) - old for key, old in zip(watched, before))))
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    stored = vm.get_account(CURVE).data
    tokens = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0]
    uva = vm.get_account(uva_key)
    return {
        'error': None, 'delta': delta, 'logs': [],
        'trades': [decode_trade(event) for event in events if event[:8] == TRADE_EVENT],
        'events': len(events),
        'reserves': struct.unpack_from('<QQQQ', stored, 8), 'complete': stored[48],
        'tokens': (tokens(ata(USER.pubkey())), tokens(ata(CURVE))),
        'uva': None if uva is None else bytes(uva.data),
    }


def host_line(item):
    trailing = item['trailing'].hex() or '-'
    tiers = ';'.join(f'{threshold}:{protocol}:{creator}' for threshold, protocol, creator in item['tiers'])
    fields = [
        item['op'], item['cashback'], item['hold'], item['lamports'], item['earned'], int(item['writable']),
        item['prior'], item['unclaimed'], item['claimed'], item['volume'], item['last'], item['vault'],
        item['vt'], item['vs'], item['rt'], item['rs'], int(item['complete']), int(item['creator']),
        item['creator_bps'], item['supply'], int(item['configurable']), item['buyback'], item['user_tokens'],
        int(item['fee_ok']), int(item['buyback_ok']), item['amount'], item['limit'], trailing, tiers,
    ]
    return ','.join(str(field) for field in fields)


def fixed_cases():
    cases = []
    add = lambda *args, **kwargs: cases.append(case(*args, **kwargs))
    # Cashback sells: the creator fee lands on the accumulator, not the vault.
    add(10**12, 0)
    add(10**12, 0, earned=7, unclaimed=11, claimed=22, volume=33, last=44)
    add(10**12, 0, vault=1)
    add(10**12, 0, vault=890_880)
    add(10**12, 0, hold='missing', lamports=0)
    add(10**12, 0, hold='funded', lamports=100)
    add(10**12, 0, hold='funded', lamports=UVA_RENT)
    add(10**12, 0, hold='funded', lamports=UVA_RENT + 50)
    add(10**12, 0, prior='zero')
    add(10**12, 0, prior='other')
    add(10**12, 0, buyback=5_000)
    add(10**12, 0, creator_bps=500, configurable=True)
    add(10**12, 0, creator=False)
    add(10**12, 0, tiers=((0, 0, 0),))
    # The same sells on a regular coin still pay the vault and leave cashback alone.
    add(10**12, 0, cashback=0, earned=9)
    add(10**12, 0, cashback=0, vault=1, earned=9)
    add(10**12, 0, cashback=0, earned=U64)
    # Buys and exact-in, both routes.
    add(10**9, 10**12, op='buy', earned=5, unclaimed=11, claimed=22, volume=33, last=44)
    add(10**9, 10**12, op='buy', vault=1, earned=5)
    add(10**9, 10**12, op='buy', hold='missing', lamports=0)
    add(10**9, 10**12, op='buy', cashback=0, vault=1, earned=5)
    add(10**9, 1, op='exact', earned=9)
    add(10**9, 1, op='exact', cashback=0, vault=890_880, earned=9)
    add(10**9, 10**12, op='buy', buyback=5_000)
    add(10**9, 1, op='exact', creator_bps=500, configurable=True)
    # Overflow panics only after the trade is otherwise going to pay a fee.
    add(10**12, 0, earned=U64, overflow=True)
    add(10**9, 10**12, op='buy', earned=U64, overflow=True)
    add(10**9, 1, op='exact', earned=U64 - 5, overflow=True)
    add(10**12, 0, earned=U64, complete=True)
    add(0, 0, earned=U64)
    add(10**12, 0, earned=U64, fee_ok=False)
    add(10**12, 10**15, earned=U64)
    # Accumulator admission, before the handler. Rent and owner beat the mut flag.
    add(10**12, 0, hold='foreign')
    add(10**12, 0, hold='baddisc')
    add(10**12, 0, hold='wrong')
    add(10**12, 0, writable=False)
    add(10**12, 0, hold='missing', writable=False)
    add(10**12, 0, hold='funded', lamports=UVA_RENT, writable=False)
    add(10**12, 0, lamports=UVA_RENT - 1)
    add(10**12, 0, lamports=UVA_RENT - 1, writable=False)
    add(10**12, 0, lamports=100, cashback=0)
    add(10**9, 10**12, op='buy', lamports=100)
    add(10**12, 0, hold='sysdata')
    add(10**12, 0, hold='baddisc', writable=False)
    add(10**12, 0, hold='foreign', writable=False)
    add(10**12, 0, hold='wrong', writable=False)
    add(10**12, 0, cashback=2)
    # Trade guards still win over the cashback credit.
    add(10**12, 0, complete=True)
    add(0, 0)
    add(10**13 + 1, 0)
    add(10**12, 0, fee_ok=False)
    add(10**12, 0, buyback_ok=False)
    add(10**12, 0, tiers=())
    add(10**12, 0, buyback=10_001)
    add(0, 10**12, op='buy')
    add(10**9, 10**12, op='buy', complete=True)
    add(10**9, 1, op='buy', trailing=b'\2')
    add(0, 1, op='exact')
    add(10**9, 0, op='exact')
    add(10**9, 1, op='exact', tiers=())
    return cases


def random_cases(count=40, seed=3030):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        op = rng.choice(('sell', 'buy', 'exact'))
        amount = rng.choice((10**6, 10**9) if op == 'exact' else (10**9, 10**12, rng.randrange(1, 10**6)))
        limit = 0 if op == 'sell' else (1 if op == 'exact' else 10**12)
        cases.append(case(
            amount, limit, op=op, cashback=rng.choice((0, 1)),
            earned=rng.choice((0, 7, 10**6)), vault=rng.choice((0, 1, UVA_RENT)),
            buyback=rng.choice((0, 5_000)), creator=rng.random() < 0.85,
            creator_bps=rng.choice((0, 500)), configurable=rng.random() < 0.4,
            hold=rng.choice(('valid', 'valid', 'missing', 'funded')),
            lamports=rng.choice((UVA_RENT, UVA_RENT + 10, 100)),
            prior=rng.choice(('self', 'zero', 'other')),
            unclaimed=rng.choice((0, 11)),
        ))
    return cases


class V2NativeCashbackCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'v2-native-cashback-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer == 'panic':
            self.assertEqual(captured['error'], 'panic')
            if item['overflow']:
                self.assertTrue(any('Overflowing cashback earned' in line for line in captured['logs']))
            return
        if answer in ('privilege', 'borsh'):
            self.assertEqual(captured['error'], answer)
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer.split(':', 1)[1]))
            return
        self.assertIsNone(captured['error'])
        head, ix_name = answer.rsplit(',', 1)
        (sol, tokens, protocol_bps, protocol_fee, creator_bps, creator_fee, buyback_fee, vault_delta, uva_delta,
         earned, event_creator_bps, event_creator_fee, event_cashback_bps, event_cashback, event_unclaimed,
         event_claimed, event_volume, event_last, vt, vs, rt, rs, complete, user_output, user_is_signer) = map(int, head.split(',')[1:])
        if item['op'] == 'sell':
            user_delta = user_output - TX_FEE - (vault_delta + uva_delta - creator_fee)
            curve_delta = -sol
            user_tokens = item['user_tokens'] - tokens
            curve_tokens = item['rt'] + tokens
        else:
            user_delta = -(TX_FEE + sol + protocol_fee + vault_delta + uva_delta)
            curve_delta = sol
            user_tokens = tokens
            curve_tokens = item['rt'] - tokens
        self.assertEqual(captured['delta'], {
            'user': user_delta, 'curve': curve_delta, 'recipient': protocol_fee - buyback_fee,
            'buyback': buyback_fee, 'vault': vault_delta, 'uva': uva_delta,
        })
        self.assertEqual(captured['reserves'], (vt, vs, rt, rs))
        self.assertEqual(captured['complete'], complete)
        self.assertEqual(captured['tokens'], (user_tokens, curve_tokens))
        self.assertEqual(captured['events'], 1 + complete if item['op'] != 'sell' else 1)
        self.assertEqual(captured['trades'], [{
            'sol_amount': sol, 'token_amount': tokens, 'is_buy': 0 if item['op'] == 'sell' else 1,
            'virtual_sol': vs, 'virtual_token': vt, 'real_sol': rs, 'real_token': rt,
            'fee_bps': protocol_bps, 'fee': protocol_fee, 'creator_bps': event_creator_bps,
            'creator_fee': event_creator_fee, 'track_volume': 0, 'unclaimed': event_unclaimed,
            'claimed': event_claimed, 'volume': event_volume, 'last': event_last, 'ix_name': ix_name,
            'cashback_bps': event_cashback_bps, 'cashback': event_cashback,
            'buyback_bps': item['buyback'], 'buyback_fee': buyback_fee,
        }])
        data = captured['uva']
        self.assertEqual(len(data), UVA_SIZE)
        self.assertEqual(data[:8], ACCOUNT_DISC['UserVolumeAccumulator'])
        expect_user = bytes(OTHER) if not user_is_signer else bytes(USER.pubkey())
        self.assertEqual(data[8:40], expect_user)
        self.assertEqual(struct.unpack_from('<Q', data, 74)[0], earned)
        if item['hold'] == 'valid':
            self.assertEqual(struct.unpack_from('<Q', data, 41)[0], item['unclaimed'])
            self.assertEqual(struct.unpack_from('<Q', data, 49)[0], item['claimed'])
            self.assertEqual(struct.unpack_from('<Q', data, 57)[0], item['volume'])
            self.assertEqual(struct.unpack_from('<q', data, 65)[0], item['last'])
            self.assertEqual(struct.unpack_from('<Q', data, 82)[0], CLAIMED_STAMP)
        else:
            self.assertEqual(data[40:74], bytes(34))
            self.assertEqual(data[82:], bytes(UVA_SIZE - 82))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_fee_paid_to_the_other_account(self):
        item = case(10**12, 0, vault=1, earned=7)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        swapped = dict(captured, delta=dict(captured['delta'], vault=captured['delta']['uva'], uva=captured['delta']['vault']))
        with self.assertRaises(AssertionError):
            self.assert_matches(item, answer, swapped)

    def test_fixed_cases_cover_success_and_the_cashback_failures(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {answer.split(',')[0] for answer in answers}
        self.assertTrue({'ok', 'panic', 'privilege', 'borsh'} <= outcomes)
        for code in (0, 2000, 2005, 2006, 3002, 3007, 6000, 6003, 6005, 6020, 6022, 6023, 6041, 6057):
            self.assertIn(f'error:{code}', outcomes)


if __name__ == '__main__':
    unittest.main()
