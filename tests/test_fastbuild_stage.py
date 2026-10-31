"""Exercise the real rsync staging path without invoking a compiler or SDK."""
import importlib.util
import os
import subprocess
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


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


class FastbuildManifestAdmissionTests(unittest.TestCase):
    def make_source(self, root):
        source = Path(root) / "crate"
        source.mkdir()
        (source / "Cargo.toml").write_text(
            MANIFEST.replace(
                "[workspace]",
                "[profile.dev]\nopt-level = 1\n\n[workspace]",
            ),
            encoding="utf-8",
        )
        return source

    def test_unsupported_manifest_layout_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="fastbuild-manifest-") as temporary:
            source = self.make_source(temporary)
            with self.assertRaisesRegex(ValueError, "unsupported manifest layout"):
                fastbuild.stage(source, Path(temporary) / "workspace")

    @unittest.skipIf(os.name == "nt", "fastbuild requires POSIX fcntl")
    def test_unsupported_manifest_layout_is_rejected_under_optimized_python(self):
        with tempfile.TemporaryDirectory(prefix="fastbuild-manifest-optimized-") as temporary:
            source = self.make_source(temporary)
            code = (
                "import pathlib, sys;"
                "sys.path.insert(0, sys.argv[1]);"
                "import fastbuild;"
                "fastbuild.stage(pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]))"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-O",
                    "-B",
                    "-c",
                    code,
                    str(ROOT / "reconstruction/harness"),
                    str(source),
                    str(Path(temporary) / "workspace"),
                ],
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("unsupported manifest layout", completed.stderr)


class FastbuildOverlapGuardTests(unittest.TestCase):
    def test_output_below_case_alias_is_rejected_before_any_writes(self):
        with tempfile.TemporaryDirectory(prefix='source-case-overlap-') as temporary:
            root = Path(temporary).resolve()
            source = root / 'source'
            source.mkdir()
            alias = root / 'SOURCE'
            if not alias.exists() or not alias.samefile(source):
                self.skipTest('requires a case-insensitive filesystem')
            (source / 'preserved.txt').write_text('original source\n')
            before = fastbuild.snapshot(source)
            paths = sorted(p.relative_to(root).as_posix() for p in root.rglob('*'))
            with self.assertRaisesRegex(ValueError, 'source must not overlap'):
                fastbuild.build(source, root / 'work', alias / 'new-output')
            self.assertEqual(fastbuild.snapshot(source), before)
            self.assertEqual(sorted(p.relative_to(root).as_posix() for p in root.rglob('*')), paths)

    def test_output_directory_containing_the_source_is_rejected(self):
        # build() used to reject only src==out and src inside out; an output
        # directory that is an ANCESTOR of the source passed the guard and the
        # build then archived and wrote outputs inside the tree holding src.
        from unittest import mock

        with tempfile.TemporaryDirectory(prefix="fastbuild-overlap-") as temporary:
            out = Path(temporary) / "lane"
            src = out / "crate"
            src.mkdir(parents=True)
            work = Path(temporary) / "work"
            with mock.patch.object(
                    fastbuild, "workspace_lock",
                    side_effect=AssertionError("the overlap guard passed")):
                with self.assertRaisesRegex(ValueError, "overlap"):
                    fastbuild.build(src, work, out)

    def test_disjoint_directories_reach_the_workspace_lock(self):
        from unittest import mock

        with tempfile.TemporaryDirectory(prefix="fastbuild-disjoint-") as temporary:
            src = Path(temporary) / "crate"
            src.mkdir()
            work = Path(temporary) / "work"
            out = Path(temporary) / "out"
            with mock.patch.object(
                    fastbuild, "workspace_lock",
                    side_effect=RuntimeError("reached the lock")) as locked:
                with self.assertRaisesRegex(RuntimeError, "reached the lock"):
                    fastbuild.build(src, work, out)
            locked.assert_called_once()


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

    def test_restored_source_edit_does_not_admit_different_staged_bytes(self):
        source = self.src / "src/lib.rs"
        original = source.read_bytes()
        transient = b"pub const TRANSIENT: u8 = 2;\n"
        expected = fastbuild.snapshot(self.src)
        actual_run = subprocess.run

        def copy_during_edit(command, *args, **kwargs):
            self.assertEqual(command[0], "rsync")
            source.write_bytes(transient)
            try:
                return actual_run(command, *args, **kwargs)
            finally:
                source.write_bytes(original)

        error = None
        with patch.object(fastbuild.subprocess, "run", side_effect=copy_during_edit):
            try:
                fastbuild.stage(self.src, self.ws)
            except ValueError as caught:
                error = caught

        fastbuild.assert_unchanged(self.src, expected)
        self.assertEqual((self.ws / "programs/pump/src/lib.rs").read_bytes(), transient)
        self.assertIsInstance(error, ValueError, "source receipt admitted different staged bytes")
        self.assertIn("src/lib.rs", str(error))

    def test_build_binds_stage_to_its_preexisting_admitted_snapshot(self):
        source = self.src / "src/lib.rs"
        original = source.read_bytes()
        transient = b"pub const TRANSIENT: u8 = 3;\n"
        expected = fastbuild.snapshot(self.src)
        actual_stage = fastbuild.stage

        def enter_during_edit(*args, **kwargs):
            source.write_bytes(transient)
            try:
                return actual_stage(*args, **kwargs)
            finally:
                source.write_bytes(original)

        work = Path(self.tmp.name) / "build work"
        output = Path(self.tmp.name) / "output"
        output.mkdir()
        prior = output / "candidate.so"
        prior.write_bytes(b"prior binary must be preserved")
        recipe = {"triple": "fixture", "rustc": work / "absent-rustc",
                  "template": work / "absent-template"}
        error = None
        with patch.object(fastbuild, "stage", side_effect=enter_during_edit), \
             patch.object(fastbuild, "SDK", work / "absent-sdk"), \
             patch.object(fastbuild, "LOCKDIR", work / "locks"), \
             patch.dict(fastbuild.RECIPES, {"isolated": recipe}), \
             patch.object(fastbuild, "run_compiler",
                          side_effect=RuntimeError("compiler boundary must not be reached")) as compiler:
            try:
                fastbuild.build(self.src, work, output, recipe="isolated", quiet=True)
            except (ValueError, RuntimeError) as caught:
                error = caught

        fastbuild.assert_unchanged(self.src, expected)
        self.assertEqual((work / "ws/programs/pump/src/lib.rs").read_bytes(), transient)
        self.assertIsInstance(error, ValueError, "build used a replacement source snapshot")
        self.assertIn("src/lib.rs", str(error))
        compiler.assert_not_called()
        self.assertEqual(prior.read_bytes(), b"prior binary must be preserved")
        self.assertFalse((output / "previous").exists())


