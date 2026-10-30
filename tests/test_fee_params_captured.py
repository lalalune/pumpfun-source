"""Captured-program checks for the recovered Pump fee-recipient parameter setters.

Every case runs Pump `set_params` or `set_reserved_fee_recipients` from the
captured `evidence/original/pump/deployed.so` on LiteSVM against a synthetic
Global account and eight (or fewer) remaining recipient accounts. The same
inputs go to `programs/pump/recovered/fee_params_host.rs`, and the error, the
stored Global bytes and the SetParamsEvent / ReservedFeeRecipientsEvent must
agree. This shows matching behavior on these inputs only; it is not a
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
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/fee_params_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
IX = {i['name']: i for i in IDL['instructions']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}

AUTHORITY = Keypair.from_seed(bytes([212]) * 32)
STRANGER = Keypair.from_seed(bytes([213]) * 32)
TIMESTAMP = 1_700_000_000
TX_FEE = 5000
U64 = 2**64 - 1
RENT_PER_BYTE = 6960  # Rent::minimum_balance(len) == (128 + len) * 6960


def pda(*seeds):
    return Pubkey.find_program_address(list(seeds), PUMP)[0]


GLOBAL = pda(b'global')
EVENT_AUTHORITY = pda(b'__event_authority')


BOOL_OFFSETS = (8, 145, 450, 515, 740, 1045, 1086)
EXECUTABLE = 255  # key fill standing for the (executable) Pump program account


def key(fill):
    return PUMP if fill == EXECUTABLE else Pubkey.from_bytes(bytes([fill]) * 32)


def old_global():
    # Every field the setters may write starts non-zero so a write is visible.
    data = bytearray(range(256)) * 4 + bytearray(64)
    data[:8] = ACCOUNT_DISC['Global']
    for offset in BOOL_OFFSETS:
        data[offset] = 1
    data[9:41] = bytes(AUTHORITY.pubkey())
    return bytes(data)


def recipient(fill, lamports=None, size=0):
    """One remaining account: key fill byte (0: the all-zero key, EXECUTABLE:
    the Pump program account as loaded), lamports, data length.
    `lamports=None` means exactly rent-exempt; 0 means the account is absent."""
    if lamports is None:
        lamports = (128 + size) * RENT_PER_BYTE
    return (fill, lamports, size)


SORTED = [recipient(100 + 10 * i) for i in range(8)]


def params(**changes):
    item = dict(ix='set_params', virtual_token=1_073_000_000_000_000, virtual_sol=30_000_000_000,
                real_token=793_100_000_000_000, supply=1_000_000_000_000_000, fee_bps=95, withdraw=31,
                migrate=1, migration_fee=15_000_001, creator_bps=5, set_creator=32, admin_set_creator=33,
                recipients=SORTED, signer=True, authority_ok=True, raw=None)
    item.update(changes)
    return item


def reserved(**changes):
    item = dict(ix='set_reserved_fee_recipients', whitelist=34, recipients=SORTED, signer=True, authority_ok=True,
                raw=None)
    item.update(changes)
    return item


def ix_data(item):
    ix = bytes(IX[item['ix']]['discriminator'])
    if item['raw'] is not None:
        return ix + item['raw']
    if item['ix'] == 'set_reserved_fee_recipients':
        return ix + bytes(key(item['whitelist']))
    return (ix + struct.pack('<5Q', item['virtual_token'], item['virtual_sol'], item['real_token'], item['supply'],
                             item['fee_bps']) + bytes(key(item['withdraw'])) + bytes([item['migrate']])
            + struct.pack('<QQ', item['migration_fee'], item['creator_bps']) + bytes(key(item['set_creator']))
            + bytes(key(item['admin_set_creator'])))


def run_captured(item):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.set_clock(Clock(100, TIMESTAMP, 0, 0, TIMESTAMP))
    signer = AUTHORITY if item['authority_ok'] else STRANGER
    vm.set_account(signer.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(GLOBAL, Account(10**9, old_global(), PUMP))
    for fill, lamports, size in item['recipients']:
        if fill and fill != EXECUTABLE and lamports:
            vm.set_account(key(fill), Account(lamports, bytes(size), SYSTEM))
    named = {'global': GLOBAL, 'authority': signer.pubkey(), 'event_authority': EVENT_AUTHORITY, 'program': PUMP}
    metas = []
    for a in IX[item['ix']]['accounts']:
        signs = a.get('signer', False) and (item['signer'] or a['name'] != 'authority')
        metas.append(AccountMeta(named[a['name']], signs, a.get('writable', False)))
    metas += [AccountMeta(key(fill), False, False) for fill, *_ in item['recipients']]
    instruction = Instruction(PUMP, ix_data(item), metas)
    if item['signer']:
        tx = Transaction.new_signed_with_payer([instruction], signer.pubkey(), [signer], vm.latest_blockhash())
    else:
        payer = Keypair.from_seed(bytes([214]) * 32)
        vm.set_account(payer.pubkey(), Account(10**12, b'', SYSTEM))
        tx = Transaction.new_signed_with_payer([instruction], payer.pubkey(), [payer], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    if isinstance(result, FailedTransactionMetadata):
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        return {'error': int(code.group(1)) if code else text, 'logs': result.meta().logs()}
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    return {'error': None, 'global': bytes(vm.get_account(GLOBAL).data), 'events': events}


def recipient_fields(fill, lamports, size):
    if fill == EXECUTABLE:
        size = PUMP_ELF.stat().st_size  # BPF Loader 2 program account: the ELF, rent-exempt
        return bytes(PUMP).hex(), (128 + size) * RENT_PER_BYTE, size, 1
    return bytes(key(fill)).hex(), lamports, size, 0


def host_line(item):
    recipients = '+'.join('/'.join(map(str, recipient_fields(*r))) for r in item['recipients'])
    fields = [item['ix'], int(item['signer']), int(item['authority_ok']), TIMESTAMP, ix_data(item)[8:].hex(),
              old_global().hex(), recipients]
    return ','.join(str(f) for f in fields)


def final_sol(item):
    return item['real_token'] * item['virtual_sol'] // (item['virtual_token'] - item['real_token'])


def fixed_cases():
    R = recipient
    cases = []
    final = final_sol(params())
    for make in (params, reserved):
        add = lambda **k: cases.append(make(**k))
        add()
        # Admin accounts; arguments decode before the signer check.
        add(signer=False)
        add(authority_ok=False)
        add(signer=False, authority_ok=False)
        add(authority_ok=False, recipients=SORTED[:7])
        add(raw=ix_data(make())[8:-1])
        add(raw=ix_data(make())[8:-1], signer=False)
        add(raw=ix_data(make())[8:] + bytes(5))
        # Remaining accounts: only the first eight are read.
        add(recipients=[])
        add(recipients=SORTED[:7])
        add(recipients=SORTED + [R(0)])
        add(recipients=SORTED + [R(250, 0)])
        add(recipients=SORTED[:7] + [R(0)])
        add(recipients=[R(0)] + SORTED[1:])
        # Rent: exact minimum, one short, absent, with data.
        add(recipients=SORTED[:4] + [R(140, size=300)] + SORTED[5:])
        add(recipients=SORTED[:4] + [R(140, (128 + 300) * RENT_PER_BYTE - 1, 300)] + SORTED[5:])
        add(recipients=SORTED[:4] + [R(140, 128 * RENT_PER_BYTE - 1)] + SORTED[5:])
        add(recipients=SORTED[:4] + [R(140, 0)] + SORTED[5:])
        add(recipients=SORTED[:7] + [R(170, 10**15)])
        # Check order across recipients.
        add(recipients=[R(100, 0)] + SORTED[1:7] + [R(0)])
        add(recipients=[R(0)] + [R(110, 0)] + SORTED[2:])
        add(recipients=[R(100, 0)] + SORTED[1:][::-1])
        add(recipients=[R(EXECUTABLE)] + SORTED[1:])
        add(recipients=SORTED[:2] + [R(EXECUTABLE)] + SORTED[3:6] + [R(0)] + SORTED[7:])
        add(recipients=SORTED[:2] + [R(0)] + SORTED[3:6] + [R(EXECUTABLE)] + SORTED[7:])
        add(recipients=[R(EXECUTABLE)] + [R(110, 0)] + SORTED[2:])
        # Ordering and uniqueness (enforced by set_params only).
        add(recipients=SORTED[::-1])
        add(recipients=[SORTED[0], SORTED[0]] + SORTED[2:])
        add(recipients=SORTED[:7] + [SORTED[6]])
        add(recipients=SORTED[1:2] + SORTED[:1] + SORTED[2:])
        add(recipients=[R(1 + i) for i in range(8)])
    add = lambda **k: cases.append(params(**k))
    add(migrate=0)
    args = ix_data(params())[8:]
    add(raw=args[:72] + bytes([2]) + args[73:])
    # Basis points: inclusive cap of 1000 on both.
    for fee in (0, 1000, 1001, U64):
        add(fee_bps=fee)
        add(creator_bps=fee)
    add(withdraw=0)
    add(withdraw=0, fee_bps=1001)
    add(withdraw=0, creator_bps=1001)
    # Supply and reserve ordering.
    add(supply=793_100_000_000_000)
    add(supply=793_100_000_000_001)
    add(supply=0, real_token=0, migration_fee=0)
    add(virtual_token=793_100_000_000_000)
    add(virtual_token=793_100_000_000_001)
    add(virtual_token=793_100_000_000_000, supply=1)
    add(virtual_token=0, real_token=0, supply=1)
    add(virtual_token=1, real_token=0, supply=1, migration_fee=0)
    add(virtual_token=793_100_000_000_000, fee_bps=1001)
    # Final real SOL reserves: floor division, migration fee strictly below.
    add(migration_fee=final - 1)
    add(migration_fee=final)
    add(migration_fee=final, creator_bps=1001)
    add(migration_fee=final - 1, creator_bps=1001)
    add(virtual_token=10, real_token=7, virtual_sol=10, supply=8, migration_fee=22)
    add(virtual_token=10, real_token=7, virtual_sol=10, supply=8, migration_fee=23)
    add(virtual_token=U64, real_token=U64 - 1, virtual_sol=1, supply=U64, migration_fee=U64 - 2)
    add(virtual_token=U64, real_token=U64 - 1, virtual_sol=1, supply=U64, migration_fee=U64 - 1)
    add(virtual_token=U64, real_token=U64 - 1, virtual_sol=2, supply=U64)
    add(virtual_token=U64, real_token=U64 - 1, virtual_sol=2, supply=U64, withdraw=0)
    add(virtual_token=U64, real_token=U64 - 1, virtual_sol=2, supply=U64, creator_bps=1001)
    add(virtual_token=2**63, real_token=2**62, virtual_sol=U64, supply=U64, migration_fee=0)
    add(virtual_token=2**63, real_token=2**62 + 1, virtual_sol=U64, supply=U64, migration_fee=0)
    return cases


def random_cases(count=60, seed=352):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        recipients = [recipient(f) for f in sorted(rng.sample(range(1, 250), 8))]
        roll = rng.random()
        if roll < 0.2:
            recipients.reverse()
        elif roll < 0.35:
            i = rng.randrange(8)
            recipients[i] = recipient(recipients[i][0], rng.choice((0, rng.randrange(1, 2 * 128 * RENT_PER_BYTE))))
        elif roll < 0.45:
            recipients[rng.randrange(8)] = recipient(0)
        elif roll < 0.5:
            recipients = recipients[:rng.randrange(8)]
        if recipients and rng.random() < 0.2:
            size = rng.randrange(0, 2000)
            recipients[-1] = recipient(recipients[-1][0], (128 + size) * RENT_PER_BYTE - rng.randrange(0, 2), size)
        if rng.random() < 0.4:
            cases.append(reserved(whitelist=rng.randrange(256), recipients=recipients,
                                  authority_ok=rng.random() < 0.95))
            continue
        supply = rng.choice((rng.randrange(1, 10**18), U64))
        real = min(U64, rng.randrange(0, supply + 1) if rng.random() < 0.9 else supply + rng.randrange(0, 2))
        virtual = min(U64, real + rng.choice((0, 1, rng.randrange(1, 10**16), rng.randrange(1, 2**63))))
        item = params(virtual_token=virtual, real_token=real, supply=supply,
                      virtual_sol=rng.choice((rng.randrange(0, 10**11), rng.randrange(0, 2**64))),
                      fee_bps=rng.choice((rng.randrange(0, 1001), rng.randrange(0, 2000))),
                      creator_bps=rng.choice((rng.randrange(0, 1001), rng.randrange(0, 2000))),
                      withdraw=rng.choice((0,) + (rng.randrange(1, 256),) * 9), migrate=rng.randrange(2),
                      recipients=recipients, set_creator=rng.randrange(256), admin_set_creator=rng.randrange(256))
        if virtual > real:
            final = final_sol(item)
            choices = (0, final - 1, final, final + 1, rng.randrange(0, U64))
            item['migration_fee'] = min(U64, max(0, rng.choice(choices)))
        cases.append(item)
    return cases


class FeeParamsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'fee-params-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, answer, captured):
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        _, global_hex, event_hex = answer.split(',')
        self.assertEqual(captured['global'].hex(), global_hex)
        self.assertEqual([e.hex() for e in captured['events']], [event_hex])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            shown = {k: v for k, v in item.items() if k not in ('recipients', 'raw')}
            with self.subTest(case=shown, recipients=item['recipients'], host=answer[:40]):
                self.assert_matches(answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_changed_write(self):
        # Negative control: a passing set_params must fail once a stored
        # recipient byte or the event's final real SOL reserves change.
        item = params()
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(answer, captured)
        stored = bytearray(captured['global'])
        stored[41] ^= 1
        with self.assertRaises(AssertionError):
            self.assert_matches(answer, dict(captured, **{'global': bytes(stored)}))
        event = bytearray(captured['events'][0])
        event[32] ^= 1
        with self.assertRaises(AssertionError):
            self.assert_matches(answer, dict(captured, events=[bytes(event)]))

    def test_fixed_cases_cover_every_outcome(self):
        answers = self.host_answers(fixed_cases())
        outcomes = {a.split(',')[0] for a in answers}
        self.assertEqual(outcomes, {
            'ok', 'error:102', 'error:2005', 'error:2007', 'error:3010', 'error:6000', 'error:6011', 'error:6012',
            'error:6013', 'error:6014', 'error:6015', 'error:6025', 'error:6027', 'error:6028', 'error:6029',
        })


if __name__ == '__main__':
    unittest.main()
