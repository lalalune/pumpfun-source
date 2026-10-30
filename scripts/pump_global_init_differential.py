#!/usr/bin/env python3
"""Normally signed, offline Pump initialize differential fixture."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,base64,json,hashlib
from pathlib import Path
from pump_differential_output import PumpReport
from solders.account import Account
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from pump_amm_reusable_harness import pin_program
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
R=Path(__file__).resolve().parents[1];IDL=json.loads((R/'evidence/upstream/pump.json').read_text(encoding='utf-8'));P=Pubkey.from_string(IDL['address']);G=Pubkey.find_program_address([b'global'],P)[0];USER=Keypair.from_seed(bytes([201])*32);PAYER=Keypair.from_seed(bytes([203])*32)
IX=next(i for i in IDL['instructions'] if i['name']=='initialize');ORIGINAL=R/'evidence/original/pump/deployed.so'
def run(c,binary=None):
 vm=LiteSVM().with_transaction_history(0).with_sigverify(True);vm.add_program_from_file(P,pin_program(binary or ORIGINAL))
 vm.set_account(USER.pubkey(),Account(c.get('funds',10**12),b'',Pubkey.default()));vm.set_account(PAYER.pubkey(),Account(10**12,b'',Pubkey.default()))
 g=Pubkey.from_bytes(bytes([91])*32) if c.get('wrong_global') else G
 vm.set_account(G,Account(0,b'',Pubkey.default()));vm.set_account(Pubkey.from_bytes(bytes([91])*32),Account(0,b'',Pubkey.default()))
 if 'existing' in c:
  e=c['existing'];data=bytearray(e.get('length',0))
  if e.get('disc') and len(data)>=8:data[:8]=bytes([167,232,232,177,200,108,114,127])
  if e.get('initialized') and len(data)>8:data[8]=1
  vm.set_account(g,Account(e.get('lamports',10**8),bytes(data),P if e.get('program_owner') else Pubkey.default()))
 system=Pubkey.from_bytes(bytes([92])*32) if c.get('wrong_system') else Pubkey.default()
 metas=[AccountMeta(g,False,not c.get('readonly_global')),AccountMeta(USER.pubkey(),not c.get('unsigned'),not c.get('readonly_user')),AccountMeta(system,False,False)][:c.get('accounts',3)]
 if c.get('extra'):metas.append(AccountMeta(PAYER.pubkey(),False,False))
 data=bytes(IX['discriminator'])[:c.get('payload_length',8)]+bytes.fromhex(c.get('trailing',''))
 tx=Transaction.new_signed_with_payer([Instruction(P,data,metas)],PAYER.pubkey(),[PAYER]+([USER] if any(m.is_signer for m in metas) else []),vm.latest_blockhash());tx.verify();res=vm.send_transaction(tx);fail=isinstance(res,FailedTransactionMetadata);meta=res.meta() if fail else res;md=json.loads(meta.to_json())
 def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'executable':a.executable,'data':None if a.executable else base64.b64encode(a.data).decode()}
 return {'error':str(res.err()) if fail else None,'accounts':{str(k):snap(vm.get_account(k)) for k in tx.message.account_keys if k!=P},'events':[l[14:] for l in meta.logs() if l.startswith('Program data: ')],'inner':md['inner_instructions'],'return_data':md.get('return_data'),'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 r=[{'name':'base'},{'name':'trailing','trailing':'deadbeef'},{'name':'extra','extra':True}]
 for k in ['wrong_global','wrong_system','readonly_global','readonly_user','unsigned']:r.append({'name':k,k:True})
 for n in range(3):r.append({'name':f'accounts_{n}','accounts':n})
 for n in [0,1,7]:r.append({'name':f'payload_{n}','payload_length':n})
 for n in [0,1,8463359,8463360,8463361]:r.append({'name':f'funds_{n}','funds':n})
 for owner in [False,True]:
  for length in [0,8,1088,1200]:
   for lamports in [1,8463360]:r.append({'name':f'existing_{owner}_{length}_{lamports}','existing':{'length':length,'program_owner':owner,'lamports':lamports}})
 for initialized in [False,True]:r.append({'name':f'existing_valid_{initialized}','existing':{'length':1088,'program_owner':True,'disc':True,'initialized':initialized}})
 for k in ['wrong_global','wrong_system','unsigned']:r.append({'name':f'combined_{k}',k:True,'existing':{'length':1088,'program_owner':True,'disc':True,'initialized':True}})
 return r
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();output=PumpReport(a.output,R,a.candidate,__file__);rows=[]
 for c in cases():
  o=run(c);r={'case':c,'original':o}
  if a.candidate:
   b=run(c,a.candidate);diff=[k for k in ['error','accounts','events','inner','return_data'] if o[k]!=b[k]];r.update(candidate=b,different_fields=diff,match=not diff)
  rows.append(r)
 d={'scope':'Offline Pump initialize only, ordinary verified test-owned signatures. Full binary identity false.','case_count':len(rows),'original_sha256':hashlib.sha256(pin_program(ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'mismatches':[i for i,r in enumerate(rows) if r.get('match') is False]};output.write((json.dumps(d,indent=2)+'\n').encode("utf-8"));print([(r['case']['name'],r['original']['error'],r.get('different_fields')) for r in rows]);assert not d['mismatches']
