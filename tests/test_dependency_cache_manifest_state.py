"""Reject dependency-cache publication if Cargo manifests change during a build."""

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dependency_cache_manifest_state",
    ROOT / "scripts/pump_dependency_cache.py",
)
CACHE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CACHE_MODULE)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class DependencyCacheManifestStateTests(unittest.TestCase):
    def cache_fixture(self, root):
        workspace = root / "workspace"
        workspace.mkdir()
        manifests = {}
        for name in ("Cargo.toml", "Cargo.lock"):
            path = workspace / name
            path.write_text("[fixture]\nvalue = 'before'\n")
            manifests[name] = sha(path)

        target = root / "target"
        artifact = target / "release/deps/libdependency-0123456789abcdef.rlib"
        artifact.parent.mkdir(parents=True)
        artifact.write_bytes(b"synthetic dependency artifact")
        report = root / "build-comparison.json"
        report.write_text(json.dumps({"returncode": 0}) + "\n")
        log = root / "build.log"
        log.write_text("")

        cache = object.__new__(CACHE_MODULE.DependencyCache)
        cache.sources = {}
        cache.sdk = root / "sdk"
        cache.tools = {}
        cache.configs = {}
        cache.workspace = workspace
        cache.target = "sbf-solana-solana"
        cache.direct = True
        cache.record = {
            "main_command": ["synthetic-rustc"],
            "main_freshly_compiled": True,
        }
        cache.crates = {"dependency"}
        cache.packages = {"dependency"}
        cache.main_names = {"pump"}
        cache.context = {"manifests": manifests}
        cache.root = root / "cache"
        cache.key = "fixture-key"
        cache.entry = cache.root / cache.key
        return cache, target, log, report

    def test_manifest_changes_are_rejected_before_cache_publication(self):
        for name in ("Cargo.toml", "Cargo.lock"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                cache, target, log, report = self.cache_fixture(root)
                (cache.workspace / name).write_text("[fixture]\nvalue = 'after'\n")

                with self.assertRaisesRegex(
                    AssertionError, "Cargo manifests changed during build"
                ):
                    cache.finish(target, log, report)
                self.assertFalse(cache.entry.exists())

    def test_unchanged_manifests_still_publish(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache, target, log, report = self.cache_fixture(root)

            cache.finish(target, log, report)

            manifest = json.loads((cache.entry / "MANIFEST.json").read_text())
            self.assertEqual(manifest["context"], cache.context)
            self.assertEqual(cache.record["published_files"], 1)


if __name__ == "__main__":
    unittest.main()
