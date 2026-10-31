"""Captured-program checks for PumpSwap `update_creator_fee_config`.

Each case builds a synthetic `GlobalConfig` (899-, 932- or 941-byte layout, or
something broken) and the two Borsh arguments (`creator_fee_configurable`,
`max_configurable_creator_fee_bps`), runs the instruction on
`evidence/original/pump_amm/deployed.so` in LiteSVM, and feeds the same bytes
to `programs/pump-amm/recovered/update_creator_fee_config_host.rs`. Owners, the
signer and writable flags, and the system / event-authority / program
addresses are worked out here from the metas actually passed.

The error (custom code, and for 2000 and 3005 the account named in the Anchor
log), the committed config bytes, both accounts' lamports, the
`UpdateCreatorFeeConfigEvent` in the log and the same bytes in the `emit_cpi!`
self-call must agree. A short config is topped up to the rent of 949 bytes and
reallocated there; the system transfer's failure modes are part of the
instruction. Failed transactions roll the bytes and the lamports back. This is
matching behaviour on these inputs only, not a byte-identity claim.
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
from solders.pubkey import Pubkey
from solders.rent import Rent
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
AMM_SHA256 = '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7'
HOST_SOURCE = ROOT / 'programs/pump-amm/recovered/update_creator_fee_config_host.rs'

AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
SYSTEM = Pubkey.from_string('11111111111111111111111111111111')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
CONFIG_DISC = hashlib.sha256(b'account:GlobalConfig').digest()[:8]
EVENT_DISC = hashlib.sha256(b'event:UpdateCreatorFeeConfigEvent').digest()[:8]
IX = hashlib.sha256(b'global:update_creator_fee_config').digest()[:8]
# Anchor's EVENT_IX_TAG, the u64 0x1d9acb512ea545e4 in little-endian order.
EVENT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], AMM)[0]
GLOBAL_CONFIG = Pubkey.find_program_address([b'global_config'], AMM)[0]
PAYER = Keypair.from_seed(bytes([181]) * 32)
ADMIN = Keypair.from_seed(bytes([182]) * 32)
OTHER = Keypair.from_seed(bytes([183]) * 32)
STRAY = Pubkey.from_bytes(bytes([77]) * 32)
NOW = 1_700_000_123
LENGTHS = (907, 940, 949)
MAYHEM, CASHBACK, BOOST_ON, CFC, MAX_BPS = 417, 642, 939, 940, 941
V941 = 949
DEFAULT_RENT = (3480, 2)
# The three accounts that share error 3005, plus the two that share 2000, as logged.
SITES = {
    'admin': 'account: admin',
    'global_config': 'account: global_config',
    'system_program': 'account: system_program',
    'event_authority': 'account: event_authority',
    'program': 'account: program',
}


def rent_of(length, spec=None):
    """LiteSVM's rent-exempt minimum. `spec` is `(lamports_per_byte_year, threshold)`."""
    per, threshold = DEFAULT_RENT if spec is None else spec
    return (128 + length) * per * threshold


def transfer_data(amount):
    """System-program `Transfer`: a little-endian instruction index of 2, then the lamports."""
    return struct.pack('<IQ', 2, amount)


def config_bytes(c):
    """A config with every non-bool byte set to a pattern, so a stray write shows."""
    n = c.get('length', 949)
    data = bytearray((i * 41 + 7) % 256 for i in range(max(n, 949)))
    data[:8] = c.get('disc', CONFIG_DISC)
    data[8:40] = bytes(c.get('admin', ADMIN.pubkey()))
    if n > MAYHEM:
        data[MAYHEM] = c.get('mayhem', 0)
    if n > CASHBACK:
        data[CASHBACK] = c.get('cashback', 1)
    if n > BOOST_ON:
        data[BOOST_ON] = c.get('boost', 1)
    if n > CFC:
        data[CFC] = c.get('cfc', 0)
    if n >= V941:
        struct.pack_into('<Q', data, MAX_BPS, c.get('old_max', 0))
    for at, value in c.get('patches', ()):
        data[at:at + len(value)] = value
    return bytes(data[:n])


