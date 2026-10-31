"""Captured-program checks for the stored length of the three slots
`tests/test_token_lengths_captured.py` leaves out, because a route decides
how each is read: `creator_vault_quote_token_account` on
`distribute_creator_fees_v2`, `user_pool_token_account` on `migrate`, and
`buyback_fee_recipient` on `multi_hop_curve_swap`.

Every case replays a fixed case of the captured test that takes the route
(`test_creator_fee_distribution_quote_captured`, `test_migrate_captured`,
`test_multi_hop_route_captured`), on the captured
`evidence/original/pump/deployed.so` under LiteSVM, with the one slot's
account rewritten to another length just as the fixture stores it. The run
on the standard length is the twin:
`programs/pump/recovered/token_lengths_skipped_slots_host.rs` says whether
that outcome holds or turns into a given failure. Per slot, the first
passing case and the first case failing with a handler error (6000 and up)
are the bases, in the base replay's own order. This shows matching behavior
on these inputs only; it is not a byte-identity claim.
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

HOST_SOURCE = ROOT / 'programs/pump/recovered/token_lengths_skipped_slots_host.rs'
JOBS = (
    ('test_creator_fee_distribution_quote_captured', 'distribute_creator_fees_v2', 'creator_vault_quote_token_account'),
    ('test_migrate_captured', 'migrate', 'user_pool_token_account'),
    ('test_multi_hop_route_captured', 'multi_hop_curve_swap', 'buyback_fee_recipient'),
)


def twin_class(twin):
    if twin is None:
        return 'pass'
    tail = twin.split(':')[-1]
    return 'fail' if tail.isdigit() and int(tail) >= 6000 else 'other'


def find_target(want_ix, want_slot):
    """The stored account the twin run names `want_slot` on `want_ix`."""
    target = None
    for slots, result, keys in tl.LOG:
        for disc, ks in slots:
            instruction = tl.INS.get(disc)
            if instruction is None or instruction['name'] != want_ix:
                continue
            names = [a['name'] for a in instruction['accounts']]
            where = {}
            for index, key in enumerate(ks):
                where.setdefault(key, names[index] if index < len(names) else f'rem{index - len(names)}')
            for key, (kind, owner, stored) in tl.SEEN.items():
                if where.get(key) == want_slot and stored == (165 if kind == 'token' else 82):
                    target = (key, kind, owner, tl.first_ops(result, keys))
    return target


def collect_module(module_name, want_ix, want_slot):
    module = importlib.import_module(module_name)
    tl.SharedVm.vm = None
    rows, picked = [], set()
    with mock.patch.object(module, 'LiteSVM', tl.SharedVm):
        for item in module.fixed_cases():
            if len(picked) == 2:
                break
            item = item[1] if isinstance(item, tuple) and len(item) == 2 and isinstance(item[0], str) else item
            tl.SHAPE.update(key=None)
            tl.SharedVm()
            twin = tl.run(module, item)
            if not tl.LOG or not tl.LOG[-1][0]:
                continue
            target = find_target(want_ix, want_slot)
            cls = twin_class(twin)
            if target is None or cls == 'other' or cls in picked:
                continue
            picked.add(cls)
            key, kind, owner, first = target
            for length in tl.LENGTHS:
                for tagged in (False, True) if length > 165 else (False,):
                    tl.SHAPE.update(key=key, length=length, tagged=tagged)
                    tl.SharedVm()
                    result = tl.run(module, item)
                    tl.SHAPE.update(key=None)
                    rows.append({'module': module_name, 'request': ','.join(map(str, (
                        want_ix, want_slot, kind, 't22' if owner == tl.T22 else 'spl', length, int(tagged),
                        int(twin is None), '-' if key not in first else first[key]))),
                        'program': 't22' if owner == tl.T22 else 'token', 'twin': twin, 'result': result})
    if len(picked) != 2:
        raise AssertionError(f'{module_name}: bases picked: {picked}')
    return rows


def replay_all():
    return [row for job in JOBS for row in collect_module(*job)]


class TokenLengthsSkippedSlots(unittest.TestCase):
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
        self.assertEqual(hashlib.sha256(tl.PUMP_ELF.read_bytes()).hexdigest(), tl.ELF_SHA256)

    def test_every_length_matches_the_captured_program(self):
        wrong = [(r['request'], r['twin'], r['result'], a) for r, a in zip(self.rows, self.answers)
                 if r['result'] != tl.expected_text(a, r)]
        self.assertEqual(len(self.rows), len(self.answers))
        self.assertEqual(wrong[:5], [])
        self.assertEqual(len(wrong), 0)

    def test_each_slot_reads_its_own_way(self):
        self.assertEqual(len(self.rows), 84)
        reached = collections.Counter(self.answers)
        for answer in ('same', 'pump:data', 'token:data'):
            self.assertGreater(reached[answer], 0, answer)
        groups = {}
        for row in self.rows:
            f = row['request'].split(',')
            groups.setdefault((f[0], row['twin']), collections.Counter())[row['result']] += 1
        self.assertEqual(groups[('distribute_creator_fees_v2', None)],
                         collections.Counter({None: 1, 'pump:InvalidAccountData': 11, 'token:InvalidAccountData': 2}))
        self.assertEqual(groups[('distribute_creator_fees_v2', 'pump:6024')],
                         collections.Counter({'pump:6024': 3, 'pump:InvalidAccountData': 11}))
        self.assertEqual(groups[('migrate', None)],
                         collections.Counter({None: 3, 'pump:InvalidAccountData': 11}))
        self.assertEqual(groups[('migrate', 'pump:6000')], collections.Counter({'pump:6000': 14}))
        self.assertEqual(groups[('multi_hop_curve_swap', None)], collections.Counter({None: 14}))
        self.assertEqual(groups[('multi_hop_curve_swap', 'pump:6004')],
                         collections.Counter({'pump:6004': 3, 'pump:InvalidAccountData': 11}))


if __name__ == '__main__':
    unittest.main()
