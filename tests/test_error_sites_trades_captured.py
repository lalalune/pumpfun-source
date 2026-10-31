"""Captured-program checks for Pump error log lines on v3, multi-hop and quote control.

A recording VM runs the fixed cases of the captured tests of the v3 trades,
`multi_hop_curve_swap` and quote control, all on
`evidence/original/pump/deployed.so`. Every failing transaction with one Pump
instruction yields the Anchor line Pump itself logged, not its callees. Each
line must equal the one `programs/pump/recovered/error_sites_trades_host.rs`
builds from the handler, the place and the code, and every table row must be
reached. The comparison is by set, not case order, so a reordered list in those
tests does not break it. This is matching behaviour on these inputs only, not a
byte-identity claim.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import hashlib
import importlib
import io
import json
import re
import subprocess
import sys
import tempfile
import unittest

import solders.litesvm
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
PUMP_SHA256 = '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'
HOST_SOURCE = ROOT / 'programs/pump/recovered/error_sites_trades_host.rs'
MODEL_SOURCE = ROOT / 'programs/pump/recovered/error_sites_trades.rs'
MODULES = ('test_quote_control_captured', 'test_multi_hop_hop_captured', 'test_multi_hop_route_captured',
           'test_v3_trade_accounting_captured', 'test_v3_vault_refactor_captured',
           'test_v3_exact_quote_captured')
FIXED_TESTS = ('test_fixed_cases', 'test_fixed_cases_match_captured_program', 'test_captured_matches_model')
ROUTES = ('buy_v3', 'sell_v3', 'buy_exact_quote_in_v3', 'multi_hop_curve_swap', 'initialize_quote_control',
          'add_quote_control_mint', 'remove_quote_control_mint', 'set_quote_control_mint_reserves',
          'set_quote_control_admin', 'set_quote_control_reserves_admin')

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = IDL['address']
HANDLERS = {bytes(i['discriminator']): i['name'] for i in IDL['instructions']}
LINE = re.compile(r'^(?:AnchorError thrown in programs/pump/src/(?P<thrown>\S+?)\.'
                  r'|AnchorError caused by account: (?P<account>[\w\[\]]+)\.'
                  r'|ProgramError caused by account: (?P<program>[\w\[\]]+)\.'
                  r'|AnchorError occurred\.) Error Code: \w+\. Error Number: (?P<code>\d+)\. Error Message: ')
RealVm = solders.litesvm.LiteSVM
RECORDED = []


class RecordingVm:
    """LiteSVM with a builder chain, keeping the Pump lines of failed transactions."""

    def __init__(self):
        object.__setattr__(self, 'vm', RealVm())

    def __getattr__(self, name):
        attribute = getattr(self.vm, name)
        if not callable(attribute):
            return attribute

        def call(*args, **kwargs):
            result = attribute(*args, **kwargs)
            if isinstance(result, RealVm):
                object.__setattr__(self, 'vm', result)
                return self
            return result
        return call

    def send_transaction(self, tx):
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            record(tx, result)
        return result


def record(tx, result):
    keys = [str(key) for key in tx.message.account_keys]
    handlers = [HANDLERS.get(bytes(ix.data)[:8]) for ix in tx.message.instructions
                if keys[ix.program_id_index] == PUMP]
    if len(handlers) != 1 or handlers[0] is None:
        return
    stack = []
    for line in result.meta().logs():
        called = re.match(r'Program (\w+) invoke', line)
        if called:
            stack.append(called.group(1))
        elif re.match(r'Program \w+ (success|failed)', line):
            if stack:
                stack.pop()
        elif line.startswith('Program log: ') and stack and stack[-1] == PUMP and LINE.match(line[13:]):
            RECORDED.append((handlers[0], line[13:]))


def harvest(name):
    """One module's fixed cases, as JSON on stdout: the source tests run in one process each."""
    sys.path.insert(0, str(ROOT / 'tests'))
    module = importlib.import_module(name)
    module.LiteSVM = RecordingVm
    fixed = unittest.TestSuite(test for group in unittest.defaultTestLoader.loadTestsFromModule(module)
                               for test in group if test.id().rsplit('.', 1)[1] in FIXED_TESTS)
    outcome = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(fixed)
    print(json.dumps({'ok': outcome.wasSuccessful(), 'ran': outcome.testsRun, 'lines': RECORDED}))


