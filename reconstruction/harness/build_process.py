"""Run a compiler process group with an optional bounded execution time (POSIX)."""
import math
import os
import signal
import subprocess


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
        except ProcessLookupError:
            pass

    timed_out = False
    try:
        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            stop_group()
            output, _ = process.communicate()
    except BaseException:
        stop_group()
        process.communicate()
        raise
    return subprocess.CompletedProcess(command, process.returncode, output), timed_out
