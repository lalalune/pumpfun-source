"""Captured-program checks for how Pump Main reads instruction data.

Every case sends raw instruction data to the captured
`evidence/original/pump/deployed.so` on LiteSVM, with no accounts unless it
says otherwise, and to `programs/pump/recovered/instruction_data_host.rs`.
With no accounts an instruction whose data is good stops at `AccountNotEnoughKeys`
(3005), so that error marks a passed decode. Each of the 56 published
instructions gets its data cut at every length, every byte set to edge values,
every length field set around the bytes left and around the heap, and random
damage. The `#[event_cpi]` entry gets its own account cases. This is matching
behaviour on these inputs only, not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import struct
import subprocess
import tempfile
import unittest

from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
PUMP_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/instruction_data_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
SYSTEM = Pubkey.default()
EVENT_TAG = bytes.fromhex('e445a52e51cb9a1d')
EVENT_AUTHORITY = Pubkey.find_program_address([b'__event_authority'], PUMP)[0]
PAYER = Keypair.from_seed(bytes([201]) * 32)
LOOSE = [Pubkey.from_bytes(bytes([50 + i]) * 32) for i in range(4)]


def sample(kind):
    """A good encoding of one argument."""
    if kind in ('u64', 'i64'):
        return bytes(range(1, 9))
    if kind == 'pubkey':
        return bytes(range(32))
    if kind == 'bool':
        return b'\x01'
    if kind == 'u8':
        return b'\x07'
    if kind in ('string', 'bytes'):
        return struct.pack('<I', 3) + b'abc'
    if 'option' in kind:
        return b'\x01' + sample(kind['option'])
    if 'vec' in kind:
        return struct.pack('<I', 2) + sample(kind['vec']) * 2
    return {'OptionBool': b'\x01', 'OptionU64': bytes(range(1, 9))}[kind['defined']['name']]


def length_fields(kind, start):
    """Offsets of the u32 length fields inside one sampled argument."""
    if kind in ('string', 'bytes') or (isinstance(kind, dict) and 'vec' in kind):
        return [start]
    return []


def layouts():
    for instruction in IDL['instructions']:
        body, fields = b'', []
        for argument in instruction.get('args', []):
            fields += length_fields(argument['type'], len(body))
            body += sample(argument['type'])
        yield bytes(instruction['discriminator']), body, fields


def plain(data):
    return data, (), 0


def instruction_cases():
    cases = [plain(bytes(n)) for n in range(9)] + [plain(b'\xff' * n) for n in (1, 7, 8, 9, 40)]
    for disc, body, fields in layouts():
        data = disc + body
        cases += [plain(data[:n]) for n in range(len(data) + 1)]
        cases += [plain(data + extra) for extra in (b'\x00', b'\x02', bytes(9))]
        for i in range(8):
            cases.append(plain(data[:i] + bytes([data[i] ^ 1]) + data[i + 1:]))
        for i in range(8, len(data)):
            cases += [plain(data[:i] + bytes([value]) + data[i + 1:]) for value in (0, 1, 2, 255)]
            cases += [plain(data[:i] + bytes([value])) for value in (2, 255)]
        for field in fields:
            at = 8 + field
            for stated in (0, 1, 2, 3, 4, 5, 16, 17, 40, 1_000, 31_000, 32_029, 32_030, 32_031, 32_768, 2**31, 2**32 - 1):
                changed = data[:at] + struct.pack('<I', stated) + data[at + 4:]
                cases.append(plain(changed))
                cases.append(plain(changed[:at + 4]))
                cases.append(plain(changed[:at + 4] + bytes(min(stated, 700))))
    return cases


def string_cases():
    """UTF-8 and the heap across several strings of `create` and `create_v2`."""
    by_name = {i['name']: bytes(i['discriminator']) for i in IDL['instructions']}
    text = lambda raw: struct.pack('<I', len(raw)) + raw
    cases = []
    for name in ('create', 'create_v2'):
        disc = by_name[name]
        for bad in (b'\xff', b'\xc0\x80', b'\xed\xa0\x80', b'\xf4\x90\x80\x80', b'ab\xe2\x82'):
            for first, second, third in ((bad, b'a', b'a'), (b'a', bad, b'a'), (b'a', b'a', bad)):
                cases.append(plain(disc + text(first) + text(second) + text(third) + bytes(33)))
        for good in (b'\x00', '€'.encode(), '\U0001f600'.encode(), b'a' * 700):
            cases.append(plain(disc + text(good) + text(good[:3]) + text(b'') + bytes(33)))
        for spent in (0, 1, 700, 900):
            head = disc + text(b'a' * spent)
            for stated in (32_029 - spent, 32_030 - spent, 32_031 - spent):
                cases.append(plain(head + struct.pack('<I', stated)))
                cases.append(plain(head + text(b'bc') + struct.pack('<I', stated - 2)))
                cases.append(plain(head + text(b'bc') + struct.pack('<I', stated - 1)))
        cut = disc + text(b'a') + text(b'b') + text(b'c') + bytes(32)
        if name == 'create_v2':
            for tail in (b'\x00\x00', b'\x00\x00\x02', b'\x00\x00\xff\xff', b'\x00\x00' + bytes(7) + b'\x02',
                         b'\x00\x00' + bytes(8) + b'\x02', b'\x00\x00' + bytes(8) + b'\x01\x02', b'\x01\x01' + b'\xff' * 8):
                cases.append(plain(cut + tail))
    return cases


def random_cases():
    rng = random.Random(20261031)
    shapes = list(layouts())
    cases = []
    for _ in range(4_000):
        disc, body, _fields = rng.choice(shapes)
        data = bytearray(body)
        for _ in range(rng.randint(1, 4)):
            if data:
                data[rng.randrange(len(data))] = rng.choice((0, 1, 2, 3, 4, 127, 128, 255, rng.randrange(256)))
        cut = rng.choice((len(data), len(data), rng.randint(0, len(data))))
        cases.append(plain(disc + bytes(data[:cut]) + bytes(rng.choice((0, 0, 1, 8, 40)))))
    return cases


def account_cases():
    """(signer, key) lists: the heap each slot takes, and the event entry."""
    disc = next(bytes(i['discriminator']) for i in IDL['instructions'] if i['name'] == 'create')
    key = lambda i, signer=False: (LOOSE[i], signer)
    cases = []
    shapes = [[key(0)], [key(0), key(1)], [key(0), key(1), key(2)], [key(0), key(0)], [key(0), key(1), key(0)],
              [key(0), key(0), key(0)], [key(0), key(1), key(2), key(0), key(1)], [(SYSTEM, False)]]
    for shape in shapes:
        distinct = len({k for k, _ in shape})
        room = 32_030 - 120 * distinct - 48 * (len(shape) - distinct)
        for stated in (room - 1, room, room + 1):
            cases.append((disc + struct.pack('<I', stated), shape))
    authority = (EVENT_AUTHORITY, False)
    signing = (EVENT_AUTHORITY, True)
    bare = [(key(0)), key(0, True)]
    for tail in (b'', b'\x00', bytes(64)):
        for shape in ([], [authority], [signing], [signing, key(0)], [authority, signing], [key(0), signing], bare,
                      [key(0, True), signing], [(PAYER.pubkey(), True)], [(PAYER.pubkey(), False)], [(SYSTEM, True)]):
            cases.append((EVENT_TAG + tail, shape))
    for i in range(8):
        cases.append((EVENT_TAG[:i] + bytes([EVENT_TAG[i] ^ 1]) + EVENT_TAG[i + 1:], [signing]))
    cases += [(EVENT_TAG[:n], [signing]) for n in range(8)]
    return [resolve(data, shape) for data, shape in cases]


def resolve(data, shape):
    """A key that appears twice carries the union of its privileges; the payer signs."""
    signers = {PAYER.pubkey(): True}
    for key, signer in shape:
        signers[key] = signers.get(key, False) or signer
    keys = [key for key, _ in shape]
    return data, tuple(shape), len(keys) - len(set(keys)), signers


def host_line(case):
    data, shape, repeated = case[:3]
    signers = case[3] if len(case) > 3 else {}
    fields = [data.hex(), str(repeated)]
    for key, _signer in shape:
        fields.append(f'{int(signers[key])}{int(key == EVENT_AUTHORITY)}')
    return ','.join(fields)


class Vm:
    def __init__(self):
        self.vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, PUMP_ELF)
        self.vm.set_account(PAYER.pubkey(), Account(10**15, b'', SYSTEM))

    def run(self, case):
        data, shape = case[:2]
        metas = [AccountMeta(key, signer, False) for key, signer in shape]
        self.vm.expire_blockhash()
        blockhash = self.vm.latest_blockhash()
        message = Message.new_with_blockhash([Instruction(PUMP, data, metas)], PAYER.pubkey(), blockhash)
        tx = Transaction.new_unsigned(message)
        tx.partial_sign([PAYER], blockhash)
        result = self.vm.send_transaction(tx)
        if not isinstance(result, FailedTransactionMetadata):
            return 'passed'
        text = str(result.err())
        custom = re.search(r'InstructionErrorCustom\((\d+)\)', text)
        if custom:
            number = int(custom.group(1))
            if number in (101, 102) or data[:8] == EVENT_TAG:
                return f'error:{number}'
            return 'passed'
        if 'ProgramFailedToComplete' in text:
            return 'out-of-memory'
        if 'NotEnoughAccountKeys' in text:
            return 'not-enough-keys'
        return text


class InstructionDataCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == PUMP_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'instruction-data-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host
        cls.vm = Vm()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        lines = [host_line(case) for case in cases]
        result = subprocess.run([str(self.host)], input='\n'.join(lines) + '\n', capture_output=True, text=True,
                                check=True)
        return result.stdout.splitlines()

    def compare(self, cases, captured):
        hosted = self.host_answers(cases)
        self.assertEqual(len(hosted), len(captured))
        wrong = [(i, cases[i][0].hex()[:60], h, c) for i, (h, c) in enumerate(zip(hosted, captured)) if h != c]
        self.assertEqual(wrong[:6], [], f'{len(wrong)} of {len(captured)} differ')

    def check(self, cases):
        answers = [self.vm.run(case) for case in cases]
        self.compare(cases, answers)
        return answers

    def test_table_is_the_published_idl(self):
        self.assertEqual(len(IDL['instructions']), 56)
        source = (ROOT / 'programs/pump/recovered/instruction_data.rs').read_text(encoding='utf-8')
        for instruction in IDL['instructions']:
            self.assertIn('[' + ', '.join(map(str, instruction['discriminator'])) + ']', source)

    def test_every_instruction(self):
        answers = self.check(instruction_cases())
        self.assertGreater(answers.count('passed'), 1_000)
        self.assertGreater(answers.count('out-of-memory'), 50)

    def test_strings(self):
        self.check(string_cases())

    def test_random_damage(self):
        self.check(random_cases())

    def test_account_slots_and_event_entry(self):
        answers = self.check(account_cases())
        self.assertIn('passed', answers)

    def test_odd_length_hex_is_rejected(self):
        # A trailing half byte must be rejected, not silently dropped.
        fields = host_line(plain(bytes(range(1, 9)))).split(',')
        fields[0] += 'a'
        result = subprocess.run([str(self.host)], input=','.join(fields) + '\n', capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('odd-length hex', result.stderr)


if __name__ == '__main__':
    unittest.main()
