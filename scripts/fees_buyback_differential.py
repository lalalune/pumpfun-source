#!/usr/bin/env python3
"""Original-only buyback probes: normal signatures and synthetic offline accounts."""
import sys,pathlib,json,hashlib,base64,argparse
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_admin_differential import *
from solders.clock import Clock
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112');MINT=Pubkey.from_bytes(bytes([61])*32)
TOKEN2022=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'

def run(c,image):
 token=TOKEN2022 if c.get('token2022') else TOKEN
 vm=LiteSVM().with_transaction_history(0);vm.add_program(PROGRAM,image);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for name,key in [('spl_token',TOKEN),('associated_token',ATA)]+([('spl_token_2022',TOKEN2022)] if c.get('token2022') else []):vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 for kp in [AUTH,OTHER,PAYER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 index=c.get('index',0);mint=WSOL if c.get('native',True) else MINT
 seeds=[b'buyback-vault',bytes([index])];vault,bump=Pubkey.find_program_address(seeds,PROGRAM)
 destination={'vault':vault,'authority':AUTH.pubkey(),'program':PROGRAM}.get(c.get('destination_alias'),OTHER.pubkey())
 ata=Pubkey.find_program_address([bytes(vault),bytes(token),bytes(mint)],ATA)[0];destata=Pubkey.find_program_address([bytes(destination),bytes(token),bytes(mint)],ATA)[0]
 for key in [vault,ata,destata,EVENT]:vm.set_account(key,Account(0,b'',Pubkey.default()))
 md=bytearray(82);md[44]=9;md[45]=1
 for offset,value in c.get('mint_patches',[]):md[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 vm.set_account(mint,Account(10**9,bytes(md),Pubkey.from_string(c.get('mint_owner',str(token)))))
 gd=bytearray(BASE);gd[41]=c.get('flags',0)
 for offset,value in c.get('global_patches',[]):gd[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 vm.set_account(GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PROGRAM)))))
 op=c.get('op','initialize_buyback');ix=next(x for x in IDL['instructions'] if x['name']==op)
 if op!='initialize_buyback' or c.get('existing'):
  data=hashlib.sha256(b'account:BuybackVault').digest()[:8]+bytes(AUTH.pubkey())+c.get('total',0).to_bytes(8,'little')+bytes(16)+c.get('last',0).to_bytes(8,'little',signed=True)+c.get('rate',60).to_bytes(8,'little',signed=True)+bytes(128)
  data=bytearray(data)
  for offset,value in c.get('patches',[]):data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  size=c.get('length',len(data));data=(data+bytes(max(0,size-len(data))))[:size]
  vm.set_account(vault,Account(vm.minimum_balance_for_rent_exemption(208)+c.get('amount',1000000),bytes(data),Pubkey.from_string(c.get('owner',str(PROGRAM)))))
 if op=='sweep_buyback':
  reserve=vm.minimum_balance_for_rent_exemption(165);td=bytearray(165);td[:32]=bytes(mint);td[32:64]=bytes(vault);td[64:72]=c.get('tokens',0).to_bytes(8,'little');td[108]=1
  if mint==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
  for offset,value in c.get('token_patches',[]):td[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  vm.set_account(ata,Account(reserve+(c.get('tokens',0) if mint==WSOL else 0),bytes(td),token))
  if not c.get('missing_destination_ata') and destata!=ata:
   td[32:64]=bytes(destination);td[64:72]=bytes(8);vm.set_account(destata,Account(reserve,bytes(td),token))
 names={'payer':AUTH.pubkey(),'authority':AUTH.pubkey(),'destination':destination,'fee_program_global':GLOBAL,'buyback_vault':vault,'buyback_vault_ata':ata,'destination_ata':destata,'mint':mint,'token_program':token,'associated_token_program':ATA,'system_program':Pubkey.default(),'event_authority':EVENT,'program':PROGRAM}
 if c.get('wrong_authority'):names['authority']=OTHER.pubkey()
 if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([77])*32)
 metas=[AccountMeta(names[x['name']],x.get('signer',False) and not c.get('unsigned'),x.get('writable',False) and c.get('readonly')!=x['name']) for x in ix['accounts']]
 metas=metas[:c.get('account_count',len(metas))]
 payload=bytes(ix['discriminator'])+bytes([index])
 if op=='update_buyback_authority':payload+=bytes(OTHER.pubkey())
 if op=='update_buyback_claim_rate_limit':payload+=c.get('new_rate',77).to_bytes(8,'little',signed=True)
 signers=[PAYER]+[kp for kp in [AUTH,OTHER] if any(m.is_signer and m.pubkey==kp.pubkey() for m in metas)]
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for name,key in names.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   out[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r
 return {'case':c,'vault':str(vault),'bump':bump,'error':str(r.err()) if failed else None,'logs':m.logs(),'before':before,'after':snap(),'inner':json.loads(m.to_json())['inner_instructions'],'return':json.loads(m.to_json()).get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode()}

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,default=ROOT/'work/fees-buyback-recovery/probes.json');a=p.parse_args()
 cases=[{'name':'init-'+str(n),'index':n} for n in [0,1,2,3,4,5,6,7,8,9,255]]
 cases += [{'name':'init-nonnative','native':False},{'name':'init-existing','existing':True}]
 for op in ['update_buyback_authority','update_buyback_claim_rate_limit','sweep_buyback']:
  cases += [{'name':op,'op':op},{'name':op+'-wrongauth','op':op,'wrong_authority':True}]
 cases += [{'name':'rate-'+str(n),'op':'update_buyback_claim_rate_limit','new_rate':n} for n in [-1,0,1,2**63-1,-2**63]]
 cases += [{'name':'sweep-'+str(i),'op':'sweep_buyback',**c} for i,c in enumerate([{'amount':0},{'amount':1000000,'tokens':1000000},{'native':False,'tokens':1000000},{'native':False,'amount':0,'tokens':1000000},{'last':1700000000},{'last':1700000001},{'rate':-1,'last':1700000000},{'rate':0,'last':1700000000},{'index':8},{'total':2**64-1}])]
 for op in ['initialize_buyback','update_buyback_authority','update_buyback_claim_rate_limit','sweep_buyback']:
  ix=next(x for x in IDL['instructions'] if x['name']==op)
  cases += [{'name':op+'-index-'+str(n),'op':op,'index':n} for n in range(256)]
  cases += [{'name':op+'-wrong-'+a['name'],'op':op,'wrong':a['name']} for a in ix['accounts'] if not a.get('signer')]
  cases += [{'name':op+'-readonly-'+a['name'],'op':op,'readonly':a['name']} for a in ix['accounts'] if a.get('writable')]
  cases += [{'name':op+'-accounts-'+str(n),'op':op,'account_count':n} for n in range(len(ix['accounts']))]
  cases += [{'name':op+'-unsigned','op':op,'unsigned':True}]
  if op!='initialize_buyback':
   cases += [{'name':op+'-length-'+str(n),'op':op,'length':n} for n in [0,7,8,39,40,72,80,207,208,209,300]]
   cases += [{'name':op+'-patch-'+str(n),'op':op,'patches':[(n,'00')]} for n in [0,8]]
   cases += [{'name':op+'-owner','op':op,'owner':str(Pubkey.default())}]
  if op.startswith('update_'):
   cases += [{'name':op+'-global-'+str(n),'op':op,'global_patches':[(n,'00')]} for n in [0,8,9]]
   cases += [{'name':op+'-globalowner','op':op,'global_owner':str(Pubkey.default())}]
 cases += [{'name':'sweep-time-'+str(last)+'-'+str(rate),'op':'sweep_buyback','last':last,'rate':rate} for last in [0,1699999939,1699999940,1699999941,1700000000,1700000001,-1,2**63-1,-2**63] for rate in [0,60,-1,2**63-1,-2**63]]
 cases += [{'name':'sweep-overflow-'+str(offset)+'-'+str(native),'op':'sweep_buyback','tokens':1,'native':native,'patches':[(offset,(2**64-1).to_bytes(8,'little').hex())]} for offset in [40,48,56] for native in [True,False]]
 for op in ['initialize_buyback','sweep_buyback']:
  cases += [{'name':op+'-token2022','op':op,'native':False,'token2022':True,'tokens':1000000}]
  cases += [{'name':op+'-mint-owner','op':op,'mint_owner':str(PROGRAM)}]
  cases += [{'name':op+'-mint-patch-'+str(n),'op':op,'mint_patches':[(n,'00')]} for n in [44,45]]
 cases += [{'name':'sweep-token-patch-'+str(n),'op':'sweep_buyback','tokens':1000000,'token_patches':[(n,'00')]} for n in [0,32,108]]
 cases += [{'name':'sweep-alias-'+alias,'op':'sweep_buyback','destination_alias':alias,'tokens':1000000} for alias in ['vault','authority','program']]
 cases += [{'name':'sweep-below-rent','op':'sweep_buyback','amount':-1},{'name':'sweep-missing-destination-ata','op':'sweep_buyback','missing_destination_ata':True}]
 rows=[];bad=[]
 # Read each image once, so every case and the receipt use the same bytes.
 original=ORIGINAL.read_bytes();candidate=a.candidate.read_bytes() if a.candidate else None
 for c in cases:
  x=run(c,original);y=run(c,candidate) if a.candidate else None
  match=all(x[k]==y[k] for k in ['error','before','after','inner','return']) and [l for l in x['logs'] if l.startswith('Program data:')]==[l for l in y['logs'] if l.startswith('Program data:')] if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps({'scope':'Normal signed synthetic buyback fixtures; no full-byte identity claim.','original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad},indent=2)+'\n')
 print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
