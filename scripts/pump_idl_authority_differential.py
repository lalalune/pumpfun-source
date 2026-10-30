#!/usr/bin/env python3
"""Offline Pump IDL-authority reconstruction with normal administrator signatures."""
import argparse,base64,gzip,hashlib,json,struct
from pathlib import Path
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from pump_amm_reusable_harness import pin_program
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));PROGRAM=Pubkey.from_string(IDL['address']);ORIGINAL=ROOT/'evidence/original/pump/deployed.so';AUTH=Keypair.from_seed(bytes([231])*32);PAYER=Keypair.from_seed(bytes([232])*32);OTHER=Keypair.from_seed(bytes([233])*32);NEW=Pubkey.from_bytes(bytes([234])*32);EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0];SIGNER=Pubkey.find_program_address([],PROGRAM)[0];GLOBAL=Pubkey.find_program_address([b'global'],PROGRAM)[0];IDLACCOUNT=Pubkey.create_with_seed(SIGNER,'anchor:idl',PROGRAM);IX=next(x for x in IDL['instructions'] if x['name']=='admin_set_idl_authority');CAPTURE=next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump')
def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(PROGRAM,pin_program(binary));vm.set_clock(Clock(100,1700000000,0,0,1700000000))
 for kp in [AUTH,PAYER,OTHER]:vm.airdrop(kp.pubkey(),10**12)
 gl=bytearray(base64.b64decode(CAPTURE['data_base64']));gl[9:41]=bytes(AUTH.pubkey());vm.set_account(GLOBAL,Account(10**9,bytes(gl),PROGRAM))
 data=hashlib.sha256(b'internal:IdlAccount').digest()[:8]+bytes(Pubkey.from_string(c.get('stored_authority',str(SIGNER))))+struct.pack('<I',c.get('data_len',5))+b'abcde'+bytes(32)
 target=OTHER.pubkey() if c.get('other_idl_address') else IDLACCOUNT;vm.set_account(target,Account(10**8,data,PROGRAM))
 names={'authority':OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey(),'global':GLOBAL,'idl_account':target,'system_program':Pubkey.default(),'program_signer':SIGNER,'event_authority':EVENT,'program':PROGRAM}
 for name,mut in c.get('mutations',{}).items():
  key=names[name];a=vm.get_account(key)
  if mut.get('missing'):vm.set_account(key,Account(0,b'',Pubkey.default()));continue
  d=bytearray(a.data)
  for off,val in mut.get('patches',[]):d[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  size=mut.get('length',len(d));d=(d+bytes(max(0,size-len(d))))[:size];vm.set_account(key,Account(mut.get('lamports',a.lamports),bytes(d),Pubkey.from_string(mut.get('owner',str(a.owner)))))
 if c.get('wrong'):names[c['wrong']]=NEW
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),(a.get('writable',False) or a['name']==c.get('writable')) and a['name']!=c.get('readonly')) for a in IX['accounts']][:c.get('account_count',len(IX['accounts']))]
 payload=(bytes(IX['discriminator'])+bytes(Pubkey.from_string(c.get('new_authority',str(NEW))))+bytes.fromhex(c.get('trailing','')))[:c.get('payload_length',1000)];ks={m.pubkey for m in metas if m.is_signer}|{PAYER.pubkey()};tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[k for k in [AUTH,PAYER,OTHER] if k.pubkey() in ks],vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for key in set(names.values())|{PAYER.pubkey(),AUTH.pubkey(),IDLACCOUNT}:
   a=vm.get_account(key)
   if a and a.executable:continue
   out[str(key)]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return {'before':before,'after':snap(),'error':str(r.err()) if fail else None,'logs':m.logs(),'events':[l for l in m.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 out=[{'name':'base'},{'name':'other-idl-address','other_idl_address':True},{'name':'wrong-authority','wrong_authority':True},{'name':'unsigned','unsigned':True}]
 for key in [Pubkey.default(),AUTH.pubkey(),NEW,SIGNER]:out.append({'name':'stored-'+str(key),'stored_authority':str(key)});out.append({'name':'new-'+str(key),'new_authority':str(key)})
 for name in ['global','idl_account']:
  for label,mut in [('missing',{'missing':True}),('owner',{'owner':str(Pubkey.default())}),('foreign',{'owner':str(NEW)}),('discriminator',{'patches':[(0,'ff')]}),('lamports1',{'lamports':1})]:out.append({'name':name+'-'+label,'mutations':{name:mut}})
  for n in ([0,1,7,8,31,32,39,40,41,42,43,44,45,80,100,10239,10240,10241,20000] if name=='idl_account' else [0,7,8,41,107,1088]):out.append({'name':name+'-length-'+str(n),'mutations':{name:{'length':n}}})
 for a in IX['accounts']:
  if not a.get('signer'):out.append({'name':'wrong-'+a['name'],'wrong':a['name']})
  out.append({'name':'readonly-'+a['name'],'readonly':a['name']})
 for n in range(7):out.append({'name':'accounts-'+str(n),'account_count':n})
 for n in [0,7,8,31,39]:out.append({'name':'payload-'+str(n),'payload_length':n})
 out += [{'name':'data-len-max','data_len':2**32-1},{'name':'trailing','trailing':'ffff'},{'name':'global-uninitialized','mutations':{'global':{'patches':[(8,'00')]}}}]
 for size in [0,7,8,43,44,81,10240,20000]:
  for field,value in [('owner',str(NEW)),('patches',[(0,'ff')])]:out.append({'name':f'length-{size}-{field}','mutations':{'idl_account':{'length':size,field:value}}})
 for bad in ['global','idl_account','system_program','program_signer','event_authority','program']:
  out.append({'name':'unauthorized-and-'+bad,'wrong_authority':True,'wrong':bad})
 for mut in [{'missing':True},{'owner':str(Pubkey.default())},{'owner':str(Pubkey.default()),'length':0}]:out.append({'name':'writable-create-'+str(mut),'writable':'authority','mutations':{'idl_account':mut}})
 for amount in [0,1,890880,10**8]:
  for writable in [False,True]:
   for size in [0,1]:out.append({'name':f'system-drain-{amount}-{writable}-{size}','writable':'authority' if writable else None,'mutations':{'idl_account':{'owner':str(Pubkey.default()),'length':size,'lamports':amount}}})
 for size in range(8,44):
  out.append({'name':f'truncated-header-{size}','mutations':{'idl_account':{'length':size}}})
 for name in ['authority','global','idl_account','system_program','program_signer','event_authority','program']:
  out.append({'name':'writable-'+name,'writable':name})
 for size in [44,81,10240,20000]:
  for amount in [72161279,72161280,72161281]:out.append({'name':f'rent-{size}-{amount}','mutations':{'idl_account':{'length':size,'lamports':amount}}})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c['name'])
 report={'scope':'Ordinary signed local synthetic fixtures; genuine program CPI signing only; no byte identity claim.','original_sha256':hashlib.sha256(pin_program(ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'mismatches':bad};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_bytes(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(len(rows),'cases',len(bad),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
