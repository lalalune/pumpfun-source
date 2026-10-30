#!/usr/bin/env python3
"""Revalidation audit packets must be byte-stable across host text defaults.

Sibling of merged #2486/#2487 (deep-section and analyze-program packets) and
open #2534 (roadmap packets). scripts/revalidate_all.py writes its whole
audit packet (results, summary, pass/fail lists, README, verify.py, manifest)
with host text-I/O defaults, so the same audit over identical inputs produces
different bytes on a Windows host (CRLF line endings, cp1252 for the README's
non-ASCII text) than on Linux, even though the packet carries a manifest of
SHA-256 hashes over those very files.
"""

import contextlib
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

import revalidate_all  # noqa: E402


def windows_text_open_factory(real_open):
    def windows_text_open(path, mode="r", buffering=-1, encoding=None,
                          errors=None, newline=None):
        # Model Windows text-I/O defaults at the actual file-open boundary.
        # Patching os.linesep alone does not change CPython TextIOWrapper.
        if "b" not in mode and any(flag in mode for flag in "wax"):
            if newline is None:
                newline = "\r\n"
            if encoding is None:
                encoding = "cp1252"
        return real_open(path, mode, buffering=buffering, encoding=encoding,
                         errors=errors, newline=newline)
    return windows_text_open


class RevalidateAllPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        packet = self.root / "research" / "fixture-packet"
        packet.mkdir(parents=True)
        source = b"fixture evidence bytes\n"
        (packet / "evidence.txt").write_bytes(source)
        (packet / "manifest.json").write_text(json.dumps({
            "evidence.txt": hashlib.sha256(source).hexdigest(),
        }), encoding="utf-8")

    def run_audit(self, output):
        argv = ["revalidate_all.py", "--output", str(output)]
        with mock.patch.object(revalidate_all, "REPO", self.root), \
                mock.patch.object(sys, "argv", argv), \
                mock.patch("time.time", return_value=1700000000.0), \
                contextlib.redirect_stdout(io.StringIO()):
            revalidate_all.main()

    def test_packet_bytes_do_not_follow_the_host_line_ending(self):
        # Capture the real opener before patching: reading Path.open inside
        # the replacement would recurse into the replacement itself.
        real_open = Path.open
        control = self.root / "control"
        windows = self.root / "windows-defaults"
        self.run_audit(control)
        with mock.patch.object(Path, "open",
                               windows_text_open_factory(real_open)):
            self.run_audit(windows)
        control_files = sorted(p.name for p in control.iterdir())
        self.assertEqual(control_files, sorted(p.name for p in windows.iterdir()))
        for name in control_files:
            with self.subTest(name=name):
                self.assertEqual((control / name).read_bytes(),
                                 (windows / name).read_bytes())

    def test_generated_verify_script_still_passes(self):
        output = self.root / "audit"
        self.run_audit(output)
        completed = subprocess.run([sys.executable, "-B", str(output / "verify.py")],
                                   capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
