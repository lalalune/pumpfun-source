"""Exercise composition failure status without a compiler or scorer."""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import integrate


class CompositionFailures(unittest.TestCase):
    def attempt(self, build_ok=True, score_code=0, score_stdout='{"normalized": 12}', no_build=False):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'crate'
            source.mkdir()
            (source / 'src').mkdir()
            (source / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
            (source / 'Cargo.lock').write_text('version = 3\n')
            baseline = root / 'pump-main/baseline/score.json'
            baseline.parent.mkdir(parents=True)
            baseline.write_text('{"windows": {}}')
            (source / 'lib.rs').write_text('// test source\n')
            argv = ['integrate.py', '--name', 'trial', '--base-src', str(source)]
            if no_build:
                argv.append('--no-build')
            response = subprocess.CompletedProcess(['scorer'], score_code, stdout=score_stdout, stderr='diagnostic')
            with patch.object(integrate, 'SC', root), patch.object(sys, 'argv', argv), \
                 patch.object(integrate, 'build_source', return_value={'ok': build_ok}) as build, \
                 patch.object(integrate.subprocess, 'run', return_value=response) as run, \
                 contextlib.redirect_stdout(io.StringIO()):
                status = integrate.main()
            report = json.loads((root / 'integ/trial/report.json').read_text())
            return status, report, build.call_count, run.call_count

    def test_build_failure_is_not_success(self):
        status, report, builds, scores = self.attempt(build_ok=False)
        self.assertEqual(status, 1)
        self.assertFalse(report['build']['ok'])
        self.assertNotIn('score', report)
        self.assertEqual((builds, scores), (1, 0))

    def test_scorer_failure_preserves_report_without_accepting_stdout(self):
        status, report, _, _ = self.attempt(score_code=2)
        self.assertEqual(status, 1)
        self.assertNotIn('score', report)
        self.assertEqual(report['score_error']['returncode'], 2)
        self.assertEqual(report['score_error']['stderr'], 'diagnostic')

    def test_malformed_success_output_preserves_diagnostic(self):
        status, report, _, _ = self.attempt(score_stdout='not JSON')
        self.assertEqual(status, 1)
        self.assertEqual(report['score_error']['stdout'], 'not JSON')
        self.assertNotIn('score', report)

    def test_success_and_no_build(self):
        status, report, builds, scores = self.attempt()
        self.assertEqual(status, 0)
        self.assertEqual(report['score'], {'normalized': 12})
        self.assertEqual((builds, scores), (1, 1))
        status, report, builds, scores = self.attempt(no_build=True)
        self.assertEqual(status, 0)
        self.assertEqual((builds, scores), (0, 0))
        self.assertNotIn('score', report)

    def test_diff_operational_failure_does_not_publish_partial_patch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('base', 'part'):
                (root / name).mkdir()
            output = root / 'result.patch'
            output.write_text('prior patch')
            response = subprocess.CompletedProcess(['diff'], 2, stdout=b'partial diff\xff', stderr=b'read failure')
            with patch.object(integrate.subprocess, 'run', return_value=response), \
                 self.assertRaises(subprocess.CalledProcessError) as error:
                integrate.make_patch(root / 'base', root / 'part', output, root / 'tmp')
            self.assertEqual(error.exception.stderr, b'read failure')
            self.assertEqual(output.read_text(), 'prior patch')

    def test_diff_zero_and_one_are_both_normal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name in ('base', 'part'):
                (root / name).mkdir()
            for code, text in ((0, ''), (1, 'complete diff')):
                with self.subTest(code=code), patch.object(integrate.subprocess, 'run',
                     return_value=subprocess.CompletedProcess(['diff'], code, stdout=text.encode())):
                    self.assertEqual(integrate.make_patch(root / 'base', root / 'part', root / 'out', root / 'tmp'), text)


if __name__ == '__main__':
    unittest.main()
