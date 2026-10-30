import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('bfi', Path(__file__).with_name('tools')/'bfi.py')
bfi = importlib.util.module_from_spec(spec); spec.loader.exec_module(bfi)
MODULE = '''
define void @test() {
entry:
  call void @to_string17h()
  store i32 307, ptr %x
  ret void
}
'''
class Diagnostics(unittest.TestCase):
    def test_missing_frequency_fails_instead_of_becoming_cold(self):
        with self.assertRaisesRegex(ValueError, 'frequency missing'):
            bfi.frequency_rows(MODULE, 'test', 'block-frequency-info: test\n - other: float = 1.0\n')
    def test_real_frequency_is_reported(self):
        row = bfi.frequency_rows(MODULE, 'test', 'block-frequency-info: test\n - entry: float = 0.022\n')[0]
        self.assertEqual(row['line'], 307); self.assertFalse(row['below_2_percent'])
    def test_missing_diagnostic_is_not_a_result(self):
        with self.assertRaisesRegex(ValueError, 'missing block-frequency'):
            bfi.frequency_rows(MODULE, 'test', '')
    def test_ambiguous_function_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'matched 2'):
            bfi.select_function(MODULE+MODULE, 'test')
if __name__ == '__main__': unittest.main()
