#!/usr/bin/env python3
"""Regression tests: the frozen revalidator must not execute a verify.py
that is not a regular file inside the packet.

run_verify() used to check only exists() before running the packet's
verify.py, so a verify.py symlinked to a script outside the packet was
executed and its exit code became the packet's verdict. The successor
qualification audit already rejects a linked verifier; the frozen tool now
applies the same admission check before executing anything.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import revalidate_all


class RunVerifyAdmissionTests(unittest.TestCase):
    def test_symlinked_verify_py_is_rejected_without_executing(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            external = root / "external_verify.py"
            marker = root / "executed.marker"
            external.write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n"
                "print('EXTERNAL-VERIFIER-EXECUTED')\n"
            )
            packet = root / "packet"
            packet.mkdir()
            (packet / "verify.py").symlink_to(external)
            result = revalidate_all.run_verify(packet)
            self.assertEqual(result["status"], "fail")
            self.assertNotIn("EXTERNAL-VERIFIER-EXECUTED", result["output"])
            self.assertFalse(marker.exists(),
                             "the external script must not have been executed")

    def test_dangling_verifier_is_invalid_not_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary)
            (packet / "verify.py").symlink_to(packet / "missing.py")
            self.assertEqual(revalidate_all.run_verify(packet)["status"], "fail")

    def test_absent_verifier_remains_missing(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assertEqual(revalidate_all.run_verify(Path(temporary))["status"], "no_verify_script")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs require POSIX")
    def test_fifo_verifier_is_rejected_without_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary); os.mkfifo(packet / "verify.py")
            self.assertEqual(revalidate_all.run_verify(packet)["status"], "fail")

    def test_regular_verify_py_still_runs(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / "packet"
            packet.mkdir()
            (packet / "verify.py").write_text("print('packet verifier ok')\n")
            result = revalidate_all.run_verify(packet)
            self.assertEqual(result["status"], "pass")
            self.assertIn("packet verifier ok", result["output"])

    def test_directory_verify_py_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / "packet"
            (packet / "verify.py").mkdir(parents=True)
            result = revalidate_all.run_verify(packet)
            self.assertEqual(result["status"], "fail")


if __name__ == "__main__":
    unittest.main()
