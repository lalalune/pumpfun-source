#!/usr/bin/env python3
"""build_fee_selection records the source and rustc hashes it actually used.

The fake rustc rewrites the source file while the build runs. A builder
that hashes its inputs only after compiling publishes a comparison that
binds the object to a source (and compiler) that were never used; the
binding must be taken before the build and a change must fail the run.
The scenario is staged in a temporary tree so the real source is never
touched.
"""
import base64
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "build_fee_selection.py"
OBJECT_B64 = "f0VMRgIBAQAAAAAAAAAAAAEAPgABAAAAAAAAAAAAAAAAAAAAAAAAAOABAAAAAAAAAAAAAEAAAAAAAEAADAALAPMPHvpVSInluCoAAABdwwBHQ0M6IChVYnVudHUgMTMuMy4wLTZ1YnVudHUyfjI0LjA0LjEpIDEzLjMuMAAAAAAEAAAAEAAAAAUAAABHTlUAAgAAwAQAAAADAAAAAAAAABQAAAAAAAAAAXpSAAF4EAEbDAcIkAEAABwAAAAcAAAAAAAAAA8AAAAARQ4QhgJDDQZGDAcIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAQA8f8AAAAAAAAAAAAAAAAAAAAAAAAAAAMAAQAAAAAAAAAAAAAAAAAAAAAABQAAABIAAQAAAAAAAAAAAA8AAAAAAAAAAHQuYwBzZWxlY3RfZmVlX3RpZXIAAAAAIAAAAAAAAAACAAAAAgAAAAAAAAAAAAAAAC5zeW10YWIALnN0cnRhYgAuc2hzdHJ0YWIALnRleHQuc2VsZWN0X2ZlZV90aWVyAC5kYXRhAC5ic3MALmNvbW1lbnQALm5vdGUuR05VLXN0YWNrAC5ub3RlLmdudS5wcm9wZXJ0eQAucmVsYS5laF9mcmFtZQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsAAAABAAAABgAAAAAAAAAAAAAAAAAAAEAAAAAAAAAADwAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAxAAAAAQAAAAMAAAAAAAAAAAAAAAAAAABPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAANwAAAAgAAAADAAAAAAAAAAAAAAAAAAAATwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAADwAAAABAAAAMAAAAAAAAAAAAAAAAAAAAE8AAAAAAAAALgAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAQAAAAAAAABFAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAB9AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAVQAAAAcAAAACAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAG0AAAABAAAAAgAAAAAAAAAAAAAAAAAAAKAAAAAAAAAAOAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAAAAABoAAAABAAAAEAAAAAAAAAAAAAAAAAAAABQAQAAAAAAABgAAAAAAAAACQAAAAcAAAAIAAAAAAAAABgAAAAAAAAAAQAAAAIAAAAAAAAAAAAAAAAAAAAAAAAA2AAAAAAAAABgAAAAAAAAAAoAAAADAAAACAAAAAAAAAAYAAAAAAAAAAkAAAADAAAAAAAAAAAAAAAAAAAAAAAAADgBAAAAAAAAFQAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAARAAAAAwAAAAAAAAAAAAAAAAAAAAAAAABoAQAAAAAAAHcAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAA"
FAKE_RUSTC = """#!{python}
import pathlib, shutil, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("rustc 1.44.0-fake")
    sys.exit(0)
source = next(a for a in argv if a.endswith(".rs"))
if "{mutate}":
    pathlib.Path(source).write_bytes(pathlib.Path(source).read_bytes() + bytes([10]) + b"// changed during build" + bytes([10]))
out = argv[argv.index("-o") + 1]
shutil.copy(pathlib.Path(__file__).with_name("obj.o"), out)
"""
SOURCE_TEXT = "pub fn select_fee_tier() -> u64 { 0 }\n"


class BuildFeeSelectionBindingTests(unittest.TestCase):
    def stage(self, temporary, mutate):
        root = Path(temporary) / "repo"
        script = root / "scripts" / "build_fee_selection.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(SCRIPT.read_bytes())
        source = root / "programs" / "pump-fees" / "recovered" / "fee_selection.rs"
        source.parent.mkdir(parents=True)
        source.write_text(SOURCE_TEXT)
        deployed = root / "evidence" / "original" / "pump_fees" / "deployed.so"
        deployed.parent.mkdir(parents=True)
        deployed.write_bytes(bytes(0xAB2D0))
        toolchain = Path(temporary) / "toolchain"
        rustc = toolchain / "rust" / "bin" / "rustc"
        rustc.parent.mkdir(parents=True)
        rustc.write_text(FAKE_RUSTC.format(python=sys.executable, mutate="1" if mutate else ""))
        (toolchain / "rust" / "bin" / "obj.o").write_bytes(base64.b64decode(OBJECT_B64))
        os.chmod(rustc, 0o755)
        output = Path(temporary) / "out"
        completed = subprocess.run([sys.executable, "-B", str(script), "--toolchain", str(toolchain),
                                    "--output", str(output)], capture_output=True, text=True)
        return completed, output, source

    def test_source_changed_during_build_fails_and_publishes_no_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output, _ = self.stage(temporary, mutate=True)
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertFalse((output / "comparison.json").exists())

    def test_unchanged_source_publishes_matching_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output, _ = self.stage(temporary, mutate=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((output / "comparison.json").read_text())
            self.assertEqual(report["source_sha256"],
                             hashlib.sha256(SOURCE_TEXT.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
