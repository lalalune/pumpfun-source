#!/usr/bin/env python3
"""Captured Pump incentive administration against synthetic normally signed state."""
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
ROOT=Path(__file__).resolve().parents[1];IDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));PROGRAM=Pubkey.from_string(IDL['address']);ORIGINAL=ROOT/'evidence/original/pump/deployed.so';AUTH=Keypair.from_seed(bytes([222])*32);PAYER=Keypair.from_seed(bytes([223])*32);OTHER=Keypair.from_seed(bytes([224])*32);MINT=Pubkey.from_bytes(bytes([225])*32);EVENT=Pubkey.find_program_address([b'__event_authority'],PROGRAM)[0];G=Pubkey.find_program_address([b'global_volume_accumulator'],PROGRAM)[0];GLOBAL=Pubkey.find_program_address([b'global'],PROGRAM)[0]
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');IX=next(x for x in IDL['instructions'] if x['name']=='admin_update_token_incentives');DISC={x['name']:bytes(x['discriminator']) for x in IDL['accounts']};CAPTURE=next(x for x in json.loads((ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump')
def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(PROGRAM,pin_program(binary));vm.set_clock(Clock(100,c.get('now',10),0,0,c.get('now',10)));vm.airdrop(PAYER.pubkey(),10**12);vm.airdrop(AUTH.pubkey(),10**12);vm.airdrop(OTHER.pubkey(),10**12)
 token=TOKEN22 if c.get('token22') else TOKEN;mint=Pubkey.from_string(c.get('mint',str(MINT)));ita=Pubkey.find_program_address([bytes(G),bytes(token),bytes(mint)],ATA)[0]
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 gl=bytearray(base64.b64decode(CAPTURE['data_base64']));gl[9:41]=bytes(AUTH.pubkey());vm.set_account(GLOBAL,Account(10**9,bytes(gl),PROGRAM))
 md=bytearray(82);md[44]=6;md[45]=1;vm.set_account(mint,Account(10**9,bytes(md),token))
 if c.get('existing',True):
  gd=DISC['GlobalVolumeAccumulator']+struct.pack('<qqq',c.get('old_start',0),c.get('old_end',0),c.get('old_day',0))+bytes.fromhex(c.get('old_mint',bytes(mint).hex()))+b''.join(struct.pack('<Q',n) for n in c.get('supplies',[0]*30))+b''.join(struct.pack('<Q',n) for n in c.get('volumes',[0]*30));gd+=bytes(max(0,c.get('g_length',600)-len(gd)));vm.set_account(G,Account(c.get('g_lamports',10**8),gd[:c.get('g_length',600)],PROGRAM))
 else:vm.set_account(G,Account(c.get('prefund',0),b'',Pubkey.default()))
 if c.get('ata_existing',True):
  td=bytearray(165);td[:32]=bytes(mint);td[32:64]=bytes(G);td[64:72]=struct.pack('<Q',c.get('tokens',10**9));td[108]=1;vm.set_account(ita,Account(2039280,bytes(td),token))
 else:vm.set_account(ita,Account(0,b'',Pubkey.default()))
 names={'authority':OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey(),'global':GLOBAL,'global_volume_accumulator':G,'mint':mint,'global_incentive_token_account':ita,'associated_token_program':ATA,'system_program':Pubkey.default(),'token_program':token,'event_authority':EVENT,'program':PROGRAM}
 for name,mutation in c.get('mutations',{}).items():
  key=names[name];a=vm.get_account(key)
  if mutation.get('missing'):vm.set_account(key,Account(0,b'',Pubkey.default()));continue
  data=bytearray(a.data)
  for off,val in mutation.get('patches',[]):data[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  length=mutation.get('length',len(data));data=(data+bytes(max(0,length-len(data))))[:length];vm.set_account(key,Account(mutation.get('lamports',a.lamports),bytes(data),Pubkey.from_string(mutation.get('owner',str(a.owner))),a.executable))
 if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([226])*32)
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for a in IX['accounts']];metas=metas[:c.get('account_count',len(metas))]
 payload=bytes(IX['discriminator'])+struct.pack('<qqqQQ',c.get('start',20),c.get('end',49),c.get('day',1),c.get('index',0),c.get('supply',1000))+bytes.fromhex(c.get('trailing',''));payload=payload[:c.get('payload_length',len(payload))]
 signerkeys={m.pubkey for m in metas if m.is_signer}|{PAYER.pubkey()};signers=[kp for kp in [PAYER,AUTH,OTHER] if kp.pubkey() in signerkeys];tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for key in set(names.values())|{G,ita,PAYER.pubkey(),AUTH.pubkey(),OTHER.pubkey()}:
   a=vm.get_account(key)
   if a and a.executable:continue
   out[str(key)]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return {'before':before,'after':snap(),'error':str(r.err()) if fail else None,'logs':m.logs(),'events':[l for l in m.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 out=[{'name':'base'},{'name':'fresh','existing':False,'ata_existing':False},{'name':'g-fresh','existing':False},{'name':'ata-fresh','ata_existing':False},{'name':'token22','token22':True}]
 for field,values in [('start',[-1,0,9,10,11,20,30,49,50]),('end',[-1,0,9,10,11,19,20,21,48,49,50,51,100]),('day',[-1,0,1,2,10,86400]),('index',[0,1,28,29,30,31,2**64-1]),('supply',[0,1,10**9,2**64-1])]:out.extend({'name':f'{field}-{v}',field:v} for v in values)
 for old in [(0,0,0),(0,9,1),(0,10,1),(0,11,1),(5,29,1),(10,39,1),(11,40,1),(20,49,1)]:
  for args in [(0,0,0,0),(0,0,0,30),(0,0,1,0),(0,0,2,0),(0,0,1,29),(0,0,1,30),(0,50,1,0),(20,49,1,0),(20,49,1,30),(30,49,1,0),(30,59,1,30),(0,19,0,0),(0,10,0,0),(0,11,0,0)]:
   c=dict(zip(['old_start','old_end','old_day'],old));c.update(dict(zip(['start','end','day','index'],args)));out.append({'name':f'transition-{old}-{args}','supplies':list(range(30)),'volumes':list(range(100,130)),'supply':999,**c})
 for old in [(0,29,1),(0,29,2),(5,29,2),(20,49,1)]:
  for index in [0,1,2,3,4,5,9,10,11,14,15,24,25,29,30]:out.append({'name':f'active-{old}-{index}','old_start':old[0],'old_end':old[1],'old_day':old[2],'start':old[0],'end':old[1],'day':old[2],'index':index,'supply':999,'supplies':list(range(30)),'volumes':list(range(100,130))})
 for start,end,day in [(20,50,1),(20,48,1),(20,100,1),(20,10,1),(20,0,1),(0,100,1),(20,50,2),(20,50,0),(20,50,-1)]:out.append({'name':f'same-{start}-{end}-{day}','old_start':20,'old_end':49,'old_day':1,'start':start,'end':end,'day':day,'index':0,'supplies':list(range(30))})
 out += [{'name':'unsigned','unsigned':True},{'name':'wrong-authority','wrong_authority':True},{'name':'trailing','trailing':'ffff'},{'name':'ata-new-token22','ata_existing':False,'token22':True},{'name':'old-mint-other','old_mint':bytes(32).hex()}]
 for a in IX['accounts']:
  if not a.get('signer'):out.append({'name':'wrong-'+a['name'],'wrong':a['name']})
  if a.get('writable'):out.append({'name':'readonly-'+a['name'],'readonly':a['name']})
 for n in range(len(IX['accounts'])):out.append({'name':'accounts-'+str(n),'account_count':n})
 for n in [0,7,8,15,16,23,24,31,32,39,40,47]:out.append({'name':'payload-'+str(n),'payload_length':n})
 for name in ['global','global_volume_accumulator','mint','global_incentive_token_account']:
  for label,mut in [('owner',{'owner':str(OTHER.pubkey())}),('empty',{'length':0}),('missing',{'missing':True}),('disc',{'patches':[(0,'ff')]}),('zero-lamports',{'lamports':0})]:out.append({'name':name+'-'+label,'mutations':{name:mut}})
 for length in [7,8,31,32,63,64,543,544,599,600,601]:out.append({'name':'g-length-'+str(length),'g_length':length})
 for label,mut in [('authority',{'patches':[(32,bytes(32).hex())]}),('mint',{'patches':[(0,bytes(32).hex())]}),('frozen',{'patches':[(108,'02')]}),('uninitialized',{'patches':[(108,'00')]})]:out.append({'name':'ata-'+label,'mutations':{'global_incentive_token_account':mut}})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[];publisher=PumpReport(a.output,ROOT,a.candidate,__file__)
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;diff=[k for k in ['before','after','error','events','inner','return'] if y is not None and x[k]!=y[k]];rows.append({'case':c,'original':x,'candidate':y,'diff':diff})
  if diff:bad.append(c['name'])
 report={'scope':'Synthetic account state; verified normal signatures; independent candidate compilation required. No byte identity claim.','original_sha256':hashlib.sha256(pin_program(ORIGINAL).read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':rows,'mismatches':bad};publisher.write(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(len(rows),'cases',len(bad),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
