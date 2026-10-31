"""Main-Pump legacy cashback boundaries and observable payment ordering.

Synthetic signed fixtures. Source coordinates and compute-unit totals are
retained but excluded from diagnostic equality. Two zero-payer cases fail at
transaction admission and provide no Pump execution coverage.
"""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import sys,json,gzip,base64,struct,hashlib,argparse,re
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'evidence/original/pump/deployed.so').is_file());sys.path.insert(0,str(ROOT/'scripts'))
from pump_differential_output import PumpReport
import pump_legacy_buy_differential as h

def diagnostics(x):
 panic=[l.split('\n',1)[-1] for l in x['logs'] if l.startswith('Program log: panicked at ')]
 anchor=[m.groups() for l in x['logs'] if (m:=re.search(r'Error Code: (.*?)\. Error Number: (\d+)\. Error Message: (.*)',l))]
 return {'panic':panic,'anchor':anchor}

def cases():
 out=[];cal=[]
 for kind in ['buy','buy_exact_sol_in']:
  base={'kind':kind,'curve_bytes':[[82,1]],'account_mutations':{'user_volume_accumulator':{'u64':[[74,0]]}}}
  original=h.run(base);assert original['error'] is None
  key=str(h.f.Pubkey.find_program_address([b'user_volume_accumulator',bytes(h.USER.pubkey())],h.P)[0]);amount=struct.unpack_from('<Q',base64.b64decode(original['accounts'][key]['data']),74)[0];assert amount>0
  cal.append({'case':base,'original':original,'amount':amount,'key':key})
  for total in [0,2**64-1-amount,2**64-amount,2**64-1]:
   out.append({**base,'name':f'{kind}-{total}','account_mutations':{'user_volume_accumulator':{'u64':[[74,total]]}}})
  for dest in ['user_volume_accumulator','bonding_curve','user']:
   mut={'user_volume_accumulator':{'u64':[[74,2**64-1]]}}
   mut.setdefault(dest,{}).update(lamports=0 if dest=='user' else 2**64-1)
   out.append({**base,'name':f'{kind}-{dest}-priority','account_mutations':mut})
 return out,cal

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();output=PumpReport(args.output,ROOT,args.candidate,__file__,extra_inputs=h.REPORT_INPUTS);fixtures,cal=cases();rows=[]
 for case in fixtures:
  a=h.run(case);b=h.run(case,args.candidate);diff=[k for k in ('error','before','accounts','events','inner','return_data') if a[k]!=b[k]]
  if diagnostics(a)!=diagnostics(b):diff.append('diagnostics')
  rows.append({'case':case,'original':a,'candidate':b,'different_fields':diff,'match':not diff})
 result={'scope':__doc__,'case_count':len(rows),'original_sha256':hashlib.sha256((ROOT/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(h.pin_program(args.candidate).read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'calibration':cal,'mismatches':[i for i,r in enumerate(rows) if r['different_fields']]}
 output.write(gzip.compress(json.dumps(result,indent=2).encode(),mtime=0));print(json.dumps({'cases':len(rows),'mismatches':result['mismatches']}));assert not result['mismatches']
if __name__=='__main__':main()
