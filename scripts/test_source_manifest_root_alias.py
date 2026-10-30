"""Accept repository paths whose root is reached through an alias."""

import tempfile
import unittest
from pathlib import Path

from build_source_manifest import source_manifest
from source_manifest_guard import strict_manifest


class SourceManifestRootAliasTests(unittest.TestCase):
    def test_alias_root_and_inputs_bind_the_same_repository_files(self):
        with tempfile.TemporaryDirectory(prefix="manifest-root-alias-") as temporary:
            base = Path(temporary)
            repository = base / "repository"
            crate = repository / "crate"
            asset = repository / "assets/table.bin"
            crate.mkdir(parents=True)
            asset.parent.mkdir()
            (crate / "Cargo.toml").write_text("[package]\nname = \"fixture\"\n")
            (crate / "src").mkdir()
            (crate / "src/lib.rs").write_text("pub fn fixture() {}\n")
            asset.write_bytes(b"bound asset")

            alias = base / "repository-alias"
            alias.symlink_to(repository, target_is_directory=True)
            expected = source_manifest(crate, crate, repository, [asset])

            self.assertEqual(
                strict_manifest(
                    alias / "crate",
                    alias / "crate",
                    alias,
                    [alias / "assets"],
                ),
                expected,
            )


if __name__ == "__main__":
    unittest.main()
