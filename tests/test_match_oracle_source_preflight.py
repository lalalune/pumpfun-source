"""The match oracle refuses a workspace inside the source before writing there."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'reconstruction/harness'))
import match_oracle


class SourcePreflightTests(unittest.TestCase):
    def test_workspace_inside_source_is_rejected_without_writing(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary).resolve() / 'crate'
            source.mkdir()
            (source / 'Cargo.toml').write_text('[package]\n', encoding='utf-8')
            before = sorted(path.relative_to(source) for path in source.rglob('*'))
            with self.assertRaisesRegex(ValueError, 'source must not overlap'):
                match_oracle.evaluate(source, source / 'scratch', source / 'build', '0x0', 'raw', None)
            self.assertEqual(sorted(path.relative_to(source) for path in source.rglob('*')), before)


if __name__ == '__main__':
    unittest.main()
