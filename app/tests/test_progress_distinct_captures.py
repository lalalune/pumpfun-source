import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('subject', Path(__file__).resolve().parents[1] / 'scripts/progress.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)
import copy

class CaptureTests(unittest.TestCase):

    def test_duplicate_capture_rows_cannot_inflate_the_denominator(self):
        real = subject.read
        manifest = copy.deepcopy(real('evidence/web/manifest.json'))
        record = next((r for r in manifest['records'] if r['url'].split('?')[0].endswith('.js')))
        manifest['records'].append(copy.deepcopy(record))
        with patch.object(subject, 'read', lambda path: manifest if path == 'evidence/web/manifest.json' else real(path)):
            with self.assertRaisesRegex(ValueError, 'Duplicate captured script'):
                subject.render()
