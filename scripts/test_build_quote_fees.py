"""Retain quote-selection compiler output when a build step fails; no compiler runs."""
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).with_name('build_quote_fees.py')


class QuoteFeesBuildLogTests(unittest.TestCase):
    def run_script(self, fail_crate, expected=subprocess.CalledProcessError):
        def fake_rustc(cmd, **kwargs):
            crate = cmd[cmd.index('--crate-name') + 1]
            if crate == fail_crate:
                return subprocess.CompletedProcess(cmd, 1, stdout='', stderr='error[E0425]: cannot find value `tier` in ' + crate + '\n')
            return subprocess.CompletedProcess(cmd, 0, stdout='', stderr='warning: built ' + crate + '\n')
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        output = Path(temp.name) / 'out'
        argv = [str(SCRIPT), '--toolchain', str(Path(temp.name) / 'toolchain'), '--output', str(output)]
        with mock.patch.object(sys, 'argv', argv), mock.patch.object(subprocess, 'run', side_effect=fake_rustc) as run:
            with self.assertRaises(expected):
                runpy.run_path(str(SCRIPT), run_name='__main__')
        return output, run

    def test_first_failed_compile_retains_its_diagnostics(self):
        output, run = self.run_script('pump_fees_math')
        self.assertEqual(run.call_count, 1)
        self.assertTrue((output / 'build.log').is_file(), 'failed compile left no build.log')
        self.assertIn('error[E0425]: cannot find value `tier` in pump_fees_math', (output / 'build.log').read_text())

    def test_later_failed_compile_retains_earlier_and_failing_output(self):
        output, run = self.run_script('pump_quote_fees')
        self.assertEqual(run.call_count, 2)
        self.assertTrue((output / 'build.log').is_file(), 'failed compile left no build.log')
        log = (output / 'build.log').read_text()
        self.assertIn('warning: built pump_fees_math', log)
        self.assertIn('error[E0425]: cannot find value `tier` in pump_quote_fees', log)
        self.assertFalse((output / 'comparison.json').exists())

    def test_successful_compiles_keep_the_joined_log_format(self):
        # No compiler ran, so reading the absent object stops the script after all three steps.
        output, run = self.run_script(None, FileNotFoundError)
        self.assertEqual(run.call_count, 3)
        crates = ('pump_fees_math', 'pump_quote_fees', 'recovered_memory')
        self.assertEqual((output / 'build.log').read_text(), '\n'.join('warning: built ' + c + '\n' for c in crates))


if __name__ == '__main__':
    unittest.main()
