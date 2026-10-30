# Regression cases retained from wallaceplayfrog PR #1285, commit 9c44b70.
#!/usr/bin/env python3
"""Exercise original-window reads with the real captured ELF and inventory."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('window_score', Path(__file__).with_name('score.py'))
score = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(score)


class OriginalWindowInputs(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='pump-score-inputs-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.previous_base = score.BASE
        score.BASE = self.base
        self.addCleanup(setattr, score, 'BASE', self.previous_base)
        self.image = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        (self.base / 'original.so').write_bytes(self.image)
        with (ROOT / 'reconstruction/base/functions.tsv').open() as source:
            reader = csv.DictReader(source, delimiter='\t')
            self.fields = reader.fieldnames
            self.rows = [row for row in reader if row['program'] == 'pump' and row['variant'] == 'selected']

    def inventory(self, rows):
        with (self.base / 'functions.tsv').open('w', newline='') as output:
            writer = csv.DictWriter(output, self.fields, delimiter='\t')
            writer.writeheader()
            writer.writerows(rows)

    def test_inventory_change_is_visible_after_an_earlier_read(self):
        self.inventory(self.rows[:1])
        first = score.original_windows()
        self.assertEqual(len(first), 1)
        self.inventory(self.rows[:2])
        second = score.original_windows()
        self.assertEqual([row['start'] for row in second], [int(row['original_start']) for row in self.rows[:2]])
        self.assertEqual(second[0], first[0])

    def test_original_bytes_change_is_visible_after_an_earlier_read(self):
        self.inventory(self.rows[:1])
        before = score.original_windows()[0]
        section = score.sections(self.image)['.text']
        offset = before['start'] - section['addr'] + section['offset']
        changed = bytearray(self.image)
        changed[offset + 2] ^= 1  # Change an instruction offset, never an ELF header.
        (self.base / 'original.so').write_bytes(changed)
        after = score.original_windows()[0]
        self.assertNotEqual(after['raw'], before['raw'])
        self.assertNotEqual(after['norm'], before['norm'])
        self.assertEqual(after['raw'], bytes(changed[offset:offset + before['bytes']]))


if __name__ == '__main__':
    unittest.main()
