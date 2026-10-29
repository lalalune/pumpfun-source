import importlib.util
from pathlib import Path
import sys, unittest, json
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-reference-pages.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class Tests(unittest.TestCase):

    def test_nested_titles_are_not_silently_omitted(self):
        N = subject.Node
        main = N('main', children=[N('h1', children=['Title']), N('section', children=[N('h1', children=['Lost title'])])])
        with self.assertRaisesRegex(subject.ExtractionError, 'nested'):
            subject.blocks(main, set())
        self.assertEqual(subject.blocks(N('main', children=[N('h1', children=['Title']), N('p', children=['Kept'])]), set())[0]['children'], ['Kept'])
