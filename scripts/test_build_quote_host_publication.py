#!/usr/bin/env python3
"""The native quote host appears only after all three compile steps succeed."""
from pathlib import Path
import contextlib
import io
import runpy
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/build_quote_host.py'


class Compiler:
    """Stand in for rustc: write each `-o` target, or fail at one step."""

    def __init__(self, fail_at=None):
        self.fail_at = fail_at
        self.calls = 0

    def __call__(self, command, check=False):
        self.calls += 1
        if self.calls == self.fail_at:
            raise subprocess.CalledProcessError(1, command)
        Path(command[command.index('-o') + 1]).write_bytes(b'artifact')
        return subprocess.CompletedProcess(command, 0)


def build(output, compiler):
    with mock.patch.object(subprocess, 'run', compiler), \
            mock.patch.object(sys, 'argv', [str(SCRIPT), '--output', str(output)]), \
            mock.patch.object(sys, 'path', [str(ROOT / 'scripts'), *sys.path]), \
            contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(SCRIPT), run_name='__main__')


class QuoteHostPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='quote-host-')
        self.addCleanup(temporary.cleanup)
        self.work = Path(temporary.name)
        self.output = self.work / 'nested' / 'quote-host'

    def test_failed_compile_leaves_no_output(self):
        for step in (1, 2, 3):
            with self.subTest(step=step):
                output = self.work / str(step) / 'quote-host'
                with self.assertRaises(subprocess.CalledProcessError):
                    build(output, Compiler(fail_at=step))
                self.assertFalse(output.exists())
                self.assertEqual(list(output.parent.iterdir()), [])

    def test_rerun_after_a_failed_compile_builds(self):
        with self.assertRaises(subprocess.CalledProcessError):
            build(self.output, Compiler(fail_at=2))
        try:
            build(self.output, Compiler())
        except FileExistsError as error:
            self.fail(f'failed build blocked the rerun: {error}')
        self.assertTrue((self.output / 'quote-fees-host').is_file())

    def test_complete_output_keeps_every_artifact(self):
        build(self.output, Compiler())
        self.assertEqual(sorted(path.name for path in self.output.iterdir()),
                         ['libpump_fees_math.rlib', 'libpump_quote_fees.rlib', 'quote-fees-host'])

    def test_existing_output_is_refused_before_any_compile(self):
        self.output.mkdir(parents=True)
        keep = self.output / 'keep'
        keep.write_bytes(b'prior')
        compiler = Compiler()
        with self.assertRaises(FileExistsError):
            build(self.output, compiler)
        self.assertEqual(compiler.calls, 0)
        self.assertEqual(keep.read_bytes(), b'prior')


if __name__ == '__main__':
    unittest.main()
