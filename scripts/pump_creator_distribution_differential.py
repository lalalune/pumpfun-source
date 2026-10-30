#!/usr/bin/env python3
"""Direct normally signed Pump distribution after captured original sharing bootstrap."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,hashlib,base64,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import fees_sharing_update_differential as fixtures
from fees_sharing_update_differential import *
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
PIDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
class Ready(Exception):pass
class Capture:
 def __init__(self,vm):self.vm=vm;self.keys=set()
 def __getattr__(self,n):return getattr(self.vm,n)
 def set_account(self,k,a):self.keys.add(k);return self.vm.set_account(k,a)
 def send_transaction(self,tx):
  for ix in tx.message.instructions:
   if tx.message.account_keys[ix.program_id_index]==PROGRAM and bytes(ix.data)[:8] in [bytes(x['discriminator']) for x in IDL['instructions'] if x['name'].startswith('update_fee_shares')]:raise Ready()
  return self.vm.send_transaction(tx)
def run(c,binary=None):
 original_type=fixtures.f.LiteSVM;vms=[]
 def factory():
  vm=Capture(original_type());vms.append(vm);return vm
 fixtures.f.LiteSVM=factory
 setup={k:v for k,v in c.items() if k not in ['op','name','wrong','unsigned','readonly','account_count']};setup['op']='update_fee_shares_v2'
 try:
  try:fixtures.run(setup)
  except Ready:pass
 finally:fixtures.f.LiteSVM=original_type
 vm=vms[0]
 for target,mutation in c.get('direct_mutations',{}).items():
  key={'auth':AUTH.pubkey(),'other':OTHER.pubkey(),'curve':CURVE,'vault':PV}[target];a=vm.get_account(key);data=bytearray(a.data if a else b'')
  for offset,value in mutation.get('patches',[]):data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  if 'length' in mutation:data=data[:mutation['length']]
  if 'data_hex' in mutation:data=bytearray.fromhex(mutation['data_hex'])
  vm.set_account(key,Account(mutation.get('lamports',a.lamports if a else 0),bytes(data),Pubkey.from_string(mutation.get('owner',str(a.owner if a else Pubkey.default()))),mutation.get('executable',False)))
 if binary:vm.add_program_from_file(PUMP,pin_program(binary))
 token=TOKEN22 if c.get('token22') else TOKEN;quote=Pubkey.from_string(c.get('quote',str(QUOTE)));pa=Pubkey.find_program_address([bytes(PV),bytes(token),bytes(quote)],ATA)[0]
 bootstrap_transactions=[];alternative_ata=None
 if c.get('alternative_ata_wallet'):
  wallet=Pubkey.from_string(c['alternative_ata_wallet']);alternative_ata=Pubkey.find_program_address([bytes(wallet),bytes(token),bytes(quote)],ATA)[0]
  create=Instruction(ATA,bytes([0]),[AccountMeta(PAYER.pubkey(),True,True),AccountMeta(alternative_ata,False,True),AccountMeta(wallet,False,False),AccountMeta(quote,False,False),AccountMeta(Pubkey.default(),False,False),AccountMeta(token,False,False)])
  bootstrap_tx=Transaction.new_signed_with_payer([create],PAYER.pubkey(),[PAYER],vm.latest_blockhash());assert all(bootstrap_tx.verify_with_results())
  created=vm.vm.send_transaction(bootstrap_tx);assert not isinstance(created,FailedTransactionMetadata),str(created)
  vm.keys.add(alternative_ata);account=vm.get_account(alternative_ata)
  assert account.owner==token and account.data[:32]==bytes(quote) and account.data[32:64]==bytes(wallet)
  assert int.from_bytes(account.data[64:72],'little')==0
  bootstrap_transactions.append({'transaction_base64':base64.b64encode(bytes(bootstrap_tx)).decode(),'signature_verified':True,'logs':created.logs(),'created_ata':str(alternative_ata),'wallet':str(wallet)})
 ix=next(x for x in PIDL['instructions'] if x['name']==c.get('op','distribute_creator_fees'))
 names={'payer':AUTH.pubkey(),'mint':MINT,'bonding_curve':CURVE,'sharing_config':SHARING,'creator_vault':PV,'system_program':Pubkey.default(),'event_authority':pump.EVENT,'program':PUMP,'creator_vault_quote_token_account':pa,'quote_mint':quote,'quote_token_program':token,'associated_token_program':ATA}
 if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([77])*32)
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for a in ix['accounts']]
 old=holders(c.get('old_shareholders',[(str(AUTH.pubkey()),10000)]));remaining=c.get('remaining',[(str(k),True) for k,bps in old]);ata_metas=[]
 for key,write in remaining:
  key=Pubkey.from_string(key);metas.append(AccountMeta(key,False,write))
  if c.get('remaining_atas'):
   ata=Pubkey.find_program_address([bytes(key),bytes(token),bytes(quote)],ATA)[0];m=AccountMeta(ata,False,c.get('ata_writable',True))
   if c.get('grouped_remaining'):ata_metas.append(m)
   else:metas.append(m)
 metas+=ata_metas
 if alternative_ata is not None:metas[-1]=AccountMeta(alternative_ata,False,True)
 metas=metas[:c.get('account_count',len(metas))]
 payload=bytes(ix['discriminator'])+(bytes([c.get('initialize_ata',1)]) if ix['name'].endswith('_v2') else b'')
 signers=[PAYER]+([AUTH] if any(m.pubkey==AUTH.pubkey() and m.is_signer for m in metas) else [])
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,payload,metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for key in vm.keys|set(names.values()):
   a=vm.get_account(key)
   if a and a.executable:continue
   out[str(key)]=None if a is None else {'lamports':a.lamports,'data':a.data.hex(),'owner':str(a.owner)}
  return out
 before=snap();r=vm.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;raw=json.loads(m.to_json())
 return {'error':str(r.err()) if failed else None,'before':before,'after':snap(),'events':[l for l in m.logs() if l.startswith('Program data:')],'logs':m.logs(),'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'bootstrap_transactions':bootstrap_transactions}
def cases():
 out=[];auth=str(AUTH.pubkey());other=str(OTHER.pubkey());third=str(Pubkey.from_bytes(bytes([91])*32))
 for op in ['distribute_creator_fees','distribute_creator_fees_v2']:
  rows=[{'name':'base'},{'name':'empty-old','old_shareholders':[]},{'name':'duplicate-old','old_shareholders':[(auth,5000),(auth,5000)],'pump_sol':1000000},{'name':'zero-share','old_shareholders':[(auth,0)],'pump_sol':1000000},{'name':'low-total','old_shareholders':[(auth,9999)],'pump_sol':1000000},{'name':'high-total','old_shareholders':[(auth,10001)],'pump_sol':1000000},{'name':'two-rounding','old_shareholders':[(auth,3333),(other,6667)],'pump_sol':1000001},{'name':'sum-overflow','old_shareholders':[(auth,65535),(other,65535)],'pump_sol':1000000},{'name':'no-remaining','remaining':[]},{'name':'wrong-remaining','remaining':[(other,True)]},{'name':'readonly-holder','old_shareholders':[(other,10000)],'remaining':[(other,False)],'pump_sol':1000000},{'name':'revoked','revoked':True},{'name':'unsigned','unsigned':True}]
  rows += [{'name':'balance-'+str(n),'pump_sol':n} for n in [-890880,-1,0,1,9999,10000,1000000,10**12]]
  rows += [{'name':'version-'+str(n),'version':n} for n in [0,1,2,255]]+[{'name':'status-'+str(n),'status':n} for n in [0,1,2,255]]
  rows += [{'name':'sharing-patch-'+str(n),'sharing_patches':[(n,'00')]} for n in [0,8,11,43]]
  rows += [{'name':'sharing-length-'+str(n),'sharing_length':n} for n in [0,7,8,75,76,80,113,114,400]]
  rows += [{'name':'curve-length-'+str(n),'account_mutations':{'bonding_curve':{'length':n}}} for n in [0,7,8,49,81,82,83,114,115,166]]
  rows += [{'name':'sharing-owner','sharing_owner':str(PUMP)},{'name':'vault-owner','account_mutations':{'pump_creator_vault':{'owner':str(PROGRAM)}}},{'name':'curve-creator-other','curve_patches':[(49,bytes(OTHER.pubkey()).hex())]}]
  for balance in [0,1,890879,890880]:
   for amount in [0,1,890879,890880,890881,1781759,1781760,1781761]:
    rows.append({'name':'recipient-floor-'+str(balance)+'-'+str(amount),'pump_sol':amount,'old_shareholders':[(other,5000),(auth,5000)],'direct_mutations':{'other':{'lamports':balance}}})
  rows += [{'name':'recipient-executable','pump_sol':1000000,'old_shareholders':[(str(PUMP),10000)]},{'name':'recipient-owned-data','pump_sol':1000000,'old_shareholders':[(other,10000)],'direct_mutations':{'other':{'owner':str(PROGRAM),'data_hex':'00'*8}}},{'name':'curve-owner','direct_mutations':{'curve':{'owner':str(PROGRAM)}}},{'name':'curve-discriminator','direct_mutations':{'curve':{'patches':[(0,'00')]}}},{'name':'paused-no-remaining','status':0,'remaining':[]},{'name':'zero-share-no-remaining','old_shareholders':[(auth,0)],'remaining':[]},{'name':'zero-share-zero-balance','old_shareholders':[(auth,0)]},{'name':'creator-mismatch-paused','status':0,'curve_patches':[(49,bytes(OTHER.pubkey()).hex())]}]
  rows += [{'name':'partial-curve-'+str(n),'direct_mutations':{'curve':{'length':n}}} for n in [47,48,50,63,64,79,80,84,100,113]]
  rows += [{'name':'curve-bool-'+str(n),'direct_mutations':{'curve':{'patches':[(n,'02')]}}} for n in [48,81,82,123,124]]
  ix=next(x for x in PIDL['instructions'] if x['name']==op)
  rows += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in ix['accounts'] if not a.get('signer')]
  rows += [{'name':'readonly-'+a['name'],'readonly':a['name'],'old_shareholders':[(other,10000)]} for a in ix['accounts'] if a.get('writable')]
  rows += [{'name':'accounts-'+str(n),'account_count':n} for n in range(len(ix['accounts']))]
  if op.endswith('_v2'):
   stable={'quote':str(Pubkey.from_bytes(bytes([88])*32)),'curve_patches':[(83,(bytes([88])*32).hex())],'remaining_atas':True,'grouped_remaining':True}
   rows += [{'name':'stable-'+str(i),**stable,**c} for i,c in enumerate([{}, {'pump_tokens':1000000},{'pump_tokens':1000000,'token22':True},{'pump_tokens':1000001,'old_shareholders':[(auth,3333),(other,6667)]},{'pump_tokens':1000000,'initialize_ata':False},{'pump_tokens':1000000,'account_mutations':{'remaining_ata_0':{'missing':True}}},{'pump_tokens':1000000,'account_mutations':{'remaining_ata_0':{'missing':True}},'initialize_ata':False},{'pump_tokens':0,'account_mutations':{'remaining_ata_0':{'missing':True}}},{'remaining_atas':False},{'pump_tokens':1000000,'ata_writable':False},{'pump_tokens':1000000,'old_shareholders':[(other,10000)],'readonly':'payer','account_mutations':{'remaining_ata_0':{'missing':True}}}])]
   rows += [{'name':'stable-quote-mismatch','quote':str(Pubkey.from_bytes(bytes([88])*32)),'remaining_atas':True,'pump_tokens':1000000},{'name':'stable-zero-frozen',**stable,'account_mutations':{'pump_creator_vault_ata':{'patches':[(108,'02')]}}},{'name':'stable-zero-uninitialized',**stable,'account_mutations':{'pump_creator_vault_ata':{'patches':[(108,'00')]}}},{'name':'stable-missing-source-and-remaining',**stable,'remaining':[],'account_mutations':{'pump_creator_vault_ata':{'missing':True}}},{'name':'stable-missing-source-paused',**stable,'status':0,'account_mutations':{'pump_creator_vault_ata':{'missing':True}}},{'name':'stable-zero-recipient-uninitialized-no-init',**stable,'initialize_ata':False,'account_mutations':{'remaining_ata_0':{'missing':True}}}]
   rows += [{'name':f'valid-other-wallet-ata-token22-{token22}-balance-{amount}-initialize-{initialize}',**stable,'pump_tokens':amount,'token22':token22,'initialize_ata':initialize,'alternative_ata_wallet':other} for token22 in [False,True] for amount in [0,1000000] for initialize in [False,True]]
   for target in ['pump_creator_vault_ata','remaining_ata_0']:
    rows += [{'name':target+'-'+label,**stable,'pump_tokens':1000000,'account_mutations':{target:mutation}} for label,mutation in [('missing',{'missing':True}),('empty',{'length':0}),('owner',{'owner':str(PROGRAM)}),('mint',{'patches':[(0,bytes(32).hex())]}),('authority',{'patches':[(32,bytes(32).hex())]}),('frozen',{'patches':[(108,'02')]})]]
  out += [{**c,'op':op,'name':op+'-'+c['name']} for c in rows]
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Direct normally signed Pump distributions after original-program sharing creation; candidate Pump loaded only after bootstrap. Synthetic local accounts; no byte identity claim.','original_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad};publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
