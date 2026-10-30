"""Exercise fresh audit output admission through the real revalidation CLI."""
import hashlib
import json
import os
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

    def test_manifest_paths_cannot_escape_the_packet(self):
        outside = self.packet.parent / 'outside.txt'
        outside.write_bytes(b'outside\n')
        digest = hashlib.sha256(outside.read_bytes()).hexdigest()
        cases = {
            'parent': '../outside.txt',
            'absolute': str(outside),
            'backslash': r'..\outside.txt',
        }
        for name, manifest_path in cases.items():
            with self.subTest(name=name):
                (self.packet / 'manifest.json').write_text(json.dumps({
                    manifest_path: digest,
                }), encoding='utf-8')
                output = self.root / ('audit-' + name)
                result = self.run_audit(output)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                row = json.loads((output / 'results.json').read_text(encoding='utf-8'))[0]
                self.assertEqual(row['manifest_check']['status'], 'fail')
                self.assertEqual(row['manifest_check']['errors'], ['unsafe_path: ' + manifest_path])
                self.assertEqual(row['overall'], 'fail')

    def test_manifest_files_and_ancestors_cannot_be_links(self):
        outside_file = self.root / 'outside.txt'
        outside_file.write_bytes(b'outside\n')
        outside_dir = self.root / 'outside'
        outside_dir.mkdir()
        (outside_dir / 'nested.txt').write_bytes(b'nested\n')
        try:
            os.symlink(outside_file, self.packet / 'alias.txt')
            os.symlink(outside_dir, self.packet / 'nested', target_is_directory=True)
        except (OSError, NotImplementedError, AttributeError) as error:
            self.skipTest(f'creating links is not permitted: {error}')
        (self.packet / 'manifest.json').write_text(json.dumps({
            'alias.txt': hashlib.sha256(outside_file.read_bytes()).hexdigest(),
            'nested/nested.txt': hashlib.sha256(
                (outside_dir / 'nested.txt').read_bytes()).hexdigest(),
        }), encoding='utf-8')
        output = self.root / 'audit-links'
        result = self.run_audit(output)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        row = json.loads((output / 'results.json').read_text(encoding='utf-8'))[0]
        self.assertEqual(row['manifest_check']['status'], 'fail')
        self.assertEqual(row['manifest_check']['errors'], [
            'linked_path: alias.txt',
            'linked_path: nested/nested.txt',
        ])
        self.assertEqual(row['overall'], 'fail')


if __name__ == '__main__':
    unittest.main()
