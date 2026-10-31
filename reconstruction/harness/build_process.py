"""Run a compiler process group with an optional bounded execution time (POSIX)."""
import math
import os
import signal
import subprocess
import sys
import time


# A compiler may leave a detached descendant holding the captured pipe open.
# Bound output draining after terminating the compiler process group so cleanup
# cannot extend a requested compiler timeout indefinitely.
TERMINATION_DRAIN_TIMEOUT = 1.0

# The compiler leaves its caller's process group, so an experiment timeout that
# kills that group cannot reach it. This helper outlives the caller and stops
# the compiler group when its stdin closes without the normal release byte.
GUARDIAN = ("import os, signal, sys\n"
            "if not sys.stdin.buffer.read(1):\n"
            "    os.killpg(int(sys.argv[1]), signal.SIGKILL)\n")


def validate_timeout(timeout):
    if timeout is not None and (isinstance(timeout, bool) or not isinstance(timeout, (int, float))
                                or not math.isfinite(timeout) or timeout <= 0):
        raise ValueError('compiler timeout must be a positive finite number of seconds')


def run_compiler(command, *, timeout=None, **kwargs):
    validate_timeout(timeout)
    kwargs.setdefault('encoding', 'utf-8')
    kwargs.setdefault('errors', 'replace')
    process = subprocess.Popen(command, start_new_session=True, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True, **kwargs)

    def stop_group():
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            # The session may already be gone after its leader exits while an
            # escaped descendant still owns a copy of the output pipe.
            pass

    def stop_and_collect():
        stop_group()
        deadline = time.monotonic() + TERMINATION_DRAIN_TIMEOUT
        try:
            output, _ = process.communicate(timeout=TERMINATION_DRAIN_TIMEOUT)
        except subprocess.TimeoutExpired as error:
            # TimeoutExpired output is bytes even when Popen uses text mode.
            output = error.output
            if process.stdout is not None:
                process.stdout.close()
            process.poll()
            remaining = deadline - time.monotonic()
            if process.returncode is None and remaining > 0:
                try:
                    process.wait(timeout=remaining)
                except subprocess.TimeoutExpired:
                    pass
        if isinstance(output, bytes):
            output = output.decode(process.encoding or 'utf-8', process.errors or 'strict')
        return output or ''

    timed_out = False
    guardian = None
    try:
        guardian = subprocess.Popen([sys.executable, '-I', '-S', '-c', GUARDIAN, str(process.pid)],
                                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            output = stop_and_collect()
        else:
            # A leader can exit while a descendant with redirected output is
            # still running. Stop the group before callers release build locks
            # or publish artifacts, just as on timeout or interruption.
            stop_group()
    except BaseException:
        stop_and_collect()
        raise
    finally:
        if guardian is not None:
            guardian.communicate(b'x')
    return subprocess.CompletedProcess(command, process.returncode, output), timed_out
