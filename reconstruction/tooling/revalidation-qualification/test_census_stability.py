import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parents[3]
class CensusMutationTests(unittest.TestCase):
 def exercise(self,mutation):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();(root/'scripts').mkdir();shutil.copyfile(ROOT/audit.FROZEN_SOURCE,root/audit.FROZEN_SOURCE)
   packet=root/'research/packet';packet.mkdir(parents=True)
   if mutation=='add':script=b"from pathlib import Path\nPath('../late-packet').mkdir()\n"
   elif mutation=='remove':
    (root/'research/zempty').mkdir();script=b"from pathlib import Path\nPath('../zempty').rmdir()\n"
   else:script=b"print('stable packet census')\n"
   (packet/'verify.py').write_bytes(script)
   (packet/'manifest.json').write_text(json.dumps({'verify.py':hashlib.sha256(script).hexdigest()}),encoding='utf-8')
   output=root/'audit';result=subprocess.run([sys.executable,'-B',str(Path(audit.__file__)),'--repo',str(root),'--output',str(output)],capture_output=True,timeout=10)
   self.assertEqual(result.returncode,0 if mutation=='stable' else 2,result.stderr)
   if mutation!='stable':
    self.assertIn(b'census changed',result.stderr);self.assertFalse(output.exists())
   else:self.assertEqual(json.loads((output/'provenance.json').read_text())['packet_census'],['packet'])
   self.assertEqual((packet/'verify.py').read_bytes(),script)
 def test_new_packet_during_verification_cannot_be_omitted(self):self.exercise('add')
 def test_stable_census_still_publishes(self):self.exercise('stable')
