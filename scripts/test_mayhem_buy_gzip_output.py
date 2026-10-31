"""A .gz Mayhem buy report must be real gzip, because its verifier decodes by suffix."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'
ORIGINAL = ROOT / 'evidence/original/mayhem/deployed.so'


def run(script, *arguments):
    environment = dict(os.environ)
    environment.pop('PYTHONOPTIMIZE', None)
    return subprocess.run([sys.executable, '-B', str(SCRIPTS / script), *map(str, arguments)],
                          cwd=ROOT, env=environment, capture_output=True, text=True, timeout=180)


class MayhemBuyGzipOutputTests(unittest.TestCase):
    def differential(self, directory, name):
        cases = directory / 'cases.json'
        cases.write_text(json.dumps({'cases': [{'name': 'paused', 'paused': 1}]}), encoding='utf-8')
        output = directory / name
        result = run('mayhem_buy_differential.py', '--candidate', ORIGINAL, '--output', output,
                     '--cases', cases)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        return output

    def test_gz_report_is_compressed_and_reaches_the_verifier(self):
        with tempfile.TemporaryDirectory(prefix='mayhem-buy-gzip-') as directory:
            directory = Path(directory)
            output = self.differential(directory, 'report.json.gz')
            raw = output.read_bytes()
            self.assertEqual(raw[:2], b'\x1f\x8b', 'report.json.gz is not gzip')
            self.assertEqual(raw[4:8], bytes(4), 'gzip mtime must stay reproducible')
            self.assertEqual(json.loads(gzip.decompress(raw))['case_count'], 1)
            verified = directory / 'verified.json'
            result = run('verify_mayhem_buy.py', '--receipts', output, '--candidate', ORIGINAL,
                         '--output', verified)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
            self.assertEqual(json.loads(verified.read_bytes())['verified_signed_transactions'], 2)

    def test_plain_report_stays_plain_json(self):
        with tempfile.TemporaryDirectory(prefix='mayhem-buy-plain-') as directory:
            output = self.differential(Path(directory), 'report.json')
            self.assertEqual(json.loads(output.read_bytes())['case_count'], 1)


if __name__ == '__main__':
    unittest.main()
