"""Only LF, CRLF and CR end a relay build-log line; no compiler or VM."""
import unittest
from measure_relay_linux_v148 import diagnostics as relay_diagnostics
from measure_relay13_linux_v148 import diagnostics as relay13_diagnostics
SCANS=(relay_diagnostics,relay13_diagnostics)
class RelayMeasureLineBreakTests(unittest.TestCase):
 def test_mid_line_separator_does_not_start_an_error_line(self):
  for scan in SCANS:
   for sep in (b'\x0b',b'\x0c','\u0085'.encode(),'\u2028'.encode(),'\u2029'.encode()):
    self.assertEqual(scan(b'note '+sep+b'Error: quoted\n'),[],(scan.__module__,sep))
 def test_lf_cr_and_crlf_errors_still_detected(self):
  for scan in SCANS:
   self.assertEqual(scan(b'Error: real\n'),['Error: real'])
   self.assertEqual(scan(b'ok\rError: cr\r\nfine\nError: b\n'),['Error: cr','Error: b'])
   self.assertEqual(scan(b'all good\n'),[]);self.assertEqual(scan(b''),[])
if __name__=='__main__':unittest.main()
