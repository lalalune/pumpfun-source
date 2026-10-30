#!/usr/bin/env python3
"""Reject retained archive aliases before downloading macOS toolchain inputs."""
import io
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_macos_frontier_qualification as target  # noqa: E402


class MacosFrontierArchivePublicationTests(unittest.TestCase):
    def test_verified_archive_is_published_and_partial_removed(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "toolchain.tar.bz2"
            raw = b"verified archive bytes"
            with mock.patch.object(target.urllib.request, "urlopen", return_value=io.BytesIO(raw)):
                target.download_archive(path, "https://example.invalid/archive", hashlib.sha256(raw).hexdigest())
            self.assertEqual(path.read_bytes(), raw)
            self.assertEqual(list(path.parent.iterdir()), [path])

    def test_digest_failure_removes_only_owned_partial(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "toolchain.tar.bz2"
            with mock.patch.object(target.urllib.request, "urlopen", return_value=io.BytesIO(b"wrong")):
                with self.assertRaises(ValueError):
                    target.download_archive(path, "https://example.invalid/archive", "0" * 64)
            self.assertEqual(list(path.parent.iterdir()), [])

    def test_partial_created_after_preflight_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "toolchain.tar.bz2"
            partial = path.with_name("." + path.name + ".partial")
            real_open = Path.open

            def race(file, mode="r", *args, **kwargs):
                if file == partial and mode == "xb":
                    partial.write_bytes(b"another writer's retained bytes")
                return real_open(file, mode, *args, **kwargs)

            with mock.patch.object(Path, "open", race), \
                    mock.patch.object(target.urllib.request, "urlopen") as download:
                with self.assertRaises(FileExistsError):
                    target.download_archive(path, "https://example.invalid/archive", "0" * 64)
            download.assert_not_called()
            self.assertEqual(partial.read_bytes(), b"another writer's retained bytes")
            self.assertFalse(path.exists())

    def test_symlinked_archive_is_rejected_before_its_target_is_modified(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            work = root / "work"
            work.mkdir()
            external = root / "external-toolchain.tar"
            external.write_bytes(b"external retained bytes\n")
            archive = work / "fixture.tar.bz2"
            try:
                archive.symlink_to(external)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f"symlinks are unavailable: {error}")
            spec = root / "inputs.json"
            spec.write_text(json.dumps({
                "archives": {
                    "fixture": {
                        "url": "https://example.invalid/tool.tar",
                        "sha256": "0" * 64,
                    },
                },
            }), encoding="utf-8")

            with mock.patch.object(target, "OUT", work), \
                    mock.patch.object(target, "EVIDENCE", work / "evidence"), \
                    mock.patch.object(target, "SPEC", spec), \
                    mock.patch.object(target.platform, "system", return_value="Darwin"), \
                    mock.patch.object(target.platform, "machine", return_value="arm64"), \
                    mock.patch.object(target.subprocess, "check_output",
                                      return_value="test-revision\n"), \
                    mock.patch.object(target.urllib.request, "urlopen",
                                      return_value=io.BytesIO(b"synthetic download")):
                with self.assertRaisesRegex(FileExistsError, "retained archive"):
                    target.main()

            self.assertEqual(external.read_bytes(), b"external retained bytes\n")
            self.assertTrue(archive.is_symlink())


if __name__ == "__main__":
    unittest.main()
