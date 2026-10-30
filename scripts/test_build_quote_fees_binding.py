#!/usr/bin/env python3
"""build_quote_fees records the source and rustc hashes it actually used.

The fake rustc rewrites quote_fees.rs while the builds run. A builder
that hashes its inputs only after compiling publishes a comparison that
binds the objects to a source (and compiler) that were never used; the
binding must be taken before the builds and a change must fail the run.
The scenario is staged in a temporary tree so the real sources are never
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

SCRIPT = Path(__file__).resolve().parent / "build_quote_fees.py"
OBJECT_B64 = "f0VMRgIBAQAAAAAAAAAAAAEAPgABAAAAAAAAAAAAAAAAAAAAAAAAAOgBAAAAAAAAAAAAAEAAAAAAAEAADAALAPMPHvpVSInluCoAAABdwwBHQ0M6IChVYnVudHUgMTMuMy4wLTZ1YnVudHUyfjI0LjA0LjEpIDEzLjMuMAAAAAAEAAAAEAAAAAUAAABHTlUAAgAAwAQAAAADAAAAAAAAABQAAAAAAAAAAXpSAAF4EAEbDAcIkAEAABwAAAAcAAAAAAAAAA8AAAAARQ4QhgJDDQZGDAcIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAQA8f8AAAAAAAAAAAAAAAAAAAAAAAAAAAMAAQAAAAAAAAAAAAAAAAAAAAAABQAAABIAAQAAAAAAAAAAAA8AAAAAAAAAAHQuYwBzZWxlY3RfZmVlX3RpZXIAAAAAIAAAAAAAAAACAAAAAgAAAAAAAAAAAAAAAC5zeW10YWIALnN0cnRhYgAuc2hzdHJ0YWIALnRleHQuZ2V0X2ZlZXNfd2l0aF9xdW90ZQAuZGF0YQAuYnNzAC5jb21tZW50AC5ub3RlLkdOVS1zdGFjawAubm90ZS5nbnUucHJvcGVydHkALnJlbGEuZWhfZnJhbWUAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAAEAAAAGAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAPAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAADUAAAABAAAAAwAAAAAAAAAAAAAAAAAAAE8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAA7AAAACAAAAAMAAAAAAAAAAAAAAAAAAABPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAQAAAAAEAAAAwAAAAAAAAAAAAAAAAAAAATwAAAAAAAAAuAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAAAAAEkAAAABAAAAAAAAAAAAAAAAAAAAAAAAAH0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAABZAAAABwAAAAIAAAAAAAAAAAAAAAAAAACAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAcQAAAAEAAAACAAAAAAAAAAAAAAAAAAAAoAAAAAAAAAA4AAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAGwAAAAEAAAAQAAAAAAAAAAAAAAAAAAAAFABAAAAAAAAGAAAAAAAAAAJAAAABwAAAAgAAAAAAAAAGAAAAAAAAAABAAAAAgAAAAAAAAAAAAAAAAAAAAAAAADYAAAAAAAAAGAAAAAAAAAACgAAAAMAAAAIAAAAAAAAABgAAAAAAAAACQAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAOAEAAAAAAAAVAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAABEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAGgBAAAAAAAAewAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAA="
FAKE_RUSTC = """#!{python}
import pathlib, shutil, sys
argv = sys.argv[1:]
if "--version" in argv:
    print("rustc 1.44.0-fake")
    sys.exit(0)
out = argv[argv.index("-o") + 1]
source = next(a for a in argv if a.endswith(".rs"))
if "{mutate}" and source.endswith("quote_fees.rs"):
    pathlib.Path(source).write_bytes(pathlib.Path(source).read_bytes() + bytes([10]) + b"// changed during build" + bytes([10]))
shutil.copy(pathlib.Path(__file__).with_name("obj.o"), out)
"""
SOURCES = {"fee_selection.rs": "pub fn a() -> u64 { 0 }\n",
           "quote_fees.rs": "pub fn b() -> u64 { 0 }\n",
           "memory_compare.rs": "pub fn c() -> u64 { 0 }\n"}


class BuildQuoteFeesBindingTests(unittest.TestCase):
    def stage(self, temporary, mutate):
        root = Path(temporary) / "repo"
        script = root / "scripts" / "build_quote_fees.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(SCRIPT.read_bytes())
        recovered = root / "programs" / "pump-fees" / "recovered"
        recovered.mkdir(parents=True)
        for name, text in SOURCES.items():
            (recovered / name).write_text(text)
        deployed = root / "evidence" / "original" / "pump_fees" / "deployed.so"
        deployed.parent.mkdir(parents=True)
        deployed.write_bytes(bytes(0x3F9D8))
        toolchain = Path(temporary) / "toolchain"
        rustc = toolchain / "rust" / "bin" / "rustc"
        rustc.parent.mkdir(parents=True)
        rustc.write_text(FAKE_RUSTC.format(python=sys.executable, mutate="1" if mutate else ""))
        (toolchain / "rust" / "bin" / "obj.o").write_bytes(base64.b64decode(OBJECT_B64))
        os.chmod(rustc, 0o755)
        output = Path(temporary) / "out"
        completed = subprocess.run([sys.executable, "-B", str(script), "--toolchain", str(toolchain),
                                    "--output", str(output)], capture_output=True, text=True)
        return completed, output

    def test_source_changed_during_build_fails_and_publishes_no_comparison(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output = self.stage(temporary, mutate=True)
            self.assertNotEqual(completed.returncode, 0, completed.stdout)
            self.assertFalse((output / "comparison.json").exists())

    def test_unchanged_sources_publish_matching_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            completed, output = self.stage(temporary, mutate=False)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            report = json.loads((output / "comparison.json").read_text())
            for name, text in SOURCES.items():
                self.assertEqual(report["source_sha256"][name],
                                 hashlib.sha256(text.encode()).hexdigest())


if __name__ == "__main__":
    unittest.main()
