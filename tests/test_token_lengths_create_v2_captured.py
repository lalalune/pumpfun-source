"""Captured-program checks for the stored length of token accounts and mints
on the `create_v2` route, which `tests/test_token_lengths_captured.py` does
not reach: its replay keeps one base case per outcome class, and the first
`create_v2` cases carry no token account or mint at the standard length.

Every case replays a fixed case of `tests/test_create_v2_captured.py`, on the
captured `evidence/original/pump/deployed.so` under LiteSVM, with the quote
mint or the pre-existing quote ATA in the remaining accounts rewritten to
another length just as the fixture stores it. The run on the standard length
is the twin: `programs/pump/recovered/token_lengths_create_v2_host.rs` says
whether that outcome holds or turns into a given failure. Four base cases are
pinned by their twin: two passing ones (a whitelisted and a listed
Token-2022 quote mint), one that fails 6027 with too few remaining accounts,
and one that fails at the ATA program over a pre-existing quote ATA. Each
base runs on a fresh VM: the fixture's `noexec` cases overwrite the SPL
Token program account inside a shared VM, which changes later SPL twins.
This shows matching behavior on these inputs only; it is not a byte-identity
claim.
"""
from pathlib import Path
import collections
import hashlib
import importlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))

import test_token_lengths_captured as tl

CREATE = importlib.import_module('test_create_v2_captured')
HOST_SOURCE = ROOT / 'programs/pump/recovered/token_lengths_create_v2_host.rs'
TOKEN = tl.TOKEN
T22 = tl.T22
# (quote kind, quote token program, ata_exists, the twin the base must show)
BASES = (
    ('whitelisted', T22, 0, None),
    ('listed', T22, 0, None),
    ('short', TOKEN, 0, 'pump:6027'),
    ('whitelisted', TOKEN, 1, 'AToken:IllegalOwner'),
)


def fresh_twin(item):
    """The outcome of one fixed case on a fresh shared VM."""
    tl.SharedVm.vm = None
    tl.SHAPE.update(key=None)
    tl.SharedVm()
    return tl.run(CREATE, item)


def find_base(quote, program, ata_exists, twin_wanted):
    for item in CREATE.fixed_cases():
        if (item['quote'], item['program'], item['ata_exists'], item['faults']) != (quote, program, ata_exists, ''):
            continue
        if fresh_twin(item) == twin_wanted:
            return item
    raise AssertionError(f'no create_v2 base case: {quote}, ata_exists={ata_exists}, twin={twin_wanted}')


def collect_rows(item):
    """One row per (token account or mint, length), as in the base replay."""
    tl.SharedVm.vm = None
    tl.SHAPE.update(key=None)
    tl.SharedVm()
    twin = tl.run(CREATE, item)
    disc, keys = tl.LOG[-1][0][-1]
    instruction = tl.INS.get(disc)
    assert instruction is not None and instruction['name'] == 'create_v2'
    names = [a['name'] for a in instruction['accounts']]
    seen, first = dict(tl.SEEN), tl.first_ops(tl.LOG[-1][1], tl.LOG[-1][2])
    where = {}
    for index, key in enumerate(keys):
        where.setdefault(key, names[index] if index < len(names) else f'rem{index - len(names)}')
    rows = []
    for key, (kind, owner, stored) in seen.items():
        slot = where.get(key)
        if slot is None or stored != (165 if kind == 'token' else 82) or (instruction['name'], slot) in tl.SKIPPED:
            continue
        for length in tl.LENGTHS:
            for tagged in (False, True) if length > 165 else (False,):
                tl.SHAPE.update(key=key, length=length, tagged=tagged)
                tl.SharedVm()
                result = tl.run(CREATE, item)
                tl.SHAPE.update(key=None)
                rows.append({'module': 'create_v2', 'request': ','.join(map(str, (
                    instruction['name'], slot, kind, 't22' if owner == T22 else 'spl', length, int(tagged),
                    int(twin is None), '-' if key not in first else first[key]))),
                    'program': 't22' if owner == T22 else 'token', 'twin': twin, 'result': result})
    return rows


def replay_bases():
    rows = []
    with mock.patch.object(CREATE, 'LiteSVM', tl.SharedVm):
        for quote, program, ata_exists, twin_wanted in BASES:
            rows += collect_rows(find_base(quote, program, ata_exists, twin_wanted))
    return rows


class TokenLengthsCreateV2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'host'
        subprocess.run(['rustc', '--edition=2021', '-D', 'warnings', '-A', 'dead_code', str(HOST_SOURCE), '-o', str(host)],
                       check=True, capture_output=True)
        cls.rows = replay_bases()
        request = ''.join(r['request'] + '\n' for r in cls.rows)
        cls.answers = subprocess.run([str(host)], input=request, capture_output=True, text=True,
                                     check=True).stdout.splitlines()
        print(f'{len(cls.rows)} cases', file=sys.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_captured_elf_is_pinned(self):
        self.assertEqual(hashlib.sha256(tl.PUMP_ELF.read_bytes()).hexdigest(), tl.ELF_SHA256)

    def test_every_length_matches_the_captured_program(self):
        wrong = [(r['request'], r['twin'], r['result'], a) for r, a in zip(self.rows, self.answers)
                 if r['result'] != tl.expected_text(a, r)]
        self.assertEqual(len(self.rows), len(self.answers))
        self.assertEqual(wrong[:5], [])
        self.assertEqual(len(wrong), 0)

    def test_bases_and_arms_were_reached(self):
        self.assertEqual(len(self.rows), 70)
        self.assertEqual({r['request'].split(',')[1] for r in self.rows}, {'rem0', 'rem1'})
        reached = collections.Counter(self.answers)
        self.assertGreater(reached['pump:6063'], 0)
        self.assertGreater(reached['same'], 0)
        passing = [(r, a) for r, a in zip(self.rows, self.answers) if r['twin'] is None]
        self.assertEqual(len(passing), 28)
        self.assertEqual(collections.Counter(a for _, a in passing),
                         collections.Counter({'pump:6063': 22, 'same': 6}))
        failing = [(r, a) for r, a in zip(self.rows, self.answers) if r['twin'] is not None]
        self.assertEqual(len(failing), 42)
        self.assertTrue(all(a == 'same' for _, a in failing))

    def test_quote_mint_refusal_is_6063_not_invalid_data(self):
        refused = [r for r in self.rows if r['result'] == 'pump:6063']
        self.assertEqual(len(refused), 22)
        self.assertTrue(all(r['request'].split(',')[1] == 'rem0' for r in refused))
        self.assertFalse(any(r['result'] == 'pump:InvalidAccountData' for r in self.rows))


if __name__ == '__main__':
    unittest.main()
