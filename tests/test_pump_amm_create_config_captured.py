"""Captured-program checks for PumpSwap `create_config`.

Each case builds the five Borsh arguments (lp bps, protocol bps, eight
protocol-fee recipients, creator bps, fee authority) and the account metas,
runs the instruction on `evidence/original/pump_amm/deployed.so` in LiteSVM,
and feeds the same bytes to `programs/pump-amm/recovered/create_config_host.rs`.
The host is told the signer and writable bits the runtime actually presents
(the fee payer is a writable signer even when the instruction meta says
otherwise), whether each address matches, and the preexisting config
account. The error (custom code, and for 6000 the fee field named in the
Anchor log), the created config bytes and lamports, the admin's lamports
after the rent move, the `CreateConfigEvent` and the same bytes in the
`emit_cpi!` self-call must agree. Failed transactions roll the accounts
back. This is matching behaviour on these inputs only, not a byte-identity
claim.

The fixed admin `8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8` has no keypair
here, so the transaction is sent with signature checks off. A separate fee
payer funds the transaction. That is how the signer bit is supplied, not a
claim that an unsigned admin passes a runtime that checks signatures.
"""
from pathlib import Path
import base64
import hashlib
from functools import cache
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
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/create_config_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.default()
FIXED = Pubkey.from_string('8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8')
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:CreateConfigEvent').digest()[:8]
IX = hashlib.sha256(b'global:create_config').digest()[:8]
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([251]) * 32)
OTHER = Keypair.from_seed(bytes([252]) * 32).pubkey()
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
AUTHORITY = Pubkey.from_bytes(bytes([0x63]) * 32)
NOW = 1_700_000_123
RENT = LiteSVM().minimum_balance_for_rent_exemption(949)
FEE_PER_SIGNATURE = 5_000
RICH = 10**12
# The three 6000 sites, as logged by the captured program.
FEE_SITE = {
    'lp': 'programs/pump-amm/src/state/global_config.rs:220',
    'protocol': 'programs/pump-amm/src/state/global_config.rs:230',
    'creator': 'programs/pump-amm/src/state/global_config.rs:243',
}
RECIPIENT_SITE = {
    6011: 'programs/pump-amm/src/state/global_config.rs:256',
    6012: 'programs/pump-amm/src/state/global_config.rs:263',
}
SORTED = [Pubkey.from_bytes(bytes([i + 1]) * 32) for i in range(8)]
PREFIXED = []
for _i in range(8):
    raw = bytearray(b'\x11' * 32)
    raw[31] = _i + 1
    PREFIXED.append(Pubkey.from_bytes(bytes(raw)))
ACCOUNTS = ('admin', 'global_config', 'system_program', 'event_authority', 'program')


def with_at(keys, index, key):
    out = list(keys)
    out[index] = key
    return out


def args_bytes(c):
    if 'args' in c:
        return bytes.fromhex(c['args'])
    recipients = c.get('recipients', SORTED)
    authority = c.get('authority', AUTHORITY)
    return (struct.pack('<QQ', c.get('lp', 20), c.get('proto', 5))
            + b''.join(bytes(key) for key in recipients)
            + struct.pack('<Q', c.get('creator', 5)) + bytes(authority))


def setup(c):
    admin = c.get('admin', FIXED)
    fee_payer = c.get('fee_payer', PAYER.pubkey())
    config_key = c.get('config_key', GLOBAL_CONFIG)
    system_key = c.get('system_key', SYSTEM)
    event_key = c.get('event_key', EVENT_AUTHORITY)
    program_key = c.get('program_key', AMM)
    metas = [
        AccountMeta(admin, not c.get('unsigned'), not c.get('admin_readonly')),
        AccountMeta(config_key, False, not c.get('config_readonly')),
        AccountMeta(system_key, c.get('system_signer', False), c.get('system_writable', False)),
        AccountMeta(event_key, c.get('event_signer', False), c.get('event_writable', False)),
        AccountMeta(program_key, c.get('program_signer', False), c.get('program_writable', False)),
    ]
    count = c.get('count', len(metas))
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = IX + args_bytes(c) + bytes.fromhex(c.get('trailing', ''))
    accounts = {}
    if 'admin_lamports' in c or admin != fee_payer:
        accounts[admin] = Account(c.get('admin_lamports', RICH), b'', SYSTEM)
    config = c.get('config')
    if config is not None:
        owner = SYSTEM if config.get('system', True) else config.get('owner', PUMP)
        accounts[config_key] = Account(config['lamports'], bytes(config.get('data_len', 0)), owner)
    if program_key == STRAY:
        accounts.setdefault(STRAY, Account(10**9, b'', SYSTEM))
    return {
        'admin': admin, 'fee_payer': fee_payer, 'config_key': config_key, 'metas': metas,
        'data': data, 'accounts': accounts, 'now': c.get('now', NOW),
    }


