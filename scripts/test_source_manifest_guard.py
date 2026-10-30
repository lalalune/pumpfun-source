import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

from source_manifest_guard import strict_manifest


class SourceManifestGuardTests(unittest.TestCase):
    def test_reparse_tag_is_rejected_before_any_input_read(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = Path(directory)
            crate = repository / 'programs/pump'
            linked = crate / 'src/linked'
            linked.mkdir(parents=True)
            (linked / 'input.rs').write_text('must not be read', encoding='utf-8')
            lstat = os.lstat

            def marked(path, *args, **kwargs):
                info = lstat(path, *args, **kwargs)
                if Path(path) == linked:
                    fields = {name: getattr(info, name) for name in dir(info)
                              if name.startswith('st_')}
                    fields['st_reparse_tag'] = 0xA0000003
                    return SimpleNamespace(**fields)
                return info

            with patch.object(os, 'lstat', marked), \
                    patch.object(Path, 'read_bytes', side_effect=AssertionError('read before rejection')):
                with self.assertRaisesRegex(ValueError, 'reparse point'):
                    strict_manifest(crate, repository, repository)

    def test_symlink_is_rejected_before_any_input_byte_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / 'repository'
            crate = repository / 'programs/pump'
            (crate / 'src').mkdir(parents=True)
            outside = base / 'outside.rs'
            outside.write_text('must not be read', encoding='utf-8')
            try:
                (crate / 'src/lib.rs').symlink_to(outside)
            except OSError as error:
                if getattr(error, 'winerror', None) == 1314:
                    self.skipTest('creating a file symlink is not permitted')
                raise

            with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before symlink rejection')):
                with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                    strict_manifest(crate, repository, repository)

    @unittest.skipUnless(sys.platform == 'win32', 'NTFS junctions exist only on Windows')
    def test_junction_under_compiler_inputs_is_rejected(self):
        import _winapi

        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / 'repository'
            crate = repository / 'programs/pump'
            assets = repository / 'assets'
            (crate / 'src').mkdir(parents=True)
            assets.mkdir()
            (crate / 'src/lib.rs').write_text('fn main() {}\n', encoding='utf-8')
            (assets / 'outside.rs').write_text('must not be a compiler input\n', encoding='utf-8')
            _winapi.CreateJunction(os.fspath(assets), os.fspath(crate / 'src/linked'))

            with self.assertRaisesRegex(ValueError, 'linked directory'):
                strict_manifest(crate, repository, repository)


if __name__ == '__main__':
    unittest.main()
