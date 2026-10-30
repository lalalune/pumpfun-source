import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parents[3]
class OutputPacketTests(unittest.TestCase):
 def exercise(self,nested,packet_alias=False):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();(root/'scripts').mkdir();shutil.copyfile(ROOT/audit.FROZEN_SOURCE,root/audit.FROZEN_SOURCE)
   packet=root/'research/packet';packet.mkdir(parents=True);(packet/'artifact.txt').write_bytes(b'evidence')
   (packet/'manifest.json').write_text(json.dumps({'artifact.txt':hashlib.sha256(b'evidence').hexdigest()}),encoding='utf-8')
   before={p.name:p.read_bytes() for p in packet.iterdir()}
   output=packet/'new'/'..' if packet_alias else packet/'new'/'audit' if nested else root/'output'
   result=subprocess.run([sys.executable,'-B',str(Path(audit.__file__)),'--repo',str(root),'--output',str(output)],capture_output=True)
   self.assertEqual(result.returncode,2 if nested else 0,result.stderr)
   if nested:
    self.assertIn(b'inside an input packet',result.stderr);self.assertFalse((packet/'new').exists())
   else:self.assertTrue((output/'results.json').is_file())
   self.assertEqual({p.name:p.read_bytes() for p in packet.iterdir()},before)
 def test_nested_output_rejected_before_input_changes(self):self.exercise(True)
 def test_separate_output_preserves_packet(self):self.exercise(False)
 def test_normalized_output_equal_to_packet_is_rejected(self):self.exercise(True,packet_alias=True)
