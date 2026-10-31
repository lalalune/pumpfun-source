#!/usr/bin/env python3
"""A published diagnostic audit keeps the same umask mode as a direct write."""
import contextlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_diagnostic_audit as gate


@unittest.skipIf(os.name == 'nt', 'POSIX permission bits')
class DiagnosticAuditUmaskModeTests(unittest.TestCase):
    def invoke(self, report, output, mask):
        suites = {'case': [{'original': {'logs': ['same']},
                            'candidate': {'logs': ['same']}}]}
        report.write_bytes(json.dumps({'suites': suites}).encode())
        argv = ['audit', '--report', str(report), '--output', str(output)]
        previous = os.umask(mask)
        try:
            with mock.patch.object(sys, 'argv', argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                gate.main()
        finally:
            os.umask(previous)
        return stat.S_IMODE(output.stat().st_mode)

    def test_new_report_keeps_the_process_umask(self):
        for mask, mode in ((0o022, 0o644), (0o027, 0o640)):
            with self.subTest(mask=oct(mask)):
                with tempfile.TemporaryDirectory(prefix='diagnostic-audit-umask-') as temporary:
                    root = Path(temporary)
                    output = root / ('audit-' + oct(mask) + '.json')
                    self.assertEqual(self.invoke(root / 'report.json', output, mask), mode)


if __name__ == '__main__':
    unittest.main()
