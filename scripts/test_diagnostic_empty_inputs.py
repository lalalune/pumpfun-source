"""A diagnostic gate cannot attest to logs that were never supplied."""
from pathlib import Path
import tempfile
import unittest
from check_sbf_backend_diagnostics import check
class DiagnosticInputTests(unittest.TestCase):
 def test_empty_iterables_are_not_a_checked_passing_gate(self):
  for paths in [[],(),iter(())]:
   with self.subTest(kind=type(paths).__name__):
    with self.assertRaisesRegex(ValueError,'log'):
     check(paths)
 def test_supplied_clean_and_failed_logs_preserve_their_gate_result(self):
  with tempfile.TemporaryDirectory() as folder:
   clean=Path(folder)/'clean.log';clean.write_text('Finished release build\n',encoding='utf-8')
   failed=Path(folder)/'failed.log';failed.write_text('Error: synthetic backend failure\n',encoding='utf-8')
   self.assertTrue(check(iter([clean]))['diagnostic_gate_passed'])
   report=check([clean,failed]);self.assertFalse(report['diagnostic_gate_passed']);self.assertEqual(report['backend_error_count'],1)
if __name__=='__main__':unittest.main()
