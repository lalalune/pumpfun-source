import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-reference-pages.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class TableSpans(unittest.TestCase):

    def test_spanned_cells_cannot_silently_become_a_different_grid(self):
        for attribute in ['colspan', 'rowspan']:
            parser = subject.TreeParser()
            parser.feed(f'<table><tr><td {attribute}="2">text</td></tr></table>')
            node = subject.descendants(parser.root, 'table')[0]
            with self.assertRaisesRegex(subject.ExtractionError, 'span'):
                subject.table_block(node)
        parser = subject.TreeParser()
        parser.feed('<table><tr><td colspan="1">text</td></tr></table>')
        self.assertEqual(len(subject.table_block(subject.descendants(parser.root, 'table')[0])['rows'][0]['cells']), 1)
