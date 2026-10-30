import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import audit

ROOT = Path(__file__).resolve().parents[3]
ARCHIVE = ROOT/'research/tooling-roadmap-call-classification-20261029'


class DuplicateManifestTests(unittest.TestCase):
    def exercise(self, variant):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            (root/'scripts').mkdir()
            shutil.copyfile(ROOT/audit.FROZEN_SOURCE, root/audit.FROZEN_SOURCE)
            packet = root/'research/packet'; packet.mkdir(parents=True)
            manifest = json.loads((ARCHIVE/'manifest.json').read_text(encoding='utf-8'))
            for name in manifest:
                target=packet/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ARCHIVE/name,target)
                self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(),manifest[name])
            # Do not execute the retained verifier: this is manifest admission.
            # Keep its authentic bytes as a payload under a non-entrypoint name.
            (packet/'verify.py').rename(packet/'retained-verifier.py')
            manifest['retained-verifier.py']=manifest.pop('verify.py')
            name='README.md'; digest=manifest[name]
            if variant=='flat':
                text='{'+json.dumps(name)+':"'+'0'*64+'",'+json.dumps(manifest)[1:]
            elif variant=='escaped':
                text='{"\\u0052EADME.md":"'+digest+'",'+json.dumps(manifest)[1:]
            elif variant=='record':
                rows=[json.dumps({'path':n,'sha256':h}) for n,h in manifest.items()]
                rows[0]=rows[0].replace('"sha256":', '"sha256":"'+'0'*64+'","sha256":',1)
                text='{"files":['+','.join(rows)+']}'
            else:text=json.dumps(manifest)
            (packet/'manifest.json').write_text(text,encoding='utf-8')
            output=root/'audit'
            result=subprocess.run([sys.executable,'-B',str(Path(audit.__file__)), '--repo',str(root),'--output',str(output)],capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr.decode(errors='replace'))
            row=json.loads((output/'results.json').read_text(encoding='utf-8'))[0]
            self.assertEqual(row['overall'],'pass' if variant=='valid' else 'fail')
            if variant!='valid':
                self.assertIn('duplicate manifest JSON field',str(row['manifest_check']['errors']))
                self.assertNotEqual(row['manifest_check_after']['status'],'pass')
            else:self.assertEqual(row['manifest_check']['files_checked'],len(manifest))
            self.assertEqual((packet/'manifest.json').read_text(encoding='utf-8'),text)

    def test_conflicting_flat_hashes(self):self.exercise('flat')
    def test_decoded_duplicate_field_names(self):self.exercise('escaped')
    def test_conflicting_file_record_hashes(self):self.exercise('record')
    def test_authentic_payload_hashes_remain_valid(self):self.exercise('valid')


if __name__=='__main__':unittest.main()
