import json
import tempfile
import unittest
from pathlib import Path

from probe_report import write_json_report


class NonfiniteProbeReportTests(unittest.TestCase):
    def test_nonfinite_values_are_rejected_and_prior_report_kept(self):
        for bad in (float('nan'), float('inf'), float('-inf')):
            with self.subTest(bad), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'report.json'
                write_json_report(path, {'ok': 1})
                with self.assertRaises(ValueError):
                    write_json_report(path, {'median_seconds': bad})
                self.assertEqual(json.loads(path.read_text()), {'ok': 1})
                self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['report.json'])

    def test_finite_floats_still_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'report.json'
            write_json_report(path, {'median_seconds': 0.5})
            self.assertEqual(json.loads(path.read_text()), {'median_seconds': 0.5})


if __name__ == '__main__':
    unittest.main()
