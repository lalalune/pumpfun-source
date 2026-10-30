import hashlib,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parents[3]
class DeadlineAdmissionTests(unittest.TestCase):
 def exercise(self,flag,value,valid=False):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();(root/'scripts').mkdir();shutil.copyfile(ROOT/audit.FROZEN_SOURCE,root/audit.FROZEN_SOURCE)
   packet=root/'research/packet';packet.mkdir(parents=True)
   script=b"from pathlib import Path\nPath('../../executed').write_bytes(b'ran')\n"
   (packet/'verify.py').write_bytes(script)
   (packet/'manifest.json').write_text(json.dumps({'verify.py':hashlib.sha256(script).hexdigest()}),encoding='utf-8')
   output=root/'output'
   result=subprocess.run([sys.executable,'-B',str(Path(audit.__file__)),'--repo',str(root),'--output',str(output),flag+'='+value],capture_output=True,timeout=10)
   self.assertEqual(result.returncode,0 if valid else 2,result.stderr)
   self.assertEqual((root/'executed').exists(),valid)
   self.assertEqual(output.exists(),valid)
   if not valid:self.assertIn(b'positive finite',result.stderr)
 def test_invalid_deadlines_rejected_before_verifier_or_output(self):
  for flag in ('--verify-timeout','--cleanup-timeout'):
   for value in ('nan','inf','-inf','0','-1'):
    with self.subTest(flag=flag,value=value):self.exercise(flag,value)
 def test_finite_deadline_still_executes_real_verifier(self):self.exercise('--verify-timeout','5',True)
