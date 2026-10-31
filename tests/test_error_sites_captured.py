"""Captured-program checks for the Pump error log lines.

Failing cases of the other captured tests run on LiteSVM from the captured
`evidence/original/pump/deployed.so`, through their own fixtures, with a
recording VM around them. Each error line logged while Pump is the running
program goes to `programs/pump/recovered/error_sites_host.rs` by handler, place
and code, and the host must rebuild the exact line. The source line of a thrown
error tells apart guards that share a code, which no outcome-only test can do.
This shows matching behavior on these inputs only; it is not a byte-identity
claim.
"""
from pathlib import Path
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.litesvm import LiteSVM
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/error_sites_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = IDL['address']
IX_NAME = {bytes(i['discriminator']): i['name'] for i in IDL['instructions']}

THROWN = re.compile(r'AnchorError thrown in programs/pump/src/(\S+:\d+)\. Error Code: \w+\. Error Number: (\d+)\. ')
ACCOUNT = re.compile(r'(AnchorError|ProgramError) caused by account: (\w+)\. Error Code: \w+\. Error Number: (\d+)\. ')
OCCURRED = re.compile(r'AnchorError occurred\. Error Code: \w+\. Error Number: (\d+)\. ')

# Module (test_<name>_captured), case list, indices. One failing case per site.
CASES = {
    'account_lifecycle': {
        'fixed_cases': [12, 14, 16, 20, 22, 24, 33, 35, 39, 40, 41, 43, 77, 81, 83, 86],
    },
    'buy_v2': {
        'fixed_cases': [17, 18, 20, 21, 22, 23, 24, 25, 31, 32, 33, 48, 51, 52, 53, 54, 56, 57, 62, 63, 67, 70, 71],
    },
    'claim_cashback': {
        'fixed_cases': [23, 30, 31, 33, 34, 36, 42, 43, 44],
    },
    'claim_cashback_v2': {
        'fixed_cases': [17, 19, 21, 22],
    },
    'create_v2': {
        'fixed_cases': [3, 4, 16, 17, 18, 19, 20, 22, 24, 25, 26, 27, 28, 29, 30, 54, 57, 60, 61, 69, 80, 85, 100,
            108, 109, 111, 112, 115, 120, 125, 130, 149, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 167,
            172, 175, 179, 195, 196, 197, 200, 204, 206],
    },
    'creator_assignment': {
        'fixed_cases': [21, 23, 24, 25, 29, 33, 34, 70, 71, 74, 75, 77, 101, 105, 107, 108, 109, 111, 113, 115,
            116, 127, 128],
    },
    'creator_fee_collect': {
        'fixed_cases': [7, 39],
    },
    'creator_fee_distribution': {
        'fixed_cases': [10, 11, 12, 14, 15, 17, 20, 21, 22, 26, 65, 69, 72, 74, 76, 77, 81],
    },
    'creator_fee_distribution_quote': {
        'fixed_cases': [9, 10, 11, 12, 16, 17, 21, 22, 23, 25, 30, 33, 34],
    },
    'fee_params': {
        'fixed_cases': [1, 2, 5, 8, 12, 26, 32, 33, 36, 39, 43, 68, 69, 72, 75, 78, 79, 82],
    },
    'global_admin': {
        'admission_cases': [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 13, 16, 17, 34],
        'business_cases': [3, 4, 5, 6, 8, 14, 16, 17, 22, 24, 29, 30, 32, 40, 43, 48, 52],
    },
    'holder_distribution': {
        'fixed_cases': [7, 41, 55, 58, 59, 60, 61],
    },
    'holder_distribution_token': {
        'fixed_cases': [13, 17, 25, 26, 27],
    },
    'idl_authority': {
        'fixed_cases': [25, 46, 49, 50, 51, 52],
    },
    'legacy_buy': {
        'fixed_cases': [26, 28, 30, 31, 32, 33, 34, 36, 42, 54, 61, 62, 63, 64, 66, 67, 68, 80, 84],
    },
    'legacy_cashback': {
        'fixed_cases': [10, 11, 12, 26, 34, 35, 36, 48, 57, 63, 96, 97, 98, 99, 106, 114, 135],
    },
    'legacy_create': {
        'fixed_cases': [2, 3, 4, 5, 6, 17],
    },
    'legacy_sell': {
        'fixed_cases': [5, 31, 40, 42, 43, 44, 46, 50, 52, 53, 63],
    },
    'mayhem_virtual_params': {
        'fixed_cases': [47, 54, 55, 60],
    },
    'migrate': {
        'fixed_cases': [1, 2, 3, 4, 6, 7, 8, 15, 26, 38, 41, 48],
    },
    'migrate_v2': {
        'fixed_cases': [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 26, 27, 33, 58, 61, 81],
    },
}

sink = []


def pump_error_lines(logs):
    """Error lines logged while Pump itself is the running program, not a callee."""
    stack, lines = [], []
    for line in logs:
        invoke = re.match(r'Program (\w+) invoke \[\d+\]$', line)
        if invoke:
            stack.append(invoke.group(1))
        elif re.match(r'Program \w+ (success$|failed: )', line):
            if stack:
                stack.pop()
        elif stack and stack[-1] == PUMP and re.match(r'Program log: (Anchor|Program)Error', line):
            lines.append(line[len('Program log: '):])
    return lines


