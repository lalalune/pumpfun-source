# Adapted from thegeronimo/pumpfun-source PR #1292, commit 4a8336358fd5d2fd00257ef5523202222d6c8cc5.
# Uses unchanged repository case definitions; adds strict exit status and control-log comparison.
import sys,json,gzip,hashlib,types,re,argparse
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
p=argparse.ArgumentParser();p.add_argument('--control',type=Path,required=True);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
sys.path.insert(0,str(ROOT/'scripts'))
# Only relocate the historical fixture input; execute the unchanged fixture logic.
p=ROOT/'scripts/pump_trade_fixture.py'
code=p.read_text();old="R/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'"
assert code.count(old)==1
code=code.replace("x=json.load(open("+old+"))","x="+repr(json.loads(gzip.decompress((HERE/'fixture.json.gz').read_bytes()))))
m=types.ModuleType('pump_trade_fixture');m.__file__=str(p);sys.modules[m.__name__]=m
exec(compile(code,str(p),'exec'),m.__dict__)
import pump_sell_v2_differential as suite
from solders.transaction import Transaction
from base64 import b64decode
images={'original':ROOT/'evidence/original/pump/deployed.so','control':args.control,'candidate':args.candidate}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=suite.cases()
fields=['error','accounts','inner','events','return_data']
rows=[];bad=[];changed=[]
def logs(row):return [x for x in row['logs'] if not re.fullmatch(r'Program [1-9A-HJ-NP-Za-km-z]+ consumed \d+ of \d+ compute units',x)]
for i,c in enumerate(cases):
 receipts={k:suite.run(c,p) for k,p in images.items()}
 for r in receipts.values():assert all(Transaction.from_bytes(b64decode(r['transaction_base64'])).verify_with_results())
 diff=[k for k in fields if receipts['original'][k]!=receipts['candidate'][k]]
 regression=[k for k in fields if receipts['control'][k]!=receipts['candidate'][k]]
 logdiff=logs(receipts['original'])!=logs(receipts['candidate'])
 rows.append({'case':c,'receipts':receipts,'different_fields':diff,'regression_fields':regression,'ordered_non_meter_logs_equal':not logdiff})
 if diff or logdiff:bad.append(i)
 if regression or logs(receipts['control'])!=logs(receipts['candidate']):changed.append(i)
 if (i+1)%20==0:print(json.dumps({'done':i+1,'total':len(cases),'differences':bad,'regressions':changed}),flush=True)
report={'case_count':len(cases),'images':{k:sha(p) for k,p in images.items()},'source_inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'scripts/pump_trade_fixture.py',ROOT/'scripts/pump_sell_v2_differential.py']},'fixture_sha256':hashlib.sha256(gzip.decompress((HERE/'fixture.json.gz').read_bytes())).hexdigest(),'rows':rows,'differences':bad,'regressions':changed}
args.output.write_bytes(gzip.compress((json.dumps(report,sort_keys=True)+'\n').encode(),mtime=0))
print(json.dumps({k:v for k,v in report.items() if k!='rows'}),flush=True)
raise SystemExit(1 if bad or changed else 0)
