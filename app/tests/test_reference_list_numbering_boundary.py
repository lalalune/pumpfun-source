import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-reference-pages.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class ListNumbers(unittest.TestCase):

    def test_numbering_overrides_are_not_reset_to_one(self):
        for markup in ['<ol start="5"><li>text</li></ol>', '<ol reversed><li>text</li></ol>', '<ol><li value="5">text</li></ol>']:
            parser = subject.TreeParser()
            parser.feed(markup)
            with self.assertRaisesRegex(subject.ExtractionError, 'numbering'):
                subject.list_block(subject.descendants(parser.root, 'ol')[0])
        parser = subject.TreeParser()
        parser.feed('<ol><li>text</li></ol>')
        self.assertTrue(subject.list_block(subject.descendants(parser.root, 'ol')[0])['ordered'])
