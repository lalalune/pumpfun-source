"""A collided exclusive staging name remains owned by its original writer."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_data_order as data_order
import pump_diagnostic_audit as diagnostic
import pump_strict_ordered_logs as strict

class StageCollisionTests(unittest.TestCase):
    def test_collided_stage_is_preserved(self):
        for module in (data_order, diagnostic, strict):
            with self.subTest(module=module.__name__), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                output = root / 'output.json'
                collision = root / '.output.json.fixed.tmp'
                collision.write_bytes(b'owned by earlier writer')
                candidate = root / 'candidate.so'
                candidate.write_bytes(b'fixture')
                report = root / 'report.json'
                report.write_bytes(json.dumps({
                    'original_sha256': strict.ORIGINAL,
                    'candidate_sha256': hashlib.sha256(b'fixture').hexdigest(),
                    'case_count': 1,
                    'suites': {'case': [{'original': {'logs': ['same']},
                                         'candidate': {'logs': ['same']}}]},
                }).encode())
                argv = ['audit', '--report', str(report), '--output', str(output)]
                if module is strict:
                    argv += ['--candidate', str(candidate)]
                with mock.patch.object(module.secrets, 'token_hex', return_value='fixed'), \
                        mock.patch.object(sys, 'argv', argv), \
                        contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(FileExistsError):
                        if module is data_order:
                            module.publish_certificate(output, {'schema': 1})
                        else:
                            module.main()
                self.assertEqual(collision.read_bytes(), b'owned by earlier writer')
                self.assertFalse(output.exists())

if __name__ == '__main__':
    unittest.main()
