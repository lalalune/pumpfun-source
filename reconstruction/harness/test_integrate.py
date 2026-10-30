#!/usr/bin/env python3
"""Synthetic orchestration tests; never run the builder, scorer or a subprocess."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import Mock, patch


SOURCE = Path(__file__).with_name('integrate.py')
SYNTHETIC_SCORE = {
    'candidate_sha256': 'synthetic-not-an-artifact',
    'gains': ['0x100'], 'losses': ['0x200'],
    'raw_gains': [], 'raw_losses': ['0x300'],
}


class IntegrationBaselineTests(unittest.TestCase):
    def exercise(self, *, no_build=False, build_ok=True, baseline_exists=True):
        # Replace integrate's lazy builder adapter so no compiler
        # configuration or artifact/cache access is needed.
        builder = types.ModuleType('fastbuild')
        builder.build = Mock(return_value={'ok': build_ok, 'runtime_valid': True})
        spec = importlib.util.spec_from_file_location('test_subject_integrate', SOURCE)
        module = importlib.util.module_from_spec(spec)
        original_path = sys.path[:]
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path[:] = original_path

        with tempfile.TemporaryDirectory(prefix='pump-integration-test-') as temporary:
            root = Path(temporary)
            base = root / 'synthetic source'
            base.mkdir()
            (base / 'src').mkdir()
            (base / 'Cargo.toml').write_text('[package]\nname="synthetic"\nversion="0.0.0"\n')
            (base / 'Cargo.lock').write_text('version = 3\n')
            (base / 'README.txt').write_text('Synthetic source-only control.\n')
            module.SC = root / 'reconstruction'
            module.H = module.SC / 'harness'
            baseline = module.SC / 'pump-main/baseline/score.json'
            baseline.parent.mkdir(parents=True)
            if baseline_exists:
                baseline.write_text('{"windows": {}}\n')
            previous_output = module.SC / 'integ/synthetic/existing.txt'
            if not baseline_exists and not no_build:
                previous_output.parent.mkdir(parents=True)
                previous_output.write_text('Preserve this on failed preflight.\n')

            calls = []
            def synthetic_subprocess(argv, **kwargs):
                calls.append(list(argv))
                return types.SimpleNamespace(
                    returncode=0, stdout=json.dumps(SYNTHETIC_SCORE), stderr='')

            argv = ['integrate.py', '--name', 'synthetic', '--base-src', str(base)]
            if no_build:
                argv.append('--no-build')
            with patch.object(sys, 'argv', argv), \
                    patch.object(module, 'build_source', side_effect=builder.build), \
                    patch.object(module.subprocess, 'run', side_effect=synthetic_subprocess), \
                    contextlib.redirect_stdout(io.StringIO()):
                if not baseline_exists and not no_build:
                    with self.assertRaisesRegex(FileNotFoundError, 'Required scoring baseline is missing:') as raised:
                        module.main()
                    self.assertIn(str(baseline), str(raised.exception))
                    self.assertEqual(previous_output.read_text(), 'Preserve this on failed preflight.\n')
                    return builder.build.call_count, calls, str(baseline), {}
                module.main()
            report = json.loads((module.SC / 'integ/synthetic/report.json').read_text())
            return builder.build.call_count, calls, str(baseline), report

    def test_successful_build_passes_checked_in_baseline_to_scorer(self):
        builds, calls, expected, report = self.exercise()
        self.assertEqual(builds, 1)
        self.assertEqual(len(calls), 1)
        self.assertIn('--baseline', calls[0])
        self.assertEqual(calls[0].count('--baseline'), 1)
        self.assertEqual(calls[0][calls[0].index('--baseline') + 1], expected)
        self.assertTrue(calls[0][1].endswith('/harness/score.py'))
        self.assertTrue(calls[0][2].endswith('/build/unstripped.so'))
        self.assertIn('--json', calls[0])
        self.assertIn('--quiet', calls[0])
        # The orchestration report preserves losses; it does not accept/reject them.
        self.assertEqual(report['score'], SYNTHETIC_SCORE)

    def test_no_build_skips_builder_and_scorer(self):
        builds, calls, _, report = self.exercise(no_build=True, baseline_exists=False)
        self.assertEqual(builds, 0)
        self.assertEqual(calls, [])
        self.assertNotIn('build', report)
        self.assertNotIn('score', report)

    def test_failed_build_is_reported_without_scoring(self):
        builds, calls, _, report = self.exercise(build_ok=False)
        self.assertEqual(builds, 1)
        self.assertEqual(calls, [])
        self.assertFalse(report['build']['ok'])
        self.assertNotIn('score', report)

    def test_missing_baseline_fails_before_builder_or_scorer(self):
        builds, calls, _, _ = self.exercise(baseline_exists=False)
        self.assertEqual(builds, 0)
        self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
