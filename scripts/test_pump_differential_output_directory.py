"""A directory --output must fail at admission, not after every case has run."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pump_differential_output import PumpReport


class ReportDirectoryOutputTests(unittest.TestCase):
    def test_directory_output_is_refused_before_the_run(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'reports'
            output.mkdir()
            (output / 'kept.json').write_bytes(b'prior report')
            with self.assertRaisesRegex(IsADirectoryError, 'report output is a directory'):
                PumpReport(output, root, None, __file__)
            self.assertEqual((output / 'kept.json').read_bytes(), b'prior report')

    def test_directory_appearing_during_the_run_is_refused_without_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'report.json'
            report = PumpReport(output, root, None, __file__)
            output.mkdir()
            with self.assertRaisesRegex(IsADirectoryError, 'report output is a directory'):
                report.write(b'complete receipt')
            self.assertEqual(sorted(path.name for path in root.iterdir()), ['report.json'])

    def test_file_output_keeps_replacement_semantics(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'report.json'
            output.write_bytes(b'prior report')
            PumpReport(output, root, None, __file__).write(b'complete receipt')
            self.assertEqual(output.read_bytes(), b'complete receipt')


if __name__ == '__main__':
    unittest.main()
