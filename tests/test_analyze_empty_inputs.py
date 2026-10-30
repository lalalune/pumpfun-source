#!/usr/bin/env python3
"""Actual analyzer CLI input admission and paired-report publication controls."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ('binary-analysis.json', 'interface-inventory.json')


class AnalyzeEmptyInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='analyze-empty-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'evidence/upstream').mkdir(parents=True)
        shutil.copyfile(ROOT / 'scripts/analyze.py', self.root / 'scripts/analyze.py')

    def add_capture(self):
        capture = self.root / 'evidence/original/pump'
        capture.mkdir(parents=True)
        for name in ('deployed.so', 'capture.json'):
            shutil.copyfile(ROOT / 'evidence/original/pump' / name, capture / name)

    def add_idl(self):
        shutil.copyfile(ROOT / 'evidence/upstream/pump.json',
                        self.root / 'evidence/upstream/pump.json')

    def invoke(self, *options):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        return subprocess.run([sys.executable, *options, '-B', 'scripts/analyze.py'],
                              cwd=self.root, env=env, capture_output=True,
                              text=True, timeout=30)

    def assert_empty_refused(self):
        for existing in (False, True):
            with self.subTest(existing_reports=existing):
                before = {}
                for name in REPORTS:
                    output = self.root / 'evidence' / name
                    if existing:
                        output.write_bytes(('prior ' + name + '\n').encode())
                        before[name] = output.read_bytes()
                result = self.invoke()
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('refusing to publish empty reports', result.stderr)
                for name in REPORTS:
                    output = self.root / 'evidence' / name
                    if existing:
                        self.assertEqual(output.read_bytes(), before[name])
                    else:
                        self.assertFalse(output.exists())
                self.assertFalse(list((self.root / 'evidence').glob('.*.json.*')))

    def test_missing_captures_and_idls_preserve_reports(self):
        self.assert_empty_refused()

    def test_captures_without_idls_preserve_reports(self):
        self.add_capture()
        self.assert_empty_refused()

    def test_idls_without_captures_preserve_reports(self):
        self.add_idl()
        self.assert_empty_refused()

    def test_empty_guard_remains_active_under_optimized_python(self):
        result = self.invoke('-O')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('refusing to publish empty reports', result.stderr)
        self.assertTrue(all(not (self.root / 'evidence' / name).exists() for name in REPORTS))

    def test_real_capture_and_idl_publish_both_reports(self):
        self.add_capture()
        self.add_idl()
        inputs = {path: path.read_bytes() for path in (self.root / 'evidence').rglob('*')
                  if path.is_file()}
        for name in REPORTS:
            (self.root / 'evidence' / name).write_bytes(b'prior report\n')
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        binary, inventory = [json.loads((self.root / 'evidence' / name).read_bytes())
                             for name in REPORTS]
        self.assertEqual(sorted(binary), ['pump'])
        self.assertEqual(sorted(inventory), ['pump'])
        self.assertGreater(binary['pump']['elf_extent'], 0)
        self.assertGreater(inventory['pump']['instructions'], 0)
        for path, raw in inputs.items():
            self.assertEqual(path.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
