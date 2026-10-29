import copy
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    'progress_script_hash',
    pathlib.Path(__file__).resolve().parents[1] / 'scripts/progress.py',
)
progress = importlib.util.module_from_spec(spec)
spec.loader.exec_module(progress)


class ProgressScriptHash(unittest.TestCase):
    def test_recorded_script_hash_must_match_before_a_report_is_rendered(self):
        original = progress.read
        manifest = original('evidence/web/manifest.json')
        record = next(
            row for row in manifest['records']
            if row['url'].endswith('.js') and row.get('status') == 200
        )
        changed = copy.deepcopy(manifest)
        row = next(item for item in changed['records'] if item['path'] == record['path'])
        row['sha256'] = '0' * 64

        def read(path):
            return changed if path == 'evidence/web/manifest.json' else original(path)

        with patch.object(progress, 'read', read):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                progress.render()

        row.pop('sha256')
        with patch.object(progress, 'read', read):
            with self.assertRaisesRegex(ValueError, 'hash mismatch'):
                progress.render()


if __name__ == '__main__':
    unittest.main()
