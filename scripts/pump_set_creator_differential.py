#!/usr/bin/env python3
"""Normally signed synthetic Pump creator setter/metadata synchronization comparisons."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from fees_donation_create_differential import *
import pump_validate_admin as pump
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');META=Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s');METADATA=Pubkey.find_program_address([b'metadata',bytes(META),bytes(MINT)],META)[0]
def metadata(c):
 def string(s):b=s.encode();return len(b).to_bytes(4,'little')+b
 creators=c.get('creators',[(str(OTHER.pubkey()),False,100)])
 d=bytes([c.get('metadata_key',4)])+bytes(AUTH.pubkey())+bytes(Pubkey.from_string(c.get('metadata_mint',str(MINT))))+string('Synthetic')+string('SYN')+string('')+bytes(2)
 d+=b'\0' if creators is None else b'\1'+len(creators).to_bytes(4,'little')+b''.join(bytes(Pubkey.from_string(k))+bytes([v,s]) for k,v,s in creators)
 return d+bytes([0,1])+bytes(16)
def run(c,binary=None):
 vm=LiteSVM().with_transaction_history(0);vm.set_clock(Clock(1000,0,0,0,1700000000));vm.add_program_from_file(PUMP,binary or ROOT/'evidence/original/pump/deployed.so')
 for kp in [PAYER,AUTH,OTHER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 gd=bytearray(pump.DATA);gd[386:418]=bytes(OTHER.pubkey() if c.get('wrong_authority') else AUTH.pubkey());vm.set_account(pump.GLOBAL,Account(10**9,bytes(gd),PUMP))
 md=bytearray(82);md[44]=6;md[45]=1;vm.set_account(MINT,Account(10**9,bytes(md),TOKEN))
 cd=bytearray(CURVE_DATA);cd[49:81]=bytes(Pubkey.from_string(c.get('current',str(Pubkey.default()))));vm.set_account(CURVE,Account(10**9,bytes(cd),PUMP));vm.set_account(METADATA,Account(10**9,metadata(c),META));vm.set_account(pump.EVENT,Account(0,b'',Pubkey.default()))
 names={'set_creator_authority':AUTH.pubkey(),'global':pump.GLOBAL,'mint':MINT,'metadata':METADATA,'bonding_curve':CURVE,'event_authority':pump.EVENT,'program':PUMP}
 for name,p in c.get('accounts',{}).items():
  k=names[name];a=vm.get_account(k);d=bytearray(a.data if a else b'')
  if 'data' in p:d=bytearray.fromhex(p['data'])
  for off,val in p.get('patches',[]):d[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  if 'length' in p:d=d[:p['length']]
  vm.set_account(k,Account(p.get('lamports',a.lamports if a else 0),bytes(d),Pubkey.from_string(p.get('owner',str(a.owner) if a else str(Pubkey.default())))))
 if c.get('wrong'):names[c['wrong']]=OTHER.pubkey()
 ix=next(i for i in pump.IDL['instructions'] if i['name']==c['op']);metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name'] not in c.get('readonly',[])) for a in ix['accounts']]
 if 'count' in c:metas=metas[:c['count']]
 data=bytes(ix['discriminator'])+(bytes(Pubkey.from_string(c.get('creator',str(OTHER.pubkey())))) if c['op']=='set_creator' else b'')+bytes.fromhex(c.get('trailing',''))
 signers=[PAYER]+([AUTH] if any(m.is_signer and m.pubkey==AUTH.pubkey() for m in metas) else [])
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,data,metas)],PAYER.pubkey(),signers,vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for n,k in {**names,'transaction_payer':PAYER.pubkey()}.items():
   a=vm.get_account(k)
   if a and a.executable:continue
   out[n]=None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'data':a.data.hex()}
  return out
 before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;raw=json.loads(m.to_json());return {'error':str(r.err()) if failed else None,'before':before,'after':snap(),'events':[l for l in m.logs() if l.startswith('Program data:')],'logs':m.logs(),'inner':raw['inner_instructions'],'return':raw['return_data'],'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signatures_verified':True}
def cases():
 rows=[]
 for op in ['set_creator','set_metaplex_creator']:
  cs=[{'name':'base'},{'name':'no-creators','creators':None},{'name':'empty-creators','creators':[]},{'name':'verified','creators':[(str(OTHER.pubkey()),True,100)]},{'name':'current-auth','current':str(AUTH.pubkey())},{'name':'current-other','current':str(OTHER.pubkey())},{'name':'zero-new','creator':str(Pubkey.default())},{'name':'metadata-wrong-mint','metadata_mint':str(AUTH.pubkey())}]
  cs += [{'name':'creator-list-'+str(i),'creators':v} for i,v in enumerate([[(str(AUTH.pubkey()),False,50),(str(OTHER.pubkey()),True,50)],[(str(AUTH.pubkey()),True,50),(str(OTHER.pubkey()),True,50)],[(str(Pubkey.default()),True,100)],[(str(AUTH.pubkey()),False,0)],[(str(OTHER.pubkey()),False,255)]])]
  cs += [{'name':'metadata-key-'+str(k),'metadata_key':k} for k in [0,1,3,4,5,255]]
  cs += [{'name':'curve-flag-'+str(off),'accounts':{'bonding_curve':{'patches':[(off,'01')]}}} for off in [48,81,82,123,124]]
  cs += [{'name':'curve-length-'+str(n),'accounts':{'bonding_curve':{'length':n}}} for n in [0,7,8,48,49,80,81,82,83,114,115,123,124,125,166]]
  for a in next(i for i in pump.IDL['instructions'] if i['name']==op)['accounts']:
   if a['name']!='set_creator_authority':cs.append({'name':'wrong-'+a['name'],'wrong':a['name']})
  cs += [{'name':'layout-'+n+'-'+str(i),'accounts':{n:p}} for n in ['mint','metadata','bonding_curve'] for i,p in enumerate([{'owner':str(Pubkey.default())},{'lamports':0},{'length':0},{'data':'00'},{'patches':[(0,'ff')]}])]
  cs += [{'name':'readonly','readonly':['bonding_curve']},{'name':'trailing','trailing':'ff'}]
  if op=='set_creator':cs += [{'name':'wrong-authority','wrong_authority':True},{'name':'unsigned','unsigned':True}]
  cs += [{'name':'metadata-length-'+str(n),'accounts':{'metadata':{'length':n}}} for n in [1,32,64,65,68,69,77,80,81,82,83,84,85,86,87,88,89,90,120,121,122,123,124,125,126,127,128,129,130,140,141]]
  cs += [{'name':'curve-bool-'+str(off),'accounts':{'bonding_curve':{'patches':[(off,'02')]}}} for off in [48,81,82,123,124]]
  cs += [{'name':'short-noop-'+str(n),'current':str(AUTH.pubkey()),'accounts':{'bonding_curve':{'length':n}}} for n in [81,82,83,125,141,165,166]]
  cs += [{'name':'short-no-creators-'+str(n),'creators':None,'accounts':{'bonding_curve':{'length':n}}} for n in [49,81,125,165]]
  cs += [{'name':'count-'+str(n),'count':n} for n in range(len(next(i for i in pump.IDL['instructions'] if i['name']==op)['accounts']))]
  cs += [{'name':'empty-noop','current':str(AUTH.pubkey()),'creators':[]},{'name':'none-zero','creators':None,'creator':str(Pubkey.default())},{'name':'none-program','creators':None,'creator':str(PUMP)},{'name':'bad-meta-noop','current':str(AUTH.pubkey()),'metadata_key':0}]
  cs += [{'name':'metadata-byte-'+str(n),'accounts':{'metadata':{'patches':[(n,'02')]}}} for n in range(65,146)]
  cs += [{'name':'metadata-tail-length-'+str(n),'accounts':{'metadata':{'length':n}}} for n in range(131,140)]
  cs += [{'name':'paired-'+str(i),**v} for i,v in enumerate([{'wrong_authority':True,'metadata_key':0},{'readonly':['bonding_curve'],'metadata_key':0},{'readonly':['bonding_curve'],'accounts':{'bonding_curve':{'length':49}}},{'creators':[],'accounts':{'bonding_curve':{'length':49}}},{'current':str(AUTH.pubkey()),'creators':[]},{'wrong':'metadata','accounts':{'bonding_curve':{'length':0}}}])]
  cs += [{'name':'metadata-option-'+str(n)+'-'+str(v),'accounts':{'metadata':{'patches':[(n,bytes([v]).hex())]}}} for n in [132,133,134,135,136,137,138,139,140,141,142] for v in [0,1,255]]
  cs += [{'name':'metadata-length-nonce-'+str(n),'accounts':{'metadata':{'patches':[(132,'01')],'length':n}}} for n in [132,133,134,135,136,137]]
  rows += [{'op':op,**c,'name':op+'-'+c['name']} for c in cs]
 return rows
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];bad=[]
 paths=[Path(__file__),ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/upstream/pump.json',ROOT/'scripts/fees_donation_create_differential.py',ROOT/'scripts/fees_admin_differential.py',ROOT/'scripts/pump_validate_admin.py']+([a.candidate] if a.candidate else []);hashes={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
 for c in cases():
  x=run(c);y=run(c,a.candidate) if a.candidate else None;match=all(x[k]==y[k] for k in ['error','before','after','events','inner','return']) if y else None;rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:bad.append(c['name'])
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'scope':'Normally signed synthetic local creator setters, no privileged signatures or live writes; bounded behavior only.','original_sha256':sha(ROOT/'evidence/original/pump/deployed.so'),'candidate_sha256':sha(a.candidate) if a.candidate else None,'case_count':len(rows),'cases':rows,'mismatches':bad,'provenance':hashes}
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in hashes.items()),'Input changed during execution'
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n');print(len(rows),bad)
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
