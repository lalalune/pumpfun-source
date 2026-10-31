"""Aggregate publication controls using synthetic suite reports, not VM evidence.

The real main path is exercised with the existing bounded worker-fixture seam.
Windows no-replace rename is injected on this POSIX host; no native Windows or
full 44-suite execution is claimed by these publication tests.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_validate_all as runner
import test_pump_validate_all_retention as retention


class ValidateAllWindowsPublishTests(unittest.TestCase):
    def setUp(self):
        self.fixture = retention.PumpValidateAllRetentionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.candidate = self.root/'candidate.so'
        self.candidate.write_bytes(b'publication fixture candidate')
        self.original = runner.ROOT/'evidence/original/pump/deployed.so'
        self.output = self.root/'aggregate/report.json'
        self.retained = self.output.parent/(self.output.name+'.suites')

    def invoke_windows(self, rename):
        windows = types.SimpleNamespace(name='nt', rename=rename,
                     link=mock.Mock(side_effect=AssertionError('Windows hardlink used')))
        with mock.patch.object(runner, 'os', windows):
            result = self.fixture.invoke(self.output, self.candidate, self.original,
                                         self.fixture.complete_suites(self.candidate, self.original))
        windows.link.assert_not_called()
        return result

    def test_main_publishes_complete_report_and_suite_set_on_windows(self):
        self.assertFalse(self.invoke_windows(os.rename))
        report=json.loads(self.output.read_bytes())
        self.assertEqual(set(report['suites']),set(self.fixture.expected))
        self.assertEqual(len(list(self.retained.glob('*.json.gz'))),44)
        self.assertEqual(list(self.output.parent.glob('.report.json.staging-*')),[])

    def test_consumed_report_path_can_belong_to_another_writer(self):
        recreated=[]
        def rename(source,destination):
            os.rename(source,destination)
            source.write_bytes(b'new staging owner')
            recreated.append(source)
        self.assertFalse(self.invoke_windows(rename))
        self.assertEqual(recreated[0].read_bytes(),b'new staging owner')
        self.assertEqual(json.loads(self.output.read_bytes())['case_count'],sum(self.fixture.expected.values()))

    def test_late_output_preserves_complete_recovery_and_late_suite_file(self):
        def rename(source,destination):
            self.output.write_bytes(b'later writer receipt')
            (self.retained/'late-file').write_bytes(b'later suite evidence')
            raise FileExistsError(destination)
        with self.assertRaises(FileExistsError) as error:
            self.invoke_windows(rename)
        self.assertEqual(self.output.read_bytes(),b'later writer receipt')
        self.assertEqual((self.retained/'late-file').read_bytes(),b'later suite evidence')
        self.assertEqual(len(list(self.retained.glob('*.json.gz'))),44)
        recovery=list(self.output.parent.glob('.report.json.staging-*/report.json'))
        self.assertEqual(len(recovery),1)
        self.assertEqual(set(json.loads(recovery[0].read_bytes())['suites']),set(self.fixture.expected))
        self.assertTrue(any('Complete suites retained' in note for note in error.exception.__notes__))

    @unittest.skipIf(os.name == 'nt', 'native POSIX hard-link path')
    def test_posix_success_preserves_new_staging_owner_and_extra_files(self):
        link=os.link;replaced=[]
        def publish(source,destination):
            link(source,destination)
            source.unlink();source.write_bytes(b'new staging owner')
            (source.parent/'late-file').write_bytes(b'late evidence')
            replaced.append(source)
        with mock.patch.object(runner.os,'link',publish):
            self.assertFalse(self.fixture.invoke(self.output,self.candidate,self.original,
                self.fixture.complete_suites(self.candidate,self.original)))
        self.assertEqual(replaced[0].read_bytes(),b'new staging owner')
        self.assertEqual((replaced[0].parent/'late-file').read_bytes(),b'late evidence')
        self.assertEqual(json.loads(self.output.read_bytes())['case_count'],sum(self.fixture.expected.values()))

    def test_rename_failure_keeps_complete_recovery(self):
        with self.assertRaisesRegex(OSError,'rename failed'):
            self.invoke_windows(mock.Mock(side_effect=OSError('rename failed')))
        self.assertFalse(self.output.exists())
        self.assertEqual(len(list(self.retained.glob('*.json.gz'))),44)
        self.assertEqual(len(list(self.output.parent.glob('.report.json.staging-*/report.json'))),1)


if __name__=='__main__':unittest.main()
