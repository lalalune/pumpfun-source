#!/usr/bin/env python3
"""A migrate_v2 length case must load an account of exactly that length."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_migrate_v2_probe as probe


def loaded_bytes(name, length):
    result = probe.run({'boost': True, 'mutations': {name: {'length': length}}})
    return len(bytes.fromhex(result['before'][result['names'][name]]['data']))


class LengthMutationTests(unittest.TestCase):
    def test_longer_accounts_are_zero_extended(self):
        # The oversized lengths named by pump_migrate_v2_differential.py.
        for name, length in (('bonding_curve', 200), ('base_mint', 165),
                             ('associated_base_bonding_curve', 200)):
            with self.subTest(name=name, length=length):
                self.assertEqual(loaded_bytes(name, length), length)

    def test_shorter_accounts_are_still_truncated(self):
        self.assertEqual(loaded_bytes('base_mint', 64), 64)


if __name__ == '__main__':
    unittest.main()
