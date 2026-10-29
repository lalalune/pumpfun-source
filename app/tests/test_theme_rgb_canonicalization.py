import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class RgbForms(unittest.TestCase):

    def test_rgb_case_spacing_and_clamped_channels_keep_color_identity(self):
        for value in ['RGB(255 0 0/var(--tw-bg-opacity,1))', 'rgb( 255 0 0 / var(--tw-text-opacity, 1) )', 'rgb(300 0 0/var(--tw-bg-opacity,1))']:
            with self.subTest(value=value):
                self.assertEqual(subject.normalize_color(value), '#ff0000')
        self.assertEqual(subject.normalize_color('rgb(1 2 3/var(--tw-bg-opacity,1))'), '#010203')
        self.assertEqual(subject.normalize_color('rgb(-2 0 0/var(--tw-bg-opacity,1))'), '#000000')