class RecordingVm:
    """LiteSVM with the failed transactions' error lines copied to `sink`."""

    def __init__(self):
        object.__setattr__(self, 'vm', LiteSVM())

    def __getattr__(self, name):
        attr = getattr(self.vm, name)
        if not callable(attr):
            return attr

        def call(*args, **kwargs):
            result = attr(*args, **kwargs)
            if isinstance(result, LiteSVM):
                object.__setattr__(self, 'vm', result)
                return self
            return result
        return call

    def send_transaction(self, tx):
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            keys = [str(key) for key in tx.message.account_keys]
            names = [IX_NAME.get(bytes(ix.data)[:8]) for ix in tx.message.instructions
                     if keys[ix.program_id_index] == PUMP]
            for line in pump_error_lines(result.meta().logs()):
                sink.append((names[0], line))
        return result


def request(handler, line):
    match = THROWN.match(line)
    if match:
        return f'line\t{handler}\tthrown\t{match[1]}\t{match[2]}'
    match = ACCOUNT.match(line)
    if match:
        kind = 'account' if match[1] == 'AnchorError' else 'program'
        return f'line\t{handler}\t{kind}\t{match[2]}\t{match[3]}'
    match = OCCURRED.match(line)
    return f'line\t{handler}\toccurred\t-\t{match[1]}' if match else None


def captured_lines():
    lines = []
    for name, lists in CASES.items():
        base = importlib.import_module(f'test_{name}_captured')
        with mock.patch.object(base, 'LiteSVM', RecordingVm):
            for list_name, indices in lists.items():
                items = getattr(base, list_name)()
                for index in indices:
                    sink.clear()
                    base.run_captured(items[index])
                    rows = [row for row in sink if request(*row)]
                    assert rows, (name, list_name, index)
                    lines += [(f'{name}/{list_name}/{index}', handler, line) for handler, line in rows]
    return lines


class ErrorSitesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'error-sites-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.lines = captured_lines()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def ask(self, requests):
        text = ''.join(r + '\n' for r in requests)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.split('\n')[:-1]

    def table(self):
        source = (ROOT / 'programs/pump/recovered/error_sites.rs').read_text(encoding='utf-8')
        rows = re.findall(r'^    \("(\w+)", Kind::(\w+), "([^"]+)", (\d+)\),$', source, re.M)
        return [(handler, kind.lower(), place, int(code)) for handler, kind, place, code in rows]

    def test_lines_match_captured_program(self):
        answers = self.ask([request(handler, line) for _, handler, line in self.lines])
        self.assertEqual(len(answers), len(self.lines))
        for (label, handler, line), answer in zip(self.lines, answers):
            with self.subTest(case=label, handler=handler):
                self.assertEqual(answer, line)

    def test_every_row_is_reached_by_a_captured_case(self):
        reached = {tuple(request(handler, line).split('\t')[1:]) for _, handler, line in self.lines}
        rows = {(handler, kind, place, str(code)) for handler, kind, place, code in self.table()}
        self.assertGreaterEqual(len(rows), 100)
        self.assertEqual(rows, reached)

    def test_guards_sharing_a_code_keep_their_own_lines(self):
        groups = {}
        for handler, kind, place, code in self.table():
            if kind == 'thrown':
                groups.setdefault((handler, code), set()).add(place)
        shared = {key: places for key, places in groups.items() if len(places) > 1}
        self.assertTrue(shared)
        answers = self.ask([f'sites\t{handler}\t{code}' for handler, code in shared])
        for (key, places), answer in zip(shared.items(), answers):
            with self.subTest(guards=key):
                self.assertEqual(answer.split(','), sorted(places))

    def test_custom_errors_match_the_idl(self):
        codes = sorted({code for *_, code in self.table()})
        expected = {e['code']: e for e in IDL['errors']}
        answers = self.ask([f'error\t{code}' for code in codes])
        custom = 0
        for code, answer in zip(codes, answers):
            if 6000 <= code < 7000:
                custom += 1
                with self.subTest(code=code):
                    # An error without a #[msg] has no IDL text to compare.
                    name, message = answer.split('\t')
                    self.assertEqual(name, expected[code]['name'])
                    self.assertEqual(message, expected[code].get('msg', message))
        self.assertGreaterEqual(custom, 30)

    def test_checker_rejects_a_moved_line(self):
        # Negative control: the same code one source line away names no row.
        label, handler, line = next(row for row in self.lines if THROWN.match(row[2]))
        match = THROWN.match(line)
        place, number = match[1].rsplit(':', 1)
        moved = line.replace(match[1], f'{place}:{int(number) + 100000}')
        answers = self.ask([request(handler, line), request(handler, moved)])
        self.assertEqual(answers, [line, 'unknown'], label)


if __name__ == '__main__':
    unittest.main()
