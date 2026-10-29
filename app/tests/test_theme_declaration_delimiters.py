import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-theme.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Declarations(unittest.TestCase):

    def test_quoted_font_names_keep_embedded_semicolons(self):
        css = '.font-sans{font-family:"semi;colon",sans-serif;color:red}'
        self.assertEqual(subject.extract_scale(css, '\\.font-(sans|serif|mono)', 'font-family'), {'sans': '"semi;colon",sans-serif'})
        self.assertEqual(subject.declarations('x:url("data:image/svg+xml;value");color:red')['x'], 'url("data:image/svg+xml;value")')
