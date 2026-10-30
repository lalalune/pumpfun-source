import json
from pathlib import Path
import tempfile
import unittest
from compare_scores import load_report


class OverlappingWindowsTests(unittest.TestCase):
    def load(self, windows):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.json'
            path.write_text(json.dumps({'windows': windows}), encoding='utf-8')
            return load_report(path)

    def test_overlapping_object_and_inventory_ranges_are_rejected(self):
        rows = {'16': {'bytes': 24, 'normalized': True, 'raw': True},
                '24': {'bytes': 8, 'normalized': True, 'raw': True}}
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.load(rows)
        inventory = [dict(start=int(k), bytes=v['bytes'], normalized_matches=['symbol'], raw_match=True)
                     for k, v in rows.items()]
        with self.assertRaisesRegex(ValueError, 'overlapping'):
            self.load(inventory)

    def test_adjacent_gapped_and_unsorted_ranges_remain_valid(self):
        rows = {str(k): {'bytes': 8, 'normalized': False, 'raw': False} for k in (40, 16, 24)}
        self.assertEqual(set(self.load(rows)), {16, 24, 40})


if __name__ == '__main__': unittest.main()
