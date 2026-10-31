"""The real offline Relay verifier must preserve the source tree it checks."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VERIFIER = ROOT / 'reconstruction/donation-relay/native-linux-v148-20261030/verify.py'


class DonationRelayOfflineOutputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='relay-offline-output-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'repo'
        self.source = self.repo / 'programs/donation-relay'
        shutil.copytree(ROOT / 'programs/donation-relay', self.source)
        for name in ('scripts/analyze.py', 'evidence/dependencies/donation_relay/deployed.so'):
            target = self.repo / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        self.before = self.snapshot()
        self.assertEqual(len(self.before), 60)

    def snapshot(self):
        return {p.relative_to(self.source).as_posix():
                (p.stat().st_mode, hashlib.sha256(p.read_bytes()).hexdigest())
                for p in self.source.rglob('*') if p.is_file()}

    def invoke(self, output):
        return subprocess.run(
            [sys.executable, '-B', *(['-O'] if sys.flags.optimize else []), str(VERIFIER),
             '--repo', str(self.repo), '--output', str(output)],
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
            capture_output=True, text=True, timeout=30)

    def test_reports_outside_source_pass_repeated_verification(self):
        reports = []
        # A report may stay within the checkout, outside the source subtree.
        for name in ('offline-first.json', 'offline-second.json'):
            output = self.repo / name
            result = self.invoke(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(output.read_text())
            self.assertEqual(report['status'], 'OFFLINE_SOURCE_PACKET_AND_LITERAL_CAPTURE_CHECK_PASS')
            self.assertEqual(report['meaningfulBytesLiteralEqual'], 818280)
            self.assertEqual(report['compilerOrSdkExecutions'], 0)
            reports.append(report)
            self.assertEqual(self.snapshot(), self.before)
        self.assertEqual(reports[0], reports[1])

    def test_new_report_inside_source_is_refused_without_creation(self):
        output = self.source / 'offline-report.json'
        result = self.invoke(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('verification output overlaps authenticated Relay source', result.stderr)
        self.assertFalse(output.exists())
        self.assertEqual(self.snapshot(), self.before)

    def test_parent_directory_symlink_alias_is_refused(self):
        alias = self.root / 'source-alias'
        try:
            alias.symlink_to(self.source, target_is_directory=True)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f'directory links unavailable: {error}')
        output = alias / 'offline-report.json'
        result = self.invoke(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('verification output overlaps authenticated Relay source', result.stderr)
        self.assertFalse(output.exists())
        self.assertTrue(alias.is_symlink())
        self.assertEqual(self.snapshot(), self.before)

    def test_existing_external_hardlink_preserves_source_bytes(self):
        source = self.source / 'Cargo.toml'
        output = self.root / 'hardlink-report.json'
        try:
            os.link(source, output)
        except (OSError, NotImplementedError) as error:
            self.skipTest(f'hard links unavailable: {error}')
        before = output.read_bytes()
        result = self.invoke(output)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('FileExistsError', result.stderr)
        self.assertEqual(output.read_bytes(), before)
        self.assertTrue(output.samefile(source))
        self.assertEqual(self.snapshot(), self.before)


if __name__ == '__main__':
    unittest.main()
