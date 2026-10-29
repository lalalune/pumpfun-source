import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-reference-pages.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Tests(unittest.TestCase):

    def test_duplicate_attributes_cannot_reverse_browser_link_precedence(self):
        for html in ['<a href="/first" href="/last">Text</a>', '<a href="/first" HREF="/last"/>']:
            with self.assertRaisesRegex(subject.ExtractionError, 'Duplicate HTML attribute'):
                subject.TreeParser().feed(html)
        parser = subject.TreeParser()
        parser.feed('<a href="/first">Text</a>')
        self.assertEqual(parser.root.children[0].attrs['href'], '/first')
