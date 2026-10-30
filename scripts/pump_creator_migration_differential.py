#!/usr/bin/env python3
"""Normally signed creator migration after captured sharing bootstrap."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,hashlib,base64,argparse,gzip
from types import SimpleNamespace
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import fees_sharing_update_differential as fixtures
from fees_sharing_update_differential import *
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
  vm=Capture(original_type().with_sigverify(True));vms.append(vm);return vm
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
 if binary:vm.add_program_from_file(PUMP,binary)
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
 return {'signature_verification':True,'error':str(r.err()) if failed else None,'before':before,'after':snap(),'events':[l for l in m.logs() if l.startswith('Program data:')],'logs':m.logs(),'inner':raw['inner_instructions'],'return':raw.get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'bootstrap_transactions':bootstrap_transactions}
d=SimpleNamespace(**globals())
def cases():
 rows=[{'name':'base'},{'name':'old-other','curve_patches':[(49,bytes(d.OTHER.pubkey()).hex())]},{'name':'already-migrated','curve_patches':[(49,bytes(d.SHARING).hex())]},{'name':'old-zero','curve_patches':[(49,bytes(32).hex())]}]
 rows += [{'name':'version-'+str(n),'version':n} for n in [0,1,2,255]]+[{'name':'status-'+str(n),'status':n} for n in [0,1,2,255]]+[{'name':'revoked','revoked':True}]
 rows += [{'name':'sharing-patch-'+str(n),'sharing_patches':[(n,'00')]} for n in [0,8,11,43]]
 rows += [{'name':'sharing-length-'+str(n),'sharing_length':n} for n in [0,7,8,75,76,80,113,114,400]]
 rows += [{'name':'curve-length-'+str(n),'account_mutations':{'bonding_curve':{'length':n}}} for n in [0,7,8,48,49,50,80,81,82,83,114,115,122,123,124,125,165,166,200,256]]
 rows += [{'name':'curve-bool-'+str(n),'curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(n,'02')]} for n in [48,81,82,123,124]]
 rows += [{'name':'mayhem','curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(81,'01')]},{'name':'holder','curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(124,'01')]},{'name':'curve-discriminator','curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(0,'ff')]},{'name':'sharing-owner','sharing_owner':str(d.PUMP)},{'name':'curve-owner','account_mutations':{'bonding_curve':{'owner':str(d.PROGRAM)}}}]
 ix=next(x for x in d.PIDL['instructions'] if x['name']=='migrate_bonding_curve_creator')
 rows += [{'name':'wrong-'+a['name'],'wrong':a['name']} for a in ix['accounts']]+[{'name':'readonly','readonly':'bonding_curve'}]+[{'name':'accounts-'+str(n),'account_count':n} for n in range(len(ix['accounts']))]
 rows += [{'name':'zero-admin-zero-creator','curve_patches':[(49,bytes(32).hex())],'sharing_patches':[(43,bytes(32).hex())]}, {'name':'other-admin-matching','curve_patches':[(49,bytes(d.OTHER.pubkey()).hex())],'sharing_patches':[(43,bytes(d.OTHER.pubkey()).hex())]}, {'name':'sharing-admin-matching','curve_patches':[(49,bytes(d.SHARING).hex())],'sharing_patches':[(43,bytes(d.SHARING).hex())]}]
 rows += [{'name':'holder-'+kind,**c,'curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(124,'01')]+c.get('curve_patches',[])} for kind,c in [('mismatch',{'sharing_patches':[(43,bytes(d.OTHER.pubkey()).hex())]}),('wrong-event',{'wrong':'event_authority'}),('wrong-program',{'wrong':'program'}),('invalid-status',{'status':2}),('wrong-mint',{'sharing_patches':[(11,bytes(d.OTHER.pubkey()).hex())]}),('readonly',{'readonly':'bonding_curve'})]]
 rows += [{'name':'legacy-zero-admin-'+str(n),'curve_patches':[(49,bytes(32).hex())],'sharing_patches':[(43,bytes(32).hex())],'account_mutations':{'bonding_curve':{'length':n}}} for n in [49,50,63,64,79,80,81,82,83,114,115,123,124,125,132,133,140,141,142,149,150,157,158,165,166]]
 rows += [{'name':'legacy-sentinel-'+str(n),'curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(125,(12345).to_bytes(8,'little').hex()),(133,(67890).to_bytes(8,'little').hex()),(142,(999).to_bytes(8,'little').hex())],'account_mutations':{'bonding_curve':{'length':n}}} for n in [125,132,133,140,141,142,149,150,157,158,165,166,200,256]]
 rows += [{'name':'combined-'+label,**c} for label,c in [('bad-curve-bad-sharing',{'curve_patches':[(0,'ff')],'sharing_owner':str(d.PUMP)}),('bad-sharing-wrong-program',{'status':2,'wrong':'program'}),('wrong-owner-readonly',{'sharing_owner':str(d.PUMP),'readonly':'bonding_curve'}),('zero-creator-nonzero-admin',{'curve_patches':[(49,bytes(32).hex())]}),('zero-admin-nonzero-creator',{'sharing_patches':[(43,bytes(32).hex())]}),('readonly-wrong-event',{'readonly':'bonding_curve','wrong':'event_authority'})]]
 rows += [{'name':'fees-'+label,'curve_patches':[(49,bytes(d.AUTH.pubkey()).hex())]+cp,'sharing_patches':sp} for label,cp,sp in [('creator',[(125,(1).to_bytes(8,'little').hex())],[]),('protocol',[(133,(1).to_bytes(8,'little').hex())],[]),('holder-creator',[(124,'01'),(125,(1).to_bytes(8,'little').hex())],[]),('mismatch-creator',[(125,(1).to_bytes(8,'little').hex())],[(43,bytes(d.OTHER.pubkey()).hex())])]]
 rows += [{'name':'protocol-tail-'+str(n),'curve_patches':[(49,bytes(d.AUTH.pubkey()).hex()),(133,(67890).to_bytes(8,'little').hex()),(142,(999).to_bytes(8,'little').hex()),(150,(888).to_bytes(8,'little').hex()),(158,(777).to_bytes(8,'little').hex())],'account_mutations':{'bonding_curve':{'length':n}}} for n in [133,140,141,142,149,150,157,158,165,166,200,256]]
 rows += [{'name':'preserve-existing-tail','direct_mutations':{'curve':{'patches':[(200,'ab'*16)]}}},{'name':'preserve-extended-tail','direct_mutations':{'curve':{'patches':[(250,'cd'*16)]}}}]
 return [{**{'op':'migrate_bonding_curve_creator','curve_patches':[(49,bytes(d.AUTH.pubkey()).hex())]},**c} for c in rows]
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();publisher=PumpReport(a.output,ROOT,a.candidate,__file__);rows=[];bad=[];paths=[Path(__file__),ROOT/'evidence/upstream/pump.json',d.ORIGINAL,ROOT/'evidence/original/pump_fees/deployed.so',ROOT/'evidence/original/pump_amm/deployed.so',Path(fixtures.__file__),Path(fixtures.f.__file__)]+([a.candidate] if a.candidate else []);hash_file=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provenance={str(p):hash_file(p) for p in paths}
 for c in cases():
  x=d.run(c);y=d.run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 assert provenance=={str(p):hash_file(p) for p in paths}
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r={'provenance':provenance,'scope':'Normal fee-payer signature, synthetic legacy account variants, real captured sharing bootstrap; candidate swaps only Pump. No full byte identity claim.','original_sha256':sha(d.ORIGINAL),'candidate_sha256':sha(a.candidate) if a.candidate else None,'case_count':len(rows),'cases':rows,'mismatches':bad};raw=(json.dumps(r,separators=(',',':'))+'\n').encode();publisher.write(gzip.compress(raw,mtime=0) if a.output.suffix=='.gz' else raw);print(json.dumps({'cases':len(rows),'mismatches':bad}));assert not bad
if __name__=='__main__':main()
