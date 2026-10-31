"""Real filesystem aliases must not bypass source/output separation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from experiment_runner import separate_trees


class PhysicalOverlapTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='experiment-tree-alias-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.source = self.root / 'CaseSource'
        self.source.mkdir()
        (self.source / 'input.txt').write_bytes(b'retained source\n')
        self.alias = self.root / 'casesource'

    def require_case_alias(self):
        if not self.alias.exists() or not self.alias.samefile(self.source):
            self.skipTest('requires a case-insensitive filesystem')

    def test_matrix_rejects_alias_before_writing_inside_source(self):
        self.require_case_alias()
        matrix = self.root / 'matrix.json'
        matrix.write_text(json.dumps([{
            'name': 'trial', 'source': str(self.source),
            'command': [sys.executable, '-c',
                        'import pathlib,sys;pathlib.Path(sys.argv[1]).write_text("ran")',
                        '{out}/marker.txt'],
        }]), encoding='utf-8')
        # target is excluded from source copies, keeping the base failure
        # bounded instead of recursively copying its own attempt directory.
        result = subprocess.run([
            sys.executable, '-B', str(Path(__file__).with_name('experiment_runner.py')),
            str(matrix), '--out', str(self.alias / 'target')],
            text=True, capture_output=True, timeout=15)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn('separate trees', result.stderr)
        self.assertEqual(list(self.source.iterdir()), [self.source / 'input.txt'])

    def test_existing_alias_and_both_ancestor_directions_are_rejected(self):
        self.require_case_alias()
        (self.source / 'nested').mkdir()
        for source, destination in ((self.source, self.alias),
                                    (self.source, self.alias / 'new/output'),
                                    (self.source / 'nested', self.alias)):
            with self.subTest(source=source, destination=destination):
                with self.assertRaisesRegex(ValueError, 'separate trees'):
                    separate_trees(source, destination)

    def test_distinct_directories_remain_admitted(self):
        other = self.root / 'other'
        other.mkdir()
        self.assertEqual(separate_trees(self.source, other / 'new'),
                         (self.source, other / 'new'))
        if not self.alias.exists():
            # Case-sensitive volumes can contain two distinct such names.
            self.alias.mkdir()
            self.assertEqual(separate_trees(self.source, self.alias),
                             (self.source, self.alias))


if __name__ == '__main__':
    unittest.main()
