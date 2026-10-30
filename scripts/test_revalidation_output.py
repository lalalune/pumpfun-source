"""Exercise fresh audit output admission through the real revalidation CLI."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]


class RevalidationOutputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(REPO / 'scripts/revalidate_all.py',
                        self.root / 'scripts/revalidate_all.py')
        self.packet = self.root / 'research/retained-idl'
        self.packet.mkdir(parents=True)
        self.source = (REPO / 'evidence/upstream/pump.json').read_bytes()
        (self.packet / 'pump.json').write_bytes(self.source)
        (self.packet / 'manifest.json').write_text(json.dumps({
            'pump.json': hashlib.sha256(self.source).hexdigest(),
        }), encoding='utf-8')

    def run_audit(self, output):
        return subprocess.run(
            [sys.executable, '-B', str(self.root / 'scripts/revalidate_all.py'),
             '--output', str(output)],
            cwd=self.root, capture_output=True, encoding='utf-8',
        )

    def test_output_under_research_is_not_counted_as_an_input_packet(self):
        output = self.root / 'research/new-audit'
        result = self.run_audit(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((output / 'results.json').read_text(encoding='utf-8'))
        self.assertEqual([row['packet'] for row in rows], ['retained-idl'])
        summary = json.loads((output / 'summary.json').read_text(encoding='utf-8'))
        self.assertEqual((summary['total_packets'], summary['pass'],
                          summary['skip_or_inconclusive']), (1, 1, 0))

    def test_existing_output_is_preserved_before_any_verifier_runs(self):
        output = self.root / 'prior-audit'
        output.mkdir()
        prior = {'results.json': b'previous sealed results\n',
                 'README.md': b'previous report\n'}
        for name, raw in prior.items():
            (output / name).write_bytes(raw)
        marker = self.root / 'verifier-ran'
        (self.packet / 'verify.py').write_text(
            'from pathlib import Path\n'
            f'Path({str(marker)!r}).write_text("ran", encoding="utf-8")\n',
            encoding='utf-8',
        )
        result = self.run_audit(output)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(marker.exists(), 'output admission must precede packet execution')
        self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, prior)
        self.assertEqual((self.packet / 'pump.json').read_bytes(), self.source)

    def test_fresh_external_report_remains_self_verifiable(self):
        output = self.root / 'reports/audit'
        result = self.run_audit(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        verified = subprocess.run([sys.executable, '-B', str(output / 'verify.py')],
                                  capture_output=True, encoding='utf-8')
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual((self.packet / 'pump.json').read_bytes(), self.source)


if __name__ == '__main__':
    unittest.main()
