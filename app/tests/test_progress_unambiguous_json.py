import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/progress.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)
import tempfile
from unittest.mock import patch

class DuplicateTests(unittest.TestCase):

    def test_duplicate_state_keys_do_not_select_last_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'input.json').write_text('{"status":"pending","status":"accepted"}', encoding='utf-8')
            with patch.object(subject, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'Duplicate progress JSON key'):
                    subject.read('input.json')
            (root / 'input.json').write_text('{"left":{"value":1},"right":{"value":2}}', encoding='utf-8')
            with patch.object(subject, 'ROOT', root):
                self.assertEqual(subject.read('input.json')['right']['value'], 2)
