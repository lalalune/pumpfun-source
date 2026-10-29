import importlib.util
from pathlib import Path
import sys, unittest
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('subject', ROOT / 'scripts/analyze.py')
subject = importlib.util.module_from_spec(spec)
sys.modules['subject'] = subject
spec.loader.exec_module(subject)

class LongestNames(unittest.TestCase):

    def test_known_input_order_cannot_shorten_a_log_name(self):
        data = b'Instruction: BuyExactSolInadjacent'
        self.assertEqual(subject.instruction_log_names(data, ['Buy', 'BuyExactSolIn']), ['BuyExactSolIn'])
        self.assertEqual(subject.instruction_log_names(data, ['BuyExactSolIn', 'Buy']), ['BuyExactSolIn'])
        self.assertEqual(subject.instruction_log_names(b'Instruction: Other'), ['Other'])
