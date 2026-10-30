"""A diagnostic gate cannot pass a log that recorded no build output."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import check_sbf_backend_diagnostics as gate


class EmptyLogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.log = Path(self.folder.name) / 'build.log'

    def test_logs_without_content_do_not_pass_the_gate(self):
        for label, raw in [('zero bytes', b''), ('signature only', b'\xef\xbb\xbf'),
                           ('blank lines', b'\n \r\n\t\n'), ('gzip of nothing', gzip.compress(b'', mtime=0))]:
            with self.subTest(label):
                self.log.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, 'empty diagnostic log'):
                    gate.check([self.log])

    def test_one_empty_log_is_not_hidden_by_a_clean_log(self):
        clean = self.log.with_name('clean.log')
        clean.write_text('Finished release\n', encoding='utf-8')
        self.log.write_bytes(b'')
        with self.assertRaisesRegex(ValueError, 'empty diagnostic log'):
            gate.check([clean, self.log])

    def test_cli_does_not_report_a_passed_gate_for_an_empty_log(self):
        self.log.write_bytes(b'')
        result = subprocess.run([sys.executable, gate.__file__, '--log', str(self.log)],
                                capture_output=True, encoding='utf-8')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout, '')

    def test_a_log_with_build_output_keeps_its_gate_result(self):
        self.log.write_text('Finished release\n', encoding='utf-8')
        report = gate.check([self.log])
        self.assertTrue(report['diagnostic_gate_passed'])
        self.assertEqual(json.loads(json.dumps(report))['backend_error_count'], 0)


if __name__ == '__main__':
    unittest.main()
