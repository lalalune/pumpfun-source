import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Tests(unittest.TestCase):

    def test_priority_is_not_part_of_a_color(self):
        self.assertEqual(subject.normalize_color('#fff !important'), '#ffffff')
        self.assertEqual(subject.normalize_color('rgb(1 2 3/var(--tw-bg-opacity,1))!IMPORTANT'), '#010203')
        self.assertEqual(subject.extract_colors('.bg-brand{background-color:#fff!important}.text-brand{color:#fff}'), {'brand': '#ffffff'})
