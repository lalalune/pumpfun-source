"""Check the router refuses flags it would otherwise route around."""
import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_reconstruction_candidate import command


class AbbreviatedRoutingFlagTests(unittest.TestCase):
    def assert_refused(self, arguments):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as refused:
            command(arguments)
        self.assertEqual(refused.exception.code, 2)
        self.assertIn('abbreviated', stderr.getvalue())

    def test_abbreviated_tools_version_is_not_overridden_by_the_default(self):
        self.assert_refused(['--program', 'pump', '--tools', 'v1.53'])
        self.assert_refused(['--program', 'pump', '--tools-v=v1.52'])

    def test_abbreviated_program_cannot_replace_the_routed_program(self):
        self.assert_refused(['--program', 'pump', '--prog', 'mayhem'])

    def test_exact_flags_and_their_values_still_route(self):
        tail = ['--program', 'pump', '--tools-version=v1.43', '--output', 'work/--tools']
        self.assertEqual(command(tail)[2:], tail)
        self.assertIn('--extra-input', command(['--program', 'mayhem', '--extra-input', 'a']))


if __name__ == '__main__':
    unittest.main()
