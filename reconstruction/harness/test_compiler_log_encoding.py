import json
from pathlib import Path
import subprocess
import sys
import unittest


class CompilerLogEncodingTests(unittest.TestCase):
    def invoke(self, payload):
        # Force the wrapper process out of UTF-8 mode to exercise host-locale behavior.
        code = ('import json,sys;from build_process import run_compiler;'
                'r,t=run_compiler([sys.executable,"-c",'
                + repr('import sys;sys.stdout.buffer.write(' + repr(payload) + ')') + ']);'
                'print(json.dumps([r.returncode,r.stdout,t]))')
        run = subprocess.run([sys.executable, '-X', 'utf8=0', '-c', code],
                             cwd=Path(__file__).parent, capture_output=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def test_utf8_diagnostics_survive_a_non_utf8_host_locale(self):
        text = 'error: 경로 café\n'
        self.assertEqual(self.invoke(text.encode('utf-8')), [0, text, False])

    def test_malformed_diagnostic_bytes_do_not_abort_log_collection(self):
        self.assertEqual(self.invoke(b'error: bad \xff byte\n'),
                         [0, 'error: bad \ufffd byte\n', False])


if __name__ == '__main__': unittest.main()
