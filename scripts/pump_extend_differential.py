#!/usr/bin/env python3
"""Normally signed local raw-account extension comparisons for captured Pump."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,base64,gzip,hashlib,json,struct
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));PROGRAM=Pubkey.from_string(IDL['address']);ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
PAYER=Keypair.from_seed(bytes([227])*32);USER=Keypair.from_seed(bytes([228])*32);TARGET=Pubkey.from_bytes(bytes([229])*32);OTHER=Pubkey.from_bytes(bytes([230])*32);EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0];TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
IX=next(x for x in IDL['instructions'] if x['name']=='extend_account');DISCS={x['name']:bytes(x['discriminator']) for x in IDL['accounts']}
def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(PROGRAM,pin_program(binary));vm.set_clock(Clock(100,1700000000,0,0,1700000000));vm.airdrop(PAYER.pubkey(),10**12);vm.airdrop(USER.pubkey(),c.get('user_lamports',10**12))
 size=c.get('size',8);data=(DISCS.get(c.get('kind','BondingCurve'),bytes(8))+bytes([c.get('fill',0)])*max(0,size-8))[:size]
 if c.get('data_hex') is not None:data=bytes.fromhex(c['data_hex'])
 vm.set_account(TARGET,Account(c.get('lamports',10**9),data,Pubkey.from_string(c.get('owner',str(PROGRAM))),c.get('executable',False)))
 keys=[TARGET,USER.pubkey(),Pubkey.default(),EVENT,PROGRAM];metas=[AccountMeta(k,a.get('signer',False),a.get('writable',False)) for k,a in zip(keys,IX['accounts'])]
 for i,a in enumerate(IX['accounts']):
  if c.get('readonly')==a['name']:metas[i]=AccountMeta(keys[i],metas[i].is_signer,False)
  if c.get('unsigned')==a['name']:metas[i]=AccountMeta(keys[i],False,metas[i].is_writable)
  if c.get('wrong')==a['name']:metas[i]=AccountMeta(OTHER,metas[i].is_signer,metas[i].is_writable)
 metas=metas[:c.get('account_count',len(metas))];payload=bytes(IX['discriminator'])+bytes.fromhex(c.get('trailing',''));payload=payload[:c.get('payload_length',len(payload))]
 signers=[PAYER]+([USER] if any(m.pubkey==USER.pubkey() and m.is_signer for m in metas) else [])
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  states={}
  for k in set(keys+[OTHER,PAYER.pubkey()]):
   a=vm.get_account(k)
   if a and a.executable:continue
   states[str(k)]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return states
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;raw=json.loads(m.to_json())
 return {'before':before,'after':snap(),'error':str(r.err()) if failed else None,'logs':m.logs(),'events':[x for x in m.logs() if x.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 out=[]
 for kind in list(DISCS)+['unknown']:
  for size in [0,1,7,8,49,81,82,137,166,200,256,600,1000,2000]:out.append({'name':f'{kind}-{size}','kind':kind,'size':size})
 for kind,target in [('BondingCurve',166),('Global',1088),('GlobalVolumeAccumulator',600),('UserVolumeAccumulator',137)]:
  for size in [8,target-1,target,target+1]:
   for funds in [0,1,(size+128)*6960-1,(size+128)*6960,(target+128)*6960,10**9]:out.append({'name':f'{kind}-rent-{size}-{funds}','kind':kind,'size':size,'lamports':funds})
  for label,mutation in [('unsigned',{'unsigned':'user'}),('readonly-user',{'readonly':'user'}),('readonly-target',{'readonly':'account'}),('wrong-event',{'wrong':'event_authority'}),('wrong-program',{'wrong':'program'}),('wrong-system',{'wrong':'system_program'}),('wrong-target',{'wrong':'account'}),('system-owner',{'owner':str(Pubkey.default())}),('token-owner',{'owner':str(TOKEN)}),('fill-ff',{'fill':255}),('no-user-funds',{'user_lamports':1}),('trailing',{'trailing':'ffffffff'})]:out.append({'name':f'{kind}-{label}','kind':kind,'size':80,**mutation})
  for n in range(5):out.append({'name':f'{kind}-missing-{n}','kind':kind,'account_count':n})
  for n in range(8):out.append({'name':f'{kind}-payload-{n}','kind':kind,'payload_length':n})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[];publisher=PumpReport(a.output,ROOT,a.candidate,__file__)
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]]
  rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c['name'])
 report={'scope':'Synthetic raw accounts and ordinary verified signatures on offline LiteSVM. Bounded differential evidence, not byte identity.','original_sha256':hashlib.sha256(pin_program(ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'mismatches':bad};publisher.write(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(len(rows),'cases',len(bad),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
