"""Backend errors behind a per-line U+FEFF marker are still reported; no compiler or VM."""
import codecs,gzip,hashlib,tempfile,unittest
from pathlib import Path
from check_sbf_backend_diagnostics import check,inspect
ERROR='Error: Function drift Stack offset of 4104 exceeded max offset of 4096 by 8 bytes, please minimize large stack variables. Estimated function frame size: 4160 bytes.'
BOM=codecs.BOM_UTF8
class LineMarkerTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)/'build.log'
 def tearDown(self):self.tmp.cleanup()
 def rejects(self,raw,line_number):
  self.p.write_bytes(raw);r=check([self.p]);self.assertFalse(r['diagnostic_gate_passed']);self.assertEqual(r['backend_error_count'],1)
  e=r['logs'][0]['backend_errors'][0];self.assertEqual((e['kind'],e['line_number'],e['reported_offset']),('stack_offset_exceeded',line_number,4104))
  self.assertEqual(r['logs'][0]['input_sha256'],hashlib.sha256(raw).hexdigest());self.assertEqual(self.p.read_bytes(),raw)
 def test_marker_at_start_of_a_later_line(self):
  self.rejects(b'Compiling fixture\n'+BOM+ERROR.encode()+b'\nCargo exit: 0\n',2)
 def test_marker_after_ansi_color(self):
  self.rejects(b'Compiling fixture\n\x1b[31m'+BOM+ERROR.encode()+b'\x1b[0m\n',2)
 def test_marker_then_whitespace(self):
  self.rejects(b'Compiling fixture\n'+BOM+b'  '+ERROR.encode()+b'\n',2)
 def test_gzip_concatenated_logs(self):
  self.rejects(gzip.compress(b'Compiling fixture\n'+BOM+ERROR.encode()+b'\n',mtime=0),2)
 def test_reported_text_keeps_the_original_line(self):
  self.p.write_bytes(b'ok\n'+BOM+b'Error: other\n');e=inspect(self.p)['backend_errors'][0];self.assertEqual(e['text'],'\ufeffError: other')
 def test_interior_marker_and_marker_only_lines_do_not_match(self):
  self.p.write_bytes(b'note \xef\xbb\xbfError: quoted\n'+BOM+b'\n'+BOM+b'Finished release\n');r=check([self.p]);self.assertEqual(r['backend_error_count'],0);self.assertTrue(r['diagnostic_gate_passed']);self.assertFalse(r['program_readiness_proven'])
if __name__=='__main__':unittest.main()
