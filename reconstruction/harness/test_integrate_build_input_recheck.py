#!/usr/bin/env python3
"""A build that rewrites its scoring inputs must not receive a score.

Sibling of merged #2945 (build_score_pair rechecks its bound sources and
tools after the paired build): integrate.py builds the composed crate and
then scores it against a baseline with score.py, but never rechecks that
the build left the composed source, the baseline, or the scorer untouched.
A crate build runs arbitrary build-script code, so a build that rewrites
any of them could publish a score for a composition that no longer exists,
or against a doctored baseline or scorer.

The build is stubbed (no toolchain here) and the scorer subprocess is
faked; only integrate's own build/score wiring is exercised. make_patch
runs the real diff binary on identical base/part trees, which yields an
empty part. The fake SC/H roots keep the test off the real repo tree.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import integrate


def crate(root):
    root.mkdir(parents=True)
    (root / 'src').mkdir()
    (root / 'src' / 'lib.rs').write_text('pub fn fixture() {}\n', encoding='utf-8')
    (root / 'Cargo.toml').write_text('[package]\nname="fixture"\nversion="0.0.0"\n', encoding='utf-8')
    (root / 'Cargo.lock').write_text('version = 3\n', encoding='utf-8')
    return root


class BuildInputRecheckTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.sc = root / 'sc'
        self.harness = root / 'harness'
        (self.sc / 'pump-main' / 'baseline').mkdir(parents=True)
        self.baseline = self.sc / 'pump-main' / 'baseline' / 'score.json'
        self.baseline.write_text('{}\n', encoding='utf-8')
        self.harness.mkdir()
        self.scorer = self.harness / 'score.py'
        self.scorer.write_text('# fake scorer\n', encoding='utf-8')
        self.base = crate(root / 'base')
        self.part = crate(root / 'part')
        self.out = self.sc / 'integ' / 'trial'
        self.score_calls = []
        real_run = subprocess.run

        def fake_run(argv, **kwargs):
            if any(str(arg) == str(self.scorer) for arg in argv):
                self.score_calls.append(argv)
                return subprocess.CompletedProcess(argv, 0, stdout='{"windows": 1}\n', stderr='')
            return real_run(argv, **kwargs)

        self.patchers = [
            mock.patch.object(integrate, 'SC', self.sc),
            mock.patch.object(integrate, 'H', self.harness),
            mock.patch.object(subprocess, 'run', side_effect=fake_run),
            mock.patch.object(sys, 'argv', ['integrate.py', '--name', 'trial',
                                            '--base-src', str(self.base),
                                            '--part', 'p=' + str(self.part)]),
        ]
        for patcher in self.patchers:
            patcher.start()
        self.addCleanup(lambda: [patcher.stop() for patcher in reversed(self.patchers)])

    def run_main(self, build):
        with mock.patch.object(integrate, 'build_source', side_effect=build):
            code = integrate.main()
        report = json.loads((self.out / 'report.json').read_text(encoding='utf-8'))
        return code, report

    def clean_build(self, src, work, out, **kwargs):
        return {'ok': True}

    def test_unchanged_inputs_are_scored(self):
        code, report = self.run_main(self.clean_build)
        self.assertEqual(code, 0)
        self.assertEqual(report['score'], {'windows': 1})
        self.assertEqual(len(self.score_calls), 1)

    def test_composed_source_changed_during_build_is_not_scored(self):
        def build(src, work, out, **kwargs):
            (src / 'src' / 'lib.rs').write_text('pub fn doctored() {}\n', encoding='utf-8')
            return {'ok': True}

        code, report = self.run_main(build)
        self.assertEqual(code, 1)
        self.assertNotIn('score', report)
        self.assertIn('changed during build', report['score_error']['error'])
        self.assertEqual(self.score_calls, [])

    def test_baseline_changed_during_build_is_not_scored(self):
        def build(src, work, out, **kwargs):
            self.baseline.write_text('{"doctored": true}\n', encoding='utf-8')
            return {'ok': True}

        code, report = self.run_main(build)
        self.assertEqual(code, 1)
        self.assertNotIn('score', report)
        self.assertIn('changed during build', report['score_error']['error'])
        self.assertEqual(self.score_calls, [])

    def test_scorer_changed_during_build_is_not_scored(self):
        def build(src, work, out, **kwargs):
            self.scorer.write_text('# doctored scorer\n', encoding='utf-8')
            return {'ok': True}

        code, report = self.run_main(build)
        self.assertEqual(code, 1)
        self.assertNotIn('score', report)
        self.assertIn('changed during build', report['score_error']['error'])
        self.assertEqual(self.score_calls, [])


if __name__ == '__main__':
    unittest.main()
