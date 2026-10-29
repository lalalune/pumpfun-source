import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class PrefixChannels(unittest.TestCase):

    def test_unrelated_text_color_does_not_override_ring_or_decoration(self):
        self.assertEqual(subject.color_value('ring', 'color:#f00;--tw-ring-color:#00f'), '#0000ff')
        self.assertEqual(subject.color_value('text', 'background-color:#f00;color:#00f'), '#0000ff')
        self.assertEqual(subject.color_value('decoration', 'color:#f00;text-decoration-color:#00f'), '#0000ff')
