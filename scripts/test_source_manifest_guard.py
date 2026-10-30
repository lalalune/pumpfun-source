import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from source_manifest_guard import strict_manifest


class SourceManifestGuardTests(unittest.TestCase):
    def test_symlink_is_rejected_before_any_input_byte_is_read(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            repository = base / 'repository'
            crate = repository / 'programs/pump'
            (crate / 'src').mkdir(parents=True)
            outside = base / 'outside.rs'
            outside.write_text('must not be read', encoding='utf-8')
            (crate / 'src/lib.rs').symlink_to(outside)

            with patch.object(Path, 'read_bytes', side_effect=AssertionError('read before symlink rejection')):
                with self.assertRaisesRegex(ValueError, 'symlinked compiler input'):
                    strict_manifest(crate, repository, repository)


if __name__ == '__main__':
    unittest.main()
