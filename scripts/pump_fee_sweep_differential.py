#!/usr/bin/env python3
import sys,json,base64,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import fees_sharing_create_differential as f
from fees_sharing_create_differential import *
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');WSOL=Pubkey.from_string('So11111111111111111111111111111111111111112');STABLE=Pubkey.from_bytes(bytes([77])*32);PIDL=json.load(open(ROOT/'evidence/upstream/pump.json',encoding='utf-8'))
def run(c,binary=None):
 orig=f.LiteSVM;v=[]
 def factory():
  vm=orig().with_sigverify(True);v.append(vm);return vm
 f.LiteSVM=factory
 try:res=f.run({})
 finally:f.LiteSVM=orig
 assert res['error'] is None;vm=v[0];vm.set_clock(Clock(1000,0,0,0,1700000000))
 if binary:vm.add_program_from_file(PUMP,binary)
 for name,key in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(key,ROOT/f'evidence/dependencies/{name}/deployed.so')
 quote=Pubkey.from_string(c.get('quote',str(WSOL)));token=TOKEN22 if c.get('token22') else TOKEN
 a=vm.get_account(CURVE);d=bytearray(a.data);d=d.ljust(250,b'\0');d[83:115]=bytes(Pubkey.from_string(c.get('curve_quote',str(quote))));d[125:133]=c.get('creator_fee',12345).to_bytes(8,'little');d[133:141]=c.get('protocol_fee',67890).to_bytes(8,'little');vm.set_account(CURVE,Account(c.get('curve_lamports',10**9),bytes(d),a.owner))
 vault=Pubkey.find_program_address([b'creator-vault',bytes(SHARING)],PUMP)[0];recipient=vault if c.get('op','sweep_creator_fee')=='sweep_creator_fee' else Pubkey.from_bytes(bytes(vm.get_account(pump.GLOBAL).data[41:73]))
 recipient=Pubkey.from_string(c.get('recipient',str(recipient)))
 vm.set_account(recipient,Account(10**9,b'',Pubkey.default()))
 md=bytearray(82);md[44]=9 if quote==WSOL else 6;md[45]=1;vm.set_account(quote,Account(10**9,bytes(md),token))
 source=Pubkey.find_program_address([bytes(CURVE),bytes(token),bytes(quote)],ATA)[0];dest=Pubkey.find_program_address([bytes(recipient),bytes(token),bytes(quote)],ATA)[0]
 for key,owner,amount,side in [(source,CURVE,c.get('tokens',10**9),'source'),(dest,recipient,77,'destination')]:
  if c.get(side+'_missing'):vm.set_account(key,Account(0,b'',Pubkey.default()));continue
  td=bytearray(165);td[:32]=bytes(quote);td[32:64]=bytes(owner);td[64:72]=amount.to_bytes(8,'little');td[108]=1;reserve=vm.minimum_balance_for_rent_exemption(165)
  if quote==WSOL:td[109:113]=(1).to_bytes(4,'little');td[113:121]=reserve.to_bytes(8,'little')
  vm.set_account(key,Account(reserve+(amount if quote==WSOL else 0),bytes(td),token))
 names={'payer':PAYER.pubkey(),'global':pump.GLOBAL,'base_mint':MINT,'quote_mint':quote,'quote_token_program':token,'associated_token_program':ATA,'system_program':Pubkey.default(),'bonding_curve':CURVE,'associated_quote_bonding_curve':source,'recipient':recipient,'associated_quote_recipient':dest,'event_authority':pump.EVENT,'program':PUMP}
 
 for name,patch in c.get('patch',{}).items():
  key=names[name];a=vm.get_account(key);data=bytearray(a.data)
  for off,h in patch.get('bytes',[]):data[off:off+len(bytes.fromhex(h))]=bytes.fromhex(h)
  vm.set_account(key,Account(patch.get('lamports',a.lamports),bytes(data[:patch.get('length',len(data))]),Pubkey.from_string(patch.get('owner',str(a.owner)))))
 if 'wrong' in c:names[c['wrong']]=Pubkey.from_bytes(bytes([78])*32)
 ix=next(x for x in PIDL['instructions'] if x['name']==c.get('op','sweep_creator_fee'));metas=[AccountMeta(names[a['name']],a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for a in ix['accounts']];metas=metas[:c.get('account_count',len(metas))];tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(PUMP,bytes(ix['discriminator']),metas)],(AUTH if c.get('unsigned') or c.get('readonly')=='payer' else PAYER).pubkey(),([AUTH] if c.get('unsigned') else [AUTH,PAYER] if c.get('readonly')=='payer' else [PAYER]),vm.latest_blockhash());assert all(tx.verify_with_results());keys=set(names.values());snap=lambda:{str(k):json.loads(vm.get_account(k).to_json()) if vm.get_account(k) and not vm.get_account(k).executable else None for k in keys};before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r
 return dict(signature_verification=True,error=str(r.err()) if fail else None,before=before,after=snap(),metadata=json.loads(m.to_json()),logs=m.logs(),transaction_base64=base64.b64encode(bytes(tx)).decode())
