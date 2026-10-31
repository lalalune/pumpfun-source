#!/usr/bin/env python3
"""Normally signed Pump migrate_v2 differential, synthetic state and captured CPIs."""
if not __debug__:
    raise SystemExit("Normal Python is required; do not use -O or PYTHONOPTIMIZE.")
from pathlib import Path
import sys,json,gzip,argparse,hashlib
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pump_migrate_v2_probe as p
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
for name in ['global','withdraw_authority','base_mint','bonding_curve','associated_base_bonding_curve','system_program','base_token_program','pump_amm','pool','pool_authority','pool_authority_mint_account','pool_authority_quote_account','amm_global_config','quote_mint','lp_mint','user_pool_token_account','pool_base_token_account','pool_quote_token_account','token_2022_program','associated_token_program','pump_amm_event_authority','event_authority','program','rent']:cases.append({'boost':True,'wrong':name})
for name in ['withdraw_authority','bonding_curve','associated_base_bonding_curve','user','pool','pool_authority','pool_authority_mint_account','pool_authority_quote_account','lp_mint','user_pool_token_account','pool_base_token_account','pool_quote_token_account']:cases.append({'boost':True,'readonly':name})


cases += [{'boost':True,'repeat':True},{'mayhem':1},{'boost':True,'mutations':{'bonding_curve':{'patches':[(83,bytes(p.WSOL).hex())]}}}]
for name in ['base_mint','associated_base_bonding_curve','global','bonding_curve','amm_global_config']:
 for off,val in [(0,bytes(8)),(32,bytes(32))]:cases.append(patch(name,off,val))
 for owner in [str(p.TOKEN),str(p.Pubkey.default())]:cases.append({'boost':True,'mutations':{name:{'owner':owner}}})
for name in ['base_mint','associated_base_bonding_curve']:
 for length in [0,8,64,81,82,164,165,200]:cases.append({'boost':True,'mutations':{name:{'length':length}}})
for value in [0,1,1000,10**9,2**64-1]:cases.append(patch('associated_base_bonding_curve',64,value.to_bytes(8,'little')))
for offset in [0,32,108]:
 for value in [bytes(32),bytes(p.USER.pubkey())] if offset!=108 else [b'\0',b'\2']:cases.append(patch('associated_base_bonding_curve',offset,value))
for value in [0,1,2,255]:cases.append(patch('base_mint',44,bytes([value])))
for name in ['pool_authority','withdraw_authority']:
 for lamports in [0,1,890880,2039280,10**9]:cases.append({'boost':True,'mutations':{name:{'lamports':lamports}}})


cases += [{'boost':True,'unsigned':True},{'boost':True,'readonly_boost':True},{'boost':True,'remaining_count':0},{'boost':True,'remaining_count':1}]
for offs in [[8,16],[8,16,24,32],[8,16,32],[16,32],[8,32]]:cases.append({'boost':True,'mutations':{'bonding_curve':{'patches':[(o,bytes(8).hex()) for o in offs]}}})
for v in [0,1,100,10000,2**64-1]:cases.append(patch('bonding_curve',115,v.to_bytes(8,'little')))
for length in [0,8,32,56,57,417,642,907,939,940,941,949]:cases.append({'boost':True,'mutations':{'amm_global_config':{'length':length}}})
for offset in [56,417,642,939,940]:
 for v in [0,1,2,255]:cases.append(patch('amm_global_config',offset,bytes([v])))
for name in ['pool','lp_mint','pool_authority_mint_account','pool_authority_quote_account','pool_base_token_account','pool_quote_token_account','user_pool_token_account']:
 for owner in [str(p.TOKEN),str(p.Pubkey.default())]:cases.append({'boost':True,'mutations':{name:{'owner':owner,'lamports':10000000}}})


# Native baseline uses Token2022; independently exercise Token and two quote-token owners.
base_cases=list(cases)
cases += [{**c,'token22':False} for c in base_cases[:104]]
cases += [{**c,'stable':True,'quote22':q} for q in [False,True] for c in base_cases]
for stable in [False,True]:
 for name in ['quote_token_program','associated_quote_bonding_curve']:
  cases.append({'boost':True,'stable':stable,'wrong':name})
  cases.append({'boost':True,'stable':stable,'readonly':name})
 for offset in [0,32,64,108]:
  for value in ([bytes(32)] if offset in [0,32] else [bytes(8)] if offset==64 else [b'\0',b'\2']):cases.append({'boost':True,'stable':stable,'mutations':{'associated_quote_bonding_curve':{'patches':[(offset,value.hex())]}}})


