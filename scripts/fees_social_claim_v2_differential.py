#!/usr/bin/env python3
"""Original-only normal-signed local SocialFeePda v2 claim probes."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from fees_social_claim_differential import *
from pump_differential_output import PumpReport
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC=Pubkey.from_bytes(bytes([198,250,122,243,190,219,173,58,61,101,243,106,171,201,116,49,177,187,228,194,210,246,224,228,124,166,2,3,69,47,93,97]))
IX=next(x for x in IDL['instructions'] if x['name']=='claim_social_fee_pda_v2')
ORIGINAL=ROOT/'evidence/original/pump_fees/deployed.so'
def run(c,image):
 vm=LiteSVM().with_transaction_history(0);vm.add_program(PROGRAM,image)
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 vm.set_clock(Clock(1000,0,0,0,c.get('time',1700000000)))
 uid=c.get('user_id','12345').encode();platform=c.get('platform',0);social,bump=Pubkey.find_program_address([b'social-fee-pda',uid,bytes([platform])],PROGRAM)
 state=hashlib.sha256(b'account:SocialFeePda').digest()[:8]+bytes([bump,c.get('version',1)])+len(uid).to_bytes(4,'little')+uid+bytes([platform])+c.get('total',0).to_bytes(8,'little')+c.get('last',0).to_bytes(8,'little')+c.get('stable_total',0).to_bytes(8,'little')+bytes(120)
 state=bytearray(state.ljust(179,b'\0'))
 for offset,value in c.get('patches',[]):state[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 vm.set_account(social,Account(vm.minimum_balance_for_rent_exemption(179)+c.get('native',1000000),bytes(state),Pubkey.from_string(c.get('social_owner',str(PROGRAM)))))
 gd=bytearray(BASE);gd[41]=c.get('flags',0);gd[42:74]=bytes(AUTH.pubkey());gd[74:82]=c.get('rate',60).to_bytes(8,'little');vm.set_account(GLOBAL,Account(10**9,bytes(gd),Pubkey.from_string(c.get('global_owner',str(PROGRAM)))))
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 quote=Pubkey.from_string(c.get('quote',str(WSOL)));token=TOKEN22 if c.get('token22') else TOKEN
 md=bytearray(82);md[44]=9 if quote==WSOL else 6;md[45]=c.get('mint_initialized',1)
 for offset,value in c.get('mint_patches',[]):md[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
 length=c.get('mint_length',len(md));md=(md+bytearray(max(0,length-len(md))))[:length]
 vm.set_account(quote,Account(10**9,bytes(md),Pubkey.from_string(c.get('mint_owner',str(token)))))
 recipient={'program':PROGRAM,'social':social,'global':GLOBAL,'authority':AUTH.pubkey()}.get(c.get('recipient_kind'),OTHER.pubkey())
 source=Pubkey.find_program_address([bytes(social),bytes(token),bytes(quote)],ATA)[0];dest=Pubkey.find_program_address([bytes(recipient),bytes(token),bytes(quote)],ATA)[0]
 for key,owner,amount,exists in [(source,social,c.get('tokens',12345),c.get('source_exists',True)),(dest,recipient,c.get('recipient_tokens',77),c.get('destination_exists',True))]:
  vm.set_account(key,Account(0,b'',Pubkey.default()))
  if exists:
   td=bytearray(165);td[:32]=bytes(quote);td[32:64]=bytes(owner);td[64:72]=amount.to_bytes(8,'little');td[108]=1
   reserve=vm.minimum_balance_for_rent_exemption(165)
   if quote==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
   for offset,value in c.get('source_patches' if key==source else 'destination_patches',[]):td[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
   vm.set_account(key,Account(reserve+(amount if quote==WSOL else 0),bytes(td),Pubkey.from_string(c.get('source_owner' if key==source else 'destination_owner',str(token)))))
 names={'recipient':recipient,'social_fee_pda':social,'quote_mint':quote,'associated_social_fee_pda':source,'associated_recipient':dest,'quote_token_program':token,'associated_token_program':ATA,'fee_program_global':GLOBAL,'social_claim_authority':AUTH.pubkey(),'system_program':Pubkey.default(),'event_authority':EVENT,'program':PROGRAM}
 if c.get('other_authority'):names['social_claim_authority']=OTHER.pubkey()
 if c.get('wrong'):names[c['wrong']]=Pubkey.from_bytes(bytes([77])*32)
 if c.get('recipient_alias'):names['recipient']=names[c['recipient_alias']]
 metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),(a.get('writable',False) or c.get('writable')==a['name']) and c.get('readonly')!=a['name']) for a in IX['accounts']]
 payload=bytes(IX['discriminator'])+len(uid).to_bytes(4,'little')+uid+bytes([platform])
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([OTHER if c.get('other_authority') else AUTH] if not c.get('unsigned') else []),vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  result={}
  for name,key in {**names,'transaction_payer':PAYER.pubkey()}.items():
   a=vm.get_account(key)
   if a and a.executable:continue
   result[name]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return result
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;raw=json.loads(meta.to_json())
 return {'case':c,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':raw['inner_instructions'],'return':raw['return_data'],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 rows=[{'name':'native-base'},{'name':'native-no-atas','source_exists':False,'destination_exists':False},{'name':'native-zero','native':0,'tokens':0},{'name':'native-tokens-only','native':0},{'name':'native-no-source','source_exists':False},{'name':'native-no-destination','destination_exists':False},{'name':'usdc','quote':str(USDC)},{'name':'arbitrary','quote':str(Pubkey.from_bytes(bytes([61])*32))}]
 rows += [{'name':'usdc-'+label,'quote':str(USDC),**extra} for label,extra in [('no-source',{'source_exists':False}),('no-destination',{'destination_exists':False}),('zero',{'tokens':0}),('token22',{'token22':True}),('native-only',{'tokens':0,'native':1000000}),('overflow',{'stable_total':2**64-1})]]
 rows += [{'name':'flags-'+str(n),'flags':n} for n in [1,2,4,8,16,32,64,128,255]]
 rows += [{'name':'last-'+str(n),'last':n} for n in [1699999940,1699999941,1700000000,1700000001,2**64-1]]
 rows += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in IX['accounts'] if a['name']!='social_claim_authority']
 rows += [{'name':'unsigned','unsigned':True},{'name':'native-token22','token22':True},{'name':'native-overflow','total':2**64-1},{'name':'version0','version':0}]
 rows += [{'name':'usdc-create-destination','quote':str(USDC),'destination_exists':False,'writable':'social_claim_authority'}, {'name':'usdc-zero-no-destination','quote':str(USDC),'tokens':0,'destination_exists':False}, {'name':'usdc-cooldown-no-source','quote':str(USDC),'source_exists':False,'last':1700000000}]
 for side in ['source','destination']:
  for offset,label,value in [(0,'mint',bytes(32)),(32,'authority',bytes(32)),(108,'frozen',bytes([2])),(108,'uninitialized',bytes([0]))]:rows.append({'name':'usdc-'+side+'-'+label,'quote':str(USDC),side+'_patches':[(offset,value.hex())]})
  rows.append({'name':'usdc-'+side+'-wrong-owner','quote':str(USDC),side+'_owner':str(PROGRAM)})
 rows += [{'name':'usdc-zero-invalid-destination','quote':str(USDC),'tokens':0,'destination_patches':[(108,'00')]}]
 rows += [{'name':'quote-length-'+str(n),'mint_length':n} for n in [0,7,81,82,83]]
 rows += [{'name':'quote-uninitialized','mint_initialized':0},{'name':'quote-wrong-owner','mint_owner':str(PROGRAM)},{'name':'quote-token22-tokenlegacy','mint_owner':str(TOKEN22)},{'name':'quote-legacy-token22','token22':True,'mint_owner':str(TOKEN)},{'name':'social-owner','social_owner':str(TOKEN)},{'name':'global-owner','global_owner':str(TOKEN)}]
 rows += [{'name':'recipient-'+kind+'-'+qname,'recipient_kind':kind,'quote':str(quote)} for kind in ['program','social','global','authority'] for qname,quote in [('native',WSOL),('stable',USDC)]]
 rows += [{'name':'readonly-'+a['name'],'readonly':a['name']} for a in IX['accounts'] if a.get('writable')]
 rows += [{'name':'wrong-authority','other_authority':True},{'name':'wrong-program-zero','wrong':'program','native':0},{'name':'stable-token22-owner-legacy-program','quote':str(USDC),'mint_owner':str(TOKEN22)},{'name':'stable-legacy-owner-token22-program','quote':str(USDC),'token22':True,'mint_owner':str(TOKEN)},{'name':'native-invalid-ata-state','source_patches':[(108,'00')],'destination_patches':[(108,'00')]}]
 for n in [2**63,2**64-1]:
  c=dict(next(c for c in rows if c['name']=='recipient-social-stable'));c.update(name='self-transfer-overflow-'+str(n),recipient_tokens=n);rows.append(c)
 rows += [{'name':'all-flags-'+str(n),'flags':n} for n in range(256)]
 rows += [{'name':'stable-flags-'+str(n),'flags':n,'quote':str(USDC)} for n in range(256)]
 rows += [{'name':'stored-'+branch+'-'+str(offset),'quote':str(quote),'patches':[(offset,'00')]} for branch,quote in [('native',WSOL),('stable',USDC)] for offset in [0,8,9,14,19]]
 rows += [{'name':'stable-last-rate-'+str(last)+'-'+str(rate),'quote':str(USDC),'last':last,'rate':rate} for last in [0,1,1700000000,1700000001,2**64-1] for rate in [0,1,2**64-1]]
 rows += [{'name':'negative-time-'+branch,'quote':str(quote),'time':-1} for branch,quote in [('native',WSOL),('stable',USDC)]]
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];bad=[]
 # Read each image once, so every case and the receipt use the same bytes.
 original=ORIGINAL.read_bytes();candidate=a.candidate.read_bytes() if a.candidate else None
 for c in cases():
  x=run(c,original);y=run(c,candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 report={'scope':'Signed synthetic local social claimv2 fixtures; not full byte identity.','original_sha256':hashlib.sha256(original).hexdigest(),'candidate_sha256':hashlib.sha256(candidate).hexdigest() if a.candidate else None,'cases':rows,'mismatches':bad}
 publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
