"""Offline main-Pump earned-cashback boundaries and payment priority.

Synthetic signed transactions; no live network or wallet activity. Compares
errors, accounts, events, inner instructions, return data and panic messages.
Source-location diagnostics and compute-unit totals are retained, not compared.
"""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import sys,json,gzip,hashlib,argparse,base64,struct
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from pump_differential_output import PumpReport
from pump_trade_fixture import REPORT_INPUTS
import pump_buy_v2_differential as buy
import pump_sell_v2_differential as sell

def messages(x):return [l.split('\n',1)[-1] for l in x['logs'] if l.startswith('Program log: panicked at ')]
def cases():
 out=[];calibration=[]
 for module,kinds in [(buy,['buy_v2','buy_exact_quote_in_v2']),(sell,['sell_v2'])]:
  for kind in kinds:
   for mode in [{},{'token_quote':True},{'token_quote':True,'token22':True}]:
    off=90 if mode.get('token_quote') else 74
    base={'kind':kind,**mode,'curve_bytes':[[82,1]],'account_mutations':{'user_volume_accumulator':{'u64':[[74,0],[90,0]]}}}
    original=module.run(base);assert original['error'] is None
    key=str(module.f.ixs[-1].accounts[11].pubkey)
    earned=struct.unpack_from('<Q',base64.b64decode(original['accounts'][key]['data']),off)[0];assert earned>0
    calibration.append({'case':base,'original':original,'earned_amount':earned,'offset':off,'accumulator_key':key})
    for total in [0,2**64-1-earned,2**64-earned,2**64-1]:
     case={**base,'name':f'{kind}-{mode}-earned-{total}','account_mutations':{'user_volume_accumulator':{'u64':[[74,0],[90,0],[off,total]]}}}
     out.append((module,case))
    case={**base,'name':f'{kind}-{mode}-inactive','curve_bytes':[[82,0]],'account_mutations':{'user_volume_accumulator':{'u64':[[74,2**64-1],[90,2**64-1]]}}}
    out.append((module,case))
 for module,kind in [(buy,'buy_v2'),(sell,'sell_v2')]:
  for token in [False,True]:
   for dest in (['associated_quote_user','associated_quote_fee_recipient','associated_quote_buyback_fee_recipient','associated_user_volume_accumulator'] if token else ['user','fee_recipient','buyback_fee_recipient','user_volume_accumulator']):
    off=90 if token else 74;mut={'user_volume_accumulator':{'u64':[[off,2**64-1]]}}
    mut.setdefault(dest,{}).update({'u64':[[64,2**64-1]]} if token else {'lamports':2**64-1})
    out.append((module,{'kind':kind,'token_quote':token,'curve_bytes':[[82,1]],'account_mutations':mut,'name':f'priority-{kind}-{token}-{dest}'}))
 return out,calibration

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();output=PumpReport(args.output,ROOT,args.candidate,__file__,extra_inputs=REPORT_INPUTS)
 fixtures,calibration=cases();rows=[]
 for module,c in fixtures:
  a=module.run(c);b=module.run(c,args.candidate);diff=[k for k in ('error','accounts','events','inner','return_data') if a[k]!=b[k]]
  if messages(a)!=messages(b):diff.append('panic_message')
  rows.append({'case':c,'original':a,'candidate':b,'different_fields':diff,'match':not diff})
 result={'scope':__doc__,'original_sha256':hashlib.sha256((ROOT/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'case_count':len(rows),'calibration':calibration,'cases':rows,'mismatches':[i for i,x in enumerate(rows) if x['different_fields']]}
 output.write((gzip.compress(json.dumps(result,indent=2).encode(),mtime=0) if args.output.suffix=='.gz' else json.dumps(result,indent=2).encode()));print(json.dumps({'cases':len(rows),'mismatches':result['mismatches']}));assert not result['mismatches']
if __name__=='__main__':main()
