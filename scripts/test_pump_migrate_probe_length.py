#!/usr/bin/env python3
"""A migrate probe length case must load the account at the requested size."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_migrate_probe as probe


def loaded_length(name, length):
    case = {'boost': True, 'mutations': {name: {'length': length}}}
    row = probe.run(case)
    return len(bytes.fromhex(row['before'][row['names'][name]]['data']))


class MigrateProbeLengthTests(unittest.TestCase):
    def test_longer_accounts_are_zero_extended(self):
        for name, length in (('bonding_curve', 200), ('mint', 165),
                             ('associated_bonding_curve', 200)):
            with self.subTest(name=name, length=length):
                self.assertEqual(loaded_length(name, length), length)

    def test_shorter_lengths_still_truncate(self):
        self.assertEqual(loaded_length('mint', 64), 64)


if __name__ == '__main__':
    unittest.main()
