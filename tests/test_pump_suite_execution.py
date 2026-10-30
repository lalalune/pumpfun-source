"""A suite deadline or invalid JSON must retain diagnostics, never aggregate success."""
import contextlib
import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import signal
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import pump_validate_parallel as validator
import test_pump_validate_parallel as fixtures


class SuiteExecution(fixtures.ParallelReportPublicationTests):
    def test_zero_exit_malformed_output_retains_original_bytes_and_identity(self):
        for raw in [b'{not json', b'\x1f\x8bnot gzip']:
            with self.subTest(raw=raw):
                self.suite.write_text('import sys\nfrom pathlib import Path\n'
                                      f'Path(sys.argv[sys.argv.index("--output")+1]).write_bytes({raw!r})\n')
                output = self.root / ('malformed-' + str(len(raw)) + '.json')
                with self.assertRaisesRegex(RuntimeError, 'suite failure'):
                    self.run_validator(output)
                self.assertFalse(output.exists())
                failure = json.loads(output.with_name(output.name + '.failed.json').read_text())
                entry = failure['failed_suite_outputs']['fixture']
                retained = self.root / entry['path']
                self.assertEqual(retained.read_bytes(), raw)
                self.assertEqual(entry['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(entry['returncode'], 0)
                self.assertEqual(entry['bytes'], len(raw))

    def test_hanging_suite_and_child_are_killed_and_log_is_retained(self):
        child_marker = self.root / 'child-survived'
        group_file = self.root / 'suite.pid'
        # The child would publish a marker if deadline cleanup killed only its parent.
        self.suite.write_text(
            'import os,subprocess,sys,time\nfrom pathlib import Path\n'
            f'Path({str(group_file)!r}).write_text(str(os.getpid()))\n'
            'subprocess.Popen([sys.executable,"-c",'
            f'{("import time; from pathlib import Path; time.sleep(2); Path(" + repr(str(child_marker)) + ").write_text(\"survived\")")!r}])\n'
            'print("suite started before hang",flush=True)\ntime.sleep(60)\n')
        output = self.root / 'hung.json'
        context = multiprocessing.get_context('fork')
        errors = context.Queue()
        def run():
            os.setsid()
            with patch.object(validator, 'DEFAULT_SUITE_TIMEOUT', 0.2, create=True):
                try:
                    self.run_validator(output)
                except RuntimeError as error:
                    errors.put(str(error))
        process = context.Process(target=run)
        process.start()
        process.join(4)
        hung = process.is_alive()
        try:
            if hung:
                self.fail('suite execution exceeded its deadline and blocked aggregate completion')
            self.assertEqual(process.exitcode, 0)
            self.assertIn('suite failure', errors.get(timeout=1))
            self.assertFalse(output.exists())
            failure = json.loads(output.with_name(output.name + '.failed.json').read_text())
            self.assertIn('TimeoutExpired', failure['errors'][0]['error'])
            self.assertIn('suite started before hang',
                          (output.parent / (output.name + '.suites/fixture.log')).read_text())
            time.sleep(2.1)
            self.assertFalse(child_marker.exists(), 'suite child survived deadline cleanup')
        finally:
            # Also bound this regression when run against the unfixed implementation.
            for group in [int(group_file.read_text()) if group_file.exists() else 0, process.pid]:
                if group:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(group, signal.SIGKILL)
            process.join(2)


if __name__ == '__main__':
    unittest.main()
