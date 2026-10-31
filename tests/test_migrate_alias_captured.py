"""Captured-program checks for `migrate` and `migrate_v2` with one key in two slots.

`Global.withdraw_authority` is pinned by no seed and the boost keys are checked
only by pump_amm, so these are the slots that can repeat a key of the call. Every
case runs `evidence/original/pump/deployed.so` with
`evidence/original/pump_amm/deployed.so` and the captured SPL Token, Token-2022
and Associated Token programs on LiteSVM. The same inputs go to
`programs/pump/recovered/migrate_alias_host.rs`, and the error, the lamports of
the key and of `user` must agree. A passing case also has to leave the pool, the
curve and the token balances of the plain run with the same fee. This shows
matching behavior on these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
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
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    AMM_ELF: '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/migrate_alias_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
AMM_IDL = json.loads((ROOT / 'programs/pump/idls/pump_amm.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
PUMP_AMM = Pubkey.from_string(AMM_IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
RENT = Pubkey.from_string('SysvarRent111111111111111111111111111111111')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()
COMMANDS = {i['name']: i for i in IDL['instructions'] if i['name'] in ('migrate', 'migrate_v2')}
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
CONFIG_DISC = bytes(next(a['discriminator'] for a in AMM_IDL['accounts'] if a['name'] == 'GlobalConfig'))
POOL_DISC = bytes(next(a['discriminator'] for a in AMM_IDL['accounts'] if a['name'] == 'Pool'))

USER = Keypair.from_seed(bytes([223]) * 32)
MINT = Pubkey.from_bytes(bytes([73]) * 32)
QUOTE = Pubkey.from_bytes(bytes([74]) * 32)
CREATOR = Pubkey.from_bytes(bytes([60]) * 32)
WITHDRAW = Pubkey.from_bytes(bytes([61]) * 32)
TS = 1_800_000_000
TX_FEE = 5000
TOKEN_RENT = 2_039_280


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA)


GLOBAL = pda([b'global'])
AMM_CONFIG = pda([b'global_config'], PUMP_AMM)


def names(item):
    token = TOKEN22 if item['t22'] else TOKEN
    base = WSOL if item['base'] == 'wsol' else MINT
    quote, program = {'sol': (WSOL, TOKEN), 'wsol': (WSOL, TOKEN), 'spl': (QUOTE, TOKEN), 't22': (QUOTE, TOKEN22), 'self': (base, token)}[item['quote']]
    curve = pda([b'bonding-curve', bytes(base)])
    authority = pda([b'pool-authority', bytes(base)])
    pool = pda([b'pool', struct.pack('<H', 0), bytes(authority), bytes(base), bytes(quote)], PUMP_AMM)
    lp_mint = pda([b'pool_lp_mint', bytes(pool)], PUMP_AMM)
    boost_authority = pda([b'boost_vault', bytes(pool)], PUMP_AMM)
    return {
        'global': GLOBAL, 'withdraw_authority': WITHDRAW, 'base_mint': base, 'quote_mint': quote,
        'bonding_curve': curve, 'associated_base_bonding_curve': ata(curve, base, token),
        'associated_quote_bonding_curve': ata(curve, quote, program), 'user': USER.pubkey(), 'system_program': SYSTEM,
        'pump_amm': PUMP_AMM, 'pool': pool, 'pool_authority': authority,
        'pool_authority_mint_account': ata(authority, base, token),
        'pool_authority_quote_account': ata(authority, quote, program), 'amm_global_config': AMM_CONFIG,
        'lp_mint': lp_mint, 'user_pool_token_account': ata(authority, lp_mint, TOKEN22),
        'pool_base_token_account': ata(pool, base, token), 'pool_quote_token_account': ata(pool, quote, program),
        'base_token_program': token, 'quote_token_program': program, 'token_2022_program': TOKEN22,
        'associated_token_program': ATA, 'pump_amm_event_authority': pda([b'__event_authority'], PUMP_AMM),
        'rent': RENT, 'event_authority': pda([b'__event_authority']), 'program': PUMP,
        'boost_authority': boost_authority, 'boost_vault': ata(boost_authority, quote, program),
        'mint': base, 'associated_bonding_curve': ata(curve, base, token), 'token_program': TOKEN,
        'pool_authority_wsol_account': ata(authority, quote, program), 'wsol_mint': WSOL,
    }


def mint_data(decimals=6, supply=10**18):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def token_data(mint, owner, amount, native=None):
    option = struct.pack('<IQ', 1, native) if native is not None else struct.pack('<IQ', 0, 0)
    return struct.pack('<32s32sQI32sB', bytes(mint), bytes(owner), amount, 0, bytes(32), 1) + option + struct.pack('<QI32s', 0, 0, bytes(32))


def global_data(fee, withdraw):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<QQQQQ', data, 73, 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**15, 95)
    data[113:145] = bytes(withdraw)
    data[145] = 1
    struct.pack_into('<QQ', data, 146, fee, 30)
    data[450] = 1
    struct.pack_into('<Q', data, 1005, 4_000_000_000)
    return bytes(data)


def curve_data(item, keys):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 279_900_000_000_000, 115_005_359_056, 0, item['rqr'], 10**15)
    data[48] = 1
    data[49:81] = bytes(CREATOR)
    if item['quote'] != 'sol':
        data[83:115] = bytes(keys['quote_mint'])
    return bytes(data)


def config_data(item):
    data = bytearray(1200)
    data[:8] = CONFIG_DISC
    struct.pack_into('<QQB', data, 40, 25, 5, 0)
    data[939] = item['boost']
    return bytes(data)


DEFAULTS = dict(command='migrate', base='mint', quote='sol', t22=0, tokens=206_900_000_000_000, rqr=85_005_359_056, fee=15_000_001,
                role='wallet', start=1_000_000, boost=0, remaining=0, b0='boost_authority', b1='boost_vault', slack=10_000_000, lamports=10**15)
FIXED_ROLES = ('user', 'bonding_curve', 'global', 'base_mint', 'quote_mint', 'associated_base_bonding_curve', 'associated_quote_bonding_curve',
               'pool_authority', 'pool', 'lp_mint', 'pool_authority_mint_account', 'pool_authority_quote_account', 'user_pool_token_account',
               'pool_base_token_account', 'pool_quote_token_account', 'amm_global_config', 'program', 'pump_amm', 'event_authority',
               'pump_amm_event_authority', 'boost_authority', 'boost_vault', 'system_program', 'token_program', 'token_2022_program',
               'associated_token_program', 'rent')


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    return dict(DEFAULTS, **changes)


class Bench:
    """One VM for all cases: the programs stay, each key is cleared after a run."""

    def __init__(self):
        self.vm = LiteSVM().with_transaction_history(0)
        programdata = pda([bytes(PUMP)], UPGRADEABLE)
        self.vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                                 UPGRADEABLE, False))
        self.vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
        self.vm.add_program_from_file(PUMP_AMM, AMM_ELF)
        self.vm.add_program_from_file(TOKEN22, TOKEN22_ELF)
        self.vm.add_program_from_file(TOKEN, TOKEN_ELF)
        self.vm.add_program_from_file(ATA, ATA_ELF)
        self.vm.set_clock(Clock(1000, 0, 0, 0, TS))
        self.fixed = {SYSTEM, TOKEN, TOKEN22, ATA, PUMP, PUMP_AMM, RENT}
        self.stale = set()

    def run(self, item):
        vm = self.vm
        for key in self.stale - self.fixed:
            vm.set_account(key, Account(0, b'', SYSTEM))
        vm.expire_blockhash()
        keys = names(item)
        native = item['quote'] == 'sol'
        real_wsol = item['quote'] in ('sol', 'wsol')
        token, quote_key, program = keys['base_token_program'], keys['quote_mint'], keys['quote_token_program']
        base_key, curve, authority = keys['base_mint'], keys['bonding_curve'], keys['pool_authority']
        withdraw = WITHDRAW if item['role'] == 'wallet' else keys[item['role']]
        keys['withdraw_authority'] = withdraw
        wrapped = lambda: TOKEN_RENT if real_wsol else None
        quote_lamports = lambda amount: TOKEN_RENT + amount if real_wsol else 3_000_000
        state = {}
        if withdraw not in self.fixed:
            state[withdraw] = (item['start'], SYSTEM, b'')
        state.update({GLOBAL: (10**9, PUMP, global_data(item['fee'], withdraw)), USER.pubkey(): (item['lamports'], SYSTEM, b''),
                      base_key: (10**7, token, mint_data(9 if item['base'] == 'wsol' else 6, 0 if item['base'] == 'wsol' else 10**18)),
                      curve: ((item['rqr'] if native else 0) + item['slack'], PUMP, curve_data(item, keys)),
                      keys['associated_base_bonding_curve']: (TOKEN_RENT, token, token_data(base_key, curve, item['tokens'])),
                      AMM_CONFIG: (10**7, PUMP_AMM, config_data(item))})
        if quote_key != base_key:
            state[quote_key] = (10**7, program, mint_data(9 if real_wsol else 6, 0 if real_wsol else 10**18))
        if not native:
            held = item['rqr']
            target = keys['associated_quote_bonding_curve']
            if target == keys['associated_base_bonding_curve']:
                held += item['tokens']
            state[target] = (quote_lamports(held), program, token_data(quote_key, curve, held, wrapped()))
        for key, (lamports, owner, data) in state.items():
            vm.set_account(key, Account(lamports, data, owner))
        watched = set(keys.values()) | set(state) | {withdraw}
        self.stale = set(watched)
        spec = COMMANDS[item['command']]
        metas = [AccountMeta(keys[a['name']], a.get('signer', False), a.get('writable', False)) for a in spec['accounts']]
        metas += [AccountMeta(keys[k], False, True) for k in (item['b0'], item['b1'])[:item['remaining']]]
        ix = Instruction(PUMP, bytes(spec['discriminator']), metas)
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), ix], USER.pubkey(), [USER],
                                               vm.latest_blockhash())
        lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
        before = {key: lamports(key) for key in watched}
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            return {'error': int(code.group(1)) if code else text}
        amount = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0] if vm.get_account(key) and len(vm.get_account(key).data) >= 72 else None
        slots = {name: keys[name] for name in FIXED_ROLES}
        slots['withdraw'] = withdraw
        return {'error': None, 'delta': {name: lamports(key) - before[key] for name, key in slots.items() if key in before},
                'tokens': {name: amount(key) for name, key in slots.items()},
                'pool': bytes(vm.get_account(keys['pool']).data), 'curve': bytes(vm.get_account(curve).data)}


ROUTES = (dict(), dict(command='migrate_v2'), dict(command='migrate_v2', quote='spl'), dict(command='migrate_v2', quote='t22'))
SECOND = {'user': 'user', 'bonding_curve': 'curve', 'pool_authority': 'authority', 'pool': 'pool', 'lp_mint': 'lp_mint',
          'pool_base_token_account': 'pool_base', 'pool_quote_token_account': 'pool_quote', 'pool_authority_mint_account': 'closed',
          'pool_authority_quote_account': 'closed', 'user_pool_token_account': 'closed_lp', 'program': 'pump', 'pump_amm': 'program',
          'system_program': 'program', 'token_program': 'program', 'token_2022_program': 'program', 'associated_token_program': 'program',
          'wallet': 'wallet'}


def vault_kind(item):
    role = item['b1']
    token = item['quote'] in ('spl', 't22')
    if role == 'boost_vault':
        return 'right'
    if role == 'program':
        return 'pump'
    if role in ('base_mint', 'quote_mint', 'lp_mint'):
        return 'mint'
    if role == 'associated_quote_bonding_curve':
        return 'other_authority' if token else 'empty'
    if role in ('associated_base_bonding_curve', 'pool_base_token_account', 'pool_authority_mint_account', 'user_pool_token_account'):
        return 'other_mint'
    if role in ('pool_quote_token_account', 'pool_authority_quote_account'):
        return 'other_authority'
    if role in ('user', 'pool_authority', 'event_authority', 'pump_amm_event_authority', 'boost_authority'):
        return 'empty'
    return 'owner'


def host_line(item):
    route = 'native' if item['quote'] == 'sol' else item['quote']
    return ','.join(map(str, [route, SECOND.get(item['role'], 'bystander'), item['fee'], item['start'], item['rqr'],
                              int(item['b0'] == 'boost_authority'), vault_kind(item), int(item['remaining'] == 2)]))


def native_need(item):
    return 14_581_200 if item['quote'] == 'sol' else 6_424_080


def fixed_cases():
    cases = []
    for route in ROUTES:
        for role in ('wallet',) + FIXED_ROLES:
            cases.append(case(role=role, **route))
        need = native_need(case(**route))
        for role in ('pool', 'lp_mint', 'pool_base_token_account', 'pool_quote_token_account', 'pool_authority', 'pool_authority_mint_account'):
            for start in (1, 3_000_000):
                for fee in (need - 1, need):
                    cases.append(case(role=role, start=start, fee=fee, **route))
        # A key that already holds a rent lowers what the fee must cover, by that rent at most.
        for role, rent in (('pool', 2_888_400), ('lp_mint', 1_461_600)):
            for start in (rent - 1, rent):
                for fee in (need - rent - 1, need - rent):
                    cases.append(case(role=role, start=start, fee=fee, **route))
        for fee in (need - 1, need):
            for role in ('wallet', 'user', 'program', 'pump_amm', 'bonding_curve'):
                cases.append(case(role=role, fee=fee, **route))
    for route in ROUTES[:1] + ROUTES[2:]:
        for role in FIXED_ROLES:
            cases.append(case(remaining=2, boost=1, b1=role, **route))
        for role in ('user', 'bonding_curve', 'pool', 'boost_vault'):
            cases.append(case(remaining=2, b0=role, **route))
    return cases


class MigrateAliasCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'migrate-alias-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.bench = Bench()
        cls.twins = {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def twin(self, item):
        key = (item['command'], item['quote'], item['fee'])
        if key not in self.twins:
            self.twins[key] = self.bench.run(case(command=item['command'], quote=item['quote'], fee=item['fee']))
        return self.twins[key]

    def assert_matches(self, item, answer, captured):
        named = {'error:-2': 'MissingAccount', 'error:-3': 'InvalidAccountData', 'error:-5': 'ExternalAccountLamportSpend',
                 'error:-6': 'PrivilegeEscalation'}
        if answer in named:
            self.assertIn(named[answer], str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        fields = answer.split(',')
        self.assertEqual(fields[0], 'ok')
        self.assertEqual(len(fields), 4)
        user_paid, key_change, extra_quote = map(int, fields[1:])
        self.assertEqual(captured['delta']['withdraw'], key_change - (TX_FEE if item['role'] == 'user' else 0))
        if item['role'] != 'user':
            self.assertEqual(captured['delta']['user'], -TX_FEE - user_paid)
        twin = self.twin(item)
        if twin['error'] is None and not item['remaining']:
            # The second slot moves lamports only: the pool and the tokens stay.
            if not extra_quote:
                self.assertEqual(captured['pool'][11:], twin['pool'][11:])
            self.assertEqual(captured['curve'], twin['curve'])
            self.assertEqual(captured['tokens']['pool_base_token_account'], twin['tokens']['pool_base_token_account'])
            self.assertEqual(captured['tokens']['pool_quote_token_account'], twin['tokens']['pool_quote_token_account'] + extra_quote)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, self.bench.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_prefunded_lp_mint_at_rent_boundary(self):
        # A start just above LP rent must not cover even one extra lamport.
        cases = []
        for route in ROUTES:
            need = native_need(case(**route))
            for fee in (need - 1_461_600 - 1, need - 1_461_600):
                cases.append(case(role='lp_mint', start=1_461_601, fee=fee, **route))
        self.run_cases(cases)

    def test_checker_rejects_changed_run(self):
        # Negative control: a passing run must fail once a lamport or the pool moves.
        item = case(role='pool_base_token_account', command='migrate_v2', quote='spl')
        answer = self.host_answers([item])[0]
        captured = self.bench.run(item)
        self.assert_matches(item, answer, captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(item, answer.replace('ok,', 'unknown,', 1), captured)
        delta = dict(captured['delta'], withdraw=captured['delta']['withdraw'] + 1)
        other = dict(captured['delta'], user=captured['delta']['user'] + 1)
        for changed in (dict(captured, delta=delta), dict(captured, delta=other), dict(captured, pool=captured['pool'][:-1] + b'\x01')):
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, changed)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'error:-2', 'error:-3', 'error:-5', 'error:-6', 'error:1', 'error:2000', 'error:2014', 'error:2015', 'error:3007'})


if __name__ == '__main__':
    unittest.main()