def args_bytes(c):
    if 'args' in c:
        return bytes.fromhex(c['args'])
    return bytes([c.get('flag', 1)]) + struct.pack('<Q', c.get('maxbps', 500))


def setup(c):
    config_key = c.get('config_key', GLOBAL_CONFIG)
    signer = c.get('signer', ADMIN)
    admin_key = c.get('admin_key', signer.pubkey())
    metas = [AccountMeta(admin_key, not c.get('unsigned'), not c.get('admin_ro')),
             AccountMeta(config_key, False, not c.get('readonly')),
             AccountMeta(c.get('system_key', SYSTEM), False, False),
             AccountMeta(c.get('event_key', EVENT_AUTHORITY), False, False),
             AccountMeta(c.get('program_key', AMM), False, False)]
    count = c.get('count', len(metas))
    if count > len(metas):
        metas.extend(AccountMeta(PAYER.pubkey(), False, False) for _ in range(count - len(metas)))
    metas = metas[:count]
    data = IX + args_bytes(c) + bytes.fromhex(c.get('trailing', ''))
    spec = c.get('rent')
    length = c.get('length', 949)
    config_lamports = c.get('config_lamports', rent_of(length, spec))
    raw = b'' if c.get('empty') else config_bytes(c)
    if c.get('raw') is not None:
        raw = c['raw']
    accounts = {}
    if not c.get('omit_config'):
        accounts[config_key] = Account(config_lamports, raw, c.get('owner', AMM))
    admin_lamports = c.get('admin_lamports', 10**10)
    admin_data = c.get('admin_data', b'')
    admin_owner = c.get('admin_owner', SYSTEM)
    return {
        'config_key': config_key, 'accounts': accounts, 'metas': metas, 'data': data,
        'signer': signer, 'admin_key': admin_key, 'sign': not c.get('unsigned') and admin_key == signer.pubkey(),
        'spec': spec, 'config_lamports': 0 if c.get('omit_config') else config_lamports,
        'admin_lamports': admin_lamports, 'admin_data': admin_data, 'admin_owner': admin_owner,
        'now': c.get('now', NOW),
        'set_stray': config_key != STRAY and (c.get('program_key') == STRAY or c.get('system_key') == STRAY),
    }


def host_line(c):
    built = setup(c)
    metas = built['metas']
    config = built['accounts'].get(built['config_key'])
    flags = [
        len(metas) > 0 and metas[0].is_signer,
        config is not None,
        config is not None and config.owner == AMM,
        len(metas) > 0 and metas[0].is_writable,
        len(metas) > 1 and metas[1].is_writable,
        len(metas) > 2 and metas[2].pubkey == SYSTEM,
        len(metas) > 3 and metas[3].pubkey == EVENT_AUTHORITY,
        len(metas) > 4 and metas[4].pubkey == AMM,
        built['admin_owner'] == SYSTEM and built['admin_lamports'] > 0,
    ]
    signer = metas[0].pubkey if metas else ADMIN.pubkey()
    return ','.join([
        str(len(metas)), ''.join('1' if flag else '0' for flag in flags), built['data'][8:].hex(),
        bytes(config.data).hex() if config is not None else '', bytes(signer).hex(), str(built['now']),
        str(built['config_lamports']), str(built['admin_lamports'] if built['admin_lamports'] > 0 else 0),
        str(rent_of(V941, built['spec'])), str(len(built['admin_data'])),
    ])


def read_captured_image(path):
    image = path.read_bytes()
    if hashlib.sha256(image).hexdigest() != AMM_SHA256:
        raise ValueError('captured AMM hash mismatch')
    return image


@cache
def captured_image():
    return read_captured_image(AMM_ELF)


