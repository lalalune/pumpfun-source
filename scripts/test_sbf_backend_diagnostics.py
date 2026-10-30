"""Regression cases for zero-exit backend errors; no compiler or VM."""
import gzip,hashlib,tempfile,unittest
from pathlib import Path
from check_sbf_backend_diagnostics import check,inspect
ERROR='Error: Function drift Stack offset of 4104 exceeded max offset of 4096 by 8 bytes, please minimize large stack variables. Estimated function frame size: 4160 bytes.'
class BackendDiagnosticTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'build.log'
 def tearDown(self):self.tmp.cleanup()
 def test_zero_exit_footer_does_not_mask_error(self):
  self.p.write_text(ERROR+'\nFinished release\nCargo exit: 0\nstrip exit: 0\n');r=check([self.p]);self.assertFalse(r['diagnostic_gate_passed']);self.assertEqual(r['backend_error_count'],1);e=r['logs'][0]['backend_errors'][0];self.assertEqual((e['reported_offset'],e['maximum_offset'],e['estimated_frame_bytes']),(4104,4096,4160))
 def test_no_reported_error_is_not_readiness(self):
  self.p.write_text('Finished release\n');r=check([self.p]);self.assertTrue(r['diagnostic_gate_passed']);self.assertFalse(r['program_readiness_proven'])
 def test_command_arguments_and_quoted_source_do_not_match(self):
  self.p.write_text('Running `rustc --cfg "Error: text" --warn large_stack_arrays -C overflow-checks=on`\n');self.assertEqual(check([self.p])['backend_error_count'],0)
 def test_gzip_and_ansi_keep_exact_input_bytes(self):
  raw=gzip.compress(('\x1b[31m'+ERROR+'\x1b[0m\n').encode(),mtime=0);self.p.write_bytes(raw);before=self.p.read_bytes();r=inspect(self.p);self.assertEqual(r['backend_errors'][0]['kind'],'stack_offset_exceeded');self.assertEqual(r['input_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(self.p.read_bytes(),before)
 def test_multiple_and_unknown_backend_errors_reject(self):
  self.p.write_text(ERROR+'\nError: other backend failure\n');r=check([self.p]);self.assertEqual(r['backend_error_count'],2);self.assertFalse(r['diagnostic_gate_passed']);self.assertFalse(r['compiler_or_strip_exit_codes_rewritten'])
 def test_malformed_utf8_does_not_mask_backend_error(self):
  self.p.write_bytes(b'\xffError: other backend failure\n')
  with self.assertRaisesRegex(UnicodeDecodeError,'utf-8'):check([self.p])
if __name__=='__main__':unittest.main()
