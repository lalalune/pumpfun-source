#!/usr/bin/env python3
"""Offline original-vs-recovered Pump administrative instruction differential tests."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse, base64, hashlib, json, pathlib
from pump_differential_output import PumpReport
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = pathlib.Path(__file__).resolve().parents[1]
IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PROGRAM = Pubkey.from_string(IDL['address'])
GLOBAL = Pubkey.find_program_address([b'global'], PROGRAM)[0]
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
AUTHORITY = Keypair.from_seed(bytes([201]) * 32)
PAYER = Keypair.from_seed(bytes([203]) * 32)
OUTSIDER = Keypair.from_seed(bytes([202]) * 32)
CAPTURE = next(x for x in json.loads((ROOT / 'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name'] == 'pump')
DATA = bytearray(base64.b64decode(CAPTURE['data_base64']))
DATA[9:41] = bytes(AUTHORITY.pubkey())
from solders.clock import Clock
ORIGINAL=ROOT/'evidence/original/pump/deployed.so'
IX=next(i for i in IDL['instructions'] if i['name']=='set_params')


def args(c):
 values={'initial_virtual_token_reserves':1073000000000000,'initial_virtual_sol_reserves':30000000000,'initial_real_token_reserves':793100000000000,'token_total_supply':1000000000000000,'fee_basis_points':100,'withdraw_authority':str(OUTSIDER.pubkey()),'enable_migrate':True,'pool_migration_fee':15000001,'creator_fee_basis_points':50,'set_creator_authority':str(OUTSIDER.pubkey()),'admin_set_creator_authority':str(OUTSIDER.pubkey())};values.update(c.get('args',{}));out=b''
 for a in IX['args']:
  v=values[a['name']];out+=int(v).to_bytes(8,'little') if a['type']=='u64' else bytes(Pubkey.from_string(v)) if a['type']=='pubkey' else bytes([int(v)])
 return out

def run(c,binary=ORIGINAL):
 vm=LiteSVM().with_transaction_history(0).with_sigverify(True);vm.add_program_from_file(PROGRAM,binary);vm.set_clock(Clock(1000,0,0,0,1700000000))
 for k in [PAYER,AUTHORITY,OUTSIDER]:vm.set_account(k.pubkey(),Account(10**12,b'',Pubkey.default()))
 data=bytearray(DATA)
 for off,h in c.get('patches',[]):data[off:off+len(bytes.fromhex(h))]=bytes.fromhex(h)
 data=data[:c.get('length',len(data))];key=Pubkey.from_bytes(bytes([91])*32) if c.get('wrong')=='global' else GLOBAL
 vm.set_account(key,Account(10**10,bytes(data),Pubkey.from_string(c.get('owner',str(PROGRAM)))))
 authority=OUTSIDER if c.get('wrong')=='authority' else AUTHORITY
 keys=[key,authority.pubkey(),EVENT,PROGRAM]
 if c.get('wrong') in ['event_authority','program']:keys[['global','authority','event_authority','program'].index(c['wrong'])]=Pubkey.from_bytes(bytes([92])*32)
 metas=[AccountMeta(k,a.get('signer',False) and not c.get('unsigned'),a.get('writable',False) and a['name']!=c.get('readonly')) for k,a in zip(keys,IX['accounts'])];metas=metas[:c.get('accounts',len(metas))]
 for i in range(c.get('remaining_count',8)):
  k=Pubkey.from_string(c['recipients'][i]) if 'recipients' in c else Pubkey.from_bytes(bytes([100+i])*32)
  if not vm.get_account(k) or not vm.get_account(k).executable:vm.set_account(k,Account(c.get('recipient_lamports',10**9),bytes(c.get('recipient_length',0)),Pubkey.default()))
  keys.append(k);metas.append(AccountMeta(k,False,False))
 payload=bytes(IX['discriminator'])+args(c);payload=payload[:c.get('payload_length',len(payload))]+bytes.fromhex(c.get('trailing',''))
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,payload,metas)],PAYER.pubkey(),[PAYER]+([authority] if any(m.is_signer for m in metas) else []),vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():return {str(k):json.loads(vm.get_account(k).to_json()) if vm.get_account(k) and not vm.get_account(k).executable else None for k in set(keys+[PAYER.pubkey(),OUTSIDER.pubkey()])}
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return dict(error=str(r.err()) if fail else None,before=before,after=snap(),events=[l for l in m.logs() if l.startswith('Program data: ')],inner=raw['inner_instructions'],returns=raw['return_data'],logs=m.logs(),signature_verification=True,transaction_base64=base64.b64encode(bytes(tx)).decode())

def cases():
 rows=[{}]
 for a in IX['args']:
  values=[0,1,999,1000,1001,10000,2**64-1] if a['type']=='u64' else [str(Pubkey.default()),str(AUTHORITY.pubkey())] if a['type']=='pubkey' else [False,True,2]
  rows += [{'args':{a['name']:v}} for v in values]
 rows += [{'remaining_count':n} for n in [0,1,7,8,9]]+[{'recipient_lamports':n} for n in [0,1,890879,890880,890881]]
 for seq in [[100]*8,list(range(107,99,-1)),[107,100,101,102,103,104,105,106],[103,100,101,102,103,104,105,106]]:rows.append({'recipients':[str(Pubkey.from_bytes(bytes([n])*32)) for n in seq]})
 rows += [{'recipients':[str(Pubkey.default())]+[str(Pubkey.from_bytes(bytes([n])*32)) for n in range(101,108)]}]
 rows += [{'wrong':n} for n in ['global','authority','event_authority','program']]+[{'readonly':n} for n in ['global','authority']]+[{'unsigned':True}]
 rows += [{'length':n} for n in [0,7,8,40,418,740,1087,1088,1200]]+[{'owner':str(Pubkey.default())}]
 rows += [{'patches':[(n,'02')]} for n in [8,145,450,515,740,1045,1086]]+[{'patches':[(0,'ff')]},{'patches':[(1190,'ab'*32)]}]
 rows += [{'payload_length':n} for n in [0,7,8,15,71,72,80,160,169]]+[{'trailing':'ff'}]
 for v,sol,real in [(10,10,3),(11,10,3),(10,10,5),(100,100,1),(2,1,1),(2**64-1,2**64-1,2**64-2)]:
  for fee in [0,1,3,4,5,10]:rows.append({'args':{'initial_virtual_token_reserves':v,'initial_virtual_sol_reserves':sol,'initial_real_token_reserves':real,'token_total_supply':2**64-1,'pool_migration_fee':fee}})
 invalid=[{'token_total_supply':0},{'initial_virtual_token_reserves':0},{'fee_basis_points':1001},{'withdraw_authority':str(Pubkey.default())},{'pool_migration_fee':2**64-1},{'creator_fee_basis_points':1001}]
 for i,a in enumerate(invalid):
  for b in invalid[i+1:]:rows.append({'args':dict(a,**b)})
 rows += [{'args':a,'remaining_count':0} for a in invalid]
 rows += [{'recipients':[str(k) for k in sorted([PROGRAM]+[Pubkey.from_bytes(bytes([n])*32) for n in range(101,108)],key=bytes)]},{'args':{'fee_basis_points':1000,'creator_fee_basis_points':1000}}]
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();output=PumpReport(a.output,ROOT,a.candidate,__file__);paths=[pathlib.Path(__file__),ORIGINAL,a.candidate,ROOT/'evidence/upstream/pump.json',ROOT/'research/imported-lab/analysis/pump_fun/config-snapshot.json'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();provenance={str(p):sha(p) for p in paths};rows=[]
 for c in cases():
  o=run(c);n=run(c,a.candidate);diff=[k for k in ['error','before','after','events','inner','returns'] if o[k]!=n[k]];rows.append(dict(case=c,original=o,candidate=n,different_fields=diff))
 assert provenance=={str(p):sha(p) for p in paths}
 report={'case_count':len(rows),'provenance':provenance,'mismatches':[i for i,r in enumerate(rows) if r['different_fields']],'cases':rows};output.write((json.dumps(report,indent=2)+'\n').encode("utf-8"));print({k:report[k] for k in ['case_count','mismatches']})
 if report['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
