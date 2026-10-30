"""Reject mutations of a captured log pair, including Source coordinates.

This is a small identical-capture control, not a historical full-suite claim.
"""
from pathlib import Path
import copy,json,re,unittest
import pump_strict_ordered_logs as gate
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'tests/fixtures/strict-ordered-logs/set-params-rejection.json'
RAW=SOURCE.read_bytes();FIXTURE=json.loads(RAW);PAIRS=[]
REPORT={'original_sha256':FIXTURE['original_sha256'],'candidate_sha256':FIXTURE['original_sha256'],'case_count':1,'suites':{'captured-control':[{'original':{'logs':FIXTURE['logs']},'candidate':{'logs':list(FIXTURE['logs'])}}]}}
def collect(value):
 if isinstance(value,dict):
  if isinstance(value.get('original'),dict)and isinstance(value.get('candidate'),dict):PAIRS.append(value)
  for name,item in value.items():
   if name not in ['original','candidate']:collect(item)
 elif isinstance(value,list):
  for item in value:collect(item)
collect(REPORT['suites'])
CASE=next(row for row in PAIRS if any('AnchorError thrown in ' in line and re.search(r':\d+\.',line)for line in row['candidate'].get('logs',[])))
class StrictLogs(unittest.TestCase):
 def setUp(self):
  self.report={'original_sha256':REPORT['original_sha256'],'candidate_sha256':REPORT['candidate_sha256'],'case_count':1,'suites':{'retained':[copy.deepcopy(CASE)]}}
  self.logs=self.report['suites']['retained'][0]['candidate']['logs']
 def audit(self):return gate.audit(self.report,REPORT['candidate_sha256'],1)
 def reject(self):self.assertGreater(self.audit()['strict_ordered_log_mismatch_cases'],0)
 def test_captured_log_control(self):self.assertEqual(gate.audit(REPORT,REPORT['candidate_sha256'],1)['strict_ordered_log_mismatch_cases'],0)
 def test_coordinate_only_change(self):
  i=next(i for i,s in enumerate(self.logs)if 'AnchorError thrown in 'in s and re.search(r':\d+\.',s))
  self.logs[i]=re.sub(r':(\d+)\.',lambda m:':'+str(int(m[1])+1)+'.',self.logs[i],count=1);self.reject()
 def test_missing_source_message(self):
  self.logs.pop(next(i for i,s in enumerate(self.logs)if 'AnchorError thrown in 'in s));self.reject()
 def test_extra_message(self):self.logs.append('Program log: extra test message');self.reject()
 def test_order(self):
  indexes=[i for i,s in enumerate(self.logs)if not gate.UNITS.fullmatch(s)];i=indexes[0];j=next(j for j in indexes[1:]if self.logs[j]!=self.logs[i]);self.logs[i],self.logs[j]=self.logs[j],self.logs[i];self.reject()
 def test_wrong_image(self):
  with self.assertRaisesRegex(ValueError,'image binding'):gate.audit(self.report,'0'*64,1)
 def test_wrong_pair_count(self):
  with self.assertRaisesRegex(ValueError,'case count'):gate.audit(self.report,REPORT['candidate_sha256'],2)
 def test_compute_meter_only(self):
  self.logs.append('Program 11111111111111111111111111111111 consumed 17 of 99 compute units');self.assertEqual(self.audit()['strict_ordered_log_mismatch_cases'],0)
 def test_program_log_meter_lookalike(self):
  self.logs.append('Program log: Program 11111111111111111111111111111111 consumed 17 of 99 compute units');self.reject()
 def tearDown(self):self.assertEqual(SOURCE.read_bytes(),RAW)
if __name__=='__main__':unittest.main()
