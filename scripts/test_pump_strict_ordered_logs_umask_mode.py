#!/usr/bin/env python3
"""A published strict-log audit keeps the same umask mode as a direct write."""
import contextlib
import hashlib
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
import pump_strict_ordered_logs as gate


@unittest.skipIf(os.name == 'nt', 'POSIX permission bits')
class StrictOrderedLogsUmaskModeTests(unittest.TestCase):
    def invoke(self, output, mask):
        root = output.parent
        candidate = root / 'candidate.so'
        candidate.write_bytes(b'bound candidate image for umask mode')
        report = root / 'report.json'
        report.write_bytes(json.dumps({'original_sha256': gate.ORIGINAL,
                                       'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
                                       'case_count': 1,
                                       'suites': {'pair': [{'original': {'logs': ['before']},
                                                             'candidate': {'logs': ['before']}}]}}).encode())
        argv = ['audit', '--candidate', str(candidate), '--report', str(report), '--output', str(output)]
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
                with tempfile.TemporaryDirectory(prefix='strict-logs-umask-') as temporary:
                    output = Path(temporary) / ('strict-' + oct(mask) + '.json')
                    self.assertEqual(self.invoke(output, mask), mode)


if __name__ == '__main__':
    unittest.main()
