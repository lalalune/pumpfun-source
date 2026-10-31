"""Cargo reads configuration from every parent of its working directory."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "dependency_cache_ancestor_config",
    ROOT / "scripts/pump_dependency_cache.py",
)
CACHE_MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CACHE_MODULE)
METADATA = json.dumps({
    "resolve": {"root": "main"},
    "packages": [{"id": "main", "name": "pump", "targets": [{"name": "pump", "kind": ["cdylib"]}]}],
})


class AncestorConfigTests(unittest.TestCase):
    def cache(self, root):
        crate = root / "outer/repo/programs/pump"
        crate.mkdir(parents=True, exist_ok=True)
        (crate / "Cargo.toml").write_text('[package]\nname = "pump"\n')
        (root / "sdk").mkdir(exist_ok=True)
        (root / "cargo-home").mkdir(exist_ok=True)
        wrapper = root / "wrapper"
        wrapper.write_text("wrapper")
        with mock.patch.object(CACHE_MODULE.subprocess, "check_output", return_value=METADATA):
            return CACHE_MODULE.DependencyCache(
                root / "cache", root / "outer/repo", crate, crate, root / "sdk",
                {"CARGO_HOME": str(root / "cargo-home")}, wrapper, direct=True)

    def test_config_above_the_repository_changes_the_key(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            ordinary = self.cache(root)
            config = root / "outer/.cargo/config.toml"
            config.parent.mkdir()
            config.write_text("[profile.release]\nopt-level = 0\n")
            changed = self.cache(root)
            self.assertIn(str(config), changed.context["configs"])
            self.assertNotEqual(changed.key, ordinary.key)


if __name__ == "__main__":
    unittest.main()
