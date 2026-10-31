#!/usr/bin/env python3
"""build_quote_fees records commands that name the selected paths.

The quote object receipt must label its compiler, source and output operands as
build_fee_selection does. Substring replacement also rewrote any output path that
merely started with the toolchain path, leaving a command that cannot be replayed.
"""
import base64
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "build_quote_fees.py"
SPEC = importlib.util.spec_from_file_location("quote_fees_binding_fixture", HERE / "test_build_quote_fees_binding.py")
FIXTURE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURE)
EXPECTED_OUTPUTS = {"libpump_fees_math.rlib", "quote_fees.o", "memory_compare.o"}


class CommandLabelTests(unittest.TestCase):
    def commands(self, temporary, toolchain_name, output_name):
        root = Path(temporary) / "repo"
        script = root / "scripts" / "build_quote_fees.py"
        script.parent.mkdir(parents=True)
        script.write_bytes(SCRIPT.read_bytes())
        recovered = root / "programs" / "pump-fees" / "recovered"
        recovered.mkdir(parents=True)
        for name, text in FIXTURE.SOURCES.items():
            (recovered / name).write_text(text)
        deployed = root / "evidence" / "original" / "pump_fees" / "deployed.so"
        deployed.parent.mkdir(parents=True)
        deployed.write_bytes(bytes(0x3F9D8))
        toolchain = Path(temporary) / toolchain_name
        rustc = toolchain / "rust" / "bin" / "rustc"
        rustc.parent.mkdir(parents=True)
        rustc.write_text(FIXTURE.FAKE_RUSTC.format(python=sys.executable, mutate=""))
        rustc.with_name("obj.o").write_bytes(base64.b64decode(FIXTURE.OBJECT_B64))
        os.chmod(rustc, 0o755)
        output = Path(temporary) / output_name
        completed = subprocess.run([sys.executable, "-B", str(script), "--toolchain", str(toolchain),
                                    "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads((output / "comparison.json").read_text())["commands"]

    def assert_labels(self, commands):
        self.assertEqual({command[0] for command in commands}, {"<toolchain>/rust/bin/rustc"})
        self.assertEqual({command[command.index("-o") + 1] for command in commands},
                         {"<output>/" + name for name in EXPECTED_OUTPUTS})
        self.assertIn("pump_fees_math=<output>/libpump_fees_math.rlib", commands[1])
        for command, source in zip(commands, ("fee_selection.rs", "quote_fees.rs", "memory_compare.rs")):
            self.assertIn("<repo>/programs/pump-fees/recovered/" + source, command)

    def test_separate_paths_keep_their_labels(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assert_labels(self.commands(temporary, "toolchain", "out"))

    def test_output_that_starts_with_the_toolchain_path_keeps_its_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assert_labels(self.commands(temporary, "sdk", "sdk-quote"))

    def test_output_inside_the_toolchain_keeps_its_label(self):
        with tempfile.TemporaryDirectory() as temporary:
            self.assert_labels(self.commands(temporary, "sdk", "sdk/quote"))


if __name__ == "__main__":
    unittest.main()
