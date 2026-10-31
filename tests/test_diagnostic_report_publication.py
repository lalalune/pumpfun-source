"""Retained ELF inputs exercise the two diagnostic CLIs' report publication."""
import gzip
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest

try:
    import resource
except ImportError:
    resource = None

ROOT = Path(__file__).resolve().parents[1]
H = ROOT / 'reconstruction/harness'


class DiagnosticPublicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            'control_flow': (
                (ROOT / 'evidence/original/pump/deployed.so').read_bytes(),
                ['--start', '288', '--size', '176']),
            'target_metric': (
                gzip.decompress((ROOT / 'research/pump-multihop-sell-fees-20261029/build/candidate/symbols.so.gz').read_bytes()),
                ['288', '--sym', 'h005e9f4277ff6fadE$']),
        }

    def invoke(self, tool, image, output, options, **kwargs):
        return subprocess.run([sys.executable, '-B', str(H / f'{tool}.py'),
                               str(image), *options, '--json', str(output)],
                              capture_output=True, text=True, **kwargs)

    @unittest.skipUnless(resource is not None and hasattr(resource, 'RLIMIT_FSIZE'),
                         'requires POSIX file-size limits')
    def test_failed_write_leaves_no_report_and_same_command_can_retry(self):
        def limited():
            signal.signal(signal.SIGXFSZ, signal.SIG_IGN)
            resource.setrlimit(resource.RLIMIT_FSIZE, (64, 64))

        for tool, (blob, options) in self.cases.items():
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image = root / 'input.so'
                image.write_bytes(blob)
                output = root / 'nested' / 'report.json'
                failed = self.invoke(tool, image, output, options, preexec_fn=limited)
                self.assertEqual(failed.returncode, 2, failed.stderr)
                self.assertIn('cannot create diagnostic report:', failed.stderr)
                self.assertEqual(failed.stdout, '')
                self.assertEqual(list(output.parent.iterdir()), [])
                retry = self.invoke(tool, image, output, options)
                self.assertEqual(retry.returncode, 0, retry.stderr)
                self.assertTrue(json.loads(output.read_text(encoding='utf-8')))
                self.assertEqual(list(output.parent.iterdir()), [output])
                self.assertEqual(image.read_bytes(), blob)

    def test_existing_outputs_and_image_aliases_remain_unchanged(self):
        for tool, (blob, options) in self.cases.items():
            with self.subTest(tool=tool), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                image, output = root / 'input.so', root / 'report.json'
                image.write_bytes(blob)
                prior = b'{"previous": "complete"}\n'
                output.write_bytes(prior)
                for destination in (image, output):
                    result = self.invoke(tool, image, destination, options)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertEqual(image.read_bytes(), blob)
                    self.assertEqual(output.read_bytes(), prior)
                    self.assertEqual(set(root.iterdir()), {image, output})


if __name__ == '__main__':
    unittest.main()
