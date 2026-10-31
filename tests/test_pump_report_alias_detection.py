"""Alias detection for report publication, including case-insensitive volumes."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_differential_output as publication


class ReportAliasTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.inputs = self.root / 'inputs'
        self.inputs.mkdir()
        self.input = self.inputs / 'Cargo.toml'
        self.input.write_text('[package]\n')

    def report(self, output):
        return publication.PumpReport(output, self.root, None, Path(__file__), extra_inputs=[self.inputs])

    def test_case_variant_path_inside_a_bound_directory_is_rejected(self):
        variant = self.root / 'INPUTS' / 'CARGO.TOML'
        if not variant.exists():
            self.skipTest('filesystem is case-sensitive')
        with self.assertRaisesRegex(ValueError, 'report output aliases an input'):
            self.report(variant)

    def test_new_file_inside_a_bound_directory_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'report output aliases an input'):
            self.report(self.inputs / 'report.json')

    def test_unrelated_report_is_accepted(self):
        report = self.report(self.root / 'reports' / 'report.json')
        self.assertEqual(report.output, self.root / 'reports' / 'report.json')

    def test_directory_input_is_compared_by_entry(self):
        # A directory input has no regular file to compare, so the check must
        # not be restricted to is_file(); this is the branch a differently-cased
        # spelling of the bound directory takes on a case-insensitive volume.
        with patch.object(Path, 'samefile', lambda self, other: True):
            self.assertTrue(publication.aliases(self.root / 'report.json', self.inputs))

    def test_unrelated_path_is_not_an_alias(self):
        self.assertFalse(publication.aliases(self.root / 'report.json', self.inputs))

    def test_absent_bound_file_is_still_protected(self):
        absent = self.root / 'not-yet-created.json'
        with self.assertRaisesRegex(ValueError, 'report output aliases an input'):
            publication.PumpReport(absent, self.root, None, __file__, extra_inputs=[absent])

    def test_absent_bound_directory_descendant_is_protected(self):
        absent = self.root / 'not-yet-created-inputs'
        with self.assertRaisesRegex(ValueError, 'report output aliases an input'):
            publication.PumpReport(absent / 'report.json', self.root, None, __file__, extra_inputs=[absent])


if __name__ == '__main__':
    unittest.main()
