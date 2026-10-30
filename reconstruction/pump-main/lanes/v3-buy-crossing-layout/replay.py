import argparse,sys,json,gzip,hashlib,types,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'scripts'))
# Only relocate the historical fixture input; execute the unchanged fixture logic.
p=ROOT/'scripts/pump_trade_fixture.py'
code=p.read_text();old="R/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'"
assert code.count(old)==1
code=code.replace('json.load(open('+old+'))','RETAINED_FIXTURE')
m=types.ModuleType('pump_trade_fixture');m.__file__=str(p);sys.modules[m.__name__]=m
m.RETAINED_FIXTURE=json.loads(gzip.decompress((WORK/'fixture.json.gz').read_bytes()))
exec(compile(code,str(p),'exec'),m.__dict__)
import pump_v3_configured_fee_differential as suite
from solders.transaction import Transaction
from base64 import b64decode
parser=argparse.ArgumentParser(description='Replay the 153 retained V3 Buy cases in a local VM; no RPC.')
for key in ('control','candidate','experimental'):parser.add_argument('--'+key,type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
images={'original':ROOT/'evidence/original/pump/deployed.so',**{k:getattr(args,k).resolve() for k in ('control','candidate','experimental')}}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=[c for c in suite.cases() if c['operation']=='buy_v3']
for quote in ('sol','token','token22'):
 for partial in (0,1):
  for amount in (1000001,1500000,2000000):
   for bps in (0,500):
    cases.append({'operation':'buy_v3','reserve_in':suite.base_in,'reserve_out':suite.base_out,'real_base':1000000,'creator_override':bps,'amount':amount,'max_cost':10**15,'token_quote':quote!='sol','quote2022':quote=='token22','replace':13,'user_lamports':10**16,'trailing':[partial],'case_group':'crossing'})

fields=['error','accounts','inner_instructions','event_payloads','return_data']
rows=[];bad=[];changed=[]
def logs(row):return [x for x in row['logs'] if not re.fullmatch(r'Program [1-9A-HJ-NP-Za-km-z]+ consumed [0-9]+ of [0-9]+ compute units',x)]
for i,c in enumerate(cases):
 receipts={k:suite.run(p,c) for k,p in images.items()}
 for r in receipts.values():assert all(Transaction.from_bytes(b64decode(r['transaction_base64'])).verify_with_results())
 comparisons={k:{'different_fields':[f for f in fields if receipts['original'][f]!=r[f]],'regression_fields':[f for f in fields if receipts['control'][f]!=r[f]],'ordered_non_meter_logs_equal':logs(receipts['original'])==logs(r),'control_non_meter_logs_equal':logs(receipts['control'])==logs(r)} for k,r in receipts.items() if k!='original'}
 rows.append({'case':c,'receipts':receipts,'comparisons':comparisons})
 if any(d['different_fields'] or not d['ordered_non_meter_logs_equal'] for d in comparisons.values()):bad.append(i)
 if any(d['regression_fields'] or not d['control_non_meter_logs_equal'] for d in comparisons.values()):changed.append(i)
 if (i+1)%20==0:print(json.dumps({'done':i+1,'total':len(cases),'differences':bad,'regressions':changed}),flush=True)
report={'case_count':len(cases),'images':{k:sha(p) for k,p in images.items()},'source_inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/pump_trade_fixture.py',ROOT/'scripts/pump_v3_configured_fee_differential.py']},'fixture_sha256':hashlib.sha256(gzip.decompress((WORK/'fixture.json.gz').read_bytes())).hexdigest(),'rows':rows,'differences':bad,'regressions':changed}
args.output.write_bytes(gzip.compress((json.dumps(report,sort_keys=True)+'\n').encode(),mtime=0))
print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)

assert not bad and not changed
