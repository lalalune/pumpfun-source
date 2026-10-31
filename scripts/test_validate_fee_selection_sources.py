#!/usr/bin/env python3
"""The fee selector receipt binds both Rust files the native host is compiled from."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RECOVERED = ROOT / 'programs/pump-fees/recovered'
# Stand in for the compiled host by answering with the captured program's own
# results; only the published source binding is under test.
DRIVER = r'''
import runpy, subprocess, sys
root, host, output = sys.argv[1:]
sys.path.insert(0, root + '/scripts')
def run(command, **kwargs):
    answers = sys._getframe(1).f_globals['expected']
    stdout = ''.join(','.join(map(str, row)) + '\n' for row in answers)
    return subprocess.CompletedProcess(command, 0, stdout, '')
subprocess.run = run
sys.argv = ['validate_fee_selection.py', '--host', host, '--output', output]
runpy.run_path(root + '/scripts/validate_fee_selection.py', run_name='__main__')
'''


class FeeSelectionSourceBindingTests(unittest.TestCase):
    def test_receipt_binds_the_host_source(self):
        with tempfile.TemporaryDirectory(prefix='fee-selection-sources-') as temporary:
            host = Path(temporary) / 'host'
            host.write_bytes(b'stand-in host image')
            output = Path(temporary) / 'report.json'
            result = subprocess.run([sys.executable, '-B', '-c', DRIVER, str(ROOT), str(host), str(output)],
                                    capture_output=True, text=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
            report = json.loads(output.read_bytes())
        self.assertTrue(report['all_matched'])
        self.assertEqual(report['source_sha256'], {
            name: hashlib.sha256((RECOVERED / name).read_bytes()).hexdigest()
            for name in ('fee_selection.rs', 'fee_selection_host.rs')})


if __name__ == '__main__':
    unittest.main()