def cases():
 rows=[]
 for op in ['sweep_creator_fee','sweep_protocol_fee']:
  for mode in ['native','token','wsol']:
   base={'op':op,'curve_quote':str(Pubkey.default()) if mode=='native' else str(WSOL if mode=='wsol' else STABLE),'quote':str(WSOL if mode in ['native','wsol'] else STABLE)}
   rows += [dict(base,**c) for c in [{},{'creator_fee':0,'protocol_fee':0},{'destination_missing':True},{'source_missing':True},{'token22':True}]]
   for target in ['global','base_mint','quote_mint','bonding_curve','associated_quote_bonding_curve','recipient','associated_quote_recipient']:
    for patch in [{'owner':str(Pubkey.default())},{'length':0},{'bytes':[(0,'ff')]}]:rows.append(dict(base,patch={target:patch}))
   rows += [dict(base,wrong=a['name']) for a in next(i for i in PIDL['instructions'] if i['name']==op)['accounts'] if a['name']!='payer']
   rows += [dict(base,readonly=n) for n in ['payer','bonding_curve','recipient','associated_quote_bonding_curve','associated_quote_recipient']]
   rows += [dict(base,unsigned=True),dict(base,creator_fee=0,protocol_fee=0,destination_missing=True),dict(base,recipient=str(OTHER.pubkey()))]
   rows += [dict(base,patch={'bonding_curve':{'length':n}}) for n in [49,81,124,133,140,141,166,200]]
   rows += [dict(base,curve_lamports=n) for n in [1,12344,12345,1000000]]
   for target in ['associated_quote_bonding_curve','associated_quote_recipient']:
    for off,value in [(0,bytes(32).hex()),(32,bytes(32).hex()),(108,'00'),(108,'02')]:
     for fee in [0,12345]:rows.append(dict(base,creator_fee=fee,protocol_fee=fee,patch={target:{'bytes':[(off,value)]}}))
 normal=[101,3,77,22,91,9,55];reserved=[14,6,12,44,13,2,8];patches=[(41,bytes([99]*32).hex()),(162,b''.join(bytes([n]*32) for n in normal).hex()),(483,bytes([88]*32).hex()),(516,b''.join(bytes([n]*32) for n in reserved).hex())]
 for mayhem in [0,1]:
  for n in [99]+normal+[88]+reserved+[199]:rows.append(dict(op='sweep_protocol_fee',curve_quote=str(Pubkey.default()),recipient=str(Pubkey.from_bytes(bytes([n]*32))),patch={'global':{'bytes':patches},'bonding_curve':{'bytes':[(81,bytes([mayhem]).hex())]}}))
 rows += [dict(quote=str(STABLE),source_missing=True,destination_missing=True),dict(quote=str(STABLE),patch={'associated_quote_bonding_curve':{'bytes':[(0,'ff')]}},destination_missing=True)]
 rows += [dict(quote=str(WSOL) if native else str(STABLE),curve_quote=str(Pubkey.default()) if native else str(STABLE),creator_fee=2**64-1,protocol_fee=1) for native in [True,False]]
 for seq in [[1,2,3,4,5,6,7],[7,6,5,4,3,2,1],[4,4,4,4,4,4,4],[2,7,1,6,3,5,4]]:
  for n in sorted(set(seq)):
   rows.append(dict(op='sweep_protocol_fee',curve_quote=str(Pubkey.default()),recipient=str(Pubkey.from_bytes(bytes([n]*32))),patch={'global':{'bytes':[(41,bytes([99]*32).hex()),(162,b''.join(bytes([v]*32) for v in seq).hex())]}}))
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();rows=[]
 paths=[Path(__file__),a.candidate,ROOT/'evidence/original/pump/deployed.so',ROOT/'evidence/upstream/pump.json',Path(f.__file__),ROOT/'evidence/original/pump_fees/deployed.so',ROOT/'evidence/original/pump_amm/deployed.so']+[ROOT/f'evidence/dependencies/{n}/deployed.so' for n in ['spl_token','spl_token_2022','associated_token']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provenance={str(p):sha(p) for p in paths}
 for c in cases():
  o=run(c);n=run(c,a.candidate);diff=[k for k in ['error','before','after'] if o[k]!=n[k]]
  for k in ['return_data','inner_instructions']:
   if o['metadata'][k]!=n['metadata'][k]:diff.append(k)
  if [l for l in o['logs'] if l.startswith('Program data: ')] != [l for l in n['logs'] if l.startswith('Program data: ')]:diff.append('events')
  rows.append(dict(case=c,original=o,candidate=n,different_fields=diff))
 assert provenance=={str(p):sha(p) for p in paths}
 report={'scope':'Normally signed offline sweep_creator_fee and sweep_protocol_fee comparisons, captured dependencies, synthetic accounts. Full binary equality remains false.','provenance':provenance,'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['different_fields']],'cases':rows};a.output.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k] for k in ['case_count','mismatches']}))
 if report['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
