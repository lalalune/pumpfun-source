#!/usr/bin/env python3
"""One real portable replay plus three early rejection/output-preservation controls."""
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
OPTIONS=None

class PortableCheckpoint(unittest.TestCase):
    def command(self,packet,repo,artifact,*extra):
        return [sys.executable,'-I','-B',str(packet/'verify.py'),'--repo',str(repo),'--artifact',str(artifact),*map(str,extra)]
    def invoke(self,command):
        return subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
            env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_ALLOW_PROTOCOL='file',PYTHONDONTWRITEBYTECODE='1'))
    def test_00_real_export_path_with_spaces(self):
        with tempfile.TemporaryDirectory(prefix='frozen 1ddb portable ') as raw:
            root=Path(raw);packet=root/'packet with spaces';shutil.copytree(HERE,packet)
            report=root/'new report.json';r=self.invoke(self.command(packet,OPTIONS.repo,OPTIONS.artifact,'--report',report))
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            value=json.loads(report.read_text());self.assertEqual((value['summary']['normalized'],value['summary']['raw'],value['summary']['total']),(1034,1034,1035))
            self.assertEqual(value['unmatched'],['0x22a10']);self.assertEqual(value['literalClosure']['windows']['sameOriginalOffsets'],1034)
            self.assertEqual(value['nativeSdkPhysicalQualification']['status'],'NOT RUN');self.assertTrue(value['physicalLocalRegistry'].startswith('NOT RUN'))
            self.assertEqual(value['sourceSha256'],'6e061e8785371cbe427c8ff591bc1a35846deafad89b8d922137a6c52c5579b9')
    def test_01_corrupt_external_zip(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'wrong.zip';p.write_bytes(b'not the authentic artifact')
            r=self.invoke(self.command(HERE,OPTIONS.repo,p));self.assertNotEqual(r.returncode,0);self.assertIn('authentic external ZIP',r.stderr)
    def test_02_existing_report_preserved(self):
        with tempfile.TemporaryDirectory() as raw:
            p=Path(raw)/'existing.json';p.write_bytes(b'untouched sentinel')
            r=self.invoke(self.command(HERE,OPTIONS.repo,OPTIONS.artifact,'--report',p))
            self.assertNotEqual(r.returncode,0);self.assertIn('report output already exists',r.stderr);self.assertEqual(p.read_bytes(),b'untouched sentinel')
    def test_03_missing_local_git_objects(self):
        with tempfile.TemporaryDirectory() as raw:
            repo=Path(raw)/'empty repository';subprocess.run(['git','init','--bare','--quiet',str(repo)],check=True)
            r=self.invoke(self.command(HERE,repo,OPTIONS.artifact));self.assertNotEqual(r.returncode,0);self.assertIn('49bf18401f5138b4d0bdb9446d7a3ef1a129509b',r.stderr)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,required=True);parser.add_argument('--artifact',type=Path,required=True)
    OPTIONS,remaining=parser.parse_known_args();before=hashlib.sha256(OPTIONS.artifact.read_bytes()).hexdigest()
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PortableCheckpoint);result=unittest.TextTestRunner(verbosity=2).run(suite)
    if hashlib.sha256(OPTIONS.artifact.read_bytes()).hexdigest()!=before:raise SystemExit('input artifact changed')
    raise SystemExit(not result.wasSuccessful())
