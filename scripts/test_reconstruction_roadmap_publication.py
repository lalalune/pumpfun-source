#!/usr/bin/env python3
"""Roadmap packets must not adopt files left in an existing output directory."""
import contextlib
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from reconstruction_roadmap import generate_roadmap


ROOT = Path(__file__).resolve().parents[1]


class ReconstructionRoadmapPublicationTests(unittest.TestCase):
    def test_nonempty_output_is_rejected_without_modifying_retained_data(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packet"
            output.mkdir()
            retained = output / "foreign-retained.txt"
            retained.write_text("retained non-roadmap evidence\n", encoding="utf-8")

            completed = subprocess.run(
                [sys.executable, "-B", str(ROOT / "scripts/reconstruction_roadmap.py"),
                 "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("output directory is not empty", completed.stderr)
            self.assertEqual(retained.read_text(encoding="utf-8"),
                             "retained non-roadmap evidence\n")
            self.assertEqual([path.name for path in output.iterdir()],
                             ["foreign-retained.txt"])

    def test_attribution_order_does_not_depend_on_the_hash_seed(self):
        # trace_handler_attribution sorted (name, depth) sets by depth only, so
        # depth ties kept set order and the published likely_callers/callees
        # (and their [:5] cuts) varied with PYTHONHASHSEED between runs.
        import os

        probe = (
            "from types import SimpleNamespace;"
            "import json, sys;"
            "sys.path.insert(0, r'%SCRIPTS%');"
            "import reconstruction_roadmap as rr;"
            "elf = SimpleNamespace(funcs=[{'start': 0x100 + i, 'name': 'caller_%02d' % i} for i in range(8)]);"
            "reverse = {0x2000: {0x100 + i for i in range(8)}};"
            "attrib = rr.trace_handler_attribution(elf, [0x2000], {}, reverse);"
            "print(json.dumps([c[0] for c in attrib[0x2000]['likely_callers']]))"
        ).replace("%SCRIPTS%", str(Path(__file__).resolve().parent))
        results = []
        for seed in ("0", "1", "2"):
            completed = subprocess.run(
                [sys.executable, "-B", "-c", probe],
                env=dict(os.environ, PYTHONHASHSEED=seed),
                capture_output=True, text=True, cwd=ROOT)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            results.append(completed.stdout.strip())
        self.assertEqual(results[0], results[1])
        self.assertEqual(results[1], results[2])

    def test_packet_bytes_do_not_follow_the_host_line_ending(self):
        # Sibling of merged #2486/#2487 (analyze_program, deep_section_analysis):
        # roadmap packet files were written with host text-I/O defaults, so a
        # Windows publication carried CRLF bytes where a Linux one carries LF.
        # Model Windows text-I/O defaults at the actual file-open boundary.
        real_open = Path.open

        def windows_text_open(path, mode="r", buffering=-1, encoding=None,
                              errors=None, newline=None):
            if "b" not in mode and any(flag in mode for flag in "wax"):
                if newline is None:
                    newline = "\r\n"
                if encoding is None:
                    encoding = "cp1252"
            return real_open(path, mode, buffering=buffering, encoding=encoding,
                             errors=errors, newline=newline)

        with tempfile.TemporaryDirectory() as temporary:
            control = Path(temporary) / "control"
            output = Path(temporary) / "windows-defaults"
            with contextlib.redirect_stdout(io.StringIO()):
                generate_roadmap(control)
                with mock.patch.object(Path, "open", windows_text_open):
                    generate_roadmap(output)
            self.assertEqual(sorted(p.name for p in control.iterdir()),
                             sorted(p.name for p in output.iterdir()))
            for path in sorted(output.iterdir()):
                with self.subTest(entry=path.name):
                    self.assertEqual(path.read_bytes(),
                                     (control / path.name).read_bytes())
                    self.assertNotIn(b"\r", path.read_bytes())
            verified = subprocess.run(
                [sys.executable, "-B", str(output / "verify.py")],
                capture_output=True, text=True)
            self.assertEqual(verified.returncode, 0,
                             verified.stdout + verified.stderr)


if __name__ == "__main__":
    unittest.main()
