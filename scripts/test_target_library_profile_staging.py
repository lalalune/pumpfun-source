#!/usr/bin/env python3
"""Regression tests: profile-manifest publication must not follow a planted
staging path.

finish() used to stage the file manifest at the fixed sibling name
``manifest.name + ".tmp"`` with a plain truncating write. A symlink planted
at that path redirected the write into an unrelated file, and the published
manifest itself ended up as that symlink while finish() still reported
``status="verified"`` with the hash read through the link. Publication now
goes through probe_report.write_json_report, which stages at an
unpredictable exclusively-created name.
"""
import json
import os
import stat
import subprocess
from pathlib import Path
import sys
import tempfile
import textwrap
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_target_library_profile as profile
import probe_report


class ProfileStagingTests(unittest.TestCase):
    def make_record(self, base):
        native = base / "native"
        prepared = base / "prepared"
        libraries = base / "libraries"
        out = base / "out"
        for directory in (native, prepared, libraries, out):
            directory.mkdir(parents=True, exist_ok=True)
        (native / "rust/bin").mkdir(parents=True)
        (native / "rust/bin/rustc").write_text("native-rustc\n")
        lib_rel = Path("rust/lib/rustlib/sbf-solana-solana/lib")
        (prepared / "rust/bin").mkdir(parents=True)
        (prepared / lib_rel).mkdir(parents=True)
        (prepared / lib_rel / "libcore.rlib").write_text("prepared-libcore\n")
        rustc = prepared / "rust/bin/rustc"
        rustc.write_text(
            "#!/bin/sh\n"
            f'if [ "$2" = "sysroot" ]; then echo "{prepared}/rust"; exit 0; fi\n'
            f'if [ "$2" = "target-libdir" ]; then echo "{prepared}/{lib_rel}"; exit 0; fi\n'
            "exit 1\n"
        )
        rustc.chmod(0o755)
        (libraries / "self-contained").mkdir()
        (libraries / "libfoo.rlib").write_text("libfoo\n")
        spec = base / "spec.json"
        spec.write_text("{}\n")
        manifest = out / "target-library-profile-files.json"
        record = {
            "profile_spec": str(spec),
            "profile_spec_sha256": profile.sha(spec),
            "implementation": str(Path(__file__).resolve().parent
                                  / "pump_target_library_profile.py"),
            "implementation_sha256": profile.sha(
                Path(__file__).resolve().parent
                / "pump_target_library_profile.py"),
            "native_sdk": str(native),
            "prepared_sdk": str(prepared),
            "library_source": str(libraries),
            "file_manifest": str(manifest),
            "cache_context": {
                "target": "sbf-solana-solana",
                "target_libraries": {
                    "libfoo.rlib": profile.sha(libraries / "libfoo.rlib")},
                "native_sdk_manifest_sha256": profile.digest(
                    profile.inventory(native)),
                "prepared_sdk_manifest_sha256": profile.digest(
                    profile.inventory(prepared)),
            },
        }
        return record, manifest

    def test_planted_staging_symlink_cannot_redirect_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            victim = manifest.parent / "victim-report.json"
            victim.write_text('{"sentinel": "do-not-touch"}\n')
            Path(str(manifest) + ".tmp").symlink_to(victim)
            result = profile.finish(dict(record))
            self.assertEqual(result["status"], "verified")
            self.assertEqual(victim.read_text(), '{"sentinel": "do-not-touch"}\n',
                             "publication followed the planted staging symlink")
            self.assertFalse(manifest.is_symlink(),
                             "published manifest must be a regular file")
            self.assertTrue(manifest.is_file())
            self.assertEqual(profile.sha(manifest),
                             result["file_manifest_sha256"])
            contents = json.loads(manifest.read_text())
            self.assertIn("rust/bin/rustc", contents["native"])

    def test_stale_regular_staging_file_does_not_corrupt_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            Path(str(manifest) + ".tmp").write_text(
                '{"native": {"FORGED": {}}, "prepared": {}}\n')
            result = profile.finish(dict(record))
            self.assertEqual(result["status"], "verified")
            self.assertFalse(manifest.is_symlink())
            contents = json.loads(manifest.read_text())
            self.assertNotIn("FORGED", contents["native"])
            self.assertEqual(profile.sha(manifest),
                             result["file_manifest_sha256"])
            self.assertFalse(Path(str(manifest) + ".tmp").exists()
                             and Path(str(manifest) + ".tmp").is_symlink())

    def test_exclusive_random_staging_retries_without_touching_a_link(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            victim = manifest.parent / "victim"
            victim.write_bytes(b"retained input")
            collision = manifest.with_name("." + manifest.name[:32] + ".4242.stale")
            collision.symlink_to(victim)
            with mock.patch.object(probe_report.os, "getpid", return_value=4242), \
                 mock.patch.object(probe_report.secrets, "token_hex", side_effect=["stale", "fresh"]):
                result = profile.finish(record)
            self.assertEqual(result["status"], "verified")
            self.assertTrue(collision.is_symlink())
            self.assertEqual(victim.read_bytes(), b"retained input")

    def test_late_destinations_are_never_replaced(self):
        for kind in ("file", "symlink", "hardlink", "directory"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                record, manifest = self.make_record(Path(temporary))
                victim = manifest.parent / "victim"
                victim.write_bytes(b"later writer")
                writer = profile.write_json_report
                def collide(path, value, **options):
                    if kind == "file":
                        path.write_bytes(b"later writer")
                    elif kind == "symlink":
                        path.symlink_to(victim)
                    elif kind == "hardlink":
                        os.link(victim, path)
                    else:
                        path.mkdir()
                    return writer(path, value, **options)
                with mock.patch.object(profile, "write_json_report", side_effect=collide):
                    with self.assertRaises(OSError):
                        profile.finish(record)
                self.assertEqual(victim.read_bytes(), b"later writer")
                if kind == "directory":
                    self.assertTrue(manifest.is_dir())
                else:
                    self.assertEqual(manifest.read_bytes(), b"later writer")
                self.assertEqual(list(manifest.parent.glob("." + manifest.name[:32] + ".*")), [])

    def test_dangling_destination_and_input_tree_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            target = manifest.parent / "missing-input"
            manifest.symlink_to(target)
            with self.assertRaisesRegex(AssertionError, "must not be a symlink"):
                profile.finish(record)
            self.assertTrue(manifest.is_symlink())
            self.assertFalse(target.exists())
            manifest.unlink()
            for key in ("native_sdk", "prepared_sdk", "library_source"):
                with self.subTest(key=key):
                    output = Path(record[key]) / "profile.json"
                    with self.assertRaisesRegex(AssertionError, "aliases an SDK or library input"):
                        profile.finish(dict(record, file_manifest=str(output)))
                    self.assertFalse(output.exists())

    def test_publication_failure_preserves_recreated_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            recreated = []
            def fail(source, destination):
                source = Path(source)
                # Retain the old inode so a filesystem cannot immediately reuse it.
                source.rename(source.with_name(source.name + ".owned"))
                source.write_bytes(b"later staging owner")
                recreated.append(source)
                raise OSError("controlled publication failure")
            publisher = "rename" if os.name == "nt" else "link"
            with mock.patch.object(probe_report.os, publisher, side_effect=fail):
                with self.assertRaisesRegex(OSError, "controlled publication failure"):
                    profile.finish(record)
            self.assertFalse(manifest.exists())
            self.assertEqual(recreated[0].read_bytes(), b"later staging owner")

    def test_parent_redirect_during_compiler_query_preserves_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            library = Path(record["library_source"])
            before = profile.inventory(library)
            query = profile.subprocess.check_output
            redirected = False
            def redirect(*args, **kwargs):
                nonlocal redirected
                result = query(*args, **kwargs)
                if not redirected:
                    manifest.parent.rename(manifest.parent.with_name("original-out"))
                    manifest.parent.symlink_to(library, target_is_directory=True)
                    redirected = True
                return result
            with mock.patch.object(profile.subprocess, "check_output", side_effect=redirect):
                with self.assertRaisesRegex(AssertionError, "manifest parent changed"):
                    profile.finish(record)
            self.assertEqual(profile.inventory(library), before)
            self.assertFalse(manifest.exists())

    def test_post_publication_replacement_is_retained_on_validation_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            writer = profile.write_json_report
            def replace_after(path, value, **options):
                writer(path, value, **options)
                path.write_bytes(b'{"later": "writer"}\n')
            with mock.patch.object(profile, "write_json_report", side_effect=replace_after):
                with self.assertRaisesRegex(AssertionError, "manifest content mismatch"):
                    profile.finish(record)
            self.assertEqual(manifest.read_bytes(), b'{"later": "writer"}\n')

    def test_manifest_hash_describes_the_bytes_that_were_validated(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            read = Path.read_bytes
            read_text = Path.read_text
            admitted = []
            def replace_after_read(path):
                raw = read(path)
                if path == manifest:
                    admitted.append(raw)
                    path.write_bytes(b'{"later": "writer"}\n')
                return raw
            def replace_after_text(path, *args, **kwargs):
                value = read_text(path, *args, **kwargs)
                if path == manifest:
                    admitted.append(value.encode())
                    path.write_bytes(b'{"later": "writer"}\n')
                return value
            with mock.patch.object(Path, "read_bytes", replace_after_read), \
                 mock.patch.object(Path, "read_text", replace_after_text):
                result = profile.finish(record)
            self.assertEqual(len(admitted), 1)
            self.assertEqual(result["file_manifest_sha256"], profile.hashlib.sha256(admitted[0]).hexdigest())
            self.assertEqual(manifest.read_bytes(), b'{"later": "writer"}\n')

    def test_windows_rename_consumes_staging_without_removing_its_replacement(self):
        # Simulate only the native rename contract; this is not a Windows run.
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            fsync = os.fsync
            link = os.link
            consumed = []
            platform = mock.patch.object(probe_report.os, "name", "nt")
            def set_windows(descriptor):
                fsync(descriptor)
                platform.start()
            def rename(source, destination):
                link(source, destination)  # raises if destination exists
                source.unlink()
                source.write_bytes(b"new staging owner")
                consumed.append(source)
            try:
                with mock.patch.object(probe_report.os, "fsync", side_effect=set_windows), \
                     mock.patch.object(probe_report.os, "rename", side_effect=rename):
                    probe_report.write_json_report(output, {"complete": True}, overwrite=False)
            finally:
                platform.stop()
            self.assertEqual(json.loads(output.read_bytes()), {"complete": True})
            self.assertEqual(consumed[0].read_bytes(), b"new staging owner")

    @unittest.skipUnless(os.name == "posix", "POSIX umask mode check")
    def test_fresh_manifest_retains_normal_umask_mode(self):
        with tempfile.TemporaryDirectory() as temporary:
            record, manifest = self.make_record(Path(temporary))
            previous = os.umask(0o027)
            try:
                profile.finish(record)
            finally:
                os.umask(previous)
            self.assertEqual(stat.S_IMODE(manifest.stat().st_mode), 0o640)

    def test_verified_builder_cli_reaches_profile_publication(self):
        # Exercise the real argparse/main integration with a fabricated SDK,
        # stopping explicitly before source staging or any compiler build.
        with tempfile.TemporaryDirectory() as temporary:
            driver = textwrap.dedent('''
                import json, sys
                from pathlib import Path
                from test_target_library_profile import Fixture, sha
                import pump_build_verified as builder
                root = Path(sys.argv[1]).resolve()
                fixture = Fixture(root, "")
                output = root / "verified"
                fixture.output = output / "profile-sdk"
                fixture.rustc.write_text("#!/bin/sh\\n"
                    + 'if [ "$2" = "sysroot" ]; then echo "' + str(fixture.output / "rust") + '"; exit 0; fi\\n'
                    + 'if [ "$2" = "target-libdir" ]; then echo "' + str(fixture.output / "rust/lib/rustlib/sbf-solana-solana/lib") + '"; exit 0; fi\\n'
                    + "exit 1\\n")
                fixture.spec["native_tools"]["rust/bin/rustc"] = sha(fixture.rustc)
                fixture.spec_path.write_text(json.dumps(fixture.spec))
                def stop_at_source(*args):
                    manifest = output / "target-library-profile-files.json"
                    if not manifest.is_file() or manifest.is_symlink():
                        raise RuntimeError("profile did not publish a regular manifest")
                    contents = json.loads(manifest.read_bytes())
                    if "rust/bin/rustc" not in contents["native"]:
                        raise RuntimeError("missing native inventory")
                    print("PROFILE_PUBLISHED_BEFORE_COMPILATION")
                    raise SystemExit(0)
                builder.source_manifest = stop_at_source
                sys.argv = ["pump_build_verified.py", "--sdk", str(fixture.native),
                    "--output", str(output), "--target-library-profile", "linux-v1.44-sbf",
                    "--target-library-directory", str(fixture.libraries)]
                with fixture.specification():
                    builder.main()
            ''')
            completed = subprocess.run([sys.executable, "-B", "-c", driver, temporary],
                cwd=Path(__file__).resolve().parent, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("PROFILE_PUBLISHED_BEFORE_COMPILATION", completed.stdout)


if __name__ == "__main__":
    unittest.main()
