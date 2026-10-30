"""Retained native Mayhem case lists plus real bounded publication controls.

Full corpus means the specified native selection, not all quote families or
rebuilt candidate equivalence. Both sides execute the captured original ELF.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from publication_cli_support import PublicationCase, ROOT

class MayhemReportsPublicationTests(PublicationCase,unittest.TestCase):
 NAMES=('mayhem_buy_differential','mayhem_sell_differential','mayhem_buy_v2_differential',
        'mayhem_sell_v2_differential','mayhem_pump_swap_differential','mayhem_initialize_state_differential')
 PROGRAM='evidence/original/mayhem/deployed.so'
 CANDIDATE_REQUIRED=True
 BASE='scripts/fixtures/mayhem-publication/'
 CASES={'mayhem_buy_differential':BASE+'buy-cases.json','mayhem_sell_differential':BASE+'sell-cases.json',
        'mayhem_buy_v2_differential':BASE+'buy-v2-cases.json','mayhem_sell_v2_differential':BASE+'sell-v2-cases.json',
        'mayhem_pump_swap_differential':BASE+'buy-pump-swap-cases.json'}
 COMMON=(PROGRAM,'evidence/original/pump/deployed.so','evidence/original/pump_fees/deployed.so',
         *(f'evidence/dependencies/{n}/deployed.so' for n in ('spl_token','spl_token_2022','associated_token')))
 CAPTURES=(*(f'evidence/original/{n}/capture.json' for n in ('pump','pump_fees')),
           *(f'evidence/dependencies/{n}/capture.json' for n in ('spl_token','spl_token_2022','associated_token')))
 CURVE='research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'
 AMM='research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'
 CONFIG='research/imported-lab/analysis/pump_fun/config-snapshot.json'
 DATA=(*COMMON,*CAPTURES,CURVE,AMM,CONFIG,'evidence/original/pump_amm/deployed.so',*CASES.values(),BASE+'sell-pump-swap-cases.json')
 INPUTS={}
 HELPERS={}
 ARGS={}
 EXPECTED=dict(zip(NAMES,(486,396,613,473,419,5)))
 KEEP_CASE={'mayhem_initialize_state_differential':'full-maximal-valid-standalone'}
 LATE_INPUT=PROGRAM

 def test_retained_input_hashes(self):
  for item in json.loads((ROOT/self.BASE/'provenance.json').read_bytes())['files']:
   self.assertEqual(hashlib.sha256((ROOT/item['retained_path']).read_bytes()).hexdigest(),item['sha256'])
   self.assertEqual(len(json.loads((ROOT/item['retained_path']).read_bytes())['cases']),item['cases'])

 def test_external_case_paths_and_bounded_quote_families(self):
  for name in self.CASES:
   with self.subTest(script=name),tempfile.TemporaryDirectory(prefix='mayhem-cases-') as d:
    path=Path(d)/'external-cases.json';shutil.copyfile(self.root/self.CASES[name],path);raw=path.read_bytes()
    old=self.ARGS[name];self.ARGS[name]=['--cases',str(path),*old[2:]]
    try:
     result=self.invoke(name);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
     report=self.report();self.assertEqual(report['case_count'],2)
     self.assertIn(str(path.resolve()),report['harness_sha256'])
     for kind in ('direct','symlink','hardlink'):
      alias=Path(d)/'alias';alias.unlink(missing_ok=True)
      if kind=='symlink':alias.symlink_to(path)
      elif kind=='hardlink':os.link(path,alias)
      result=self.invoke(name,output=path if kind=='direct' else alias)
      self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
      self.assertEqual(path.read_bytes(),raw)
    finally:self.ARGS[name]=old
  for name in ('mayhem_buy_v2_differential','mayhem_sell_v2_differential','mayhem_pump_swap_differential'):
   old=self.ARGS[name]
   for family in ('token','token22'):
    args=list(old);args[args.index('--family')+1]=family;self.ARGS[name]=args
    try:
     result=self.invoke(name);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
     self.assertEqual(self.report()['case_count'],2);self.assertEqual(self.report()['mismatches'],[])
    finally:self.ARGS[name]=old

 def test_late_external_case_alias_preserves_input(self):
  name='mayhem_buy_differential';old_args=self.ARGS[name]
  with tempfile.TemporaryDirectory(prefix='mayhem-late-case-') as temporary:
   case=Path(temporary)/'cases.json';shutil.copyfile(self.root/self.CASES[name],case);raw=case.read_bytes()
   self.ARGS[name]=['--cases',str(case)];self.LATE_INPUT=str(case)
   try:
    result=self.invoke(name,'late')
    self.assertNotEqual(result.returncode,0);self.assertIn('report output aliases an input',result.stderr)
    self.assertEqual(case.read_bytes(),raw)
    self.assertEqual(json.loads((self.root/'execution.json').read_bytes())['selected'],2)
   finally:self.ARGS[name]=old_args

 def test_legacy_default_retained_case_path(self):
  name='mayhem_sell_differential';old=self.ARGS[name];self.ARGS[name]=[]
  try:
   result=self.invoke(name);self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertEqual(self.report()['case_count'],2)
   self.assertIn(self.CASES[name],self.report()['harness_sha256'])
  finally:self.ARGS[name]=old

 def test_full_sell_pump_swap_selection(self):
  name='mayhem_pump_swap_differential';old=self.ARGS[name]
  self.ARGS[name]=['--cases',self.BASE+'sell-pump-swap-cases.json','--family','native','--instruction','sell_pump_swap']
  try:
   result=self.invoke(name,'full');self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertEqual(self.report()['case_count'],413);self.assertEqual(self.report()['mismatches'],[])
   if os.environ.get(self.PROOF_ENV):shutil.copyfile(self.output,Path(os.environ[self.PROOF_ENV])/'mayhem_sell_pump_swap_differential.json')
  finally:self.ARGS[name]=old

for name in MayhemReportsPublicationTests.NAMES:
 c=MayhemReportsPublicationTests
 if name=='mayhem_initialize_state_differential':
  c.INPUTS[name]=(*c.COMMON,*(f'evidence/dependencies/{n}/capture.json' for n in ('spl_token','spl_token_2022','associated_token')))
  c.HELPERS[name]=('pump_amm_reusable_harness',)
 elif name=='mayhem_pump_swap_differential':
  c.INPUTS[name]=(*c.COMMON,c.AMM,c.CONFIG,'evidence/original/pump_amm/deployed.so',c.CASES[name])
  c.HELPERS[name]=('mayhem_pump_swap_fixture','pump_amm_reusable_harness','pump_diagnostic_audit')
 else:
  c.INPUTS[name]=(*c.COMMON,*c.CAPTURES,c.CURVE,c.CASES[name])
  c.HELPERS[name]=(name.replace('_differential','_fixture'),'pump_trade_fixture','pump_amm_reusable_harness','pump_diagnostic_audit')
 if name in c.CASES:
  c.ARGS[name]=['--cases',c.CASES[name]]
  if name in ('mayhem_buy_v2_differential','mayhem_sell_v2_differential','mayhem_pump_swap_differential'):c.ARGS[name]+=['--family','native']
  if name=='mayhem_pump_swap_differential':c.ARGS[name]+=['--instruction','buy_pump_swap']

del c,name

if __name__=='__main__':unittest.main()
