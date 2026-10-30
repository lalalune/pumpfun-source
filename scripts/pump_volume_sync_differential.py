#!/usr/bin/env python3
"""Pump synchronization: verified ordinary signatures and explicit synthetic state."""
import argparse,base64,gzip,hashlib,json,struct
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));PROGRAM=Pubkey.from_string(IDL['address']);ORIGINAL=ROOT/'evidence/original/pump/deployed.so';USER=Keypair.from_seed(bytes([222])*32);PAYER=Keypair.from_seed(bytes([223])*32);OTHER=Pubkey.from_bytes(bytes([224])*32);EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0];G=Pubkey.find_program_address([b'global_volume_accumulator'],PROGRAM)[0];V=Pubkey.find_program_address([b'user_volume_accumulator',bytes(USER.pubkey())],PROGRAM)[0]
IX=next(x for x in IDL['instructions'] if x['name']=='sync_user_volume_accumulator');DISC={x['name']:bytes(x['discriminator']) for x in IDL['accounts']}
def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(PROGRAM,binary);vm.set_clock(Clock(100,c.get('now',10),0,0,c.get('now',10)));vm.airdrop(PAYER.pubkey(),10**12);vm.airdrop(USER.pubkey(),10**12)
 gd=DISC['GlobalVolumeAccumulator']+struct.pack('<qqq',c.get('start',0),c.get('end',100),c.get('day',1))+bytes(32)+b''.join(struct.pack('<Q',n) for n in c.get('supplies',[1000]*30))+b''.join(struct.pack('<Q',n) for n in c.get('volumes',[100]*30))
 ud=DISC['UserVolumeAccumulator']+bytes.fromhex(c.get('stored_user',bytes(USER.pubkey()).hex()))+struct.pack('<BQQQqBQQQQ',c.get('needs_claim',1),c.get('unclaimed',0),c.get('claimed',0),c.get('volume',20),c.get('last',0),c.get('has_claimed',0),c.get('cashback',0),c.get('claimed_cashback',0),c.get('stable_cashback',0),c.get('claimed_stable_cashback',0))
 for key,data,name in [(G,gd,'global'),(V,ud,'user')]:
  data=bytearray(data)
  for off,val in c.get(name+'_patches',[]):data[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  length=c.get(name+'_length',600 if name=='global' else 137);data=(data+bytes(max(0,length-len(data))))[:length]
  vm.set_account(key,Account(c.get(name+'_lamports',10**8),bytes(data),Pubkey.from_string(c.get(name+'_owner',str(PROGRAM)))))
 keys=[USER.pubkey(),G,V,EVENT,PROGRAM];metas=[AccountMeta(k,a.get('signer',False),a.get('writable',False)) for k,a in zip(keys,IX['accounts'])]
 for i,a in enumerate(IX['accounts']):
  if c.get('readonly')==a['name']:metas[i]=AccountMeta(keys[i],False,False)
  if c.get('wrong')==a['name']:metas[i]=AccountMeta(OTHER,False,metas[i].is_writable)
 metas=metas[:c.get('account_count',len(metas))];payload=(bytes(IX['discriminator'])+bytes.fromhex(c.get('trailing','')))[:c.get('payload_length',99)];tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for k in keys+[PAYER.pubkey(),OTHER]:
   a=vm.get_account(k)
   if a and a.executable:continue
   out[str(k)]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json());a=vm.get_account(V)
 return {'before':before,'after':snap(),'error':str(r.err()) if fail else None,'logs':m.logs(),'events':[l for l in m.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'decoded_user':struct.unpack('<BQQQqBQQQQ',a.data[40:106]) if a and len(a.data)>=106 else None}
def cases():
 rows=[{'name':'base'}]
 for name,values in [('needs_claim',[0,1,2]),('has_claimed',[0,1,2]),('unclaimed',[0,1,100,2**64-1]),('claimed',[0,1,100,2**64-1]),('volume',[0,1,99,100,101,2**64-1]),('last',[-1,0,1,9,10,11,29,30,100]),('now',[-1,0,1,9,10,29,30,99,100,101]),('day',[-1,0,1,2,100]),('end',[-1,0,1,10,11,100]),('start',[-1,0,1,10,11,100])]:rows.extend({'name':f'{name}-{v}',name:v} for v in values)
 for start in [0,10,100]:
  for now in [-1,0,9,10,11,99,100,101]:
   for last in [-1,0,9,10,99,100,101]:rows.append({'name':f'reset-{start}-{now}-{last}','start':start,'now':now,'last':last,'claimed':123,'has_claimed':1,'unclaimed':456,'needs_claim':1,'volume':789})
 for name in ['global','user']:
  lengths=[0,7,8,31,32,63,64,303,304,543,544,599,600,601] if name=='global' else [0,7,8,39,40,41,73,74,81,82,89,90,97,98,105,106,136,137,138]
  for n in lengths:rows.append({'name':f'{name}-length-{n}',name+'_length':n})
  for owner in [str(Pubkey.default()),str(OTHER)]:rows.append({'name':f'{name}-owner-{owner}',name+'_owner':owner})
  for amount in [0,1]:rows.append({'name':f'{name}-funds-{amount}',name+'_lamports':amount})
  rows.append({'name':f'{name}-discriminator',name+'_patches':[(0,'ff')]})
 for account in IX['accounts']:
  rows.append({'name':'wrong-'+account['name'],'wrong':account['name']})
  rows.append({'name':'readonly-'+account['name'],'readonly':account['name']})
 for n in range(5):rows.append({'name':'missing-'+str(n),'account_count':n})
 for n in range(8):rows.append({'name':'payload-'+str(n),'payload_length':n})
 for extra in [{'stored_user':bytes(32).hex()},{'trailing':'ffffffff'},{'start':100,'claimed':0,'has_claimed':1},{'start':100,'claimed':2**64-1,'has_claimed':0},{'start':100,'claimed':123,'has_claimed':1,'cashback':3,'claimed_cashback':4,'stable_cashback':5,'claimed_stable_cashback':6},{'start':100,'claimed':123,'has_claimed':1,'global_patches':[(32,'ff'*32)]}]:rows.append({'name':'extra-'+str(len(rows)),**extra})
 for claimed in [0,1,2**64-1]:
  for has in [0,1]:
   for needs in [0,1]:
    for stored in [bytes(USER.pubkey()).hex(),bytes(32).hex()]:rows.append({'name':f'joint-{claimed}-{has}-{needs}-{stored[:8]}','start':100,'claimed':claimed,'has_claimed':has,'needs_claim':needs,'stored_user':stored,'unclaimed':2**64-1,'volume':2**64-1,'cashback':7,'claimed_cashback':8,'stable_cashback':9,'claimed_stable_cashback':10})
 for start in [-2**63,2**63-1]:
  for now in [-2**63,0,2**63-1]:
   for last in [-2**63,0,2**63-1]:rows.append({'name':f'extreme-{start}-{now}-{last}','start':start,'now':now,'last':last,'claimed':123,'has_claimed':1})
 for c in [{'end':-2**63,'day':0,'supplies':[2**64-1]*30,'volumes':[0]*30},{'end':2**63-1,'day':-1,'supplies':[0]*30,'volumes':[2**64-1]*30}]:rows.append({'name':f'unused-{len(rows)}','start':100,'claimed':123,'has_claimed':1,**c})
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c['name'])
 report={'scope':'Explicit synthetic state; normally signed local transactions; no byte identity claim.','original_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest() if a.candidate else None,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'mismatches':bad};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(len(rows),'cases',len(bad),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
