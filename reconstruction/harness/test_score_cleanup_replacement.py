from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import score


class ReportStagingOwnership(unittest.TestCase):
    def test_recreated_staging_name_survives_successful_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / 'report.json'
            replace = Path.replace
            observed = []
            def recreate(source, target):
                result = replace(source, target)
                source.write_bytes(b'another writer')
                observed.append(source)
                return result
            with patch.object(Path, 'replace', recreate):
                score.write_report(report, 'published\n')
            self.assertEqual(report.read_bytes(), b'published\n')
            self.assertEqual(observed[0].read_bytes(), b'another writer')

    def test_replaced_staging_name_survives_failed_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report = root / 'report.json'
            report.write_bytes(b'prior')
            moved = root / 'retained-staging'
            observed = []
            def replace_with_other(source, target):
                source.rename(moved)
                source.write_bytes(b'another writer')
                observed.append(source)
                raise OSError('publication failed')
            with patch.object(Path, 'replace', replace_with_other):
                with self.assertRaisesRegex(OSError, 'publication failed'):
                    score.write_report(report, 'new')
            self.assertEqual(report.read_bytes(), b'prior')
            self.assertEqual(moved.read_bytes(), b'new')
            self.assertEqual(observed[0].read_bytes(), b'another writer')


if __name__ == '__main__': unittest.main()
