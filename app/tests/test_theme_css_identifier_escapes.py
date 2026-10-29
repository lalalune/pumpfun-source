import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class UtilityEscapes(unittest.TestCase):

    def test_hex_escaped_responsive_prefix_does_not_hide_a_color(self):
        self.assertEqual(subject.extract_colors('.\\32 xl\\:bg-brand{background-color:#fff}'), {'brand': '#ffffff'})
        self.assertEqual(subject.utility_of('hover\\:bg-brand'), 'bg-brand')
        self.assertEqual(subject.extract_colors('.bg-\\62 rand{background-color:#123}'), {'brand': '#112233'})
