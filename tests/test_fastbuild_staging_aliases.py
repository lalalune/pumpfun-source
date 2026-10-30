"""A reused staging tree must not redirect writes into the original source."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import fastbuild
from source_inputs import snapshot

MANIFEST = ('[package]\nname="pump-recovered"\nversion="0.1.0"\n'
            '[lib]\ncrate-type=["cdylib"]\n'
            '[profile.release]\npanic="abort"\n[workspace]\n')


@unittest.skipUnless(shutil.which('rsync'), 'requires the real rsync staging command')
class StagingAliasTests(unittest.TestCase):
    def source(self, root):
        source = root / 'source'
        (source / 'src').mkdir(parents=True)
        (source / 'src/lib.rs').write_text('pub fn retained() {}\n')
        (source / 'Cargo.toml').write_text(MANIFEST)
        (source / 'Cargo.lock').write_text('version=3\n')
        return source

    def test_metadata_links_do_not_rewrite_their_source_targets(self):
        for relative in ('Cargo.toml', 'Cargo.lock', 'programs/pump/Cargo.toml'):
            for kind in ('symlink', 'hardlink'):
                with self.subTest(relative=relative, kind=kind), tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    source = self.source(root)
                    workspace = root / 'work/ws'
                    linked = workspace / relative
                    linked.parent.mkdir(parents=True)
                    if kind == 'symlink':
                        linked.symlink_to(source / 'Cargo.toml')
                    else:
                        os.link(source / 'Cargo.toml', linked)
                    before = snapshot(source)
                    error = None
                    try:
                        fastbuild.stage(source, workspace)
                    except ValueError as caught:
                        error = caught
                    self.assertEqual(snapshot(source), before, 'staging rewrote the original source')
                    self.assertIsNotNone(error, 'linked metadata was admitted')
                    self.assertIn('staging metadata', str(error))

    def test_linked_staging_directories_preserve_the_other_tree(self):
        for relative in ('.', 'programs', 'programs/pump'):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source = self.source(root)
                workspace = root / 'work/ws'
                outside = root / 'previous-workspace'
                outside.mkdir()
                (outside / 'retained').write_bytes(b'previous input')
                linked = workspace / relative
                linked.parent.mkdir(parents=True)
                linked.symlink_to(outside, target_is_directory=True)
                before = snapshot(outside)
                error = None
                try:
                    fastbuild.stage(source, workspace)
                except ValueError as caught:
                    error = caught
                self.assertEqual(snapshot(outside), before, 'staging changed the linked workspace')
                self.assertIsNotNone(error, 'linked directory was admitted')
                self.assertIn('staging directory', str(error))

    def test_real_build_cli_rejects_alias_before_source_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.source(root)
            work, output = root / 'work', root / 'output'
            crate = work / 'ws/programs/pump'
            crate.mkdir(parents=True)
            (crate / 'Cargo.toml').symlink_to(source / 'Cargo.toml')
            before = snapshot(source)
            result = subprocess.run([sys.executable, '-B', str(Path(fastbuild.__file__)),
                                     '--src', str(source), '--work', str(work), '--out', str(output)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(snapshot(source), before)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('staging metadata', result.stderr)
            self.assertFalse(output.exists())

    def test_ordinary_workspace_can_be_reused_without_touching_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.source(root)
            before = snapshot(source)
            workspace = root / 'work/ws'
            crate = fastbuild.stage(source, workspace)
            paths = [workspace / 'Cargo.toml', workspace / 'Cargo.lock', crate / 'Cargo.toml']
            staged = {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}
            self.assertEqual(fastbuild.stage(source, workspace), crate)
            self.assertEqual({path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths}, staged)
            self.assertEqual(snapshot(source), before)
            self.assertEqual((crate / 'src/lib.rs').read_bytes(), (source / 'src/lib.rs').read_bytes())


if __name__ == '__main__':
    unittest.main()
