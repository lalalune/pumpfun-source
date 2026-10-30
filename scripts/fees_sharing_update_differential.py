#!/usr/bin/env python3
"""Signed local sharing-update cases; original bootstrap precedes candidate load."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import fees_sharing_create_differential as f
from fees_sharing_create_differential import *
from pump_amm_reusable_harness import pin_program
from solders.clock import Clock
from solders.system_program import transfer,TransferParams
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
PV=Pubkey.find_program_address([b'creator-vault',bytes(SHARING)],PUMP)[0];AV=Pubkey.find_program_address([b'creator_vault',bytes(SHARING)],AMM)[0]
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'
def holders(values):return [(Pubkey.from_string(key),bps) for key,bps in values]
def run(c,binary=None):
 orig=f.LiteSVM;vms=[]
 def factory():
  vm=orig();vm.set_clock(Clock(1000,0,0,0,1700000000));vms.append(vm);return vm
 f.LiteSVM=factory
 try:created=f.run(c.get('bootstrap',{}))
 finally:f.LiteSVM=orig
 assert created['error'] is None,created['error'];vm=vms[0]
 if binary:vm.add_program_from_file(PROGRAM,pin_program(binary))
 for key,patches in [(pump.GLOBAL,c.get('global_patches',[])),(CURVE,c.get('curve_patches',[]))]:
  a=vm.get_account(key);data=bytearray(a.data)
  for offset,value in patches:data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  vm.set_account(key,Account(a.lamports,bytes(data),a.owner))
 token=TOKEN22 if c.get('token22') else TOKEN;quote=Pubkey.from_string(c.get('quote',str(QUOTE)))
 for name,key in [('spl_token',TOKEN),('associated_token',ATA)]+([('spl_token_2022',TOKEN22)] if c.get('token22') else []):vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 pa=Pubkey.find_program_address([bytes(PV),bytes(token),bytes(quote)],ATA)[0];aa=Pubkey.find_program_address([bytes(AV),bytes(token),bytes(quote)],ATA)[0]
 md=bytearray(82);md[44]=9 if quote==QUOTE else 6;md[45]=1;vm.set_account(quote,Account(10**9,bytes(md),token))
 for key,amount in [(PV,c.get('pump_sol',0)),(AV,c.get('amm_sol',0))]:vm.set_account(key,Account(vm.minimum_balance_for_rent_exemption(0)+amount,b'',Pubkey.default()))
 def token_account(key,owner,amount):
  reserve=vm.minimum_balance_for_rent_exemption(165);td=bytearray(165);td[:32]=bytes(quote);td[32:64]=bytes(owner);td[64:72]=amount.to_bytes(8,'little');td[108]=1
  if quote==QUOTE:td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
  vm.set_account(key,Account(reserve+(amount if quote==QUOTE else 0),bytes(td),token))
 for key,owner,amount in [(pa,PV,c.get('pump_tokens',0)),(aa,AV,c.get('amm_tokens',0))]:token_account(key,owner,amount)
 old=holders(c.get('old_shareholders',[(str(AUTH.pubkey()),10000)]));sd=bytearray(vm.get_account(SHARING).data)
 if 'old_shareholders' in c:
  tail=len(old).to_bytes(4,'little')+b''.join(bytes(k)+bps.to_bytes(2,'little') for k,bps in old);sd[76:76+len(tail)]=tail
 for offset,value in c.get('sharing_patches',[]):sd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 if 'status' in c:sd[10]=c['status']
 if 'version' in c:sd[9]=c['version']
 if c.get('revoked'):sd[75]=1
 sd=sd[:c.get('sharing_length',len(sd))];a=vm.get_account(SHARING);vm.set_account(SHARING,Account(a.lamports+c.get('sharing_sol',0),bytes(sd),Pubkey.from_string(c.get('sharing_owner',str(PROGRAM)))))
 names={'event_authority':EVENT,'program':PROGRAM,'authority':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'sharing_config':SHARING,'bonding_curve':CURVE,'pump_creator_vault':PV,'pump_creator_vault_ata':pa,'system_program':Pubkey.default(),'pump_program':PUMP,'pump_event_authority':pump.EVENT,'pump_amm_program':AMM,'amm_event_authority':Pubkey.find_program_address([b'__event_authority'],AMM)[0],'wsol_mint':quote,'quote_mint':quote,'token_program':token,'associated_token_program':ATA,'coin_creator_vault_authority':AV,'coin_creator_vault_ata':aa}
 if c.get('wrong_authority'):names['authority']=OTHER.pubkey()
 if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([77])*32)
 ix=next(x for x in IDL['instructions'] if x['name']==c.get('op','update_fee_shares'))
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for a in ix['accounts']]
 remaining=c.get('remaining',[(str(key),True) for key,bps in old])
 extras={};ata_metas=[]
 for i,(key,write) in enumerate(remaining):
  key=Pubkey.from_string(key)
  if vm.get_account(key) is None:vm.set_account(key,Account(10**9,b'',Pubkey.default()))
  extras['remaining_'+str(i)]=key;metas.append(AccountMeta(key,False,write))
  if c.get('remaining_atas'):
   holder_ata=Pubkey.find_program_address([bytes(key),bytes(token),bytes(quote)],ATA)[0];token_account(holder_ata,key,0)
   if c.get('grouped_remaining'):ata_metas.append(AccountMeta(holder_ata,False,True))
   else:metas.append(AccountMeta(holder_ata,False,True))
   extras['remaining_ata_'+str(i)]=holder_ata
 metas.extend(ata_metas)
 for name,mutation in c.get('account_mutations',{}).items():
  key={**names,**extras}[name];account=vm.get_account(key)
  if mutation.get('missing'):vm.set_account(key,Account(0,b'',Pubkey.default()));continue
  assert account is not None
  data=bytearray(account.data)
  for offset,value in mutation.get('patches',[]):data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  if 'length' in mutation:data=data[:mutation['length']]
  vm.set_account(key,Account(mutation.get('lamports',account.lamports),bytes(data),Pubkey.from_string(mutation.get('owner',str(account.owner)))))
 metas=metas[:c.get('account_count',len(metas))]
 new=holders(c.get('shareholders',[(str(OTHER.pubkey()),10000)]));payload=bytes(ix['discriminator'])+len(new).to_bytes(4,'little')+b''.join(bytes(key)+bps.to_bytes(2,'little') for key,bps in new)
 signers=[PAYER]+[kp for kp in [AUTH,OTHER] if any(m.is_signer and m.pubkey==kp.pubkey() for m in metas)]
 instructions=[set_compute_unit_limit(1400000)]
 if c.get('fund_pump_transfer'):instructions.append(transfer(TransferParams(from_pubkey=PAYER.pubkey(),to_pubkey=PV,lamports=c['fund_pump_transfer'])))
 instructions.append(Instruction(PROGRAM,payload,metas))
 tx=Transaction.new_signed_with_payer(instructions,PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for name,key in {**names,**extras,'transaction_payer':PAYER.pubkey()}.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   out[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;raw=json.loads(m.to_json())
 return {'error':str(r.err()) if failed else None,'logs':m.logs(),'before':before,'after':snap(),'inner':raw['inner_instructions'],'return':raw.get('return_data'),'events':[l for l in m.logs() if l.startswith('Program data:')],'transaction_base64':base64.b64encode(bytes(tx)).decode(),'bootstrap_transaction_base64':created['transaction_base64']}
def cases():
 out=[];auth=str(AUTH.pubkey());other=str(OTHER.pubkey())
 for op in ['update_fee_shares','update_fee_shares_v2']:
  rows=[{'name':'base'},{'name':'no-remaining','remaining':[]},{'name':'wrong-remaining','remaining':[(other,True)]},{'name':'readonly-remaining','remaining':[(auth,False)]},{'name':'extra-remaining','remaining':[(auth,True),(other,True)]},{'name':'empty-new','shareholders':[]},{'name':'zero-share','shareholders':[(other,0)]},{'name':'sum-low','shareholders':[(other,9999)]},{'name':'sum-high','shareholders':[(other,10001)]},{'name':'duplicate','shareholders':[(other,5000),(other,5000)]},{'name':'two-valid','shareholders':[(auth,5000),(other,5000)]},{'name':'same-shareholders','shareholders':[(auth,10000)]},{'name':'zero-key','shareholders':[(str(Pubkey.default()),10000)]},{'name':'revoked','revoked':True},{'name':'wrong-authority','wrong_authority':True},{'name':'unsigned','unsigned':True}]
  rows += [{'name':'new-count-'+str(n),'shareholders':[(str(Pubkey.from_bytes(bytes([90+i])*32)),10000-n+1 if i==0 else 1) for i in range(n)]} for n in [8,10,11,16,20,21,22,25,30]]
  rows += [{'name':'status-'+str(n),'status':n} for n in [0,1,2,255]]+ [{'name':'version-'+str(n),'version':n} for n in [0,1,2,255]]
  rows += [{'name':'sharing-patch-'+str(n),'sharing_patches':[(n,'00')]} for n in [0,8,11,43,75]]
  rows += [{'name':'sharing-length-'+str(n),'sharing_length':n} for n in [0,7,8,75,76,80,113,114,400]]
  rows += [{'name':'sharing-owner','sharing_owner':str(PUMP)}]
  rows += [{'name':'pump-sol-'+str(n),'pump_sol':n} for n in [1,1000000]]+[{'name':'amm-token-'+str(n),'amm_tokens':n} for n in [1,1000000]]
  rows += [{'name':'pump-tokens','pump_tokens':1000000},{'name':'amm-sol','amm_sol':1000000},{'name':'sharing-sol','sharing_sol':1000000},{'name':'both-balances','pump_sol':1000000,'amm_tokens':1000000}]
  rows += [{'name':'old-two','old_shareholders':[(auth,3333),(other,6667)],'pump_sol':1000001},{'name':'old-two-reversed','old_shareholders':[(auth,3333),(other,6667)],'remaining':[(other,True),(auth,True)],'pump_sol':1000001},{'name':'old-two-missing','old_shareholders':[(auth,3333),(other,6667)],'remaining':[(auth,True)]}]
  rows += [{'name':'admin-other-signed','sharing_patches':[(43,bytes(OTHER.pubkey()).hex())],'wrong_authority':True},{'name':'global-authority-zero','global_patches':[(9,bytes(32).hex())]},{'name':'readonly-authority-unmasked','old_shareholders':[(other,10000)],'readonly':'authority'},{'name':'paused-and-revoked','status':0,'revoked':True},{'name':'paused-and-empty','status':0,'shareholders':[]},{'name':'wrongauth-and-revoked','wrong_authority':True,'revoked':True},{'name':'wrongremaining-and-empty','remaining':[(other,True)],'shareholders':[]},{'name':'duplicate-and-zero','shareholders':[(other,0),(other,10000)]}]
  rows += [{'name':'readonly-oldholder-funded','old_shareholders':[(other,10000)],'remaining':[(other,False)],'pump_sol':1000000},{'name':'token22-mint-program','token22':True},{'name':'non-native-unmatched','quote':str(Pubkey.from_bytes(bytes([88])*32))},{'name':'new-limit-and-zero','shareholders':[(other,0)]*11}]
  rows += [{'name':'graduated-'+str(i),'bootstrap':{'tokens':0,'pool':True},**d} for i,d in enumerate([{}, {'amm_tokens':1000000},{'amm_sol':1000000},{'pump_sol':1000000,'amm_tokens':1000000}])]
  rows += [{'name':'new-sum-overflow-'+str(i),'shareholders':shares} for i,shares in enumerate([[(auth,65535),(other,1)],[(auth,65535),(other,65535)]])]
  rows += [{'name':'duplicate-overflow','shareholders':[(auth,65535),(auth,65535)]},{'name':'overflow-before-zero','shareholders':[(auth,65535),(other,1),(str(Pubkey.from_bytes(bytes([90])*32)),0)]},{'name':'zero-before-overflow','shareholders':[(auth,0),(other,65535),(str(Pubkey.from_bytes(bytes([90])*32)),1)]}]
  rows += [{'name':'fund-then-update','fund_pump_transfer':1000000},{'name':'fund-then-invalid-new','fund_pump_transfer':1000000,'shareholders':[]},{'name':'readonly-funded-and-invalid-new','old_shareholders':[(other,10000)],'remaining':[(other,False)],'pump_sol':1000000,'shareholders':[]}]
  for graduated in [False,True]:
   branch={'bootstrap':{'tokens':0,'pool':True}} if graduated else {}
   for name in ['pump_creator_vault_ata','coin_creator_vault_ata']:
    if op=='update_fee_shares' and name=='pump_creator_vault_ata':continue
    for label,mutation in [('missing',{'missing':True}),('short',{'length':100}),('owner',{'owner':str(PROGRAM)}),('mint',{'patches':[(0,bytes(32).hex())]}),('authority',{'patches':[(32,bytes(32).hex())]}),('frozen',{'patches':[(108,'02')]})]:
     rows.append({'name':name+'-'+label+'-grad-'+str(graduated),**branch,'pump_sol':1000000,'amm_tokens':1000000,'account_mutations':{name:mutation}})
  rows += [{'name':'curve-length-'+str(n),'account_mutations':{'bonding_curve':{'length':n}}} for n in [0,7,8,49,81,82,83,114,115,124,166]]
  ix=next(x for x in IDL['instructions'] if x['name']==op)
  rows += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in ix['accounts'] if not a.get('signer')]
  rows += [{'name':'readonly-'+a['name'],'readonly':a['name']} for a in ix['accounts'] if a.get('writable')]
  rows += [{'name':'account-count-'+str(n),'account_count':n} for n in range(len(ix['accounts']))]
  rows += [{'name':'invalid-combination','revoked':True,'status':0,'shareholders':[],'remaining':[]},{'name':'invalid-new-and-remaining','shareholders':[],'remaining':[]}]
  if op.endswith('_v2'):
   rows += [{'name':'matching-quote-'+str(i),'quote':str(Pubkey.from_bytes(bytes([88])*32)),'curve_patches':[(83,bytes([88]*32).hex())],**d} for i,d in enumerate([{}, {'remaining_atas':True},{'remaining_atas':True,'pump_tokens':1000000},{'remaining_atas':True,'token22':True,'pump_tokens':1000000}])]
   stable={'quote':str(Pubkey.from_bytes(bytes([88])*32)),'curve_patches':[(83,bytes([88]*32).hex())],'remaining_atas':True}
   for label,mutation in [('missing',{'missing':True}),('owner',{'owner':str(PROGRAM)}),('mint',{'patches':[(0,bytes(32).hex())]}),('authority',{'patches':[(32,bytes(32).hex())]}),('frozen',{'patches':[(108,'02')]}),('short',{'length':100})]:
    rows.append({'name':'stable-recipient-'+label,**stable,'pump_tokens':1000000,'account_mutations':{'remaining_ata_0':mutation}})
   rows += [{'name':'stable-recipient-missing-zero',**stable,'account_mutations':{'remaining_ata_0':{'missing':True}}},{'name':'stable-recipient-missing-readonly-authority',**stable,'old_shareholders':[(other,10000)],'readonly':'authority','pump_tokens':1000000,'account_mutations':{'remaining_ata_0':{'missing':True}}},{'name':'stable-old-two',**stable,'old_shareholders':[(auth,3333),(other,6667)],'pump_tokens':1000001},{'name':'stable-old-two-missing-second',**stable,'old_shareholders':[(auth,3333),(other,6667)],'remaining':[(auth,True)],'pump_tokens':1000001},{'name':'stable-old-two-reversed',**stable,'old_shareholders':[(auth,3333),(other,6667)],'remaining':[(other,True),(auth,True)],'pump_tokens':1000001}]
   rows += [{'name':'stable-old-two-grouped',**stable,'grouped_remaining':True,'old_shareholders':[(auth,3333),(other,6667)],'pump_tokens':1000001},{'name':'stable-old-two-grouped-missing-atas',**stable,'grouped_remaining':True,'old_shareholders':[(auth,3333),(other,6667)],'pump_tokens':1000001,'account_mutations':{'remaining_ata_0':{'missing':True},'remaining_ata_1':{'missing':True}}}]
   rows += [{'name':'graduated-stable-'+str(i),**stable,'bootstrap':{'tokens':0,'pool':True},**d} for i,d in enumerate([{}, {'amm_tokens':1000000},{'pump_tokens':1000000,'amm_tokens':1000000},{'token22':True,'pump_tokens':1000000,'amm_tokens':1000000}])]
   rows += [{'name':'token22-native','token22':True},{'name':'non-native','quote':str(Pubkey.from_bytes(bytes([88])*32))},{'name':'non-native-with-atas','quote':str(Pubkey.from_bytes(bytes([88])*32)),'remaining_atas':True},{'name':'non-native-tokens','quote':str(Pubkey.from_bytes(bytes([88])*32)),'remaining_atas':True,'pump_tokens':1000000,'amm_tokens':1000000}]
  out += [{**c,'name':op+'-'+c['name'],'op':op} for c in rows]
 # Edge matrix: version1 precedence and graduated AMM account presence.
 for op in ['update_fee_shares','update_fee_shares_v2']:
  for count,old in [(1,[(auth,10000)]),(2,[(auth,5000),(other,5000)])]:
   for label,extra in [('plain',{}),('wrong-authority',{'wrong_authority':True}),('revoked',{'revoked':True}),('paused',{'status':0}),('all-three',{'wrong_authority':True,'revoked':True,'status':0}),('bad-status',{'status':2}),('empty-new',{'shareholders':[]})]:
    out.append({'name':f'{op}-edge-version1-old{count}-{label}','op':op,'version':1,'old_shareholders':old,**extra})
  for graduated in [False,True]:
   for lamports in [0,1,2039280,10000000]:
    for owner in [str(Pubkey.default()),str(TOKEN),str(PROGRAM)]:
     out.append({'name':f'{op}-edge-empty-amm-grad{graduated}-lamports{lamports}-owner{owner}','op':op,'bootstrap':{'tokens':0,'pool':True} if graduated else {},'pump_sol':1000000,'account_mutations':{'coin_creator_vault_ata':{'length':0,'lamports':lamports,'owner':owner}}})
  for length in [1,100,165]:
   out.append({'name':f'{op}-edge-graduated-system-data{length}','op':op,'bootstrap':{'tokens':0,'pool':True},'pump_sol':1000000,'account_mutations':{'coin_creator_vault_ata':{'length':length,'lamports':10000000,'owner':str(Pubkey.default())}}})
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Normally signed synthetic sharing updates; captured original bootstraps creation before candidate replacement. No complete-source or byte identity claim.','original_sha256':hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
