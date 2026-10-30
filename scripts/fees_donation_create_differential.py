#!/usr/bin/env python3
"""Recover donation-PDA creation with normally signed synthetic local transactions."""
import argparse, base64, hashlib, json, pathlib, sys
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.pubkey import Pubkey
from fees_admin_differential import IDL, PROGRAM, GLOBAL, BUMP, EVENT, AUTH, OTHER, PAYER, BASE
from solders.litesvm import LiteSVM
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from pump_amm_reusable_harness import pin_program
PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
AMM=Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
MINT=Pubkey.from_bytes(bytes([61])*32);CONFIG=Pubkey.from_bytes(bytes([62])*32);POOL=Pubkey.from_bytes(bytes([63])*32)
QUOTE=Pubkey.from_string('So11111111111111111111111111111111111111112')
POOL_AUTH=Pubkey.find_program_address([b'pool-authority',bytes(MINT)],PUMP)[0]
POOL,POOL_BUMP=Pubkey.find_program_address([b'pool',bytes(2),bytes(POOL_AUTH),bytes(MINT),bytes(QUOTE)],AMM)
CURVE=Pubkey.find_program_address([b'bonding-curve',bytes(MINT)],PUMP)[0]
SHARING=Pubkey.find_program_address([b'sharing-config',bytes(MINT)],PROGRAM)[0]
DONATION,DONATION_BUMP=Pubkey.find_program_address([b'donation-fee-pda',bytes(MINT),bytes(CONFIG)],PROGRAM)
CURVE_DATA=hashlib.sha256(b'account:BondingCurve').digest()[:8]+bytes(40)+bytes([0])+bytes(AUTH.pubkey())+bytes([0])+bytes(118)
INSTRUCTION=next(x for x in IDL['instructions'] if x['name']=='create_donation_fee_pda')
class Fixture:
 def __init__(self,binary):self.vm=LiteSVM().with_transaction_history(0);self.vm.add_program_from_file(PROGRAM,binary)
 def run(self,c):
  for kp in [AUTH,OTHER,PAYER]:self.vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
  for k in [EVENT,MINT,CONFIG,POOL,SHARING]:self.vm.set_account(k,Account(0,b'',Pubkey.default()))
  mint_data=bytearray(82);mint_data[44]=6;mint_data[45]=1
  for offset,value in c.get('mint_patches',[]):mint_data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  if 'mint_length' in c:mint_data=(mint_data+bytearray(max(0,c['mint_length']-len(mint_data))))[:c['mint_length']]
  self.vm.set_account(MINT,Account(10**9,bytes(mint_data),Pubkey.from_string(c.get('mint_owner','TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'))))
  pool_data=hashlib.sha256(b'account:Pool').digest()[:8]+bytes([POOL_BUMP])+bytes(2)+bytes(POOL_AUTH)+bytes(MINT)+bytes(QUOTE)+bytes(32*3)+bytes(8)+bytes(AUTH.pubkey())+bytes(2)+bytes(16)
  pool_data=bytearray(pool_data)
  for offset,value in c.get('pool_patches',[]): pool_data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
  if c.get('sharing'):
   pool_data[211:243]=bytes(SHARING)
   sd=c['sharing']; sharing_data=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([Pubkey.find_program_address([b'sharing-config',bytes(MINT)],PROGRAM)[1],sd.get('version',1),sd.get('status',1)])+bytes.fromhex(sd.get('mint',bytes(MINT).hex()))+bytes.fromhex(sd.get('admin',bytes(AUTH.pubkey()).hex()))+bytes([sd.get('revoked',0)])+bytes(4)
   if sd.get('bad_disc'):sharing_data=bytes([0])+sharing_data[1:]
   self.vm.set_account(SHARING,Account(10**9,sharing_data,Pubkey.from_string(sd.get('owner',str(PROGRAM)))))
  if 'pool_length' in c:pool_data=(pool_data+bytearray(max(0,c['pool_length']-len(pool_data))))[:c['pool_length']]
  self.vm.set_account(POOL,Account(10**9,bytes(pool_data),Pubkey.from_string(c.get('pool_owner',str(AMM)))))
  global_data=bytearray(BASE);global_data[41]=c.get('flags',0)
  curve_data=bytearray(CURVE_DATA)
  if 'creator' in c:curve_data[49:81]=bytes.fromhex(c['creator'])
  mutation=c.get('mutation','none');global_key=GLOBAL;donation=DONATION;curve=CURVE;sharing=SHARING;event=EVENT;program=PROGRAM;system=Pubkey.default();global_owner=PROGRAM;curve_owner=PUMP
  if mutation=='global_key':global_key=OTHER.pubkey()
  if mutation=='global_owner':global_owner=PUMP
  if mutation=='global_discriminator':global_data[0]^=1
  if mutation=='global_bump':global_data[8]^=1
  if mutation=='donation_key':donation=OTHER.pubkey()
  if mutation=='curve_key':curve=OTHER.pubkey()
  if mutation=='curve_owner':curve_owner=PROGRAM
  if mutation=='curve_discriminator':curve_data[0]^=1
  if mutation=='curve_empty':curve_data=bytearray();curve_owner=Pubkey.default()
  if mutation=='sharing_key':sharing=OTHER.pubkey()
  if mutation=='event':event=OTHER.pubkey()
  if mutation=='program':program=Pubkey.default()
  if mutation=='system':system=OTHER.pubkey()
  if mutation.startswith('curve_length:'):curve_data=curve_data[:int(mutation.split(':')[1])]
  self.vm.set_account(global_key,Account(10**9,bytes(global_data),global_owner));self.vm.set_account(curve,Account(10**9 if curve_data else 0,bytes(curve_data),curve_owner))
  self.vm.set_account(donation,Account(c.get('prefund',0),b'',Pubkey.default()))
  if c.get('existing_valid'):
   state=hashlib.sha256(b'account:DonationFeePda').digest()[:8]+bytes([DONATION_BUMP,7])+bytes(CONFIG)+bytes(MINT)+bytes(QUOTE)+bytes(OTHER.pubkey())+(42).to_bytes(8,'little')+(77).to_bytes(8,'little')+bytes([55])*64
   state=bytearray(state)
   for offset,value in c.get('existing_patches',[]):state[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
   self.vm.set_account(donation,Account(10**9,bytes(state),PROGRAM))
  if mutation=='existing':self.vm.set_account(donation,Account(10**9,bytes(218),PROGRAM))
  names={'event_authority':event,'program':program,'payer':AUTH.pubkey(),'system_program':system,'fee_program_global':global_key,'donation_fee_pda':donation,'config_id':CONFIG,'base_mint':MINT,'bonding_curve':curve,'pool':POOL,'sharing_config':sharing}
  metas=[AccountMeta(names[a['name']],a.get('signer',False) and mutation!='unsigned',a.get('writable',False) and not (mutation=='readonly_donation' and a['name']=='donation_fee_pda')) for a in INSTRUCTION['accounts']]
  if mutation.startswith('accounts:'):metas=metas[:int(mutation.split(':')[1])]
  signers=[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else [])
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,bytes(INSTRUCTION['discriminator'])+bytes.fromhex(c.get('trailing','')),metas)],PAYER.pubkey(),signers,self.vm.latest_blockhash())
  assert all(tx.verify_with_results())
  r=self.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;after=self.vm.get_account(donation)
  return {'error':str(r.err()) if failed else None,'data':after.data.hex() if after else None,'owner':str(after.owner) if after else None,'lamports':after.lamports if after else None,'payer_delta':self.vm.get_account(PAYER.pubkey()).lamports-10**12,'authority_delta':self.vm.get_account(AUTH.pubkey()).lamports-10**12,'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 rows=[{'name':'base'},{'name':'prefund-one','prefund':1},{'name':'prefund-large','prefund':10**9},{'name':'zero-creator','creator':bytes(32).hex()}]
 rows += [{'name':'flags-'+str(n),'flags':n} for n in range(256)]
 for mutation in ['global_key','global_owner','global_discriminator','global_bump','donation_key','curve_key','curve_owner','curve_discriminator','curve_empty','sharing_key','event','program','system','unsigned','readonly_donation','existing']+['accounts:'+str(n) for n in range(11)]+['curve_length:'+str(n) for n in [0,7,8,48,49,80,81,82,83,150,151,200]]:rows.append({'name':mutation,'mutation':mutation})
 rows.extend([{'name':'existing-valid','existing_valid':True},{'name':'existing-disabled','existing_valid':True,'flags':4},{'name':'existing-pool-owner','existing_valid':True,'pool_owner':str(PUMP)}])
 for label,sd in [('valid',{'status':1}),('paused',{'status':0}),('version0',{'version':0}),('version255',{'version':255}),('wrong_mint',{'mint':bytes(OTHER.pubkey()).hex()}),('wrong_admin',{'admin':bytes(OTHER.pubkey()).hex()}),('revoked',{'revoked':1}),('wrong_owner',{'owner':str(PUMP)}),('bad_disc',{'bad_disc':True})]:rows.append({'name':'sharing-'+label,'sharing':sd})
 for offset,label,values in [(0,'disc',[bytes(1)]),(8,'bump',[bytes(1)]),(9,'index',[(1).to_bytes(2,'little')]),(11,'pool_creator',[bytes(32),bytes(OTHER.pubkey())]),(43,'base_mint',[bytes(32)]),(75,'quote_mint',[bytes(32),bytes(OTHER.pubkey())]),(211,'coin_creator',[bytes(32),bytes(OTHER.pubkey()),bytes(SHARING)]),(243,'mayhem',[bytes([1]),bytes([2])]),(244,'cashback',[bytes([1]),bytes([2])])]:
  for i,val in enumerate(values):rows.append({'name':'pool-'+label+'-'+str(i),'pool_patches':[(offset,val.hex())]})
 for n in [0,7,8,10,42,74,106,211,243,244,245,260,261,300]:rows.append({'name':'pool-length-'+str(n),'pool_length':n})
 for offset,label in [(8,'bump'),(9,'version'),(10,'config'),(42,'base'),(74,'quote'),(106,'creator')]:
  rows.append({'name':'existing-zero-'+label,'existing_valid':True,'existing_patches':[(offset,bytes(1 if offset<10 else 32).hex())]})
 for n in [0,7,81,82,83]:rows.append({'name':'mint-length-'+str(n),'mint_length':n})
 rows += [{'name':'mint-token2022','mint_owner':'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'},{'name':'mint-wrong-owner','mint_owner':str(PUMP)},{'name':'mint-uninitialized','mint_patches':[(45,'00')]}]
 rows.append({'name':'pool-wrong-owner','pool_owner':str(PUMP)})
 rows.append({'name':'extra-arguments','trailing':'01ff'})
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 original=pin_program(ROOT/'evidence/original/pump_fees/deployed.so');o=Fixture(original);b=Fixture(pin_program(a.candidate)) if a.candidate else None;rows=[];failures=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data','owner','lamports','payer_delta','authority_delta','events','inner']) if b else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 report={'scope':'Synthetic signed local creation fixtures; no crank or full program identity claim.','original_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pin_program(a.candidate).read_bytes()).hexdigest() if a.candidate else None,'cases':rows,'mismatches':failures}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n');print('Cases',len(rows),'mismatches',failures)
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
