"""Only LF, CRLF and CR end a log line; no compiler or VM."""
import tempfile,unittest
from pathlib import Path
from check_sbf_backend_diagnostics import check,inspect
class LineBreakTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'build.log'
 def tearDown(self):self.tmp.cleanup()
 def test_unicode_separator_does_not_shift_line_numbers(self):
  self.p.write_bytes('note \u2028 kept\x0cinline\nError: real\n'.encode());e=inspect(self.p)['backend_errors']
  self.assertEqual([(r['line_number'],r['text']) for r in e],[(2,'Error: real')])
 def test_mid_line_control_character_does_not_start_an_error_line(self):
  for sep in ('\x0b','\x0c','\x1c','\x85','\u2028','\u2029'):
   self.p.write_bytes(f'note {sep}Error: quoted\n'.encode());r=check([self.p])
   self.assertEqual(r['backend_error_count'],0,repr(sep));self.assertTrue(r['diagnostic_gate_passed'])
 def test_cr_lf_and_crlf_still_end_lines(self):
  self.p.write_bytes(b'Compiling\rError: a\r\nok\nError: b\n');e=inspect(self.p)['backend_errors']
  self.assertEqual([(r['line_number'],r['text']) for r in e],[(2,'Error: a'),(4,'Error: b')])
if __name__=='__main__':unittest.main()
