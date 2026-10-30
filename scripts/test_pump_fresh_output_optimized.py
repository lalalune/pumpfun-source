#!/usr/bin/env python3
"""Ensure Pump reports reject existing outputs under optimized Python."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
DIFFERENTIALS = ("pump_virtual_reserve_differential.py",)
ERROR = "Refusing to overwrite existing output"


def run(script, output, *arguments, environment=None):
    return subprocess.run(
        [
            sys.executable,
            *arguments,
            str(SCRIPTS / script),
            "--candidate",
            str(SCRIPTS / "missing-candidate.so"),
            "--output",
            str(output),
        ],
        cwd=SCRIPTS.parent,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class PumpFreshOutputOptimizedTests(unittest.TestCase):
    def check_rejection(self, script, arguments=(), environment=None):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "existing-report.json"
            output.write_text("existing report\n")
            completed = run(
                script, output, *arguments, environment=environment
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(ERROR, completed.stderr)
            self.assertEqual(output.read_text(), "existing report\n")

    def test_optimized_python_still_rejects_existing_output(self):
        for script in DIFFERENTIALS:
            with self.subTest(script=script):
                self.check_rejection(script, ("-O",))

    def test_pythonoptimize_environment_still_rejects_existing_output(self):
        environment = dict(os.environ, PYTHONOPTIMIZE="1")
        for script in DIFFERENTIALS:
            with self.subTest(script=script):
                self.check_rejection(script, environment=environment)

    def test_normal_python_still_rejects_existing_output(self):
        for script in DIFFERENTIALS:
            with self.subTest(script=script):
                self.check_rejection(script)

    def test_optimized_python_rejects_dangling_output_symlink(self):
        script = DIFFERENTIALS[0]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "dangling-report.json"
            output.symlink_to(Path(directory) / "missing-target.json")
            completed = run(script, output, "-O")
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn(ERROR, completed.stderr)
            self.assertTrue(output.is_symlink())

    def test_output_created_while_cases_run_is_not_replaced(self):
        sys.path.insert(0, str(SCRIPTS))
        import pump_virtual_reserve_differential as differential
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); candidate = root/'candidate.so'; candidate.write_bytes(b'candidate')
            output = root/'racing-report.json'
            def cases():
                output.write_bytes(b'report from another writer')
                return []
            with mock.patch.object(sys, 'argv', ['test', '--candidate', str(candidate), '--output', str(output)]), \
                    mock.patch.object(differential, 'cases', cases):
                with self.assertRaises(FileExistsError):
                    differential.main()
            self.assertEqual(output.read_bytes(), b'report from another writer')


if __name__ == "__main__":
    unittest.main()
