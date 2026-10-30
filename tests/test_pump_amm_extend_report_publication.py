"""Real AMM extension corpus and actual selected-CWD publication protection."""
from pathlib import Path
import shutil
import tempfile
import unittest
from publication_cli_support import PublicationCase

class AmmExtendPublicationTests(PublicationCase,unittest.TestCase):
 NAMES=('pump_amm_extend_differential',)
 TRADE='research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'
 DATA=('evidence/upstream/pump_amm.json','evidence/original/pump_amm/deployed.so',
       'research/imported-lab/analysis/pump_fun/config-snapshot.json',TRADE)
 HELPERS=('pump_amm_liquidity_differential','pump_amm_admin_differential','pump_amm_reusable_harness')
 PROGRAM='evidence/original/pump_amm/deployed.so'
 EXPECTED={'pump_amm_extend_differential':317}
 CANDIDATE_REQUIRED=True
 LATE_INPUT=TRADE

 def test_actual_external_cwd_fixture(self):
  with tempfile.TemporaryDirectory(prefix='amm-extend-caller-') as temporary:
   caller=Path(temporary).resolve();fixture=caller/self.TRADE;fixture.parent.mkdir(parents=True)
   shutil.copyfile(self.root/self.TRADE,fixture);raw=fixture.read_bytes()
   for kind in ('direct','symlink','hardlink'):
    alias=caller/'alias';alias.unlink(missing_ok=True)
    if kind=='symlink':alias.symlink_to(fixture)
    elif kind=='hardlink':
     import os
     os.link(fixture,alias)
    result=self.invoke(self.NAMES[0],output=fixture if kind=='direct' else alias,cwd=caller)
    self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
    self.assertIn('report output aliases an input',result.stderr);self.assertEqual(fixture.read_bytes(),raw)
   result=self.invoke(self.NAMES[0],cwd=caller)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertEqual(self.report()['case_count'],2)

if __name__=='__main__':unittest.main()
