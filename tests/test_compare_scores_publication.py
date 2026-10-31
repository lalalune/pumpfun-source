"""Actual saved-score CLI publication with retained 1,035-window reports."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import resource
except ImportError:
    resource = None


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / 'reconstruction/harness/compare_scores.py'
BASELINE = ROOT / 'reconstruction/pump-main/baseline/score.json'
CANDIDATE = ROOT / 'reconstruction/pump-main/baseline/rescore.json'


class ComparisonPublicationTests(unittest.TestCase):
    def invoke(self, baseline, candidate, output, **kwargs):
        return subprocess.run(
            [sys.executable, '-B', str(CLI), str(baseline), str(candidate),
             '--json', str(output)], capture_output=True, text=True, **kwargs)

    @unittest.skipUnless(resource is not None and hasattr(resource, 'RLIMIT_FSIZE'),
                         'requires POSIX file-size limits')
    def test_failed_write_leaves_no_report_and_same_command_can_retry(self):
        def limited():
            signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
            resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'nested' / 'report.json'
            before = [path.read_bytes() for path in (BASELINE, CANDIDATE)]
            result = self.invoke(BASELINE, CANDIDATE, output, preexec_fn=limited)
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertIn('cannot create comparison report:', result.stderr)
            self.assertEqual(result.stdout, '')
            self.assertEqual(list(output.parent.iterdir()), [])
            retry = self.invoke(BASELINE, CANDIDATE, output)
            self.assertEqual(retry.returncode, 0, retry.stderr)
            self.assertEqual(output.read_text(encoding='utf-8'), retry.stdout)
            self.assertTrue(json.loads(retry.stdout)['accepted'])
            self.assertEqual(list(output.parent.iterdir()), [output])
            self.assertEqual([path.read_bytes() for path in (BASELINE, CANDIDATE)], before)

    def test_existing_reports_and_input_destinations_remain_unchanged(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            baseline, candidate, report = [root / name for name in
                                            ('baseline.json', 'candidate.json', 'report.json')]
            baseline.write_bytes(BASELINE.read_bytes())
            candidate.write_bytes(CANDIDATE.read_bytes())
            report.write_bytes(b'{"previous": "complete"}\n')
            before = {path: path.read_bytes() for path in (baseline, candidate, report)}
            for output in before:
                with self.subTest(output=output.name):
                    result = self.invoke(baseline, candidate, output)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual({path: path.read_bytes() for path in before}, before)
                    self.assertEqual(set(root.iterdir()), set(before))

    @unittest.skipUnless(os.name == 'posix', 'POSIX exclusive-link publication control')
    def test_destination_created_during_publication_is_preserved(self):
        spec = importlib.util.spec_from_file_location('comparison_publication', CLI)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original_link = os.link
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'report.json'

            def competing_writer(source, destination):
                output.write_bytes(b'concurrent complete report\n')
                return original_link(source, destination)

            with patch.object(module.os, 'link', side_effect=competing_writer):
                with self.assertRaises(FileExistsError):
                    module.publish_report(output, '{"accepted": true}\n')
            self.assertEqual(output.read_bytes(), b'concurrent complete report\n')
            self.assertEqual(list(root.iterdir()), [output])


if __name__ == '__main__':
    unittest.main()
