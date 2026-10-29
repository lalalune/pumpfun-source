import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-shell-icons.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class IconAttributes(unittest.TestCase):

    def test_line_coordinates_are_not_silently_lost(self):
        result = subject.to_jsx('<svg><line x1="1" y1="2" x2="3" y2="4"/></svg>')
        self.assertIn('<line ', result)
        for key, value in [('x1', '1'), ('y1', '2'), ('x2', '3'), ('y2', '4')]:
            self.assertIn(f'{key}="{value}"', result)
        self.assertIn('<path ', subject.to_jsx('<svg><path d="M0 0"/></svg>'))
