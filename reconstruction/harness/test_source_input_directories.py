"""Source receipts must include directory inputs observable by build scripts."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from source_inputs import snapshot, assert_unchanged


class SourceDirectoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='source-directories-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / 'source'
        (self.source / 'src').mkdir(parents=True)
        (self.source / 'Cargo.toml').write_text(
            '[package]\nname="directory_probe"\nversion="0.1.0"\nedition="2021"\n'
            '[profile.release]\npanic="abort"\n[workspace]\n', encoding='utf-8')
        (self.source / 'Cargo.lock').write_text('version = 3\n', encoding='utf-8')
        (self.source / 'src/main.rs').write_text('fn main() {}\n', encoding='utf-8')

    def test_directory_add_remove_and_rename_change_receipt(self):
        before = snapshot(self.source)
        (self.source / 'settings/empty').mkdir(parents=True)
        added = snapshot(self.source)
        self.assertNotEqual(before['sha256'], added['sha256'])
        with self.assertRaisesRegex(ValueError, 'settings'):
            assert_unchanged(self.source, before)
        (self.source / 'settings/empty').rename(self.source / 'settings/renamed')
        self.assertNotEqual(added['sha256'], snapshot(self.source)['sha256'])
        (self.source / 'settings/renamed').rmdir()
        (self.source / 'settings').rmdir()
        self.assertEqual(before, snapshot(self.source))
        with self.assertRaisesRegex(ValueError, 'settings'):
            assert_unchanged(self.source, added)

    def test_directory_receipt_is_portable_and_preserves_exclusions(self):
        (self.source / 'settings/empty').mkdir(parents=True)
        (self.source / 'src/target/empty').mkdir(parents=True)
        receipt = snapshot(self.source)
        copy = self.root / 'copy'
        shutil.copytree(self.source, copy)
        os.utime(copy / 'settings', (1, 1))
        for directory in ('target/generated', '.git/objects', 'src/.git/objects'):
            (copy / directory).mkdir(parents=True)
        self.assertEqual(receipt, snapshot(copy))
        self.assertNotIn(str(self.root), json.dumps(receipt))
        self.assertIn('src/target/empty', receipt['directories'])

    @unittest.skipIf(os.name == 'nt', 'POSIX staging uses fcntl and rsync')
    def test_real_staging_checks_admitted_directory_membership(self):
        import fastbuild
        (self.source / 'settings/empty').mkdir(parents=True)
        admitted = snapshot(self.source)
        crate = fastbuild.stage(self.source, self.root / 'workspace', expected_inputs=admitted)
        self.assertTrue((crate / 'settings/empty').is_dir())
        (self.source / 'late').mkdir()
        with self.assertRaisesRegex(ValueError, 'staged source inputs.*late'):
            fastbuild.stage(self.source, self.root / 'workspace', expected_inputs=admitted)

    @unittest.skipIf(os.name == 'nt', 'POSIX staging uses fcntl and rsync')
    def test_transient_directory_copied_then_source_restored_is_rejected(self):
        import fastbuild
        admitted = snapshot(self.source)
        workspace = self.root / 'workspace'
        real_run = subprocess.run

        def copy_during_change(command, *args, **kwargs):
            self.assertEqual(command[0], 'rsync')
            (self.source / 'transient/empty').mkdir(parents=True)
            try:
                return real_run(command, *args, **kwargs)
            finally:
                (self.source / 'transient/empty').rmdir()
                (self.source / 'transient').rmdir()

        with mock.patch.object(fastbuild.subprocess, 'run', side_effect=copy_during_change):
            with self.assertRaisesRegex(ValueError, 'staged source inputs.*transient'):
                fastbuild.stage(self.source, workspace, expected_inputs=admitted)
        self.assertEqual(snapshot(self.source), admitted)
        self.assertTrue((workspace / 'programs/pump/transient/empty').is_dir())

    @unittest.skipIf(os.name == 'nt', 'POSIX staging uses fcntl and rsync')
    def test_reused_staging_removes_unbound_crate_root_lock(self):
        import fastbuild
        (self.source / 'path-crate').mkdir()
        nested_lock = b'version = 3\n# retained path-crate lock\n'
        (self.source / 'path-crate/Cargo.lock').write_bytes(nested_lock)
        admitted = snapshot(self.source)
        fresh = fastbuild.stage(self.source, self.root / 'fresh', expected_inputs=admitted)
        reused = fastbuild.stage(self.source, self.root / 'reused', expected_inputs=admitted)
        (reused / 'Cargo.lock').write_bytes(b'version = 3\n# unrelated stale lock\n')
        fastbuild.stage(self.source, self.root / 'reused', expected_inputs=admitted)
        self.assertFalse((reused / 'Cargo.lock').exists())
        self.assertEqual(snapshot(fresh), snapshot(reused))
        self.assertEqual((self.root / 'reused/Cargo.lock').read_bytes(),
                         (self.source / 'Cargo.lock').read_bytes())
        self.assertEqual((reused / 'path-crate/Cargo.lock').read_bytes(), nested_lock)
        self.assertEqual(snapshot(self.source), admitted)

    @unittest.skipIf(os.name == 'nt', 'POSIX staging uses fcntl and rsync')
    def test_staging_does_not_mask_an_unexpected_crate_root_lock(self):
        import fastbuild
        admitted = snapshot(self.source)
        workspace = self.root / 'workspace'
        real_run = subprocess.run

        def add_lock_after_copy(command, *args, **kwargs):
            result = real_run(command, *args, **kwargs)
            (workspace / 'programs/pump/Cargo.lock').write_bytes(b'stale lock')
            return result

        with mock.patch.object(fastbuild.subprocess, 'run', side_effect=add_lock_after_copy):
            with self.assertRaisesRegex(ValueError, 'staged source inputs.*Cargo.lock'):
                fastbuild.stage(self.source, workspace, expected_inputs=admitted)
        self.assertEqual(snapshot(self.source), admitted)

    @unittest.skipUnless(shutil.which('cargo') and shutil.which('rustc'), 'requires host Cargo and rustc')
    def test_real_cargo_observes_empty_directory_input(self):
        (self.source / 'src/main.rs').write_text(
            'fn main(){println!("{}",env!("DIRECTORY_PRESENT"));}\n', encoding='utf-8')
        (self.source / 'build.rs').write_text(
            'fn main(){println!("cargo:rustc-env=DIRECTORY_PRESENT={}",'
            'std::path::Path::new("settings").is_dir());}\n', encoding='utf-8')
        environment = dict(os.environ, CARGO_HOME=str(self.root / 'cargo-home'))
        for key in ('RUSTC_WRAPPER', 'RUSTC_WORKSPACE_WRAPPER', 'CARGO_BUILD_RUSTC_WORKSPACE_WRAPPER'):
            environment.pop(key, None)
        cargo = shutil.which('cargo')
        subprocess.run([cargo, 'generate-lockfile', '--offline'], cwd=self.source,
                       env=environment, check=True, capture_output=True)
        receipts, outputs = [], []
        for name in ('absent', 'empty'):
            if name == 'empty':
                (self.source / 'settings').mkdir()
            receipts.append(snapshot(self.source))
            target = self.root / name
            subprocess.run([cargo, 'build', '--offline', '--locked', '--target-dir', str(target)],
                           cwd=self.source, env=environment, check=True, capture_output=True)
            executable = target / 'debug' / ('directory_probe.exe' if os.name == 'nt' else 'directory_probe')
            outputs.append(subprocess.check_output([str(executable)], text=True).strip())
        self.assertEqual(outputs, ['false', 'true'])
        self.assertNotEqual(receipts[0]['sha256'], receipts[1]['sha256'])


if __name__ == '__main__':
    unittest.main()
