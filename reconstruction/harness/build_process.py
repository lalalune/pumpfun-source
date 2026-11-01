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


def validate_monitor(monitor, interval):
    if monitor is None:
        return
    if not callable(monitor):
        raise ValueError('compiler monitor must be callable')
    if (isinstance(interval, bool) or not isinstance(interval, (int, float))
            or not math.isfinite(interval) or interval <= 0):
        raise ValueError('compiler monitor interval must be a positive finite number')


def run_compiler(command, *, timeout=None, monitor=None, monitor_interval=1.0, **kwargs):
    """Run one owned compiler group.

    An optional monitor is polled while the compiler is alive. Returning a
    non-None value requests owned-group termination and is exposed as
    ``CompletedProcess.monitor_result``. The callback never receives a PID and
    cannot authorize signals to any other process.
    """
    validate_timeout(timeout)
    validate_monitor(monitor, monitor_interval)
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
    monitor_result = None
    guardian = None
    try:
        guardian = subprocess.Popen([sys.executable, '-I', '-S', '-c', GUARDIAN, str(process.pid)],
                                    stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = None if timeout is None else time.monotonic() + timeout
        while True:
            if monitor is not None:
                monitor_result = monitor()
                if monitor_result is not None:
                    output = stop_and_collect()
                    break
            remaining = None if deadline is None else deadline - time.monotonic()
            if remaining is not None and remaining <= 0:
                timed_out = True
                output = stop_and_collect()
                break
            wait = remaining
            if monitor is not None:
                wait = monitor_interval if wait is None else min(wait, monitor_interval)
            try:
                output, _ = process.communicate(timeout=wait)
            except subprocess.TimeoutExpired:
                # This may be the monitor cadence rather than the caller's
                # overall compiler deadline. Recheck both on the next loop.
                continue
            else:
                # A leader can exit while a descendant with redirected output is
                # still running. Stop the group before callers release build locks
                # or publish artifacts, just as on timeout or interruption.
                stop_group()
                break
    except BaseException:
        stop_and_collect()
        raise
    finally:
        if guardian is not None:
            guardian.communicate(b'x')
    result = subprocess.CompletedProcess(command, process.returncode, output)
    result.monitor_result = monitor_result
    return result, timed_out
