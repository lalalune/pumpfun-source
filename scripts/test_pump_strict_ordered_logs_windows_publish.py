"""Exercise strict-log publication ownership through the real main and CLI.

Windows branch tests inject no-replace rename semantics on this host. They are
not a claim of native Windows execution; POSIX links and CLI races are real.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_strict_ordered_logs as gate


class StrictOrderedLogsWindowsPublishTests(unittest.TestCase):
    def fixture(self, root, mismatch=False):
        candidate, report, output = root/'candidate.so', root/'report.json', root/'audit.json'
        candidate.write_bytes(b'bound candidate image for publication controls')
        image_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
        raw = json.dumps({'original_sha256': gate.ORIGINAL, 'candidate_sha256': image_sha,
                          'case_count': 1, 'suites': {'pair': [{'original': {'logs': ['before']},
                          'candidate': {'logs': ['after' if mismatch else 'before']}}]}}).encode()
        report.write_bytes(raw)
        return candidate, report, output, raw

    def invoke(self, candidate, report, output, windows_rename=None):
        with contextlib.ExitStack() as stack:
            if windows_rename is not None:
                windows = types.SimpleNamespace(name='nt', fsync=os.fsync, rename=windows_rename,
                    link=mock.Mock(side_effect=AssertionError('Windows used a hard link')))
                stack.enter_context(mock.patch.object(gate, 'os', windows))
            stack.enter_context(mock.patch.object(sys, 'argv', ['audit', '--candidate', str(candidate),
                                '--report', str(report), '--output', str(output)]))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            result = gate.main()
            if windows_rename is not None:
                windows.link.assert_not_called()
            return result

    def test_windows_main_publishes_complete_bound_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, raw = self.fixture(Path(directory))
            self.invoke(candidate, report, output, os.rename)
            result = json.loads(output.read_bytes())
            self.assertEqual(result['source_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(result['candidate_sha256'], hashlib.sha256(candidate.read_bytes()).hexdigest())
            self.assertEqual(result['case_pairs'], 1)
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_windows_no_clobber_preserves_late_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, raw = self.fixture(Path(directory))
            def rename(source, destination):
                output.write_bytes(b'late complete receipt')
                raise FileExistsError(destination)
            with self.assertRaises(FileExistsError):
                self.invoke(candidate, report, output, rename)
            self.assertEqual(output.read_bytes(), b'late complete receipt')
            self.assertEqual(report.read_bytes(), raw)
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_windows_failure_cleans_owned_staging(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, _ = self.fixture(Path(directory))
            with self.assertRaisesRegex(OSError, 'rename failed'):
                self.invoke(candidate, report, output, mock.Mock(side_effect=OSError('rename failed')))
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_consumed_staging_name_belongs_to_later_writer(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, _ = self.fixture(Path(directory))
            recreated = []
            def rename(source, destination):
                os.rename(source, destination)
                source.write_bytes(b'new staging owner')
                recreated.append(source)
            self.invoke(candidate, report, output, rename)
            self.assertEqual(recreated[0].read_bytes(), b'new staging owner')
            self.assertEqual(json.loads(output.read_bytes())['case_pairs'], 1)

    def test_postpublication_input_changes_retain_bound_receipt(self):
        for changed in ('candidate', 'report'):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as directory:
                candidate, report, output, raw = self.fixture(Path(directory))
                old_candidate_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
                def rename(source, destination):
                    os.rename(source, destination)
                    (candidate if changed == 'candidate' else report).write_bytes(b'changed after publication')
                with self.assertRaisesRegex(ValueError, 'Input changed during audit') as error:
                    self.invoke(candidate, report, output, rename)
                receipt = json.loads(output.read_bytes())
                self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(receipt['candidate_sha256'], old_candidate_sha)
                self.assertTrue(any('already published' in note for note in error.exception.__notes__))
                self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_postpublication_failure_never_removes_later_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, _ = self.fixture(Path(directory))
            def rename(source, destination):
                os.rename(source, destination)
                output.write_bytes(b'receipt from later writer')
                candidate.write_bytes(b'changed image')
            with self.assertRaisesRegex(ValueError, 'Input changed during audit'):
                self.invoke(candidate, report, output, rename)
            self.assertEqual(output.read_bytes(), b'receipt from later writer')

    @unittest.skipIf(os.name == 'nt', 'native POSIX hard-link path')
    def test_posix_postpublication_failure_preserves_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, _ = self.fixture(Path(directory))
            link = os.link
            def link_then_replace(source, destination):
                link(source, destination)
                output.unlink()
                output.write_bytes(b'new complete receipt')
                report.write_bytes(b'changed source')
            with mock.patch.object(gate.os, 'link', link_then_replace):
                with self.assertRaisesRegex(ValueError, 'Input changed during audit'):
                    self.invoke(candidate, report, output)
            self.assertEqual(output.read_bytes(), b'new complete receipt')
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_candidate_change_before_publication_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate, report, output, _ = self.fixture(Path(directory))
            audit = gate.audit
            def mutate(*args):
                result = audit(*args)
                candidate.write_bytes(b'changed before publication')
                return result
            with mock.patch.object(gate, 'audit', mutate):
                with self.assertRaisesRegex(ValueError, 'Input changed during audit'):
                    self.invoke(candidate, report, output)
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob('.audit.json.*')), [])

    def test_actual_cli_match_mismatch_and_concurrent_no_clobber(self):
        for mismatch in (False, True):
            with self.subTest(mismatch=mismatch), tempfile.TemporaryDirectory() as directory:
                candidate, report, output, raw = self.fixture(Path(directory), mismatch)
                command = [sys.executable, '-B', str(Path(gate.__file__).resolve()), '--candidate', str(candidate),
                           '--report', str(report), '--output', str(output)]
                processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(4)]
                results = [process.communicate(timeout=30) for process in processes]
                receipt = json.loads(output.read_bytes())
                self.assertEqual(receipt['strict_ordered_log_mismatch_cases'], int(mismatch))
                self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(raw).hexdigest())
                if mismatch:
                    winners = [i for i, (_, error) in enumerate(results) if b'Strict ordered logs differ' in error]
                else:
                    winners = [i for i, (_, error) in enumerate(results) if not error]
                self.assertEqual(len(winners), 1, results)
                self.assertEqual(processes[winners[0]].returncode, int(mismatch))
                for i, process in enumerate(processes):
                    if i not in winners:
                        self.assertNotEqual(process.returncode, 0)
                        self.assertTrue(b'Output already exists' in results[i][1] or b'FileExistsError' in results[i][1])
                self.assertEqual(report.read_bytes(), raw)
                self.assertEqual(list(output.parent.glob('.audit.json.*')), [])


if __name__ == '__main__':
    unittest.main()
