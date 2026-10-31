"""Captured-program checks for handler-read precedence over handler errors.

`tests/test_token_lengths_captured.py` replays only twins that succeed or
fail with a Pump custom error of 6000 or more, and its model leaves open
whether a handler read comes before every handler error. This test drops
that filter: it replays fixed cases of the captured tests whose instructions
open token accounts in the handler, keeps twins with every outcome the
fixtures produce -- Anchor errors, CPI-surfaced errors, token-program
errors, the Pump Fees program, panics, runtime failures -- and reshapes
each handler-opened token account to lengths the Pump decoder refuses.
`programs/pump/recovered/token_lengths_precedence_host.rs` says whether
the twin outcome stands or the decoder's `InvalidAccountData` replaces it.
This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import collections
import hashlib
import importlib
import json
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_token_lengths_captured as base

SharedVm = base.SharedVm
PUMP_ELF = base.PUMP_ELF
ELF_SHA256 = base.ELF_SHA256
HOST_SOURCE = ROOT / 'programs/pump/recovered/token_lengths_precedence_host.rs'
MODEL_SOURCE = ROOT / 'programs/pump/recovered/token_lengths.rs'
MODULES = ('v2_token_quote', 'v3_trade_accounting', 'v3_exact_quote', 'migrate_v2', 'multi_hop_hop')
# Stored lengths the Pump decoder refuses for a token account: short,
# one short of tagged, tagged but under the decoder's 167, untagged long.
BAD = [(0, False), (83, False), (164, False), (166, False), (166, True), (167, False), (200, False)]
# Twin outcomes the base replay filtered out, all required to be reached.
NEW_ERRORS = {'pump:2000', 'pump:2006', 'pump:2012', 'pump:3012', 'pump:4102', 'token:1', 't22:1',
              'panic', 'fees', 'rent', 'pump:BorshIoError', 'pump:ArithmeticOverflow', '111111:1'}

HANDLER = collections.defaultdict(set)
for _m in re.finditer(r'\("([a-z0-9_]+)", ([^)]+)\) => Read::Handler', MODEL_SOURCE.read_text()):
    for _s in re.findall(r'"([a-z0-9_]+)"', _m.group(2)):
        HANDLER[_m.group(1)].add(_s)


def twin_key(twin):
    if twin is None:
        return 'ok'
    if twin == 'panic':
        return 'panic'
    if 'TransactionErrorInsufficientFundsForRent' in twin:
        return 'rent'
    if twin.startswith('pfeeUx'):
        return 'fees'
    return twin


def same_outcome(result, twin):
    if result == twin:
        return True
    return (result is not None and twin is not None
            and 'TransactionErrorInsufficientFundsForRent' in result
            and 'TransactionErrorInsufficientFundsForRent' in twin)


def replay(name):
    """One row per (base case, handler-opened token account, refused length),
    keeping up to two base cases per (instruction, twin outcome)."""
    SharedVm.vm = None
    module = importlib.import_module(f'test_{name}_captured')
    rows, chosen = [], collections.Counter()
    with mock.patch.object(module, 'LiteSVM', SharedVm):
        for item in module.fixed_cases():
            item = item[1] if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) else item
            base.SHAPE.update(key=None)
            SharedVm()
            twin = base.run(module, item)
            if twin == 'unsent' or not base.LOG or not base.LOG[-1][0]:
                continue
            disc, keys = base.LOG[-1][0][-1]
            instruction = base.INS.get(disc)
            if instruction is None:
                continue
            iname = instruction['name']
            if iname not in HANDLER:
                continue
            if chosen[(iname, twin)] >= 2:
                continue
            chosen[(iname, twin)] += 1
            names = [a['name'] for a in instruction['accounts']]
            seen = dict(base.SEEN)
            where = {}
            for index, key in enumerate(keys):
                where.setdefault(key, names[index] if index < len(names) else f'rem{index - len(names)}')
            targets = [(key, where[key]) for key, (kind, owner, stored) in seen.items()
                       if where.get(key) in HANDLER[iname] and stored == 165 and kind == 'token']
            for key, slot in targets:
                for length, tagged in BAD:
                    base.SHAPE.update(key=key, length=length, tagged=tagged)
                    SharedVm()
                    result = base.run(module, item)
                    base.SHAPE.update(key=None)
                    rows.append({'module': name, 'request': f'{iname},{slot},{twin_key(twin)}',
                                 'twin': twin, 'result': result})
    return rows


def replay_all():
    def one(name):
        done = subprocess.run([sys.executable, '-I', '-B', __file__, '--replay', name], capture_output=True, text=True,
                              check=True, timeout=900)
        return json.loads(done.stdout.splitlines()[-1])
    with ThreadPoolExecutor(5) as pool:
        return [row for rows in pool.map(one, MODULES) for row in rows]


class TokenLengthsPrecedence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'host'
        subprocess.run(['rustc', '--edition=2021', '-D', 'warnings', '-A', 'dead_code', str(HOST_SOURCE), '-o', str(host)],
                       check=True, capture_output=True)
        cls.rows = replay_all()
        request = ''.join(r['request'] + '\n' for r in cls.rows)
        cls.answers = subprocess.run([str(host)], input=request, capture_output=True, text=True,
                                     check=True).stdout.splitlines()
        print(f'{len(cls.rows)} cases', file=sys.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_captured_elf_is_pinned(self):
        self.assertEqual(hashlib.sha256(PUMP_ELF.read_bytes()).hexdigest(), ELF_SHA256)

    def test_every_row_matches_the_model(self):
        self.assertEqual(len(self.rows), len(self.answers))
        wrong = []
        for row, answer in zip(self.rows, self.answers):
            if answer == 'preempts':
                ok = row['result'] == 'pump:InvalidAccountData'
            elif answer == 'stands':
                ok = same_outcome(row['result'], row['twin'])
            else:
                ok = row['result'] == 'pump:InvalidAccountData' or same_outcome(row['result'], row['twin'])
            if not ok:
                wrong.append((row['request'], row['twin'], row['result'], answer))
        self.assertEqual(wrong[:5], [])
        self.assertEqual(len(wrong), 0)

    def test_the_full_error_set_was_reached(self):
        self.assertGreaterEqual(len(self.rows), 3000)
        keys = {r['request'].split(',', 2)[2] for r in self.rows}
        self.assertTrue(NEW_ERRORS <= keys, NEW_ERRORS - keys)
        reached = collections.Counter(self.answers)
        for answer in ('stands', 'preempts', 'unconfirmed'):
            self.assertGreater(reached[answer], 0, answer)
        split = collections.Counter(
            'data' if r['result'] == 'pump:InvalidAccountData' else 'stood'
            for r, a in zip(self.rows, self.answers) if a == 'unconfirmed')
        self.assertGreater(split['data'], 0)
        self.assertGreater(split['stood'], 0)

    def test_every_handler_instruction_was_reached(self):
        self.assertEqual({r['request'].split(',')[0] for r in self.rows}, set(HANDLER))


if __name__ == '__main__':
    if sys.argv[1:2] == ['--replay']:
        print(json.dumps(replay(sys.argv[2])))
    else:
        unittest.main()
