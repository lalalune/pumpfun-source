import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class SelectorTokens(unittest.TestCase):

    def test_selector_strings_cannot_invent_theme_utilities(self):
        self.assertEqual(subject.extract_colors('[data-name=".bg-fake"]{background-color:red}'), {})
        self.assertEqual(subject.extract_colors('.bg-real[data-name=".bg-fake"]{background-color:#fff}'), {'real': '#ffffff'})
