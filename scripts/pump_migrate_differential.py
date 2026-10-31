#!/usr/bin/env python3
"""Normally signed legacy Pump migration differential, synthetic state and captured CPIs."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import sys,json,gzip,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pump_migrate_probe as p
from pump_differential_output import PumpReport
cases=[{'boost':True},{},{'boost':True,'complete':0},{'boost':True,'enable_migrate':0}]
def patch(name,offset,val):return {'boost':True,'mutations':{name:{'patches':[(offset,val.hex())]}}}
for v in [0,1,10,2039280,15000001,10**9,2**64-1]:cases.append(patch('global',146,v.to_bytes(8,'little')))
for off in [8,16,24,32,40]:
 for v in [0,1,100,10**9,2**64-1]:cases.append(patch('bonding_curve',off,v.to_bytes(8,'little')))
for off in [81,82,123,124]:
 for v in [0,1,2]:cases.append(patch('bonding_curve',off,bytes([v])))
for size in [0,7,8,48,49,81,82,83,114,115,123,124,125,166,200]:cases.append({'boost':True,'mutations':{'bonding_curve':{'length':size}}})
for v in [0,1,10**6,10**9,10**11]:cases.append({'boost':True,'mutations':{'bonding_curve':{'lamports':v}}})
for name in ['global','withdraw_authority','mint','bonding_curve','associated_bonding_curve','system_program','token_program','pump_amm','pool','pool_authority','pool_authority_mint_account','pool_authority_wsol_account','amm_global_config','wsol_mint','lp_mint','user_pool_token_account','pool_base_token_account','pool_quote_token_account','token_2022_program','associated_token_program','pump_amm_event_authority','event_authority','program','rent']:cases.append({'boost':True,'wrong':name})
for name in ['withdraw_authority','bonding_curve','associated_bonding_curve','user','pool','pool_authority','pool_authority_mint_account','pool_authority_wsol_account','lp_mint','user_pool_token_account','pool_base_token_account','pool_quote_token_account']:cases.append({'boost':True,'readonly':name})


cases += [{'boost':True,'repeat':True},{'mayhem':1},{'boost':True,'mutations':{'bonding_curve':{'patches':[(83,bytes(p.WSOL).hex())]}}}]
for name in ['mint','associated_bonding_curve','global','bonding_curve','amm_global_config']:
 for off,val in [(0,bytes(8)),(32,bytes(32))]:cases.append(patch(name,off,val))
 for owner in [str(p.TOKEN),str(p.Pubkey.default())]:cases.append({'boost':True,'mutations':{name:{'owner':owner}}})
for name in ['mint','associated_bonding_curve']:
 for length in [0,8,64,81,82,164,165,200]:cases.append({'boost':True,'mutations':{name:{'length':length}}})
for value in [0,1,1000,10**9,2**64-1]:cases.append(patch('associated_bonding_curve',64,value.to_bytes(8,'little')))
for offset in [0,32,108]:
 for value in [bytes(32),bytes(p.USER.pubkey())] if offset!=108 else [b'\0',b'\2']:cases.append(patch('associated_bonding_curve',offset,value))
for value in [0,1,2,255]:cases.append(patch('mint',44,bytes([value])))
for name in ['pool_authority','withdraw_authority']:
 for lamports in [0,1,890880,2039280,10**9]:cases.append({'boost':True,'mutations':{name:{'lamports':lamports}}})


cases += [{'boost':True,'unsigned':True},{'boost':True,'readonly_boost':True},{'boost':True,'remaining_count':0},{'boost':True,'remaining_count':1}]
for offs in [[8,16],[8,16,24,32],[8,16,32],[16,32],[8,32]]:cases.append({'boost':True,'mutations':{'bonding_curve':{'patches':[(o,bytes(8).hex()) for o in offs]}}})
for v in [0,1,100,10000,2**64-1]:cases.append(patch('bonding_curve',115,v.to_bytes(8,'little')))
for length in [0,8,32,56,57,417,642,907,939,940,941,949]:cases.append({'boost':True,'mutations':{'amm_global_config':{'length':length}}})
for offset in [56,417,642,939,940]:
 for v in [0,1,2,255]:cases.append(patch('amm_global_config',offset,bytes([v])))
for name in ['pool','lp_mint','pool_authority_mint_account','pool_authority_wsol_account','pool_base_token_account','pool_quote_token_account','user_pool_token_account']:
 for owner in [str(p.TOKEN),str(p.Pubkey.default())]:cases.append({'boost':True,'mutations':{name:{'owner':owner,'lamports':10000000}}})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();rows=[];publisher=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[ROOT/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'])
 for c in cases:
  x=p.run(c);y=p.run(c,a.candidate) if a.candidate else None
  for r in [x,y]:
   if r is not None:r['events']=[l for l in r['logs'] if l.startswith('Program data:')]
  diff=[] if y is None else [k for k in ['error','before','after','events','inner','return'] if x[k]!=y[k]]
  rows.append({'case':c,'original':x,'candidate':y,'mismatched_fields':diff})
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();result={'scope':'Legacy migrate only; ordinary owned-key signatures, synthetic completed curves and captured genuine AMM/Token/Token22/ATA CPIs. Partial reconstruction evidence, not binary identity.','case_count':len(rows),'candidate_sha256':sha(a.candidate) if a.candidate else None,'original_sha256':sha(ROOT/'evidence/original/pump/deployed.so'),'script_sha256':sha(Path(__file__)),'fixture_sha256':sha(Path(p.__file__)),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r['mismatched_fields']]};raw=json.dumps(result,separators=(',',':')).encode();publisher.write(gzip.compress(raw,mtime=0) if a.output.suffix=='.gz' else raw);print(json.dumps({'case_count':len(rows),'mismatches':result['mismatches']}));assert not result['mismatches']
if __name__=='__main__':main()
