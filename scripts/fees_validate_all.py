#!/usr/bin/env python3
"""Run all implemented Pump Fees handler suites against one candidate ELF."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,hashlib,json,pathlib,sys,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
from serial_suite_process import PROCESS_INPUTS,run_suite_process,validate_timeout
DEFAULT_SUITE_TIMEOUT=1800.0
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--suite-timeout',type=float,default=DEFAULT_SUITE_TIMEOUT);a=p.parse_args()
validate_timeout(a.suite_timeout)
# Child imports are not visible in this process. Protect their Python sources
# and Fees-specific fixture inputs as well as the original CLI candidate path.
publisher=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[
 *sorted((ROOT/'scripts').glob('*.py')), *PROCESS_INPUTS,
 ROOT/'programs/pump-fees',
 ROOT/'research/fees-query-inputs/quote-selector-cases.json.gz',
 ROOT/'research/fees-query-inputs/fee-selector-cases.json.gz',
 ROOT/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
 ROOT/'evidence/dependencies/donation_relay/deployed.so',
])
CASE_DIFFERENCE_FIELDS=('different_fields','diff','differences','mismatched_fields','mismatches','failures')
# Match each producer's comparison contract; raw logs/compute are deliberately
# excluded except for the event lines those producers compare themselves.
OUTCOME_FIELDS={
 'queries':(),
 'administration':('error','data_hex','lamports','owner','payer_delta','events','inner_instructions'),
 'initialization':('error','data_hex','lamports','owner','balance_deltas','pump_data','events','inner_instructions'),
 'configuration':('error','data_hex','lamports','owner','balance_deltas','events','inner_instructions'),
 'extension':('error','data_hex','lamports','owner','balance_deltas','events','inner_instructions'),
 'deprecated':('error','accounts','payer_delta','events','inner_instructions'),
 'upsert':('error','data_hex','lamports','owner','balance_deltas','events','inner_instructions'),
 'admin_transfer':('error','data_hex','lamports','owner','payer_delta','events','inner_instructions'),
 'donation_create':('error','data','owner','lamports','payer_delta','authority_delta','events','inner'),
 'donation_crank':('error','before','after','inner'),
 'social_create':('error','data','lamports','owner','authority_lamports','inner'),
 'social_claim':('error','before','after','events','inner','return'),
 'social_claim_v2':('error','before','after','events','inner','return'),
 'withdrawal':('error','before','after','events','inner','return'),
 'buyback':('error','before','after','inner','return'),
 'sharing_creation':('error','sharing','curve','payer_lamports','authority_lamports','sharing_lamports','pool','pool_lamports','curve_lamports','events','inner'),
 'sharing_update':('error','before','after','events','inner','return'),
 'sharing_admin_cto':('error','before','after','events','inner','return'),
}
EVENT_LOG_SUITES={'donation_crank','social_create','buyback'}
def exact_json_equal(left,right):
 if type(left) is not type(right):return False
 if type(left) is dict:return left.keys()==right.keys() and all(exact_json_equal(left[key],right[key]) for key in left)
 if type(left) is list:return len(left)==len(right) and all(exact_json_equal(a,b) for a,b in zip(left,right))
 return left==right
def validate_outcomes(name,index,row):
 original,candidate=row.get('original'),row.get('candidate')
 assert isinstance(original,dict) and isinstance(candidate,dict),f'{name} case {index}: incomplete original/candidate outcome'
 if name=='queries':
  assert set(original) in ({'fees'},{'error'}) and set(candidate) in ({'fees'},{'error'}),f'{name} case {index}: query outcome is missing'
 for field in OUTCOME_FIELDS[name]:
  assert field in original and field in candidate,f'{name} case {index}: missing retained {field}'
  assert exact_json_equal(original[field],candidate[field]),f'{name} case {index}: retained {field} differs'
 if name in ('queries','deprecated'):
  assert exact_json_equal(original,candidate),f'{name} case {index}: retained outcomes differ'
 if name in EVENT_LOG_SUITES:
  events=[]
  for outcome in (original,candidate):
   logs=outcome.get('logs')
   assert isinstance(logs,list) and all(isinstance(line,str) for line in logs),f'{name} case {index}: event log source missing'
   events.append([line for line in logs if line.startswith('Program data:')])
  assert events[0]==events[1],f'{name} case {index}: retained events differ'
def validate_suite_receipt(name,suite):
 assert isinstance(suite,dict),f'{name}: suite receipt must be an object'
 cases=suite.get('cases')
 assert isinstance(cases,list) and cases,f'{name}: a non-empty cases list is required'
 # A default of len(cases) is true by construction: a producer that stopped
 # declaring case_count would still pass, so require the declared key.
 assert 'case_count' in suite,f'{name}: case_count must be declared'
 count=suite['case_count']
 assert type(count) is int and count==len(cases),f'{name}: case_count differs from retained cases'
 suite['case_count']=count
 suite_mismatches=[]
 for key in ('mismatches','failures'):
  if key in suite:
   assert isinstance(suite[key],list),f'{name}: {key} must be a list'
   suite_mismatches.extend(suite[key])
 if 'mismatch_count' in suite:
  assert type(suite['mismatch_count']) is int and suite['mismatch_count']==len(suite_mismatches),f'{name}: mismatch_count differs from retained failures'
 for index,row in enumerate(cases):
  assert isinstance(row,dict),f'{name} case {index}: result must be an object'
  if 'match' in row:
   assert row['match'] is True,f'{name} case {index}: match is not true'
  diff_fields=tuple(field for field in CASE_DIFFERENCE_FIELDS if field in row)
  for field in diff_fields:
   assert row[field]==[],f'{name} case {index}: {field} is not an empty difference list'
  validate_outcomes(name,index,row)
 return suite_mismatches
candidate=pin_program(a.candidate.resolve())
process_hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in PROCESS_INPUTS}
suites={};suite_mismatches={}
with tempfile.TemporaryDirectory(prefix='fees-differential-') as temp:
 for name,script in [('queries','validate_fee_handlers.py'),('administration','fees_admin_differential.py'),('initialization','fees_initialize_differential.py'),('configuration','fees_config_differential.py'),('extension','fees_extend_differential.py'),('deprecated','fees_deprecated_differential.py'),('upsert','fees_upsert_differential.py'),('admin_transfer','fees_admin_transfer_differential.py'),('donation_create','fees_donation_create_differential.py'),('donation_crank','fees_donation_crank_probe.py'),('social_create','fees_social_create_differential.py'),('social_claim','fees_social_claim_differential.py'),('social_claim_v2','fees_social_claim_v2_differential.py'),('withdrawal','fees_withdraw_differential.py'),('buyback','fees_buyback_differential.py'),('sharing_creation','fees_sharing_create_differential.py'),('sharing_update','fees_sharing_update_differential.py'),('sharing_admin_cto','fees_admin_cto_differential.py')]:
  output=pathlib.Path(temp)/(name+'.json')
  completed,timed_out=run_suite_process([sys.executable,str(ROOT/'scripts'/script),'--candidate',str(candidate),'--output',str(output)],timeout=a.suite_timeout)
  if completed.stdout:print(completed.stdout,end='',flush=True)
  if timed_out:raise SystemExit(f'suite {name} exceeded {a.suite_timeout}s')
  completed.check_returncode()
  assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in process_hashes.items()), 'suite process helper changed'
  suites[name]=json.loads(output.read_text(encoding='utf-8'))
  suite_mismatches[name]=validate_suite_receipt(name,suites[name])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'Thirty handler paths, including two deprecated dispatches; historical fixed-admin initializer replay is indexed separately. Independent SBF original/candidate execution; no complete source or byte identity. Per-suite limits are preserved.','original_sha256':sha(ROOT/'evidence/original/pump_fees/deployed.so'),'candidate_sha256':sha(candidate),'case_count':sum(s['case_count'] for s in suites.values()),'mismatches':[f'{n}: {m}' for n,items in suite_mismatches.items() for m in items],'suite_timeout_seconds':a.suite_timeout,'process_runner_sha256':process_hashes,'suites':suites}
assert all(s['original_sha256']==report['original_sha256'] and s['candidate_sha256']==report['candidate_sha256'] for s in suites.values())
print(json.dumps({'cases':report['case_count'],'mismatches':report['mismatches']}));assert not report['mismatches'];publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'))
