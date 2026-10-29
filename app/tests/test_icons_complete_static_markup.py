import importlib.util
from pathlib import Path
import sys, unittest
APP = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', APP / 'scripts/extract-shell-icons.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class IconMarkup(unittest.TestCase):

    def test_unknown_and_unbalanced_fragments_do_not_disappear(self):
        for svg in ['<svg>text</svg>', "<svg><path d='M0 0'/></svg>", '<svg><path></svg></path>', '<svg></svg><svg></svg>']:
            with self.subTest(svg=svg), self.assertRaises(SystemExit):
                subject.to_jsx(svg)
        self.assertEqual(subject.to_jsx('<svg><g><path d="M0 0"/></g></svg>'), '<svg><g><path d="M0 0" /></g></svg>')
