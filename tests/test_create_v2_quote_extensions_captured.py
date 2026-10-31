"""Captured-program checks for the raw-byte quote mint check of Pump `create_v2`.

Every case runs `create_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the fixtures and programs
of `tests/test_create_v2_captured.py`, for the whitelisted quote mint holding
the given bytes. The same bytes go to
`programs/pump/recovered/create_v2_quote_extensions_host.rs`, and the error or
the created curve and quote account must agree. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_create_v2_captured as base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_v2_quote_extensions_host.rs'
TOKEN, TOKEN22 = base.TOKEN, base.TOKEN22
BODY = {1: bytes(108), 2: bytes(8), 3: bytes(32), 4: bytes(65), 5: bytes(295), 6: b'\1', 7: b'', 8: b'\1', 9: b'', 10: bytes(52),
        11: b'\1', 12: bytes(32), 13: b'', 14: bytes(64), 15: b'\1', 16: bytes(64), 17: bytes(64), 18: bytes(64), 19: bytes(64),
        20: bytes(64), 21: bytes(40), 22: bytes(32), 23: bytes(64), 24: bytes(32), 25: bytes(56), 26: bytes(33), 27: b''}


def tlv(kind, body=None):
    body = BODY.get(kind, b'') if body is None else body
    return struct.pack('<HH', kind, len(body)) + body


# Other failures of the same create: host gate -> changes to the base case.
GATES = {
    'before:6046': dict(create_v2=0), 'before:6030': dict(creator_zero=1),
    'before:6099': dict(quote='curve', curve=dict(base.DEFAULT_CURVE), curve_flaw='key'),
    'after:6065': dict(ata_wrong=1), 'late:6043': dict(name='x' * 40), 'late:6044': dict(symbol='x' * 40),
    'exists': dict(ata_exists=1),
}
HEAD = base.mint_data()
PADDED = HEAD.ljust(165, b'\0')
START = PADDED + b'\1'


def fixed_cases():
    cases = [('t22', HEAD, '-'), ('spl', HEAD, '-')]
    add = lambda data: cases.append(('t22', data, '-'))
    # Every kind on its own, and after an accepted one.
    for kind in range(1, 34):
        add(START + tlv(kind))
        add(START + tlv(18) + tlv(kind))
        add(START + tlv(kind) + tlv(0, b''))
    for kind in (99, 255, 256, 65535):
        add(START + tlv(kind))
    # Combinations of accepted kinds.
    accepted = (1, 4, 6, 12, 14, 16, 18, 19, 25, 26)
    for i, left in enumerate(accepted):
        for right in accepted[i:]:
            add(START + tlv(left) + tlv(right))
    add(START + b''.join(tlv(k) for k in accepted))
    add(START + b''.join(tlv(k) for k in reversed(accepted)))
    # Bodies.
    for size in (0, 1, 107, 108, 109, 200):
        add(START + tlv(1, bytes(size)))
    for size in (0, 1, 63, 64, 65):
        add(START + tlv(14, bytes(size)))
    add(START + tlv(14, bytes(32) + bytes([7]) * 32))
    add(START + tlv(14, bytes([7]) * 32 + bytes(32)))
    add(START + tlv(14, bytes(63) + b'\1'))
    add(START + tlv(14, bytes(32) + b'\1' + bytes(31)))
    for state in (0, 1, 2, 3):
        add(START + tlv(6, bytes([state])))
    add(START + tlv(6, b''))
    add(START + tlv(6, b'\1\0'))
    # The walk's edges.
    for tail in (b'\0', b'\1', b'\0\0', b'\1\0', b'\0\1', b'\1\0\0', b'\0\0\0', b'\3\0\0', b'\0\0\0\0', b'\1\0\0\0'):
        add(START + tail)
        add(START + tlv(18) + tail)
    add(START + tlv(0, bytes(8)) + tlv(9))
    add(START + bytes(8) + tlv(9))
    add(START + struct.pack('<HH', 18, 500) + bytes(32))
    add(START + struct.pack('<HH', 18, 65) + bytes(64))
    add(START + struct.pack('<HH', 18, 64) + bytes(64))
    # Layout before the walk.
    for size in (0, 44, 81, 83, 100, 164, 165):
        add(PADDED[:size])
    add(START)
    add(PADDED + b'\2')
    add(PADDED + b'\2' + tlv(18))
    add(PADDED + b'\0' + tlv(18))
    add(PADDED + b'\3' + tlv(18))
    for offset in (82, 100, 164):
        data = bytearray(START + tlv(18))
        data[offset] = 1
        add(bytes(data))
    add(bytes(36) + b'\1' + bytes(44))
    # A multisig-sized mint: the walk still runs first.
    for data in (START + tlv(18), START + tlv(9), START, START + tlv(18) + bytes(8)):
        add(data.ljust(354, b'\0'))
        add(data.ljust(355, b'\0'))
        add(data.ljust(356, b'\0'))
    # SPL Token holds a mint of its own only, and the walk does not run for it.
    for data in (START + tlv(18), START + tlv(9), START, PADDED, PADDED[:83], PADDED[:81], PADDED[:44], START.ljust(355, b'\0')):
        cases.append(('spl', data, '-'))
    # The other failures of a create, around the bytes.
    for program, data in (('t22', HEAD), ('t22', START + tlv(18)), ('t22', START + tlv(9)), ('t22', START.ljust(355, b'\0')),
                          ('spl', HEAD), ('spl', START + tlv(9))):
        for gate in GATES:
            cases.append((program, data, gate))
    return cases


def random_cases(count=120, seed=2333):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        kinds = [rng.choice((1, 4, 6, 12, 14, 16, 18, 19, 25, 26, rng.randrange(1, 40))) for _ in range(rng.randrange(1, 5))]
        data = START + b''.join(tlv(k) for k in kinds)
        if rng.random() < 0.3:
            data += bytes(rng.randrange(0, 5))
        if rng.random() < 0.2:
            data = data[:-rng.randrange(1, 4)]
        cases.append(('t22', data, rng.choice(('-',) * 8 + tuple(GATES))))
    return cases


def run_captured(program, data, gate='-'):
    changes = dict(dict(quote='whitelisted'), **GATES.get(gate, {}))
    item = base.case(program=TOKEN if program == 'spl' else TOKEN22, **changes)
    with mock.patch.object(base, 'mint_data', lambda: data):
        return base.run_captured(item), item


def outcome(captured):
    text = str(captured['error'])
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    name = re.search(r'Fieldless\((\w+)\)', text)
    return name.group(1) if name else text


def host_line(program, data, gate='-'):
    return f"{int(program == 'spl')},{gate},{data.hex()}"


class CreateV2QuoteExtensionsCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-v2-quote-extensions-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(*c) + '\n' for c in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if not answer.startswith('ok,'):
            self.assertEqual(outcome(captured), answer)
            return
        self.assertIsNone(captured['error'])
        account = captured['quote_ata']
        self.assertEqual(len(account.data), int(answer[3:]))
        self.assertEqual(account.owner, item['program'])
        self.assertEqual(bytes(account.data)[:64], bytes(base.quote_mint_key(item)) + bytes(base.CURVE))
        self.assertEqual(bytes(captured['curve'].data)[83:115], bytes(base.quote_mint_key(item)))
        self.assertEqual(len(captured['events']), 1)

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for one, answer in zip(cases, answers):
            with self.subTest(case=host_line(*one), host=answer):
                captured, item = run_captured(*one)
                self.assert_matches(item, answer, captured)

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_a_wrong_account_size(self):
        case = ('t22', START + tlv(1), '-')
        answer = self.host_answers([case])[0]
        captured, item = run_captured(*case)
        self.assert_matches(item, answer, captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(item, 'ok,170', captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(item, 'error:6063', captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'IllegalOwner', 'error:2', 'error:6030', 'error:6043', 'error:6044', 'error:6046',
                                    'error:6063', 'error:6065', 'error:6099'})


if __name__ == '__main__':
    unittest.main()
