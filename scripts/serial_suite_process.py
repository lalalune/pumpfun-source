"""Bound serial suites; terminate their process group on POSIX.

The Windows fallback retains subprocess.run's single-process timeout behavior.
It does not claim to terminate detached descendants or a Windows process tree.
"""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
from build_process import run_compiler, validate_timeout

PROCESS_INPUTS = (Path(__file__).resolve(), Path(run_compiler.__code__.co_filename).resolve())
USE_PROCESS_GROUPS = os.name == 'posix'


def run_suite_process(command, *, timeout, **kwargs):
    validate_timeout(timeout)
    if USE_PROCESS_GROUPS:
        return run_compiler(command, timeout=timeout, **kwargs)
    try:
        # Retain inherited streams on Windows. A PIPE held by a descendant can
        # keep communicate() blocked after the leader has been killed.
        completed = subprocess.run(command, timeout=timeout, **kwargs)
        return completed, False
    except subprocess.TimeoutExpired as error:
        output = error.output or ''
        if isinstance(output, bytes):
            output = output.decode('utf-8', 'replace')
        return subprocess.CompletedProcess(command, -1, output), True
