"""A directory cannot receive a report, so refuse it before the analysis runs."""
import contextlib
import importlib.util
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

H = Path(__file__).resolve().parent
RAN = AssertionError('the analysis ran before the destination was refused')
sys.path.insert(0, str(H))

import score  # noqa: E402
from score_admission import report_destination  # noqa: E402


def load(name):
    spec = importlib.util.spec_from_file_location('directory_' + name, H / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


coords = load('coords')
triage = load('triage')


class DirectoryDestinationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = score.BASE / 'original.so'
        self.directory = self.root / 'reports'
        self.directory.mkdir()

    def refused(self, module, attribute, argv):
        with patch.object(module, attribute, side_effect=RAN), patch.object(sys, 'argv', argv), \
             contextlib.redirect_stderr(io.StringIO()) as stderr:
            with self.assertRaises(SystemExit) as caught:
                module.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn('is a directory', stderr.getvalue())

    def test_admission_refuses_a_directory(self):
        with self.assertRaisesRegex(ValueError, 'is a directory'):
            report_destination(self.directory, [self.candidate])

    def test_admission_keeps_a_new_path(self):
        report_destination(self.directory / 'new.json', [self.candidate])

    def test_triage_refuses_before_scoring(self):
        self.refused(triage, 'score', ['triage.py', '--cand', str(self.candidate),
                                       '--json', str(self.directory)])

    def test_coordinate_report_refuses_before_scoring(self):
        self.refused(coords, 'score_with_hash', ['coords.py', 'unmatched', '--cand', str(self.candidate),
                                                 '--json', str(self.directory)])

    def test_score_refuses_before_scoring(self):
        argv = ['score.py', str(self.candidate), '--no-baseline', '--json', str(self.directory)]
        with patch.object(score, 'score_with_hash', side_effect=RAN), patch.object(sys, 'argv', argv):
            with self.assertRaisesRegex(ValueError, 'is a directory'):
                score.main()


if __name__ == '__main__':
    unittest.main()
