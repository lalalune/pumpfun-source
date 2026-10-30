#!/usr/bin/env python3
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import fees_sharing_create_differential as f
from fees_sharing_create_differential import *
PIDL=json.loads((ROOT/'evidence/upstream/pump.json').read_text(encoding='utf-8'));VAULT=Pubkey.find_program_address([b'creator-vault',bytes(SHARING)],PUMP)[0]
def run(c,binary=None):
 original=f.LiteSVM;v=[]
 def factory():
  vm=original().with_sigverify(True);v.append(vm);return vm
 f.LiteSVM=factory
 try:created=f.run({})
 finally:f.LiteSVM=original
 assert created['error'] is None;vm=v[0]
 if binary:vm.add_program_from_file(PUMP,binary)
 a=vm.get_account(SHARING);d=bytearray(a.data);shares=c.get('shares',[10000]);recipients=[Pubkey.from_bytes(bytes([150+i])*32) for i in range(len(shares))] if 'recipient_lamports' in c else [AUTH.pubkey()]*len(shares);recipients=[Pubkey.from_string(k) for k in c.get('recipients',[str(k) for k in recipients])];tail=len(shares).to_bytes(4,'little')+b''.join(bytes(key)+n.to_bytes(2,'little') for key,n in zip(recipients,shares));d[76:76+len(tail)]=tail
 if 'version' in c:d[9]=c['version']
 if 'status' in c:d[10]=c['status']
 if 'revoked' in c:d[75]=c['revoked']
 for key in recipients:
  if 'recipient_lamports' in c:vm.set_account(key,Account(c['recipient_lamports'],bytes(c.get('recipient_length',0)),Pubkey.from_string(c.get('recipient_owner',str(Pubkey.default()))),c.get('recipient_executable',False)))
 vm.set_account(SHARING,Account(a.lamports,bytes(d),a.owner));vm.set_account(VAULT,Account(c.get('amount',1000000),b'',Pubkey.default()))
 for name,key in [('mint',MINT),('curve',CURVE),('sharing',SHARING),('vault',VAULT)]:
  if name in c.get('patch',{}):
   old=vm.get_account(key);patch=c['patch'][name];data=bytearray(old.data)
   for offset,value in patch.get('bytes',[]):data[offset:offset+len(bytes.fromhex(value))]=bytes.fromhex(value)
   vm.set_account(key,Account(patch.get('lamports',old.lamports),bytes(data[:patch.get('length',len(data))]),Pubkey.from_string(patch.get('owner',str(old.owner))),patch.get('executable',old.executable)))
 ix=next(x for x in PIDL['instructions'] if x['name']=='get_minimum_distributable_fee');keys=[MINT,CURVE,SHARING,VAULT]
 if 'wrong' in c:keys[c['wrong']]=Pubkey.from_bytes(bytes([82])*32)
 remaining=[Pubkey.from_string(k) for k in c['remaining']] if 'remaining' in c else recipients;metas=[AccountMeta(k,False,False) for k in keys]+[AccountMeta(k,False,False) for k in remaining];metas=metas[:c.get('account_count',len(metas))];tx=Transaction.new_signed_with_payer([Instruction(PUMP,bytes(ix['discriminator']),metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());assert all(tx.verify_with_results());snapshot_keys=set(keys+remaining+[PAYER.pubkey()]);snap=lambda:{str(k):json.loads(vm.get_account(k).to_json()) if vm.get_account(k) and not vm.get_account(k).executable else None for k in snapshot_keys};before=snap();r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);m=r.meta() if failed else r;raw=json.loads(m.to_json())
 return {'events':[line for line in m.logs() if line.startswith('Program data: ')],'before':before,'after':snap(),'signature_verification':True,'error':str(r.err()) if failed else None,'logs':m.logs(),'metadata':raw,'transaction_base64':base64.b64encode(bytes(tx)).decode()}
def cases():
 rows=[]
 for shares in [[10000],[5000,5000],[1,9999],[3333,6667],[],[0],[9999],[10001],[65535]]:
  for amount in [0,890880,890881,1000000,10000000]:rows.append(dict(shares=shares,amount=amount))
 for shares in [[10000],[5000,5000],[1,9999],[3333,6667],[0],[]]:
  for n in [0,1,890879,890880]:rows.append(dict(shares=shares,recipient_lamports=n))
 for shares in [[10000],[3333,6667],[0]]:
  for length in [0,1,165]:
   for owner in [str(Pubkey.default()),str(PUMP)]:rows.append(dict(shares=shares,recipient_lamports=1,recipient_length=length,recipient_owner=owner))
 rows += [dict(version=n) for n in [0,1,3,255]]+[dict(status=n) for n in [0,2]]+[dict(revoked=1)]+[dict(wrong=n) for n in range(4)]
 rows += [dict(remaining=[]),dict(remaining=[str(OTHER.pubkey())]),dict(remaining=[str(AUTH.pubkey()),str(OTHER.pubkey())])]
 for target in ['mint','curve','sharing','vault']:
  rows += [dict(patch={target:{'owner':str(Pubkey.default())}}),dict(patch={target:{'length':0}}),dict(patch={target:{'bytes':[(0,'ff')]}})]
 rows += [dict(patch={'curve':{'bytes':[(49,bytes(OTHER.pubkey()).hex())]}}),dict(patch={'sharing':{'bytes':[(11,bytes(OTHER.pubkey()).hex())]}})]
 rows += [dict(recipient_lamports=0,amount=n) for n in [0,890880,1781759,1781760,1781761]]
 rows += [dict(recipients=[str(PUMP)]),dict(shares=[0],recipients=[str(PUMP)])]
 for length in [0,1,7,8,48,49,50,80,81,82,83,114,115,150]:rows.append(dict(patch={'curve':{'length':length}}))
 for length in [0,7,8,9,75,76,79,80,113,114]:rows.append(dict(patch={'sharing':{'length':length}}))
 for length in [0,1,81,82,165]:rows.append(dict(patch={'mint':{'length':length}}))
 rows += [dict(patch={'curve':{'bytes':[(48,'02')]}}),dict(patch={'sharing':{'bytes':[(75,'02')]}})]
 rows += [dict(patch={'vault':{'owner':str(PROGRAM)}})]+[dict(account_count=n) for n in range(4)]
 rows += [dict(patch={'curve':{'bytes':[(n,'02')]}}) for n in [81,82,123,124]]+[dict(patch={'sharing':{'bytes':[(8,'00')]}}),dict(status=0,remaining=[]),dict(status=0,shares=[0]),dict(patch={'vault':{'lamports':0}})]
 rows += [dict(patch={'curve':{'length':n,'bytes':[(124,'02')]}}) for n in [8,48,49,80,81,82,83,114,115,122,123,124,125,164,165]]
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[];paths=[Path(__file__),a.candidate,ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/upstream/pump.json',Path(f.__file__),ROOT/'evidence/original/pump_fees/deployed.so',ROOT/'evidence/original/pump_amm/deployed.so'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provenance={str(p):sha(p) for p in paths}
 for c in cases():
  o=run(c);n=run(c,a.candidate);fields=['error','before','after','events'];diff=[k for k in fields if o[k]!=n[k]]
  for k in ['return_data','inner_instructions']:
   if o['metadata'][k]!=n['metadata'][k]:diff.append(k)
  rows.append(dict(case=c,original=o,candidate=n,different_fields=diff))
 assert provenance=={str(p):sha(p) for p in paths}
 report={'scope':'Normally signed offline readonly query using synthetic state bootstrapped by captured Fees/Pump. Compare states, returns, errors and inner instructions; not full byte identity.','provenance':provenance,'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['different_fields']],'cases':rows}
 a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['case_count','mismatches']}))
 if report['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