# Transfer-fee source accounts are synthetic and normally signed through the actual Pump CPI.
def fee_extension_cases():
 import base64,struct
 for target in ['base','quote']:
  for bps in [0,1,100,10000]:
   mint=bytearray(base64.b64decode(p.SAVED['mint']['data_base64'])[:82]) if target=='base' else bytearray(82)
   if target=='quote':mint[44]=6;mint[45]=1
   curve=p.pda([b'bonding-curve',bytes(p.MINT)],p.P);m=p.MINT if target=='base' else p.Pubkey.from_bytes(bytes([217])*32)
   acct=bytearray(base64.b64decode(p.SAVED['curve_base']['data_base64'])[:165]) if target=='base' else bytearray(165);acct[:32]=bytes(m);acct[32:64]=bytes(curve)
   if target=='quote':acct[64:72]=(85005359063).to_bytes(8,'little');acct[108]=1
   conf=bytes(72)+struct.pack('<QQH',0,2**64-1,bps)*2;mint=bytes(mint)+bytes(83)+bytes([1])+struct.pack('<HH',1,len(conf))+conf;acct=bytes(acct)+bytes([2])+struct.pack('<HHQ',2,8,0)
   for writable in [[],['quote_mint']]:yield {'boost':True,'stable':True,'quote22':True,'writable':writable,'mutations':{target+'_mint':{'patches':[(0,mint.hex())]},'associated_'+target+'_bonding_curve':{'patches':[(0,acct.hex())]}}}
cases+=list(fee_extension_cases())


cases.append({'boost':True,'stable':True,'mutations':{'global':{'patches':[(1013,bytes(32).hex())]}}})
for stable in [False,True]:
 for field in ['pool_authority_mint_account','pool_authority_quote_account']:
  pa=p.pda([b'pool-authority',bytes(p.MINT)],p.P);mint=p.MINT if field=='pool_authority_mint_account' else p.Pubkey.from_bytes(bytes([217])*32) if stable else p.WSOL;tp=p.T22 if field=='pool_authority_mint_account' else p.TOKEN;data=bytearray(165);data[:32]=bytes(mint);data[32:64]=bytes(pa);data[64:72]=(1000).to_bytes(8,'little');data[108]=1;lamports=2039280
  if not stable and field=='pool_authority_quote_account':data[109:113]=(1).to_bytes(4,'little');data[113:121]=(2039280).to_bytes(8,'little');lamports+=1000
  cases.append({'boost':True,'stable':stable,'mutations':{field:{'owner':str(tp),'lamports':lamports,'patches':[(0,data.hex())]}}})

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path);parser.add_argument('--output',type=Path,required=True);a=parser.parse_args();rows=[];publisher=PumpReport(a.output,ROOT,a.candidate,__file__,extra_inputs=[ROOT/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'])
 for c in cases:
  x=p.run(c);y=p.run(c,a.candidate) if a.candidate else None
  for r in [x,y]:
   if r is not None:r['events']=[l for l in r['logs'] if l.startswith('Program data:')]
  diff=[] if y is None else [k for k in ['error','before','after','events','inner','return'] if x[k]!=y[k]]
  rows.append({'case':c,'original':x,'candidate':y,'mismatched_fields':diff})
 sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();result={'scope':'Migrate_v2 native and synthetic whitelisted stable quotes only; ordinary owned-key signatures, synthetic completed curves and captured genuine AMM/Token/Token22/ATA CPIs. Partial reconstruction evidence, not binary identity.','case_count':len(rows),'candidate_sha256':sha(a.candidate) if a.candidate else None,'original_sha256':sha(ROOT/'evidence/original/pump/deployed.so'),'script_sha256':sha(Path(__file__)),'fixture_sha256':sha(Path(p.__file__)),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r['mismatched_fields']]};raw=json.dumps(result,separators=(',',':')).encode();publisher.write(gzip.compress(raw,mtime=0) if a.output.suffix=='.gz' else raw);print(json.dumps({'case_count':len(rows),'mismatches':result['mismatches']}));assert not result['mismatches']
if __name__=='__main__':main()
