"""Atomic publication checks for analyze.py's paired evidence reports."""
import os
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import analyze


class AnalyzePublicationTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix', 'POSIX file modes and umask')
    def test_real_analysis_reports_honor_umask_without_changing_bytes(self):
        source = Path(analyze.__file__).resolve().parents[1]
        script = '''
import os, runpy, sys
os.umask(int(sys.argv[2], 8))
runpy.run_path(sys.argv[1], run_name='__main__')
'''
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'scripts').mkdir()
            executable = root / 'scripts/analyze.py'
            shutil.copyfile(source / 'scripts/analyze.py', executable)
            shutil.copytree(source / 'evidence/original/mayhem', root / 'evidence/original/mayhem')
            shutil.copytree(source / 'evidence/upstream', root / 'evidence/upstream')
            expected_bytes = None
            for mask, mode in ((0o022, 0o644), (0o027, 0o640), (0o077, 0o600)):
                result = subprocess.run(
                    [sys.executable, '-c', script, str(executable), oct(mask)],
                    cwd=root, capture_output=True, text=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                reports = {name: (root / 'evidence' / name).read_bytes()
                           for name in ('binary-analysis.json', 'interface-inventory.json')}
                self.assertEqual(set(json.loads(reports['binary-analysis.json'])), {'mayhem'})
                self.assertIn('pump', json.loads(reports['interface-inventory.json']))
                if expected_bytes is None:
                    expected_bytes = reports
                else:
                    self.assertEqual(reports, expected_bytes)
                for name in reports:
                    with self.subTest(umask=oct(mask), report=name):
                        self.assertEqual(stat.S_IMODE((root / 'evidence' / name).stat().st_mode), mode)

    def test_missing_second_parent_does_not_replace_first_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / 'binary-analysis.json'
            second = root / 'missing/interface-inventory.json'
            first.write_text('prior\n', encoding='utf-8')

            with self.assertRaises(FileNotFoundError):
                analyze.publish_reports([(first, 'replacement\n'), (second, 'new\n')])

            self.assertEqual(first.read_text(encoding='utf-8'), 'prior\n')
            self.assertFalse(second.exists())

    def test_failed_second_stage_keeps_reports_and_removes_all_temporaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / 'first.json', root / 'second.json'
            first.write_text('prior first\n', encoding='utf-8')
            second.write_text('prior second\n', encoding='utf-8')
            fdopen = os.fdopen

            class FailingWriter:
                def __init__(self, stream):
                    self.stream = stream
                def __enter__(self):
                    return self
                def __exit__(self, *exc):
                    self.stream.close()
                def write(self, text):
                    if text == 'new second\n':
                        raise OSError('simulated disk full')
                    return self.stream.write(text)

            with mock.patch.object(analyze.os, 'fdopen',
                                   side_effect=lambda *a, **kw: FailingWriter(fdopen(*a, **kw))):
                with self.assertRaisesRegex(OSError, 'disk full'):
                    analyze.publish_reports([(first, 'new first\n'), (second, 'new second\n')])
            self.assertEqual(first.read_text(), 'prior first\n')
            self.assertEqual(second.read_text(), 'prior second\n')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['first.json', 'second.json'])

    def test_successful_pair_replaces_both_reports_without_staging_residue(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / 'first.json', root / 'second.json'
            analyze.publish_reports([(first, 'first\n'), (second, 'second\n')])
            self.assertEqual(first.read_text(), 'first\n')
            self.assertEqual(second.read_text(), 'second\n')
            self.assertEqual(sorted(p.name for p in root.iterdir()), ['first.json', 'second.json'])


if __name__ == '__main__':
    unittest.main()
