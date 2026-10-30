"""Exercise the real rsync staging path without invoking a compiler or SDK."""
import importlib.util
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fastbuild", ROOT / "reconstruction/harness/fastbuild.py"
)
fastbuild = importlib.util.module_from_spec(SPEC)
# The builder imports sibling helpers, including under the workflow's -I mode.
sys.path.insert(0, str(ROOT / "reconstruction/harness"))
try:
    SPEC.loader.exec_module(fastbuild)
finally:
    sys.path.pop(0)

MANIFEST = '''[package]
name = "pump-recovered"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[profile.release]
panic = "abort"
overflow-checks = true
lto = false
codegen-units = 1

[workspace]
'''


class FastbuildStageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="fastbuild-stage-")
        self.addCleanup(self.tmp.cleanup)
        self.src = Path(self.tmp.name) / "source crate"
        self.ws = Path(self.tmp.name) / "workspace"
        self.write("Cargo.toml", MANIFEST.encode())
        self.write("Cargo.lock", b"version = 3\n")
        self.write("src/lib.rs", b"pub mod target;\n")

    def write(self, name, data):
        path = self.src / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def test_nested_target_inputs_are_staged_but_root_build_directory_is_not(self):
        self.write("Cargo.toml", MANIFEST.replace(
            "[profile.release]",
            '[dependencies]\nhelper = { path = "helper" }\n\n[profile.release]',
        ).encode())
        inputs = {
            "src/target/mod.rs": b"pub const VALUE: u8 = 1;\n",
            "helper/Cargo.toml": b'[package]\nname = "helper"\nversion = "0.1.0"\n',
            "helper/src/lib.rs": b"pub mod target;\n",
            "helper/src/target/mod.rs": b"pub const VALUE: u8 = 2;\n",
            "assets/target/data.bin": b"\x00\xff\r\n",
        }
        for name, data in inputs.items():
            self.write(name, data)
        self.write("target/debug/generated.o", b"generated build output")

        crate = fastbuild.stage(self.src, self.ws)

        for name, data in inputs.items():
            with self.subTest(path=name):
                path = crate / name
                self.assertTrue(path.is_file(), f"staging omitted {name}")
                self.assertEqual(path.read_bytes(), data)
        self.assertFalse((crate / "target").exists())
        self.assertNotIn("[profile.release]", (crate / "Cargo.toml").read_text())
        self.assertIn("[profile.release]", (self.ws / "Cargo.toml").read_text())
        self.assertEqual((self.ws / "Cargo.lock").read_bytes(), b"version = 3\n")

    def test_restage_updates_same_mtime_sources_and_deletes_removed_sources(self):
        name = "src/target/mod.rs"
        source = self.write(name, b"pub const VALUE: u8 = 1;\n")
        crate = fastbuild.stage(self.src, self.ws)
        self.assertTrue((crate / name).is_file(), "staging omitted the module")
        unchanged_mtime = (crate / "src/lib.rs").stat().st_mtime_ns
        before = source.stat()
        source.write_bytes(b"pub const VALUE: u8 = 2;\n")
        os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns))
        fastbuild.stage(self.src, self.ws)
        self.assertEqual((crate / name).read_bytes(), source.read_bytes())
        self.assertEqual((crate / "src/lib.rs").stat().st_mtime_ns, unchanged_mtime)

        source.unlink()
        (self.src / "src/lib.rs").write_bytes(b"pub const VALUE: u8 = 3;\n")
        fastbuild.stage(self.src, self.ws)
        self.assertFalse((crate / name).exists())
        self.assertEqual((crate / "src/lib.rs").read_bytes(), b"pub const VALUE: u8 = 3;\n")

    def test_regular_file_named_target_is_not_a_build_directory(self):
        self.write("src/lib.rs", b'pub const DATA: &[u8] = include_bytes!("../target");\n')
        self.write("target", b"source asset\x00")
        crate = fastbuild.stage(self.src, self.ws)
        self.assertTrue((crate / "target").is_file())
        self.assertEqual((crate / "target").read_bytes(), b"source asset\x00")


if __name__ == "__main__":
    unittest.main()