def presented(meta, fee_payer):
    """Signer and writable bits the program sees. The fee payer is both."""
    if meta is None:
        return False, False
    is_payer = meta.pubkey == fee_payer
    return meta.is_signer or is_payer, meta.is_writable or is_payer


def host_line(c):
    built = setup(c)
    metas = built['metas']
    admin_meta = metas[0] if metas else None
    config_meta = metas[1] if len(metas) > 1 else None
    signer, writable = presented(admin_meta, built['fee_payer'])
    config = built['accounts'].get(built['config_key'])
    flags = [
        signer,
        writable,
        bool(config_meta and config_meta.is_writable),
        bool(config_meta and config_meta.pubkey == GLOBAL_CONFIG),
        len(metas) > 2 and metas[2].pubkey == SYSTEM,
        len(metas) > 3 and metas[3].pubkey == EVENT_AUTHORITY,
        len(metas) > 4 and metas[4].pubkey == AMM,
    ]
    admin = admin_meta.pubkey if admin_meta else FIXED
    if config is None:
        lamports, data_len, system_owned = 0, 0, 1
    else:
        lamports, data_len = config.lamports, len(config.data)
        system_owned = 1 if config.owner == SYSTEM else 0
    admin_account = built['accounts'].get(admin)
    admin_lamports = RICH if admin_account is None else admin_account.lamports
    payload = built['data'][8:]
    return ','.join([
        str(len(metas)), ''.join('1' if flag else '0' for flag in flags), payload.hex(),
        bytes(admin).hex(), str(built['now']), str(lamports), str(data_len), str(system_owned),
        str(admin_lamports), str(RENT),
    ])


def lamports_of(account):
    return 0 if account is None else account.lamports


def read_captured_image(path):
    image = path.read_bytes()
    if hashlib.sha256(image).hexdigest() != AMM_SHA256:
        raise ValueError('captured AMM hash mismatch')
    return image


@cache
def captured_image():
    return read_captured_image(AMM_ELF)


def run_captured(c):
    built = setup(c)
    vm = LiteSVM().with_sigverify(False).with_transaction_history(0).with_log_bytes_limit(None)
    vm.add_program(AMM, captured_image())
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch, built['now']))
    vm.airdrop(built['fee_payer'], RICH)
    for key, account in built['accounts'].items():
        vm.set_account(key, account)
    watched = [built['config_key'], built['admin']]
    before = {key: vm.get_account(key) for key in watched}
    ix = Instruction(AMM, built['data'], built['metas'])
    tx = Transaction.new_unsigned(Message.new_with_blockhash([ix], built['fee_payer'], vm.latest_blockhash()))
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    logs = '\n'.join(meta.logs())
    after = {key: vm.get_account(key) for key in watched}
    cpi = [bytes(inner.instruction().data) for group in meta.inner_instructions() for inner in group]
    out = {
        'events': events, 'cpi': cpi, 'logs': logs, 'before': before, 'after': after,
        'admin': built['admin'], 'config_key': built['config_key'], 'fee_payer': built['fee_payer'],
        'signatures': tx.message.header.num_required_signatures,
    }
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        out['error'] = int(custom.group(1)) if custom else re.search(r'Fieldless\((\w+)\)', text).group(1)
        return out
    out['error'] = None
    return out