def lamports_of(account):
    return 0 if account is None else account.lamports


def run_captured(c):
    built = setup(c)
    vm = LiteSVM().with_transaction_history(0).with_log_bytes_limit(None)
    vm.add_program(AMM, captured_image())
    if built['spec'] is not None:
        per, threshold = built['spec']
        vm.set_rent(Rent(per, float(threshold), 50))
    clock = vm.get_clock()
    vm.set_clock(Clock(clock.slot, clock.epoch_start_timestamp, clock.epoch, clock.leader_schedule_epoch, built['now']))
    vm.airdrop(PAYER.pubkey(), 10**12)
    if built['admin_lamports'] > 0 or built['admin_data']:
        vm.set_account(built['admin_key'], Account(built['admin_lamports'], built['admin_data'], built['admin_owner']))
    for key, account in built['accounts'].items():
        if key != built['admin_key']:
            vm.set_account(key, account)
    if built['set_stray']:
        vm.set_account(STRAY, Account(10**9, b'', SYSTEM))
    before_cfg = vm.get_account(built['config_key'])
    before_admin = vm.get_account(built['admin_key'])
    signers = [PAYER]
    if any(m.is_signer and m.pubkey == built['signer'].pubkey() for m in built['metas']):
        signers.append(built['signer'])
    tx = Transaction.new_signed_with_payer(
        [Instruction(AMM, built['data'], built['metas'])], PAYER.pubkey(), signers, vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    events = [base64.b64decode(line[len('Program data: '):]) for line in meta.logs() if line.startswith('Program data: ')]
    logs = '\n'.join(meta.logs())
    after_cfg = vm.get_account(built['config_key'])
    after_admin = vm.get_account(built['admin_key'])
    cpi = [bytes(ix.instruction().data) for group in meta.inner_instructions() for ix in group]

    def same(before, after):
        if before is None and after is None:
            return True
        if before is None or after is None:
            return False
        return ((after.lamports, after.owner, after.executable, after.rent_epoch, bytes(after.data))
                == (before.lamports, before.owner, before.executable, before.rent_epoch, bytes(before.data)))

    out = {
        'events': events, 'cpi': cpi, 'logs': logs,
        'rolled_back': same(before_cfg, after_cfg) and same(before_admin, after_admin),
        'cfg_lamports': lamports_of(after_cfg), 'admin_lamports': lamports_of(after_admin),
        'cfg_len': 0 if after_cfg is None else len(after_cfg.data),
        'cfg_owner': None if after_cfg is None else after_cfg.owner,
    }
    if failed:
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        field = re.search(r'Fieldless\((\w+)\)', text)
        out['error'] = int(custom.group(1)) if custom else field.group(1)
        return out
    out.update(error=None, config=bytes(after_cfg.data))
    return out


def k(**kwargs):
    return dict(kwargs)


def fixed_cases():
    cases = []
    # Both flags, the whole u64 range, and ignored trailing bytes.
    for flag in (0, 1):
        for maxbps in (0, 1, 500, 1000, 1001, 10_000, 2**32, 2**64 - 1):
            cases.append(k(flag=flag, maxbps=maxbps))
    cases += [k(trailing='ffeeddcc'), k(trailing='aa' * 16), k(count=6), k(count=7),
              k(flag=0, maxbps=0, cfc=0, old_max=0), k(now=1), k(now=2**31)]
    # Layouts. Under 949 the account grows, missing fields become zero, and the
    # two creator fields are written. At 949 and above only those two fields change.
    for n in (907, 908, 939, 940, 941, 948, 949, 950, 1024, 1100):
        cases += [k(length=n, flag=flag, maxbps=maxbps)
                  for flag, maxbps in ((1, 777), (0, 0), (1, 2**64 - 1))]
    cases += [k(length=n, config_lamports=rent_of(V941)) for n in (907, 940, 948)]
    cases += [k(length=907, config_lamports=rent_of(V941) - 1),
              k(length=907, config_lamports=1, admin_lamports=rent_of(V941)),
              k(length=949, config_lamports=10**9), k(length=949, config_lamports=1000),
              k(length=1024, patches=[(949, b'\xab' * 75)]),
              k(config_key=STRAY, flag=0, maxbps=9),
              k(admin_lamports=rent_of(V941) - rent_of(907), length=907)]
    # The rent sysvar, not a hardcoded minimum, sets the top-up.
    cases.append(k(length=907, rent=(1, 100), flag=1, maxbps=4))
    # Bytes already in the legacy tail are replaced by the zero default, not kept.
    cases += [k(length=908, patches=[(907, b'\xff')]), k(length=941, patches=[(940, b'\x02')]),
              k(length=948, cfc=2, flag=0, maxbps=42)]
    # Arguments are decoded first, including a bool that is not 0 or 1.
    cases += [k(args=''), k(args='01'), k(args='00' * 8), k(args='01' + '00' * 7),
              k(args='02' + '00' * 8), k(args='ff' + '00' * 8), k(args='', count=0),
              k(args='02' + '00' * 8, unsigned=True), k(args='02' + '00' * 8, count=0)]
    # Account presence, one missing meta at a time.
    cases += [k(count=n) for n in range(5)]
    cases += [k(count=0, args=''), k(count=4, admin_ro=True), k(count=2, owner=SYSTEM),
              k(count=3, length=100), k(count=1, unsigned=True)]
    # Signer, then init, owner, and the layout floor. Mut is after the load.
    cases += [k(unsigned=True), k(unsigned=True, admin_ro=True), k(unsigned=True, owner=SYSTEM),
              k(unsigned=True, omit_config=True), k(omit_config=True), k(omit_config=True, admin_ro=True),
              k(owner=SYSTEM), k(owner=PUMP), k(owner=SYSTEM, disc=b'\x00' * 8),
              k(empty=True), k(raw=b'', length=0), k(raw=CONFIG_DISC, length=8)]
    for n in (0, 7, 8, 100, 906, 939):
        cases.append(k(length=n))
    cases += [k(disc=b'\x00' * 8), k(patches=[(0, b'\x00')]), k(patches=[(7, b'\x00')])]
    # Bools are checked only in the fields the layout has.
    for at, versions in ((MAYHEM, (907, 940, 949)), (CASHBACK, (907, 940, 949)),
                         (BOOST_ON, (940, 949)), (CFC, (949,))):
        for n in versions:
            cases += [k(length=n, patches=[(at, bytes([v]))]) for v in (2, 255)]
    cases += [k(length=939, patches=[(BOOST_ON, b'\x02')]), k(length=948, patches=[(CFC, b'\x07')]),
              k(patches=[(MAYHEM, b'\x02')], unsigned=True),
              k(patches=[(MAYHEM, b'\x02')], owner=SYSTEM),
              k(patches=[(MAYHEM, b'\x02')], admin_ro=True),
              k(patches=[(CASHBACK, b'\x02')], readonly=True),
              k(patches=[(CASHBACK, b'\x02')], signer=OTHER),
              k(patches=[(CFC, b'\x02')], system_key=TOKEN),
              k(patches=[(BOOST_ON, b'\x02')], event_key=STRAY),
              k(length=906, admin_ro=True), k(length=906, system_key=TOKEN)]
    # Constraint order: system id, then mut (admin, then config), has_one, seeds.
    cases += [k(admin_ro=True), k(readonly=True), k(admin_ro=True, readonly=True)]
    cases += [k(system_key=key) for key in (TOKEN, AMM, STRAY)]
    cases += [k(admin_ro=True, system_key=TOKEN), k(readonly=True, system_key=TOKEN),
              k(signer=OTHER, system_key=TOKEN), k(system_key=TOKEN, event_key=STRAY),
              k(event_key=STRAY), k(event_key=AMM), k(event_key=GLOBAL_CONFIG),
              k(admin_ro=True, event_key=STRAY), k(readonly=True, event_key=STRAY),
              k(signer=OTHER, event_key=STRAY), k(signer=OTHER), k(admin=OTHER.pubkey()),
              k(admin=SYSTEM), k(admin_ro=True, signer=OTHER), k(readonly=True, signer=OTHER),
              k(length=907, event_key=STRAY), k(length=907, admin_ro=True)]
    # The program account is checked only by emit_cpi, after the top-up and the log.
    cases += [k(program_key=STRAY), k(program_key=EVENT_AUTHORITY), k(program_key=SYSTEM),
              k(program_key=STRAY, length=907), k(program_key=STRAY, length=907, config_lamports=rent_of(V941)),
              k(program_key=STRAY, length=949), k(program_key=STRAY, flag=0, maxbps=0)]
    # Rent top-up failures. Data on `from` is rejected before the balance, and the
    # balance before the owner. No top-up means none of these run.
    short = rent_of(V941) - rent_of(907)
    cases += [k(length=907, admin_lamports=0), k(length=907, admin_lamports=1000),
              k(length=907, admin_lamports=short - 1),
              k(length=907, admin_data=b'\x11', admin_lamports=10**9),
              k(length=907, admin_data=b'\x11', admin_lamports=1),
              k(length=907, admin_owner=AMM, admin_data=b'\x02', admin_lamports=10**9),
              k(length=907, admin_owner=AMM, admin_lamports=1),
              k(length=907, admin_owner=AMM, admin_lamports=10**9),
              k(length=907, admin_owner=PUMP, admin_lamports=10**9),
              k(length=949, admin_data=b'\x11' * 40, admin_lamports=10**9),
              k(length=949, admin_owner=AMM, admin_lamports=10**9),
              k(length=907, config_lamports=rent_of(V941), admin_data=b'\x01', admin_lamports=10**9)]
    return cases


def random_cases():
    rng = random.Random(20261030)
    cases = []
    for _ in range(200):
        c = {'mayhem': rng.randint(0, 1), 'cashback': rng.randint(0, 1), 'boost': rng.randint(0, 1),
             'cfc': rng.randint(0, 1), 'flag': rng.randint(0, 1),
             'maxbps': rng.choice([0, 1, 500, 1000, 1001, 2**64 - 1, rng.randint(0, 2**64 - 1)])}
        if rng.random() < 0.08:
            c['args'] = rng.choice(['', '01', '00' * 8, '02' + '00' * 8, 'ff' + 'ab' * 4])
        if rng.random() < 0.35:
            c['length'] = rng.choice([906, 907, 908, 939, 940, 948, 949, 950, 960, 1024])
        if rng.random() < 0.08:
            c['patches'] = [(rng.choice([MAYHEM, CASHBACK, BOOST_ON, CFC]), bytes([rng.choice([2, 255])]))]
        if rng.random() < 0.05:
            c['config_lamports'] = rng.choice([1, rent_of(907), rent_of(V941) - 1, rent_of(V941), 10**9])
        roll = rng.random()
        if roll < 0.04:
            c['unsigned'] = True
        elif roll < 0.08:
            c['admin_ro'] = True
        elif roll < 0.11:
            c['readonly'] = True
        elif roll < 0.14:
            c['signer'] = OTHER
        elif roll < 0.17:
            c['owner'] = rng.choice([SYSTEM, PUMP])
        elif roll < 0.2:
            c['system_key'] = rng.choice([TOKEN, STRAY, AMM])
        elif roll < 0.23:
            c['event_key'] = STRAY
        elif roll < 0.26:
            c['program_key'] = STRAY
        elif roll < 0.29:
            c['count'] = rng.randint(0, 4)
        if rng.random() < 0.04:
            c['length'] = c.get('length', 907)
            c['admin_lamports'] = rng.choice([0, 1, 1000])
        if rng.random() < 0.03:
            c['admin_data'] = b'\x05' * rng.randint(1, 8)
            c['length'] = 907
        if rng.random() < 0.03:
            c['admin_owner'] = AMM
            c['length'] = 907
            c['admin_lamports'] = 10**9
        if rng.random() < 0.03:
            c['omit_config'] = True
        if rng.random() < 0.04:
            c['rent'] = (1, 100)
        cases.append(c)
    return cases


class PumpAmmUpdateCreatorFeeConfigCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_image()
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'update-creator-fee-config-host'
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

    def assert_matches(self, answer, captured, case):
        if answer.startswith('error:'):
            rest = answer[6:]
            if rest.startswith('1,'):
                amount = int(rest.split(',')[1])
                self.assertEqual(captured['error'], 1)
                self.assertIn('insufficient lamports', captured['logs'])
                self.assertEqual(captured['cpi'], [transfer_data(amount)])
            elif ',' in rest:
                code, site = rest.split(',')
                self.assertEqual(captured['error'], int(code))
                self.assertIn(SITES[site], captured['logs'])
                self.assertEqual(captured['cpi'], [])
            else:
                self.assertEqual(captured['error'], int(rest) if rest.isdigit() else rest)
                self.assertEqual(captured['cpi'], [])
            self.assertEqual(captured['events'], [])
            self.assertTrue(captured['rolled_back'])
            return
        if answer.startswith('transfer-fail:'):
            name, amount = answer[len('transfer-fail:'):].split(',')
            self.assertEqual(captured['error'], name)
            self.assertEqual(captured['cpi'], [transfer_data(int(amount))])
            self.assertEqual(captured['events'], [])
            self.assertTrue(captured['rolled_back'])
            if name == 'InvalidArgument':
                self.assertIn('must not carry data', captured['logs'])
            else:
                self.assertIn('does not own', captured['logs'])
            return
        if answer.startswith('event-then:'):
            _, amount, event = answer.split(',')
            self.assertEqual(captured['error'], 'MissingAccount')
            self.assertEqual(captured['events'], [bytes.fromhex(event)])
            expected = [transfer_data(int(amount))] if int(amount) else []
            self.assertEqual(captured['cpi'], expected)
            self.assertTrue(event.startswith(EVENT_DISC.hex()))
            self.assertTrue(captured['rolled_back'])
            return
        self.assertTrue(answer.startswith('ok,'), 'unknown model outcome')
        _, config, event, cfg_lamports, admin_lamports = answer.split(',')
        built = setup(case)
        before_cfg = built['config_lamports']
        before_admin = built['admin_lamports'] if built['admin_lamports'] > 0 else 0
        paid = int(cfg_lamports) - before_cfg
        self.assertEqual(before_admin - int(admin_lamports), paid)
        self.assertGreaterEqual(paid, 0)
        self.assertIsNone(captured['error'])
        self.assertEqual(captured['config'], bytes.fromhex(config))
        self.assertEqual(captured['cfg_lamports'], int(cfg_lamports))
        self.assertEqual(captured['admin_lamports'], int(admin_lamports))
        self.assertEqual(captured['cfg_len'], len(bytes.fromhex(config)))
        self.assertEqual(captured['cfg_owner'], AMM)
        self.assertEqual(captured['events'], [bytes.fromhex(event)])
        body = bytes.fromhex(event)
        self.assertEqual(captured['cpi'], ([transfer_data(paid)] if paid else []) + [EVENT_CPI_TAG + body])
        self.assertTrue(body.startswith(EVENT_DISC))
        self.assertEqual(len(body), 57)

    def run_cases(self, cases):
        for c, answer in zip(cases, self.host_answers(cases)):
            with self.subTest(case=repr(c), host=answer[:100]):
                self.assert_matches(answer, run_captured(c), c)

    def test_rejects_wrong_image_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = Path(directory) / 'wrong.so'
            wrong.write_bytes(b'not the captured AMM')
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                read_captured_image(wrong)

    def test_admitted_image_is_used_after_source_path_moves(self):
        case = {'flag': 1, 'maxbps': 500}
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
        case = {'count': 6, 'flag': 0, 'maxbps': 3}
        self.assertEqual(len(setup(case)['metas']), 6)
        self.assert_matches(self.host_answers([case])[0], run_captured(case), case)

    def test_checker_rejects_tampered_outcomes(self):
        samples = (k(flag=1, maxbps=500), k(length=907, flag=1, maxbps=777),
                   k(args=''), k(admin_ro=True), k(count=2), k(program_key=STRAY, length=907),
                   k(length=907, admin_data=b'\x11', admin_lamports=10**9),
                   k(length=907, admin_owner=AMM, admin_lamports=10**9),
                   k(length=907, admin_lamports=1), k(omit_config=True))
        flip = lambda h, i: h[:2 * i] + format(int(h[2 * i:2 * i + 2], 16) ^ 1, '02x') + h[2 * i + 2:]
        for c, answer in zip(samples, self.host_answers(samples)):
            captured = run_captured(c)
            self.assert_matches(answer, captured, c)
            if not answer.startswith('ok,'):
                with self.assertRaises(AssertionError):
                    self.assert_matches(answer, dict(captured, rolled_back=False), c)
            if answer.startswith('ok,'):
                _, config, event, cfg_l, admin_l = answer.split(',')
                tampered = ['ok,' + flip(config, CFC) + ',' + event + ',' + cfg_l + ',' + admin_l,
                            'ok,' + config + ',' + flip(event, 8) + ',' + cfg_l + ',' + admin_l,
                            'ok,' + config + ',' + event + ',' + str(int(cfg_l) + 1) + ',' + admin_l,
                            'error:6005', 'error:1,1']
            elif answer.startswith('event-then:'):
                _, amount, event = answer.split(',')
                tampered = ['event-then:MissingAccount,' + str(int(amount) + 1) + ',' + event,
                            'event-then:MissingAccount,' + amount + ',' + flip(event, 16),
                            'error:2006']
            elif answer.startswith('transfer-fail:') or answer.startswith('error:1,'):
                tampered = ['error:6005', 'error:2000,admin', 'transfer-fail:InvalidArgument,1',
                            'error:1,1', 'ok,' + '00' * 949 + ',' + '00' * 57 + ',1,1']
            else:
                tampered = [text for text in ('error:6005', 'error:3010', 'error:3007', 'error:102',
                                              'error:2000,global_config', 'error:3005,program') if text != answer]
            for text in tampered:
                if text == answer:
                    continue
                with self.subTest(case=repr(c), tampered=text[:70]), self.assertRaises(AssertionError):
                    self.assert_matches(text, captured, c)

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        self.assertEqual({a for a in answers if a.startswith('error:') and not a.startswith('error:1,')}, {
            'error:102', 'error:2000,admin', 'error:2000,global_config', 'error:2006',
            'error:3005,admin', 'error:3005,global_config', 'error:3005,system_program',
            'error:3005,event_authority', 'error:3005,program', 'error:3007', 'error:3008',
            'error:3010', 'error:3012', 'error:6005', 'error:InvalidAccountData', 'error:BorshIoError'})
        self.assertTrue(any(a.startswith('error:1,') for a in answers))
        self.assertEqual({a.split(',')[0] for a in answers if a.startswith('transfer-fail:')},
                         {'transfer-fail:InvalidArgument', 'transfer-fail:ExternalAccountLamportSpend'})
        missing = [a for a in answers if a.startswith('event-then:')]
        self.assertTrue(any(a.split(',')[1] == '0' for a in missing))
        self.assertTrue(any(int(a.split(',')[1]) > 0 for a in missing))
        self.assertGreater(sum(a.startswith('ok,') for a in answers), 20)
