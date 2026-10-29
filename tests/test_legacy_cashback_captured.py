"""Captured-program checks for creator-fee routing on legacy cashback coins.

Every case runs Pump `buy` or `sell` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, and Associated Token programs, against synthetic accounts. The
same inputs go to `programs/pump/recovered/legacy_cashback_host.rs`, and the
error code, where the creator fee goes, user volume accumulator state, and
TradeEvent fee fields must agree. This shows matching behavior on these
inputs only; it is not a byte-identity claim.
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
HOST_SOURCE = ROOT / 'programs/pump/recovered/legacy_cashback_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
TRADE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'TradeEvent'))

USER = Keypair.from_seed(bytes([211]) * 32)
CREATOR = Pubkey.from_bytes(bytes([12]) * 32)
FEE_RECIPIENT = Pubkey.from_bytes(bytes([13]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([14]) * 32)
MINT = Pubkey.from_bytes(bytes([15]) * 32)
OTHER = Pubkey.from_bytes(bytes([16]) * 32)


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)


GLOBAL = pda(b'global')[0]
CURVE = pda(b'bonding-curve', bytes(MINT))[0]
CURVE_V2 = pda(b'bonding-curve-v2', bytes(MINT))[0]
EVENT_AUTHORITY = pda(b'__event_authority')[0]
FEE_CONFIG, FEE_CONFIG_BUMP = pda(b'fee_config', bytes(PUMP), program=FEES)
VAULT = pda(b'creator-vault', bytes(CREATOR))[0]
DEFAULT_VAULT = pda(b'creator-vault', bytes(32))[0]
GLOBAL_VOLUME = pda(b'global_volume_accumulator')[0]
USER_VOLUME = pda(b'user_volume_accumulator', bytes(USER.pubkey()))[0]
SLOT_KEYS = {'curve_v2': CURVE_V2, 'buyback': BUYBACK, 'uva': USER_VOLUME, 'other': OTHER}
UVA_RENT = 1_844_400  # Rent::minimum_balance(137)

TX_FEE = 5000
USER_LAMPORTS = 10**12
CURVE_RENT = 2_046_960
TOKEN_RENT = 2_039_280
# A curve partway along the standard path: 200M tokens already bought.
VT, VS = 873_000_000_000_000, 36_872_852_233
RT, RS, SUPPLY = 593_100_000_000_000, 6_872_852_233, 10**15
VAULT_RENT = 890_880  # Rent::minimum_balance(0)
U64 = 2**64 - 1


def ata(owner):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN), bytes(MINT)], ATA)[0]


def mint_data(supply):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


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
    data[82] = int(item['cashback'])
    struct.pack_into('<Q', data, 115, item['creator_bps'])
    return bytes(data)



DEFAULTS = dict(vt=VT, vs=VS, rt=RT, rs=RS, supply=SUPPLY, complete=False, creator=True, creator_bps=0,
                cashback=True, buyback=0, vault=0, uva=('valid', UVA_RENT, 0, True), slots=None,
                tiers=((0, 95, 30),))


def case(side, amount, limit, **changes):
    item = dict(DEFAULTS, **changes)
    item['side'], item['args'] = side, (amount, limit)
    if item['slots'] is not None:  # remaining accounts are positional: drop gaps
        present = [s for s in item['slots'] if s != 'absent']
        item['slots'] = tuple(present) + ('absent',) * (3 - len(present))
    else:
        if side == 'buy':
            item['slots'] = ('curve_v2', 'buyback', 'absent')
        elif item['cashback']:
            item['slots'] = ('uva', 'curve_v2', 'buyback')
        else:
            item['slots'] = ('curve_v2', 'buyback', 'absent')
    return item


def uva_account(state):
    kind = state[0]
    if kind == 'missing':
        return None
    if kind == 'funded':  # system-owned, no data, some lamports already present
        return Account(state[1], b'', SYSTEM)
    data = bytearray(137)
    data[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
    if kind == 'baddisc':
        data[0] ^= 1
    if kind == 'valid' and state[3]:
        data[8:40] = bytes(USER.pubkey())
    if kind == 'valid':
        struct.pack_into('<Q', data, 74, state[2])
    return Account(state[1] if kind == 'valid' else UVA_RENT, bytes(data), OTHER if kind == 'foreign' else PUMP)


def decode_trade(data):
    offset = 8 + 32
    def take(fmt):
        nonlocal offset
        value = struct.unpack_from(fmt, data, offset)[0]
        offset += struct.calcsize(fmt)
        return value
    event = {'sol_amount': take('<Q'), 'token_amount': take('<Q')}
    offset += 1 + 32 + 8 + 32 + 32
    event['fee_bps'], event['fee'] = take('<Q'), take('<Q')
    offset += 32
    event['creator_bps'], event['creator_fee'] = take('<Q'), take('<Q')
    offset += 1 + 32  # track_volume and four user-volume snapshot fields
    name_len = take('<I')
    offset += name_len + 1  # ix_name, mayhem_mode
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
    accounts = {
        USER.pubkey(): Account(USER_LAMPORTS, b'', SYSTEM),
        GLOBAL: Account(10**9, global_data(item['buyback'], False), PUMP),
        MINT: Account(10**9, mint_data(item['supply']), TOKEN),
        CURVE: Account(CURVE_RENT + item['rs'], curve_data(item), PUMP),
        ata(CURVE): Account(TOKEN_RENT, token_data(CURVE, item['rt']), TOKEN),
        ata(USER.pubkey()): Account(TOKEN_RENT, token_data(USER.pubkey(), 10**14), TOKEN),
        FEE_CONFIG: Account(10**9, fee_config_data(item['tiers']), FEES),
        CURVE_V2: Account(10**7, b'', SYSTEM),
        GLOBAL_VOLUME: Account(10**9, ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), PUMP),
    }
    if item['vault']:
        accounts[vault] = Account(item['vault'], b'', SYSTEM)
    uva = uva_account(item['uva'])
    if uva is not None:
        accounts[USER_VOLUME] = uva
    for key, account in accounts.items():
        vm.set_account(key, account)
    names = {
        'global': GLOBAL, 'fee_recipient': FEE_RECIPIENT, 'mint': MINT, 'bonding_curve': CURVE,
        'associated_bonding_curve': ata(CURVE), 'associated_user': ata(USER.pubkey()), 'user': USER.pubkey(),
        'system_program': SYSTEM, 'token_program': TOKEN, 'creator_vault': vault,
        'event_authority': EVENT_AUTHORITY, 'program': PUMP, 'fee_config': FEE_CONFIG, 'fee_program': FEES,
        'global_volume_accumulator': GLOBAL_VOLUME, 'user_volume_accumulator': USER_VOLUME,
    }
    ix = IX[item['side']]
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    metas += [AccountMeta(SLOT_KEYS[s], False, s != 'curve_v2') for s in item['slots'] if s != 'absent']
    watched = (USER.pubkey(), CURVE, FEE_RECIPIENT, BUYBACK, vault, USER_VOLUME)
    lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
    before = [lamports(key) for key in watched]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', *item['args'])
    tx = Transaction.new_signed_with_payer([Instruction(PUMP, data, metas)], USER.pubkey(), [USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text}
    delta = dict(zip(('user', 'curve', 'recipient', 'buyback', 'vault', 'uva'),
                     (lamports(k) - b for k, b in zip(watched, before))))
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'delta': delta, 'trade': decode_trade(next(e for e in events if e[:8] == TRADE_EVENT)),
            'uva': uva_summary(vm.get_account(USER_VOLUME))}


def uva_summary(account):
    if account is None or not account.data:
        return None
    data = account.data
    return (str(account.owner), len(data), data[:8] == ACCOUNT_DISC['UserVolumeAccumulator'],
            data[8:40] == bytes(USER.pubkey()), struct.unpack_from('<Q', data, 74)[0])


def creator_quote(item):
    """Creator fee and bps the trade prices (single fee tier; amounts are
    already checked against the captured program by the legacy buy/sell
    harnesses, and re-checked here against the TradeEvent sol_amount)."""
    amount = item['args'][0]
    if item['side'] == 'buy':
        sol = item['vs'] * amount // (item['vt'] - amount) + 1
    else:
        sol = item['vs'] * amount // (item['vt'] + amount)
    bps = item['tiers'][0][2]
    fee = -(-sol * bps // 10_000) if item['creator'] else 0
    return sol, fee, bps


def host_line(item):
    _, fee, bps = creator_quote(item)
    uva = item['uva']
    lamports = uva[1] if uva[0] in ('funded', 'valid') else 0
    earned = uva[2] if uva[0] == 'valid' else 0
    fields = [item['side'], int(item['cashback']), fee, bps, uva[0], lamports, earned, item['vault'], *item['slots']]
    return ','.join(str(f) for f in fields)


def fixed_cases():
    cases = []
    add = lambda *a, **k: cases.append(case(*a, **k))
    for side, amount, limit in (('buy', 10**9, U64), ('sell', 10**12, 0)):
        # Cashback route: fee to the UVA, event fee fields swapped.
        add(side, amount, limit)
        add(side, amount, limit, tiers=((0, 95, 250),))
        add(side, 1, limit, tiers=((0, 95, 1),))
        # UVA creation: missing, partly funded, funded past rent; user field fill-in.
        add(side, amount, limit, uva=('missing',))
        for lamports in (1, UVA_RENT - 1, UVA_RENT, UVA_RENT + 9):
            add(side, amount, limit, uva=('funded', lamports))
        add(side, amount, limit, uva=('valid', UVA_RENT, 5, False))
        add(side, amount, limit, uva=('valid', 10**9, 77, True))
        add(side, amount, limit, uva=('foreign',))
        add(side, amount, limit, uva=('baddisc',))
        add(side, amount, limit, uva=('valid', UVA_RENT, U64, True))
        add(side, amount, limit, uva=('valid', UVA_RENT, U64 - 30_000_000, True), tiers=((0, 95, 250),))
        # No creator fee: no cashback even on a cashback coin.
        add(side, amount, limit, tiers=((0, 95, 0),))
        add(side, amount, limit, creator=False)
        add(side, amount, limit, tiers=((0, 95, 0),), uva=('valid', UVA_RENT, U64, True))
        # Regular coin controls: creator vault route with rent top-up.
        for vault in (0, 1, VAULT_RENT - 1, VAULT_RENT):
            add(side, amount, limit, cashback=False, vault=vault)
        add(side, amount, limit, cashback=False, uva=('missing',))
        add(side, amount, limit, cashback=False, uva=('valid', UVA_RENT, U64, True))
        add(side, amount, limit, buyback=5_000)
    # Remaining-account order per route.
    two = (('absent', 'absent'), ('curve_v2', 'absent'), ('curve_v2', 'buyback'), ('other', 'buyback'),
           ('buyback', 'buyback'), ('curve_v2', 'other'), ('uva', 'buyback'), ('buyback', 'absent'),
           ('curve_v2', 'curve_v2'))
    three = (('uva', 'curve_v2', 'buyback'), ('uva', 'curve_v2', 'absent'), ('uva', 'other', 'buyback'),
             ('uva', 'curve_v2', 'other'), ('uva', 'absent', 'absent'), ('other', 'curve_v2', 'buyback'),
             ('curve_v2', 'curve_v2', 'buyback'))
    for side, amount, limit in (('buy', 10**9, U64), ('sell', 10**12, 0)):
        for slots in [s + ('absent',) for s in two] + list(three):
            for changes in ({}, {'cashback': False}, {'tiers': ((0, 95, 0),)}):
                add(side, amount, limit, slots=slots, **changes)
    # Guard order: UVA checks against later account checks.
    add('buy', 10**9, U64, uva=('valid', UVA_RENT, U64, True), slots=('curve_v2', 'other', 'absent'))
    add('buy', 10**9, U64, uva=('valid', UVA_RENT, U64, True), slots=('other', 'buyback', 'absent'))
    add('buy', 10**9, U64, uva=('foreign',), slots=('absent', 'absent', 'absent'))
    add('sell', 10**12, 0, uva=('valid', UVA_RENT, U64, True), slots=('uva', 'other', 'absent'))
    add('sell', 10**12, 0, uva=('missing',), slots=('uva', 'other', 'buyback'))
    add('sell', 10**12, 0, uva=('baddisc',), slots=('uva', 'absent', 'absent'))
    add('sell', 10**12, 0, uva=('foreign',), slots=('other', 'curve_v2', 'buyback'))
    return cases


def random_cases(count=60, seed=1895):
    rng = random.Random(seed)
    slot_names = ('absent', 'curve_v2', 'uva', 'buyback', 'other')
    cases = []
    for _ in range(count):
        side = rng.choice(('buy', 'sell'))
        cashback = rng.random() < 0.8
        amount = rng.choice((rng.randrange(10**8, 10**10), rng.randrange(10**8, 10**13)))
        uva = rng.choice((('missing',), ('funded', rng.randrange(1, 2 * UVA_RENT)),
                          ('valid', UVA_RENT + rng.randrange(0, 10**9), rng.randrange(0, 10**12), rng.random() < 0.5),
                          ('valid', UVA_RENT, U64 - rng.randrange(0, 10**7), True), ('foreign',), ('baddisc',)))
        changes = dict(cashback=cashback, uva=uva, tiers=((0, rng.randrange(0, 300), rng.choice((0, rng.randrange(1, 500)))),),
                       creator=rng.random() < 0.9, vault=rng.choice((0, 1, VAULT_RENT, 10**9)),
                       buyback=rng.choice((0, rng.randrange(0, 10_001))))
        if rng.random() < 0.25:
            changes['slots'] = tuple(rng.choice(slot_names) for _ in range(3))
        cases.append(case(side, amount, U64 if side == 'buy' else 0, **changes))
    return cases


class LegacyCashbackCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'legacy-cashback-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def check(self, item, answer):
        captured = run_captured(item)
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        rent, uva_credit, vault_credit, top_up, earned, ev_cbps, ev_cfee, ev_kbps, ev_kfee = answer.split(',')[1:]
        rent, uva_credit, vault_credit, top_up = int(rent), int(uva_credit), int(vault_credit), int(top_up)
        sol, creator_fee, _ = creator_quote(item)
        trade = captured['trade']
        self.assertEqual(trade['sol_amount'], sol)
        self.assertEqual((trade['creator_bps'], trade['creator_fee'], trade['cashback_bps'], trade['cashback']),
                         (int(ev_cbps), int(ev_cfee), int(ev_kbps), int(ev_kfee)))
        paid = trade['fee'] + creator_fee + rent + top_up + TX_FEE
        delta = captured['delta']
        self.assertEqual(delta['user'], -sol - paid if item['side'] == 'buy' else sol - paid)
        self.assertEqual(delta['curve'], sol if item['side'] == 'buy' else -sol)
        self.assertEqual(delta['recipient'] + delta['buyback'], trade['fee'])
        self.assertEqual((delta['uva'], delta['vault']), (uva_credit, vault_credit))
        if earned == '-':  # route leaves the accumulator untouched
            self.assertEqual(captured['uva'], uva_summary(uva_account(item['uva'])))
        else:
            touched = item['side'] == 'buy' or int(ev_kfee) > 0
            user_set = touched or item['uva'][0] != 'valid' or item['uva'][3]
            self.assertEqual(captured['uva'], (str(PUMP), 137, True, user_set, int(earned)))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.check(item, answer)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'error:3002', 'error:3007', 'error:6024', 'error:6057', 'error:6062', 'error:6072', 'error:6073',
            'error:6074',
        })


if __name__ == '__main__':
    unittest.main()