def fixed_cases():
    k = lambda **kw: dict(kw)
    cases = []
    # In-range fees, including the inclusive bound of 1000, and a zero authority.
    for lp, proto, creator in ((0, 0, 0), (1, 2, 3), (20, 5, 5), (1000, 0, 1000), (0, 1000, 1),
                               (1000, 1000, 1000), (999, 1000, 0)):
        cases += [k(lp=lp, proto=proto, creator=creator), k(lp=lp, proto=proto, creator=creator, authority=SYSTEM)]
    cases += [k(recipients=PREFIXED), k(recipients=PREFIXED, authority=FIXED),
              k(recipients=PREFIXED, lp=1000, proto=1000, creator=1000),
              k(authority=GLOBAL_CONFIG), k(authority=STRAY), k(trailing='ffeeddcc'),
              k(count=6), k(count=7), k(now=1_234_567_890),
              k(system_signer=True, system_writable=True, event_signer=True, event_writable=True,
                program_signer=True, program_writable=True)]
    # The message compiler marks the fee payer writable and signing.
    cases.append(k(fee_payer=FIXED, unsigned=True, admin_readonly=True, admin_lamports=RICH))
    # A zero-lamport account is created from scratch, data and owner included.
    cases += [k(config={'lamports': 0, 'data_len': 8, 'system': True}),
              k(config={'lamports': 0, 'data_len': 4, 'system': False, 'owner': PUMP})]
    # Top up an empty system account. Excess lamports stay. An exact balance moves nothing.
    cases += [k(config={'lamports': 1, 'data_len': 0}),
              k(config={'lamports': 100, 'data_len': 0}),
              k(config={'lamports': RENT - 1, 'data_len': 0}),
              k(config={'lamports': RENT, 'data_len': 0}),
              k(config={'lamports': RENT + 77, 'data_len': 0}),
              k(config={'lamports': 100, 'data_len': 0}, admin_lamports=RENT - 100),
              k(config={'lamports': RENT, 'data_len': 0}, admin_lamports=0)]
    # Each fee field rejects 1001 and above. The field is named in the log.
    for name, big in (('lp', {'lp': 1001}), ('proto', {'proto': 1001}), ('creator', {'creator': 1001})):
        for value in (1001, 1002, 65_535, 2**32, 2**64 - 1):
            over = dict(big)
            over[name] = value
            cases.append(k(**over))
    # Check order: lp, protocol, recipients (zero then strictly ascending), creator.
    cases += [k(lp=1001, proto=1001), k(lp=1001, recipients=list(reversed(SORTED))),
              k(lp=1001, recipients=with_at(SORTED, 0, SYSTEM)), k(lp=1001, creator=1001),
              k(proto=1001, recipients=list(reversed(SORTED))), k(proto=1001, recipients=with_at(SORTED, 3, SYSTEM)),
              k(proto=1001, creator=1001), k(creator=1001, recipients=list(reversed(SORTED))),
              k(creator=1001, recipients=with_at(SORTED, 7, SYSTEM)),
              k(lp=1001, proto=1001, creator=1001, recipients=[SYSTEM] * 8)]
    cases += [k(recipients=with_at(SORTED, i, SYSTEM)) for i in (0, 3, 7)]
    cases += [k(recipients=[SYSTEM] * 8), k(recipients=SORTED[:7] + [SORTED[6]]),
              k(recipients=list(reversed(SORTED))), k(recipients=list(reversed(PREFIXED)))]
    # Short payloads fail before accounts. Trailing bytes are ignored.
    cases += [k(args=''), k(args='00' * 311), k(args='ff' * 312), k(args=args_bytes({}).hex() + 'aa'),
              k(args='', count=0), k(count=0, lp=1001)]
    # Missing accounts. The signer is checked as soon as admin is present, and the
    # system-program id as soon as that account is present. Seeds wait until all five.
    cases += [k(count=0), k(count=1), k(count=1, unsigned=True), k(count=2), k(count=2, unsigned=True),
              k(count=2, config_key=STRAY), k(count=3), k(count=3, unsigned=True),
              k(count=3, config_key=STRAY), k(count=3, system_key=STRAY),
              k(count=4), k(count=4, unsigned=True), k(count=4, config_key=STRAY),
              k(count=4, system_key=STRAY), k(count=4, system_key=STRAY, config_key=STRAY),
              k(count=5, unsigned=True)]
    # Constraint order once every meta is present.
    cases += [k(system_key=STRAY), k(system_key=AMM), k(system_key=STRAY, config_key=STRAY),
              k(system_key=STRAY, admin=OTHER), k(config_key=STRAY), k(config_key=STRAY, admin=OTHER),
              k(config_key=STRAY, config_readonly=True),
              k(config_key=STRAY, config={'lamports': RENT, 'data_len': 4})]
    # Init. Privilege escalation before the system program; already-in-use before ConstraintMut;
    # ConstraintMut before the admin address; the address before the event seeds.
    cases += [k(config_readonly=True), k(admin_readonly=True),
              k(config_readonly=True, admin_readonly=True),
              k(config_readonly=True, config={'lamports': RENT, 'data_len': 3}),
              k(config_readonly=True, config={'lamports': RENT, 'data_len': 0}),
              k(admin_readonly=True, config={'lamports': RENT, 'data_len': 1}),
              k(admin_readonly=True, config={'lamports': RENT, 'data_len': 0}),
              k(admin_readonly=True, config={'lamports': RENT + 10, 'data_len': 0}),
              k(admin_readonly=True, config={'lamports': 100, 'data_len': 0}),
              k(admin_readonly=True, config={'lamports': RENT, 'data_len': 0}, admin=OTHER),
              k(admin_readonly=True, config={'lamports': RENT, 'data_len': 0}, event_key=STRAY),
              k(admin_lamports=0), k(admin_lamports=1), k(admin_lamports=RENT - 1),
              k(admin_lamports=RENT), k(admin_lamports=RENT + 1),
              k(admin_lamports=50, config={'lamports': 100, 'data_len': 0}),
              k(admin_lamports=RENT - 101, config={'lamports': 100, 'data_len': 0}),
              k(admin_lamports=50, config={'lamports': 100, 'data_len': 4}),
              k(admin=OTHER, admin_lamports=0), k(admin=OTHER, admin_lamports=100),
              k(admin=OTHER), k(admin=OTHER, lp=1001), k(admin=OTHER, event_key=STRAY),
              k(config={'lamports': RENT, 'data_len': 10}),
              k(config={'lamports': 100, 'data_len': 2}),
              k(config={'lamports': RENT, 'data_len': 0, 'system': False, 'owner': PUMP}),
              k(config={'lamports': 100, 'data_len': 0, 'system': False, 'owner': AMM}),
              k(config={'lamports': RENT, 'data_len': 0, 'system': False, 'owner': AMM}, admin=OTHER),
              k(config={'lamports': RENT, 'data_len': 10}, admin_readonly=True),
              k(event_key=STRAY), k(event_key=STRAY, lp=1001), k(event_key=STRAY, program_key=STRAY),
              k(program_key=STRAY), k(program_key=STRAY, lp=1001),
              k(program_key=STRAY, recipients=list(reversed(SORTED))),
              k(config={'lamports': 1, 'data_len': 0}, event_key=STRAY),
              k(config={'lamports': RENT, 'data_len': 10}, event_key=STRAY)]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        c = {}
        roll = rng.random()
        if roll < 0.45:
            c['lp'] = rng.choice([0, 1, 20, 999, 1000, rng.randint(0, 1000)])
            c['proto'] = rng.choice([0, 5, 1000, rng.randint(0, 1000)])
            c['creator'] = rng.choice([0, 5, 1000, rng.randint(0, 1000)])
        elif roll < 0.7:
            field = rng.choice(['lp', 'proto', 'creator'])
            c[field] = rng.choice([1001, 1002, rng.randint(1001, 2**64 - 1)])
        else:
            c['args'] = rng.choice(['', '00' * 311, 'ff' * 7, args_bytes({}).hex()[:20], args_bytes({}).hex()])
        roll = rng.random()
        if roll < 0.5:
            c['recipients'] = list(SORTED) if rng.random() < 0.5 else list(PREFIXED)
        elif roll < 0.75:
            keys = list(SORTED)
            keys[rng.randrange(8)] = rng.choice([SYSTEM, keys[rng.randrange(8)], STRAY])
            if rng.random() < 0.5:
                rng.shuffle(keys)
            c['recipients'] = keys
        else:
            c['recipients'] = list(reversed(SORTED))
        if rng.random() < 0.15:
            c['authority'] = rng.choice([SYSTEM, FIXED, STRAY, AUTHORITY])
        if rng.random() < 0.05:
            c['unsigned'] = True
        if rng.random() < 0.05:
            c['admin_readonly'] = True
        if rng.random() < 0.05:
            c['config_readonly'] = True
        if rng.random() < 0.05:
            c['admin'] = OTHER
        if rng.random() < 0.04:
            c['config_key'] = STRAY
        if rng.random() < 0.04:
            c['system_key'] = STRAY
        if rng.random() < 0.04:
            c['event_key'] = STRAY
        if rng.random() < 0.04:
            c['program_key'] = STRAY
        if rng.random() < 0.05:
            c['count'] = rng.randint(0, 6)
        if rng.random() < 0.12:
            c['config'] = {
                'lamports': rng.choice([0, 1, 100, RENT - 1, RENT, RENT + 50]),
                'data_len': rng.choice([0, 0, 1, 8]),
                'system': rng.random() < 0.7,
            }
        if rng.random() < 0.08:
            c['admin_lamports'] = rng.choice([0, 1, 50, RENT - 1, RENT, RENT + 5, RICH])
        cases.append(c)
    return cases


class PumpAmmCreateConfigCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-config-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(c) + '\n' for c in cases)
        answers = subprocess.run([str(self.host)], input=text, capture_output=True, text=True,
                                 check=True).stdout.splitlines()
        self.assertEqual(len(answers), len(cases))
        return answers

    def assert_matches(self, answer, captured):
        logs = captured['logs']
        before, after = captured['before'], captured['after']
        config_key, admin = captured['config_key'], captured['admin']
        fee = FEE_PER_SIGNATURE * captured['signatures'] if admin == captured['fee_payer'] else 0

        def admin_lamports(side):
            return lamports_of(side[admin])

        if answer.startswith('error:'):
            body = answer[6:]
            code, _, site = body.partition(',')
            if code == 'PrivilegeEscalation':
                self.assertEqual(captured['error'], 'PrivilegeEscalation')
                self.assertIn('Cross-program invocation with unauthorized signer or writable account', logs)
            elif code == '6000':
                self.assertEqual(captured['error'], 6000)
                self.assertIn(FEE_SITE[site], logs)
            elif code == '0':
                self.assertEqual(captured['error'], 0)
                self.assertIn('already in use', logs)
            elif code == '1':
                self.assertEqual(captured['error'], 1)
                self.assertIn('insufficient lamports', logs)
            else:
                if not code.isdigit():
                    self.fail(f'unexpected error class {answer}')
                self.assertEqual(captured['error'], int(code))
            if code == '3005' and site == '':
                self.assertNotIn('caused by account:', logs)
            elif site and code != '6000':
                self.assertIn(f'caused by account: {site}', logs)
            if captured['error'] in RECIPIENT_SITE:
                self.assertIn(RECIPIENT_SITE[captured['error']], logs)
            self.assertEqual(captured['events'], [])
            self.assertFalse(any(item.startswith(EVENT_CPI_TAG) for item in captured['cpi']))
            self.assertEqual(lamports_of(after[config_key]), lamports_of(before[config_key]))
            self.assertEqual(admin_lamports(after), admin_lamports(before) - fee)
            for key in (config_key,):
                if before[key] is None:
                    self.assertIsNone(after[key])
                else:
                    self.assertEqual(bytes(after[key].data), bytes(before[key].data))
                    self.assertEqual(after[key].owner, before[key].owner)
                    self.assertEqual(after[key].executable, before[key].executable)
            return
        if answer.startswith('event-then:'):
            name, event_hex = answer[11:].split(',')
            event = bytes.fromhex(event_hex)
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['events'], [event])
            self.assertFalse(any(item.startswith(EVENT_CPI_TAG) for item in captured['cpi']))
            self.assertTrue(any(item[:4] == b'\x00\x00\x00\x00' or item[:1] == b'\x02' or item[:1] == b'\x08'
                                for item in captured['cpi']))
            self.assertTrue(event.startswith(EVENT_DISC))
            self.assertEqual(lamports_of(after[config_key]), lamports_of(before[config_key]))
            self.assertEqual(admin_lamports(after), admin_lamports(before) - fee)
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config_hex, event_hex, config_lamports, admin_after = answer.split(',')
        event = bytes.fromhex(event_hex)
        self.assertIsNone(captured['error'])
        created = after[config_key]
        self.assertIsNotNone(created)
        self.assertEqual(bytes(created.data), bytes.fromhex(config_hex))
        self.assertEqual(created.lamports, int(config_lamports))
        self.assertEqual(created.owner, AMM)
        self.assertFalse(created.executable)
        self.assertEqual(len(created.data), 949)
        self.assertEqual(admin_lamports(after), int(admin_after) - fee)
        self.assertEqual(captured['events'], [event])
        self.assertEqual(captured['cpi'][-1], EVENT_CPI_TAG + event)
        self.assertTrue(event.startswith(EVENT_DISC))

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c), host=answer[:80]):
                self.assert_matches(answer, run_captured(c))

    def test_rejects_wrong_image_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.so'
            wrong.write_bytes(b'not the captured AMM')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                read_captured_image(wrong)

    def test_admitted_image_is_used_after_source_path_moves(self):
        case = {'lp': 20, 'proto': 5, 'creator': 5}
        expected = run_captured(case)
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'replacement.so'
            wrong.write_bytes(b'wrong ELF')
            with patch(__name__ + '.AMM_ELF', wrong):
                self.assertEqual(run_captured(case), expected)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_extra_account_case_really_supplies_more_metas(self):
        case = {'count': 6, 'lp': 4, 'proto': 5, 'creator': 6}
        self.assertEqual(len(setup(case)['metas']), 6)
        self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_fee_payer_is_presented_as_writable_signer(self):
        case = {'fee_payer': FIXED, 'unsigned': True, 'admin_readonly': True, 'admin_lamports': RICH}
        built = setup(case)
        self.assertFalse(built['metas'][0].is_signer)
        self.assertFalse(built['metas'][0].is_writable)
        self.assertTrue(host_line(case).split(',')[1].startswith('11'))
        self.assert_matches(self.host_answers([case])[0], run_captured(case))

    def test_checker_rejects_tampered_outcomes(self):
        samples = (
            {'lp': 20, 'proto': 5, 'creator': 5},
            {'lp': 1001}, {'proto': 1001}, {'creator': 1001},
            {'recipients': list(reversed(SORTED))},
            {'recipients': with_at(SORTED, 0, SYSTEM)},
            {'program_key': STRAY}, {'args': ''}, {'count': 0}, {'count': 1},
            {'admin': OTHER}, {'admin_readonly': True, 'config': {'lamports': RENT, 'data_len': 0}},
            {'config': {'lamports': RENT, 'data_len': 4}}, {'admin_lamports': 0},
            {'config_readonly': True}, {'config_key': STRAY}, {'system_key': STRAY},
        )
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured)
            if answer.startswith('ok,'):
                _, config, event, config_lamports, admin_after = answer.split(',')
                tampered = ['ok,' + flip(config, at) + ',' + event + f',{config_lamports},{admin_after}'
                            for at in (8, 40, 48, 56, 57, 313, 321, 948)]
                tampered += ['ok,' + config + ',' + flip(event, 8) + f',{config_lamports},{admin_after}',
                             'ok,' + config + ',' + event + f',{int(config_lamports) - 1},{admin_after}',
                             'ok,' + config + ',' + event + f',{config_lamports},{int(admin_after) - 1}',
                             'error:6000,lp', 'error:6005,admin']
            elif answer.startswith('event-then:'):
                name, event = answer[11:].split(',')
                tampered = ['event-then:' + name + ',' + flip(event, 16), 'error:MissingAccount',
                            'ok,' + '00' * 949 + ',' + event + ',0,0']
            elif answer.startswith('error:6000,'):
                field = answer.split(',')[1]
                other = next(name for name in FEE_SITE if name != field)
                tampered = ['error:6000,' + other, 'error:6011', 'error:6012', 'error:1']
            else:
                tampered = [text for text in (
                    'error:102', 'error:3005,admin', 'error:3005', 'error:3010,admin', 'error:3008,system_program',
                    'error:2006,global_config', 'error:2006,event_authority', 'error:PrivilegeEscalation',
                    'error:2000,admin', 'error:0', 'error:1', 'error:6005,admin', 'error:6011') if text != answer]
            for text in tampered:
                with self.subTest(case=repr(c), tampered=text[:70]), self.assertRaises(AssertionError):
                    self.assert_matches(text, captured)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        classes = set()
        for answer in answers:
            if answer.startswith('ok,'):
                classes.add('ok')
            elif answer.startswith('event-then:'):
                classes.add(answer.split(',')[0])
            else:
                classes.add(answer)
        self.assertEqual(classes, {
            'error:102', 'error:3005,admin', 'error:3005', 'error:3005,system_program',
            'error:3005,event_authority', 'error:3005,program', 'error:3010,admin',
            'error:3008,system_program', 'error:2006,global_config', 'error:2006,event_authority',
            'error:PrivilegeEscalation', 'error:2000,admin', 'error:0', 'error:1', 'error:6005,admin',
            'error:6000,lp', 'error:6000,protocol', 'error:6000,creator', 'error:6011', 'error:6012',
            'event-then:MissingAccount', 'ok'})
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)


if __name__ == '__main__':
    unittest.main()
