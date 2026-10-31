"""Regression tests for symlink, .cargo/toolchain, dangling-link, and FIFO admission in source_manifest_guard."""

import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from source_manifest_guard import strict_manifest


def _symlink_or_skip(testcase, link_path, target_path, *, target_is_directory=False):
    try:
        link_path.symlink_to(target_path, target_is_directory=target_is_directory)
    except OSError as error:
        if getattr(error, 'winerror', None) == 1314:
            testcase.skipTest('symlink privilege unavailable')
        raise


class SourceManifestGuardLinksAndSpecialsTests(unittest.TestCase):
    def _make_repo(self, base):
        root = (base / 'repo').resolve()
        workspace = root / 'workspace'
        crate = workspace / 'programs/pump'
        (crate / 'src').mkdir(parents=True)
        (crate / 'Cargo.toml').write_text('[package]\nname = "pump"\nversion = "0.1.0"\n', encoding='utf-8')
        (crate / 'src/lib.rs').write_text('pub fn entry() {}\n', encoding='utf-8')
        return root, workspace, crate

    def test_in_repo_symlinked_crate_workspace_and_cwd_are_rejected_before_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root, workspace, crate = self._make_repo(Path(directory))
            crate_link = workspace / 'programs/pump_link'
            _symlink_or_skip(self, crate_link, crate, target_is_directory=True)
            ws_link = root / 'workspace_link'
            _symlink_or_skip(self, ws_link, workspace, target_is_directory=True)
            sub = root / 'invocations/sub'
            sub.mkdir(parents=True)
            cwd_link = root / 'invocations/cwd_link'
            _symlink_or_skip(self, cwd_link, sub, target_is_directory=True)
            hop_parent = workspace / 'hop'
            hop_parent.mkdir()
            _symlink_or_skip(self, hop_parent / 'programs_hop', workspace / 'programs', target_is_directory=True)
            dotdot_crate = hop_parent / 'programs_hop/../programs/pump'

            with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                with self.subTest('symlinked crate'):
                    with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                        strict_manifest(crate_link, workspace, root)
                with self.subTest('symlinked workspace'):
                    with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                        strict_manifest(crate, ws_link, root)
                with self.subTest('symlinked cwd'):
                    with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                        strict_manifest(crate, workspace, root, cwd=cwd_link)
                with self.subTest('dotdot across symlinked component'):
                    with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                        strict_manifest(dotdot_crate, workspace, root)

    def test_cargo_directory_and_toolchain_links_are_rejected_before_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, workspace, crate = self._make_repo(base)
            empty_dir = (base / 'outside-empty').resolve()
            empty_dir.mkdir()

            with self.subTest('symlinked .cargo directory'):
                _symlink_or_skip(self, root / '.cargo', empty_dir, target_is_directory=True)
                try:
                    with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                        with self.assertRaisesRegex(ValueError, 'symlinked directory'):
                            strict_manifest(crate, workspace, root)
                finally:
                    (root / '.cargo').unlink()

            with self.subTest('reparse-tagged .cargo directory'):
                (root / '.cargo').mkdir()
                real_lstat = os.lstat

                def marked_lstat(path, *args, **kwargs):
                    info = real_lstat(path, *args, **kwargs)
                    if Path(path) == root / '.cargo':
                        fields = {name: getattr(info, name) for name in dir(info) if name.startswith('st_')}
                        fields['st_reparse_tag'] = 0xA0000003
                        return SimpleNamespace(**fields)
                    return info

                try:
                    with patch.object(os, 'lstat', marked_lstat), \
                            patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                        with self.assertRaisesRegex(ValueError, 'reparse point'):
                            strict_manifest(crate, workspace, root)
                finally:
                    (root / '.cargo').rmdir()

            cwd_dir = root / 'runner'
            cwd_dir.mkdir()
            probes = [
                root / '.cargo/config',
                root / '.cargo/config.toml',
                root / 'rust-toolchain',
                root / 'rust-toolchain.toml',
                cwd_dir / '.cargo/config.toml',
                cwd_dir / 'rust-toolchain.toml',
                workspace / 'Cargo.lock',
            ]
            for probe in probes:
                with self.subTest(probe=str(probe.relative_to(root))):
                    probe.parent.mkdir(parents=True, exist_ok=True)
                    _symlink_or_skip(self, probe, base / 'missing-target')
                    try:
                        with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                            with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                                strict_manifest(crate, workspace, root, cwd=cwd_dir)
                    finally:
                        probe.unlink()

            # A real .cargo directory acting as CARGO_HOME with registry symlinks stays permitted
            # when config files are absent or plain regular files.
            (root / '.cargo/registry').mkdir(parents=True, exist_ok=True)
            _symlink_or_skip(self, root / '.cargo/registry/src', empty_dir, target_is_directory=True)
            (root / '.cargo/config.toml').write_text('[net]\noffline = true\n', encoding='utf-8')
            manifest = strict_manifest(crate, workspace, root, cwd=cwd_dir)
            self.assertIn('.cargo/config.toml', manifest)

    def test_dangling_symlinks_under_crate_idls_and_extra_inputs_are_rejected_before_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, workspace, crate = self._make_repo(base)
            (workspace / 'idls').mkdir()
            assets = root / 'assets'
            assets.mkdir()

            cases = [
                ('crate broken symlink', crate / 'src/broken.rs', ()),
                ('idls broken symlink', workspace / 'idls/broken.json', ()),
                ('extra_inputs dir broken symlink', assets / 'broken.bin', (assets,)),
            ]
            for label, link_path, extras in cases:
                with self.subTest(label):
                    _symlink_or_skip(self, link_path, base / 'does-not-exist')
                    try:
                        with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                            with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                                strict_manifest(crate, workspace, root, extras)
                    finally:
                        link_path.unlink()

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'POSIX named pipes required')
    def test_fifo_compiler_inputs_are_rejected_before_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root, workspace, crate = self._make_repo(base)
            (workspace / 'idls').mkdir()
            (root / '.cargo').mkdir()
            assets = root / 'assets'
            assets.mkdir()

            explicit_fifo = root / 'explicit.bin'
            os.mkfifo(explicit_fifo)
            with self.subTest('explicit extra_inputs fifo'):
                with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                    with self.assertRaisesRegex(ValueError, 'non-regular compiler input'):
                        strict_manifest(crate, workspace, root, [explicit_fifo])
            explicit_fifo.unlink()

            nested_fifos = [
                ('crate fifo', crate / 'src/pipe.rs', ()),
                ('idls fifo', workspace / 'idls/pipe.json', ()),
                ('assets fifo', assets / 'pipe.bin', (assets,)),
                ('.cargo config fifo', root / '.cargo/config.toml', ()),
                ('workspace Cargo.lock fifo', workspace / 'Cargo.lock', ()),
            ]
            for label, fifo_path, extras in nested_fifos:
                with self.subTest(label):
                    os.mkfifo(fifo_path)
                    try:
                        with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                            with self.assertRaisesRegex(ValueError, 'non-regular compiler input'):
                                strict_manifest(crate, workspace, root, extras)
                    finally:
                        fifo_path.unlink()

    def test_crate_outside_workspace_fails_without_probing_outside_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory).resolve()
            root, _, crate = self._make_repo(base)
            other_workspace = root / 'other_workspace'
            other_workspace.mkdir()
            real_lstat = os.lstat

            def guarded_lstat(path, *args, **kwargs):
                candidate = Path(path)
                if candidate == base / 'idls' or candidate == base.parent / 'idls':
                    raise AssertionError(f'probed outside repository: {candidate}')
                return real_lstat(path, *args, **kwargs)

            with patch.object(os, 'lstat', guarded_lstat):
                with self.assertRaises(ValueError):
                    strict_manifest(crate, other_workspace, root)


if __name__ == '__main__':
    unittest.main()
