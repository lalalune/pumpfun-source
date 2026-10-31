"""A permission change may remove owner execution while other execute bits remain."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import experiment_runner as runner


@unittest.skipUnless(os.name == 'posix' and os.geteuid() != 0, 'requires ordinary POSIX permission checks')
class SourceOutputModes(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='experiment-execute-modes-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.helper = self.source / 'helper.sh'
        self.helper.write_text('#!/bin/sh\nexit 0\n')
        self.helper.chmod(0o700)
        self.command = [sys.executable, '-c',
                        'import pathlib,shutil,subprocess,sys; '
                        'helper=pathlib.Path(sys.argv[1])/"helper.sh"; '
                        'subprocess.run([str(helper)],check=True); '
                        'shutil.copy2(helper,pathlib.Path(sys.argv[2])/"runner.sh")',
                        '{source}', '{out}']

    def trial(self, name='cached'):
        return runner.run_trial(self.source, self.command, self.root / name)

    def test_source_owner_execute_change_recomputes_the_predicate(self):
        first = self.trial()
        self.assertEqual(first['status'], 'pass')
        self.helper.chmod(0o601)  # still has an execute bit, but not for its owner
        cached, fresh = self.trial(), self.trial('fresh')
        self.assertEqual(fresh['status'], 'fail')
        self.assertFalse(cached['reused'])
        self.assertEqual(cached['status'], fresh['status'])
        self.assertNotEqual(cached['key'], first['key'])
        self.assertTrue((self.root / 'cached' / first['attempt']).is_dir())

    def test_output_owner_execute_change_invalidates_the_retained_artifact(self):
        first = self.trial()
        output = self.root / 'cached' / first['attempt'] / 'output/runner.sh'
        subprocess.run([str(output)], check=True)
        output.chmod(0o601)
        with self.assertRaises(PermissionError):
            subprocess.run([str(output)], check=True)
        second = self.trial()
        self.assertFalse(second['reused'])
        self.assertEqual(second['status'], 'pass')
        repaired = self.root / 'cached' / second['attempt'] / 'output/runner.sh'
        subprocess.run([str(repaired)], check=True)
        self.assertEqual(output.stat().st_mode & 0o777, 0o601, 'old attempt must remain unchanged')

    def test_write_only_permission_changes_keep_valid_cache_hits(self):
        first = self.trial()
        self.helper.chmod(0o500)
        output = self.root / 'cached' / first['attempt'] / 'output/runner.sh'
        output.chmod(0o500)
        second = self.trial()
        self.assertTrue(second['reused'])
        self.assertEqual(second['attempt'], first['attempt'])


if __name__ == '__main__':
    unittest.main()