def fields(handler, line):
    match = LINE.match(line)
    for kind in ('thrown', 'account', 'program'):
        if match[kind]:
            return handler, kind, match[kind], match['code']
    return handler, 'occurred', '', match['code']


class ErrorSitesTradesCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        assert hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest() == PUMP_SHA256
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'error-sites-trades-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

        def run(name):
            done = subprocess.run([sys.executable, '-I', '-B', __file__, '--harvest', name], stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, check=True)
            return name, json.loads(done.stdout.splitlines()[-1])
        with ThreadPoolExecutor(len(MODULES)) as pool:
            cls.reports = dict(pool.map(run, MODULES))
        cls.lines = collections.Counter(tuple(item) for report in cls.reports.values() for item in report['lines'])
        source = MODEL_SOURCE.read_text(encoding='utf-8')
        cls.errors = {int(code): (name, message) for code, name, message in
                      re.findall(r'^    \((\d+), "(\w+)", "(.*)"\),$', source, re.M)}
        cls.sites = [(h, k.lower(), p, c) for h, k, p, c in
                     re.findall(r'^    \("(\w+)", Kind::(\w+), "([^"]*)", (\d+)\),$', source, re.M)]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def answers(self, queries):
        text = ''.join('\t'.join(map(str, query)) + '\n' for query in queries)
        result = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True)
        return result.stdout.splitlines()

    def test_source_tests_still_pass(self):
        for name, report in self.reports.items():
            self.assertTrue(report['ok'], name)
            self.assertEqual(report['ran'], 1, name)
            self.assertGreater(len(report['lines']), 20, name)
        self.assertGreater(sum(self.lines.values()), 400)

    def test_every_route_logs_lines(self):
        counts = collections.Counter(handler for handler, _ in self.lines)
        self.assertEqual({route for route in ROUTES if counts[route] == 0}, set())
        self.assertEqual({row[0] for row in self.sites}, set(ROUTES))

    def test_every_recorded_line_is_the_hosted_line(self):
        recorded = sorted(self.lines)
        answers = self.answers([fields(handler, line) for handler, line in recorded])
        wrong = [(handler, line[:80], answer[:80]) for (handler, line), answer in zip(recorded, answers)
                 if line != answer]
        self.assertEqual(wrong[:6], [], f'{len(wrong)} of {len(recorded)} differ')

    def test_every_row_is_reached(self):
        reached = {fields(handler, line) for handler, line in self.lines}
        self.assertEqual(set(self.sites) - reached, set())
        self.assertEqual(reached - set(self.sites), set())

    def test_one_code_keeps_each_site(self):
        by_code = collections.defaultdict(set)
        for handler, line in self.lines:
            row = fields(handler, line)
            if row[1] == 'thrown':
                by_code[row[0], row[3]].add(row[2])
        tracked = collections.defaultdict(set)
        for handler, kind, place, code in self.sites:
            if kind == 'thrown':
                tracked[handler, code].add(place)
        self.assertEqual(by_code, tracked)
        self.assertGreater(sum(len(places) > 1 for places in tracked.values()), 0)

    def test_names_and_messages_match_the_idl(self):
        published = {e['code']: e for e in IDL['errors']}
        for code, (name, message) in self.errors.items():
            if code in published:
                self.assertEqual(name, published[code]['name'])
                if 'msg' in published[code]:
                    self.assertEqual(message, published[code]['msg'] + '.')

    def test_unknown_sites_answer_unknown(self):
        handler, kind, place, code = next(row for row in self.sites if row[1] == 'thrown')
        queries = [(handler, kind, place + '0', code), ('no_such_handler', kind, place, code),
                   (handler, 'account', place, code), (handler, kind, place, 1)]
        self.assertEqual(self.answers(queries), ['unknown'] * 4)


if __name__ == '__main__':
    if sys.argv[1:2] == ['--harvest']:
        harvest(sys.argv[2])
    else:
        unittest.main()
