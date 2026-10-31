"""A killed caller must not leave the compiler session running.

experiment_runner stops a timed-out trial with SIGKILL to the trial's process
group. The compiler started by run_compiler is in its own session.
"""
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time
import unittest

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))

import build_process

CALLER = """
import sys
sys.path.insert(0, sys.argv[1])
from build_process import run_compiler
fd = int(sys.argv[2])
script = 'import os, sys, time; os.write(%d, (str(os.getpid()) + chr(10)).encode()); time.sleep(30)' % fd
run_compiler([sys.executable, '-c', script], pass_fds=(fd,))
"""


class CallerKilledTests(unittest.TestCase):
    def read_until(self, descriptor, finished, deadline):
        data = b''
        while not finished(data):
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not select.select([descriptor], [], [], remaining)[0]:
                return data, False
            chunk = os.read(descriptor, 64)
            if not chunk:
                return data, True
            data += chunk
        return data, False

    def test_compiler_stops_with_its_caller(self):
        read_end, write_end = os.pipe()
        self.addCleanup(os.close, read_end)
        caller = subprocess.Popen([sys.executable, '-I', '-B', '-c', CALLER, str(H), str(write_end)],
                                  pass_fds=(write_end,))
        self.addCleanup(caller.wait)
        self.addCleanup(caller.kill)
        os.close(write_end)
        started, _ = self.read_until(read_end, lambda data: data.endswith(b'\n'), time.monotonic() + 20)
        self.assertTrue(started.endswith(b'\n'), 'compiler did not start')
        compiler = int(started)

        def stop_escaped_compiler():
            try:
                os.kill(compiler, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.addCleanup(stop_escaped_compiler)
        caller.kill()
        caller.wait()
        # Every copy of the write end closes only when the compiler has exited.
        _, closed = self.read_until(read_end, lambda data: False, time.monotonic() + 5)
        self.assertTrue(closed, 'compiler kept running after its caller was killed')


if __name__ == '__main__':
    unittest.main()
