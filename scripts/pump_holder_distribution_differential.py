#!/usr/bin/env python3
"""Normally signed holder distribution comparisons against captured original."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import json,gzip,argparse,hashlib,sys,struct
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));import pump_holder_distribution_probe as p
cases=[]
for mode in [{},{'source':True},{'stable':True},{'stable':True,'token22':True}]:
 rows=[{}, {'amounts':[]},{'amounts':[0]},{'amounts':[0,0]},{'amounts':[1000,2000]},{'amounts':[1,2**64-1]},{'amounts':[2**64-1]},{'remaining_count':0},{'remaining_count':1},{'remaining_count':3},{'existing_dest':True},{'readonly_owner':True},{'readonly_dest':True},{'unsigned':True},{'source':False}]
 for amount in [0,1,890880,20_000_000,20_000_001,10**9,10**9+1]:rows.append({'amounts':[amount]})
 for n in [0,1,890879,890880,890881,1000]:rows.append({'holder_lamports':n})
 for name in ['global','mint','holder_rewards','holder_rewards_token_account','quote_mint','quote_token_program','associated_token_program','system_program','event_authority','program']:rows.append({'wrong':name})
 for name in ['holder_reward_claim_authority','holder_rewards','holder_rewards_token_account']:rows.append({'readonly':name})
 for name in ['global','mint','holder_rewards','holder_rewards_token_account','quote_mint']:
  for owner in [str(p.PUMP),str(p.Pubkey.default())]:rows.append({'mutations':{name:{'owner':owner}}})
 for n in [0,7,8,32,64,81,82,108,164,165]:rows.append({'mutations':{'quote_mint':{'length':n}}})
 for n in [0,32,64,108,164,165]:rows.append({'mutations':{'holder_rewards_token_account':{'length':n}}})
 for n,val in [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\0'),(108,b'\2')]:rows.append({'mutations':{'holder_rewards_token_account':{'patches':[(n,val.hex())]}}})
 rows += [{'mutations':{'global':{'patches':[(1054,bytes(p.OTHER.pubkey()).hex())]}}},{'mutations':{'owner':{'lamports':0}}},{'mutations':{'owner':{'lamports':1}}}]
 cases += [{**mode,**c} for c in rows if not (not mode.get('source',mode.get('stable',False)) and ('holder_rewards_token_account' in c.get('mutations',{}) or c.get('wrong')=='holder_rewards_token_account'))]
# Edge cases preserve genuine normal authority signatures and dependency CPIs.
for mode in [{},{'source':True},{'stable':True},{'stable':True,'token22':True}]:
 rows=[{'extra_remaining':1},{'amounts':[],'source':False},{'holder_lamports':1,'amounts':[]},{'holder_lamports':891880},{'holder_lamports':891879},{'holder_lamports':891881},{'alternate_source':True},{'alternate_dest':True},{'alternate_dest':True,'existing_dest':True},{'amounts':[0],'alternate_dest':True,'existing_dest':True}]
 for key in ['global','mint','holder_rewards']:
  for n in [0,1,7,8,32,82,165,166,1086,1087]:rows.append({'mutations':{key:{'length':n}}})
 for key in ['dest','owner']:
  for owner in [str(p.TOKEN),str(p.PUMP),str(p.Pubkey.default())]:rows.append({'existing_dest':True,'mutations':{key:{'owner':owner}}})
 for off,v in [(0,bytes(32)),(32,bytes(32)),(108,b'\0'),(108,b'\2')]:rows.append({'existing_dest':True,'mutations':{'dest':{'patches':[(off,v.hex())]}}})
 for n in [0,1,164,165]:rows.append({'existing_dest':True,'mutations':{'dest':{'length':n}}})
 for c in [{'remaining_count':0},{'amounts':[]},{'amounts':[0]}]:
  rows.append({**c,'mutations':{'holder_rewards_token_account':{'patches':[(0,bytes(32).hex())]}}})
 rows += [{'amounts':[1000,2000],'owners':[str(p.HOLDER),str(p.OTHER.pubkey())]},{'amounts':[0,0],'existing_dest':True,'mutations':{'holder_rewards_token_account':{'patches':[(108,'02')]}}}]
 cases += [{**mode,**c} for c in rows if not (not mode.get('source',mode.get('stable',False)) and 'holder_rewards_token_account' in c.get('mutations',{}))]
for mode in [{},{'source':True},{'token22':True},{'source':True,'token22':True},{'stable':True},{'stable':True,'token22':True}]:
 rows=[{'swap_token_program':True},{'amounts':[0],'swap_token_program':True},{'amounts':[0],'source':False},{'amounts':[0],'source':False,'alternate_dest':True},{'amounts':[],'swap_token_program':True},{'source_amount':0},{'holder_lamports':0,'amounts':[0]},{'holder_lamports':1,'amounts':[0]},{'amounts':[2**64-1,1],'owners':[str(p.HOLDER)]*2,'source_amount':2**64-1,'stable':True},{'amounts':[1,2**64-1],'owners':[str(p.HOLDER)]*2,'source_amount':2**64-1,'stable':True}]
 for key in ['global','holder_rewards','mint','quote_mint']:
  rows.append({'mutations':{key:{'patches':[(0,'ff')]}},'remaining_count':0})
 for key in ['quote_mint','holder_rewards_token_account']:
  if key=='holder_rewards_token_account' and not mode.get('source',mode.get('stable',False)):continue
  rows += [{'mutations':{key:{'owner':str(p.PUMP)}},'wrong':'global'},{'mutations':{key:{'patches':[(0,bytes(32).hex())]}},'wrong':'holder_rewards'}]
 cases += [{**mode,**c} for c in rows]
for mode in [{'source':True},{'stable':True},{'stable':True,'token22':True}]:
 for offset,size in [(0,64),(0,32),(32,32)]:
  for swap in [False,True]:cases.append({**mode,'swap_token_program':swap,'mutations':{'holder_rewards_token_account':{'patches':[(offset,bytes(size).hex())]}}})
for bps in [0,100,10000]:
 md=bytearray(82);md[44]=6;md[45]=1
 fee=bytes(72)+struct.pack('<QQH',0,2**64-1,bps)*2
 mint=bytes(md)+bytes(83)+b'\1'+struct.pack('<HH',1,len(fee))+fee
 src=p.token_data(p.STABLE,p.HOLDER,10**9)+b'\2'+struct.pack('<HHQ',2,8,0)
 for amount in [0,1000,10**9]:cases.append({'stable':True,'token22':True,'amounts':[amount],'mutations':{'quote_mint':{'patches':[(0,mint.hex())]},'holder_rewards_token_account':{'patches':[(0,src.hex())]}}})
def main():
 a=argparse.ArgumentParser();a.add_argument('--candidate',type=Path);a.add_argument('--output',type=Path,required=True);args=a.parse_args();rows=[]
 for c in cases:
  x=p.run(c);y=p.run(c,args.candidate) if args.candidate else None;diff=[] if y is None else [k for k in ['error','before','after','events','inner','return'] if x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'mismatched_fields':diff})
 sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest();r={'scope':'Normally signed local holder distributions with synthetic configured authority and captured actual Token/Token22/ATA CPIs. Bounded parity only; full byte identity remains false.','case_count':len(rows),'original_sha256':sha(ROOT/'evidence/original/pump/deployed.so'),'candidate_sha256':sha(args.candidate) if args.candidate else None,'script_sha256':sha(Path(__file__)),'fixture_sha256':sha(Path(p.__file__)),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r['mismatched_fields']]};args.output.parent.mkdir(parents=True,exist_ok=True);raw=json.dumps(r,separators=(',',':')).encode();args.output.write_bytes(gzip.compress(raw,mtime=0) if args.output.suffix=='.gz' else raw);print(json.dumps({'case_count':len(rows),'mismatches':r['mismatches']}));assert not r['mismatches']
if __name__=='__main__':main()