class FastbuildStagedOutputTests(unittest.TestCase):
    """Exercise real staging and retention, stopping at an absent compiler executable."""

    previous = {
        "candidate.so": b"prior candidate",
        "unstripped.so": b"prior unstripped",
        "build.log": b"prior compiler log",
        "source-inputs.json": b"prior source receipt",
        "link-receipt.json": b"prior link receipt",
        "link.map": b"prior link map",
    }

    def fixture(self, root):
        source, work = root / "source", root / "work"
        (source / "src").mkdir(parents=True)
        (source / "Cargo.toml").write_text(MANIFEST, encoding="utf-8")
        (source / "Cargo.lock").write_text("version = 3\n", encoding="utf-8")
        (source / "src/lib.rs").write_text("pub fn fixture() {}\n", encoding="utf-8")
        return source, work

    def seed(self, output):
        output.mkdir(parents=True, exist_ok=True)
        for name, data in self.previous.items():
            (output / name).write_bytes(data)
        older = output / "previous/build-old/receipt.json"
        older.parent.mkdir(parents=True)
        older.write_bytes(b"older retained evidence")

    def tree(self, root):
        return {path.relative_to(root).as_posix():
                ("link", os.readlink(path)) if path.is_symlink() else
                ("file", path.read_bytes()) if path.is_file() else ("directory",)
                for path in root.rglob("*")}

    def build(self, root, source, work, output):
        # Configure locations only: staging, locking and archiving remain real.
        # The absent SDK ensures no compiler can run even on the unfixed helper.
        recipe = {"triple": "fixture", "rustc": root / "absent-rustc",
                  "template": root / "absent-template"}
        with patch.object(fastbuild, "SDK", root / "absent-sdk"), \
             patch.object(fastbuild, "LOCKDIR", root / "locks"), \
             patch.dict(fastbuild.RECIPES, {"isolated": recipe}):
            return fastbuild.build(source, work, output, recipe="isolated", quiet=True)

    def test_staged_outputs_are_rejected_before_existing_evidence_changes(self):
        for layout in ("root", "nested", "alias"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                source, work = self.fixture(root)
                staged = work / "ws/programs/pump"
                output = staged if layout == "root" else staged / "published"
                self.seed(output)
                if layout == "alias":
                    alias = root / "output-alias"
                    alias.symlink_to(output, target_is_directory=True)
                    output = alias
                before = self.tree(root)
                error = None
                try:
                    self.build(root, source, work, output)
                except (ValueError, FileNotFoundError) as caught:
                    error = caught
                self.assertEqual(self.tree(root), before, "rejected build changed prior evidence")
                self.assertIsInstance(error, ValueError)
                self.assertIn("staged source", str(error))

    def test_new_staged_output_is_rejected_before_workspace_creation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            source, work = self.fixture(root)
            before = self.tree(root)
            with self.assertRaisesRegex(ValueError, "staged source"):
                self.build(root, source, work, work / "ws/programs/pump/new-output")
            self.assertEqual(self.tree(root), before)

    def test_supported_outputs_archive_evidence_before_missing_tool_failure(self):
        for layout in ("shared", "default", "separate"):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                source, work = self.fixture(root)
                output = {"shared": work, "default": work / "last",
                          "separate": root / "output"}[layout]
                self.seed(output)
                before_source = self.tree(source)
                with self.assertRaises(FileNotFoundError) as caught:
                    self.build(root, source, work, output)
                self.assertEqual(caught.exception.filename, str(root / "absent-sdk/rust/bin/cargo"))
                self.assertEqual(self.tree(source), before_source)
                archives = [path for path in (output / "previous").iterdir()
                            if path.name != "build-old"]
                self.assertEqual(len(archives), 1)
                for name, data in self.previous.items():
                    self.assertEqual((archives[0] / name).read_bytes(), data)
                self.assertEqual((output / "previous/build-old/receipt.json").read_bytes(),
                                 b"older retained evidence")


if __name__ == "__main__":
    unittest.main()
