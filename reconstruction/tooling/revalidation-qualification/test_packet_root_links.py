import os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
import audit
ROOT=Path(__file__).resolve().parents[3]
def link_directory(target,link):
 if os.name=='nt':
  import _winapi
  _winapi.CreateJunction(str(target),str(link))
 else:link.symlink_to(target,target_is_directory=True)
class PacketRootLinkTests(unittest.TestCase):
 def test_linked_root_does_not_supply_snapshot_entries(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();target=root/'outside';target.mkdir();(target/'evidence.txt').write_bytes(b'outside evidence')
   link=root/'packet';link_directory(target,link)
   try:
    with self.assertRaisesRegex(ValueError,'packet root'):audit.packet_snapshot(link)
    self.assertEqual((target/'evidence.txt').read_bytes(),b'outside evidence')
   finally:
    if os.name=='nt':link.rmdir()
    else:link.unlink()
 def test_actual_cli_refuses_linked_research_packet(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary).resolve();(root/'scripts').mkdir();shutil.copyfile(ROOT/audit.FROZEN_SOURCE,root/audit.FROZEN_SOURCE)
   (root/'research').mkdir();target=root/'outside';target.mkdir();(target/'evidence.txt').write_bytes(b'outside evidence')
   link=root/'research/linked';link_directory(target,link)
   try:
    output=root/'audit';result=subprocess.run([sys.executable,'-B',str(Path(audit.__file__)),'--repo',str(root),'--output',str(output)],capture_output=True,timeout=10)
    self.assertEqual(result.returncode,2,result.stderr);self.assertIn(b'packet root',result.stderr);self.assertFalse(output.exists())
    self.assertEqual((target/'evidence.txt').read_bytes(),b'outside evidence')
   finally:
    if os.name=='nt':link.rmdir()
    else:link.unlink()
 def test_regular_packet_retains_snapshot(self):
  with tempfile.TemporaryDirectory() as temporary:
   packet=Path(temporary);(packet/'evidence.txt').write_bytes(b'local evidence')
   snapshot=audit.packet_snapshot(packet);self.assertEqual(snapshot['regular_file_count'],1);self.assertEqual(snapshot['entries'][0]['path'],'evidence.txt')
