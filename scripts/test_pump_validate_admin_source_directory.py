#!/usr/bin/env python3
"""The administration suite binds the source tree its aggregate runner selected."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))
TOOL = SCRIPTS / 'pump_validate_admin.py'
CANDIDATE = ROOT / 'evidence/original/pump/deployed.so'


def run(source, output):
    return subprocess.run(
        [sys.executable, '-B', str(TOOL), '--candidate', str(CANDIDATE),
         '--source-directory', str(source), '--output', str(output)],
        cwd=ROOT, capture_output=True, text=True, timeout=300)


@unittest.skipUnless(importlib.util.find_spec('solders'), 'requires the documented solders runtime')
class AdministrationSourceDirectoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.source = self.folder / 'compiled'

    def test_aggregate_forwards_the_selected_source_directory(self):
        import pump_validate_all as runner
        command = runner.suite_command('administration', TOOL, CANDIDATE, self.folder / 'report.json',
                                       self.source, self.folder / 'build-comparison.json')
        self.assertIn('--source-directory', command)
        self.assertEqual(command[command.index('--source-directory') + 1], str(self.source.resolve()))

    def test_report_binds_the_selected_source_directory(self):
        library = self.source / 'src/lib.rs'
        library.parent.mkdir(parents=True)
        library.write_bytes((ROOT / 'programs/pump/src/lib.rs').read_bytes() + b'// compiled copy\n')
        output = self.folder / 'report.json'
        completed = run(self.source, output)
        self.assertEqual(completed.returncode, 0, completed.stderr[-2000:])
        report = json.loads(output.read_bytes())
        self.assertEqual(report['source_sha256'], hashlib.sha256(library.read_bytes()).hexdigest())

    def test_directory_without_the_handler_source_runs_no_cases(self):
        self.source.mkdir()
        output = self.folder / 'report.json'
        completed = run(self.source, output)
        self.assertIn('no Rust/Cargo inputs under', completed.stderr)
        self.assertNotEqual(completed.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
