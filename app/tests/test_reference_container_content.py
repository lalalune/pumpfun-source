import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-reference-pages.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Tests(unittest.TestCase):

    def test_unrepresented_container_content(self):
        N = subject.Node
        for node, fn in [(N('ul', children=['Lost', N('li', children=['Kept'])]), subject.list_block), (N('table', children=[N('tr', children=['Lost', N('td', children=['Kept'])])]), subject.table_block)]:
            with self.assertRaises(subject.ExtractionError):
                fn(node)
        self.assertEqual(subject.list_block(N('ul', children=[' ', N('li', children=['Kept'])]))['items'][0]['children'], ['Kept'])
        self.assertEqual(len(subject.table_block(N('table', children=[N('tr', children=[N('td', children=['Kept'])])]))['rows']), 1)
