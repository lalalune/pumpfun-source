import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=['pump_validate_admin.py','pump_validate_authority.py','pump_validate_buy.py','pump_validate_sell.py','pump_validate_quote.py']

@unittest.skipUnless(importlib.util.find_spec('solders'),'requires the documented solders runtime')
class ValidationReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary=tempfile.TemporaryDirectory();cls.addClassCleanup(cls.temporary.cleanup)
        cls.fixture=Path(cls.temporary.name)
        for name in [*SCRIPTS,'pump_trade_fixture.py','probe_report.py','validation_report.py']:
            path=ROOT/'scripts'/name
            if path.exists():
                (cls.fixture/'scripts').mkdir(exist_ok=True)
                shutil.copyfile(path,cls.fixture/'scripts'/name)
        for parent,names in [('original',['pump','pump_fees']),('dependencies',['spl_token','spl_token_2022','associated_token'])]:
            for name in names:
                source=ROOT/'evidence'/parent/name
                for filename in ['deployed.so','capture.json']:
                    dest=cls.fixture/'evidence'/parent/name/filename;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/filename,dest)
        for relative in ['evidence/upstream/pump.json',
                         'research/imported-lab/analysis/pump_fun/config-snapshot.json',
                         'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json']:
            dest=cls.fixture/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/relative,dest)
        # The checkout has no generated constant-product report. Use a minimal
        # test-only report; the validators still execute their fixed VM cases.
        math=cls.fixture/'repro/pump/constant-product-differential.json';math.parent.mkdir(parents=True);math.write_text('{"cases":[]}')
        crate=cls.fixture/'programs/pump';(crate/'src').mkdir(parents=True)
        (crate/'src/lib.rs').write_text('// temporary source receipt fixture\n')

    def invoke(self,name,candidate,output):
        return subprocess.run([sys.executable,str(self.fixture/'scripts'/name),'--candidate',str(candidate),'--output',str(output)],capture_output=True,text=True)
    def test_input_aliases_are_rejected_before_writes(self):
        for name in SCRIPTS:
            for kind in ['direct','symlink','hardlink']:
                with self.subTest(script=name,kind=kind),tempfile.TemporaryDirectory() as temp:
                    root=Path(temp);candidate=root/'candidate.so';shutil.copyfile(ROOT/'evidence/original/pump/deployed.so',candidate);before=candidate.read_bytes();output=candidate
                    if kind=='symlink':output=root/'report.json';output.symlink_to(candidate)
                    if kind=='hardlink':output=root/'report.json';os.link(candidate,output)
                    result=self.invoke(name,candidate,output)
                    self.assertNotEqual(result.returncode,0)
                    self.assertEqual(candidate.read_bytes(),before)
                    self.assertIn('aliases',result.stderr)
    def test_original_and_source_input_aliases_are_rejected(self):
        for name in SCRIPTS:
            for relative in ['evidence/original/pump_fees/deployed.so','programs/pump/src/lib.rs']:
                with self.subTest(script=name,input=relative),tempfile.TemporaryDirectory() as temp:
                    protected=self.fixture/relative;before=protected.read_bytes()
                    alias=Path(temp)/'report.json';os.link(protected,alias)
                    result=self.invoke(name,ROOT/'evidence/original/pump/deployed.so',alias)
                    self.assertNotEqual(result.returncode,0);self.assertIn('aliases',result.stderr)
                    self.assertEqual(protected.read_bytes(),before)

    def test_nested_report_controls(self):
        for name in SCRIPTS:
            with self.subTest(script=name),tempfile.TemporaryDirectory() as temp:
                output=Path(temp)/'new/nested/report.json';candidate=ROOT/'evidence/original/pump/deployed.so';before=hashlib.sha256(candidate.read_bytes()).hexdigest()
                result=self.invoke(name,candidate,output)
                self.assertEqual(result.returncode,0,result.stderr)
                report=json.loads(output.read_text());self.assertGreater(report['case_count'],0);self.assertEqual(report['mismatches'],[])
                self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(),before)
    def test_administrative_mismatch_exit_and_gzip_publication(self):
        for name in SCRIPTS[:2]:
            with self.subTest(script=name),tempfile.TemporaryDirectory() as temp:
                output=Path(temp)/('new/report.json.gz' if name.endswith('authority.py') else 'new/report.json')
                result=self.invoke(name,ROOT/'evidence/original/pump_fees/deployed.so',output)
                self.assertEqual(result.returncode,1,result.stderr)
                report=json.loads(gzip.decompress(output.read_bytes()) if output.suffix=='.gz' else output.read_bytes());self.assertTrue(report['mismatches'])
if __name__=='__main__':unittest.main()
