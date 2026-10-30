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
candidate=pin_program(a.candidate.resolve())
process_hashes={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in PROCESS_INPUTS}
suites={}
with tempfile.TemporaryDirectory(prefix='fees-differential-') as temp:
 for name,script in [('queries','validate_fee_handlers.py'),('administration','fees_admin_differential.py'),('initialization','fees_initialize_differential.py'),('configuration','fees_config_differential.py'),('extension','fees_extend_differential.py'),('deprecated','fees_deprecated_differential.py'),('upsert','fees_upsert_differential.py'),('admin_transfer','fees_admin_transfer_differential.py'),('donation_create','fees_donation_create_differential.py'),('donation_crank','fees_donation_crank_probe.py'),('social_create','fees_social_create_differential.py'),('social_claim','fees_social_claim_differential.py'),('social_claim_v2','fees_social_claim_v2_differential.py'),('withdrawal','fees_withdraw_differential.py'),('buyback','fees_buyback_differential.py'),('sharing_creation','fees_sharing_create_differential.py'),('sharing_update','fees_sharing_update_differential.py'),('sharing_admin_cto','fees_admin_cto_differential.py')]:
  output=pathlib.Path(temp)/(name+'.json')
  completed,timed_out=run_suite_process([sys.executable,str(ROOT/'scripts'/script),'--candidate',str(candidate),'--output',str(output)],timeout=a.suite_timeout)
  if completed.stdout:print(completed.stdout,end='',flush=True)
  if timed_out:raise SystemExit(f'suite {name} exceeded {a.suite_timeout}s')
  completed.check_returncode()
  assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in process_hashes.items()), 'suite process helper changed'
  suites[name]=json.loads(output.read_text())
  if 'case_count' not in suites[name]:suites[name]['case_count']=len(suites[name]['cases'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'scope':'Thirty handler paths, including two deprecated dispatches; historical fixed-admin initializer replay is indexed separately. Independent SBF original/candidate execution; no complete source or byte identity. Per-suite limits are preserved.','original_sha256':sha(ROOT/'evidence/original/pump_fees/deployed.so'),'candidate_sha256':sha(candidate),'case_count':sum(s['case_count'] for s in suites.values()),'mismatches':[f'{n}: {m}' for n,s in suites.items() for m in s.get('mismatches',s.get('failures',[]))],'suite_timeout_seconds':a.suite_timeout,'process_runner_sha256':process_hashes,'suites':suites}
assert all(s['original_sha256']==report['original_sha256'] and s['candidate_sha256']==report['candidate_sha256'] for s in suites.values())
publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode());print(json.dumps({'cases':report['case_count'],'mismatches':report['mismatches']}));assert not report['mismatches']
