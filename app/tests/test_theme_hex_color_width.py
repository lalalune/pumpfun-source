import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Tests(unittest.TestCase):

    def test_invalid_hex_width_is_not_qualified_as_a_theme_color(self):
        for value in ('#12', '#12345', '#1234567', '#123456789'):
            with self.assertRaisesRegex(SystemExit, 'hexadecimal'):
                subject.normalize_color(value)
        self.assertEqual(subject.normalize_color('#abcd'), '#aabbccdd')
        self.assertEqual(subject.normalize_color('#abcdef'), '#abcdef')
