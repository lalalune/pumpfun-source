#!/usr/bin/env python3
"""Exercise the real Fees exact-source staging gate without a compiler or SDK."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "programs/pump-fees"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def builder(source=SOURCE):
    spec = importlib.util.spec_from_file_location("fees_exact_staging_under_test", SOURCE / "build_exact.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.HERE = source
    return module


class FeesExactStagingTests(unittest.TestCase):
    def test_current_source_stages_every_pinned_input(self):
        module = builder()
        with tempfile.TemporaryDirectory(prefix="fees exact staging ") as directory:
            workspace, mapping, expected = module.stage(Path(directory))
            self.assertEqual(set(mapping), set(expected))
            self.assertEqual(
                {p.relative_to(workspace).as_posix() for p in workspace.rglob("*") if p.is_file()},
                set(expected),
            )
            self.assertEqual(expected["programs/pump-fees/README.md"], sha(SOURCE / "exact/research-README.md"))
            for name, digest in expected.items():
                self.assertEqual(mapping[name]["sha256"], digest, name)
                self.assertEqual(sha(SOURCE / mapping[name]["canonical"]), digest, name)
                if name != "Cargo.toml":
                    self.assertEqual(sha(workspace / name), digest, name)
            # This pre-existing locator adaptation is explicit; all other bytes
            # come from the pinned inputs, including the current research README.
            original = (SOURCE / "exact/workspace-Cargo.toml").read_text()
            old = 'anchor-attribute-program = { path = "vendor/used-public" }'
            self.assertEqual(original.count(old), 1)
            self.assertEqual(
                (workspace / "Cargo.toml").read_text(),
                original.replace(old, 'anchor-attribute-program = { path = "' + module.MACRO + '" }'),
            )

    def rejected_copy(self, relative, change, message):
        with tempfile.TemporaryDirectory(prefix="fees exact rejection ") as directory:
            directory = Path(directory)
            source = directory / "source"
            shutil.copytree(SOURCE, source, ignore=shutil.ignore_patterns("__pycache__"))
            path = source / relative
            path.write_bytes(change(path.read_bytes()))
            output = directory / "output"
            output.mkdir()
            with self.assertRaisesRegex(ValueError, message):
                builder(source).stage(output)

    def test_changed_readme_remains_rejected(self):
        self.rejected_copy(
            "exact/research-README.md",
            lambda data: data + b"\nchanged staging input\n",
            r"canonical input changed: programs/pump-fees/README\.md",
        )

    def test_changed_rust_remains_rejected(self):
        self.rejected_copy(
            "src/lib.rs",
            lambda data: data + b"\n// changed staging input\n",
            r"canonical input changed: programs/pump-fees/src/lib\.rs",
        )

    def test_unreviewed_package_manifest_change_remains_rejected(self):
        self.rejected_copy(
            "Cargo.toml",
            lambda data: data + b"\n[package.metadata.stage-regression]\nchanged = true\n",
            "unexpected canonical package manifest",
        )


if __name__ == "__main__":
    unittest.main()
