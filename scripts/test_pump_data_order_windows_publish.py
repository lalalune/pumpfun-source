"""Publication controls; Windows semantics are injected, POSIX calls are real."""
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
import pump_data_order as gate


class DataOrderWindowsPublishTests(unittest.TestCase):
    def publish_windows(self, path, rename):
        windows = types.SimpleNamespace(name='nt', rename=rename, fsync=os.fsync,
                    link=mock.Mock(side_effect=AssertionError('Windows hard link')))
        with mock.patch.object(gate, 'os', windows):
            gate.publish_certificate(path, {'schema': 1, 'payload': {'roles': ['control']}})
        windows.link.assert_not_called()

    def test_windows_complete_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'certificate.json'
            self.publish_windows(output, os.rename)
            self.assertEqual(json.loads(output.read_bytes())['payload']['roles'], ['control'])
            self.assertEqual(list(output.parent.glob('.certificate.json.*')), [])

    def test_consumed_staging_path_may_be_recreated(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'certificate.json'
            recreated = []
            def rename(source, target):
                os.rename(source, target)
                source.write_bytes(b'later owner')
                recreated.append(source)
            self.publish_windows(output, rename)
            self.assertEqual(recreated[0].read_bytes(), b'later owner')
            self.assertEqual(json.loads(output.read_bytes())['schema'], 1)

    def test_windows_late_output_and_rename_failure(self):
        for collision in (False, True):
            with self.subTest(collision=collision), tempfile.TemporaryDirectory() as directory:
                output = Path(directory)/'certificate.json'
                def rename(source, target):
                    if collision:
                        output.write_bytes(b'later certificate')
                        raise FileExistsError(target)
                    raise OSError('rename failed')
                with self.assertRaises(OSError):
                    self.publish_windows(output, rename)
                self.assertEqual(output.read_bytes() if output.exists() else None,
                                 b'later certificate' if collision else None)
                self.assertEqual(list(output.parent.glob('.certificate.json.*')), [])

    def test_real_posix_publication_and_no_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'certificate.json'
            gate.publish_certificate(output, {'schema': 1})
            original = output.read_bytes()
            with self.assertRaises(FileExistsError):
                gate.publish_certificate(output, {'schema': 2})
            self.assertEqual(output.read_bytes(), original)
            self.assertEqual(list(output.parent.glob('.certificate.json.*')), [])

    def test_failed_staging_preserves_previous_certificate(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'certificate.json'
            output.write_bytes(b'previous certificate')
            with mock.patch.object(gate.os, 'fsync', side_effect=OSError('write failed')):
                with self.assertRaisesRegex(OSError, 'write failed'):
                    gate.publish_certificate(output, {'schema': 1})
            self.assertEqual(output.read_bytes(), b'previous certificate')
            self.assertEqual(list(output.parent.glob('.certificate.json.*')), [])

    def test_actual_cli_concurrent_publication_preserves_inputs(self):
        # Only the unchanged, expensive derivation is replaced with a labelled
        # payload. This runs the actual CLI admission/publication in processes.
        driver = '''
import sys
sys.path.insert(0,sys.argv.pop(1))
import pump_data_order as tool
tool.derive_payload=lambda *args: {'roles':['publication-control']}
tool.main()
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); output = root/'certificate.json'
            baseline, order = root/'baseline', root/'order.ld'
            baseline.mkdir(); (baseline/'sentinel').write_bytes(b'unchanged build')
            order.write_bytes(b'unchanged order')
            cmd=[sys.executable,'-B','-c',driver,str(Path(gate.__file__).parent),
                 '--baseline-build',str(baseline),'--text-section-order',str(order),'--output',str(output)]
            processes=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE) for _ in range(4)]
            results=[process.communicate(timeout=30) for process in processes]
            self.assertEqual(sum(p.returncode==0 for p in processes),1,results)
            self.assertEqual(json.loads(output.read_bytes())['payload']['roles'],['publication-control'])
            self.assertEqual((baseline/'sentinel').read_bytes(),b'unchanged build')
            self.assertEqual(order.read_bytes(),b'unchanged order')
            self.assertEqual(list(root.glob('.certificate.json.*')),[])


if __name__=='__main__':unittest.main()
