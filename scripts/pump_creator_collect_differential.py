#!/usr/bin/env python3
"""Offline normally signed creator collection differential fixtures."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import base64
import argparse,json,pathlib,gzip,hashlib
from solders.account import Account
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_differential_output import PumpReport
R=pathlib.Path(__file__).resolve().parents[1];J=json.load(open(R/'evidence/upstream/pump.json',encoding='utf-8'));P=Pubkey.from_string(J['address']);U=Keypair.from_seed(bytes([222])*32);PAY=Keypair.from_seed(bytes([223])*32);V=Pubkey.find_program_address([b'user_volume_accumulator',bytes(U.pubkey())],P)[0];E=Pubkey.find_program_address([b'__event_authority'],P)[0];D=bytes(next(a['discriminator'] for a in J['accounts'] if a['name']=='UserVolumeAccumulator'))
def execute(binary,mutation,amount=1000000):
 vm=LiteSVM().with_transaction_history(0).with_sigverify(True);vm.add_program_from_file(P,binary);vm.airdrop(PAY.pubkey(),10**12);vm.airdrop(U.pubkey(),10**12)
 creator=Pubkey.default() if mutation=='creator_zero' else P if mutation=='creator_program' else U.pubkey();vault=Pubkey.find_program_address([b'creator-vault',bytes(creator)],P)[0]
 if mutation=='pda_wrong':vault=Pubkey(bytes([224])*32)
 data=b'x' if mutation=='vault_data' else b'';owner=P if mutation=='vault_owner' else Pubkey.default();vm.set_account(vault,Account(amount,data,owner));keys=[creator,vault,Pubkey.default(),E,P];idef=next(i for i in J['instructions'] if i['name']=='collect_creator_fee');metas=[AccountMeta(k,False,a.get('writable',False)) for k,a in zip(keys,idef['accounts'])]
 for i,a in enumerate(idef['accounts']):
  if mutation==a['name']+'_readonly':metas[i]=AccountMeta(keys[i],False,False)
  if mutation==a['name']+'_wrong':metas[i]=AccountMeta(Pubkey.default(),False,metas[i].is_writable)
 if mutation.startswith('missing_'):metas=metas[:int(mutation[8:])]
 creator_before=vm.get_account(creator)
 tx=Transaction.new_signed_with_payer([Instruction(P,bytes(idef['discriminator'])+(b'\xff' if mutation=='trailing_data' else b''),metas)],PAY.pubkey(),[PAY],vm.latest_blockhash());verified=tx.verify_with_results();assert all(verified);r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;a=vm.get_account(vault);c=vm.get_account(creator)
 return {'transaction_base64':base64.b64encode(bytes(tx)).decode(),'signature_verification':verified,'error':str(r.err()) if failed else None,'account':json.loads(a.to_json()) if a else None,'creator':({'lamports_delta':c.lamports-creator_before.lamports,'executable_data_unchanged':c.data==creator_before.data} if c.executable else json.loads(c.to_json())) if c else None,'payer_lamports':vm.get_account(PAY.pubkey()).lamports,'logs':meta.logs(),'events':[s[14:] for s in meta.logs() if s.startswith('Program data: ')],'inner_instructions':json.loads(meta.to_json())['inner_instructions']}

def cases():
 return [dict(mutation=m,amount=a) for m in ['none','pda_wrong','event_authority_wrong','program_wrong','creator_readonly','creator_vault_readonly','trailing_data','creator_zero','creator_program','vault_owner','vault_data','system_program_wrong']+['missing_'+str(i) for i in range(5)] for a in [0,1,890879,890880,890881,1000000,1000000000]]

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 publisher=PumpReport(a.output,R,a.candidate,__file__)
 original=R/'evidence/original/pump/deployed.so';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 provenance={str(p):sha(p) for p in [original,a.candidate,pathlib.Path(__file__),R/'evidence/upstream/pump.json']};rows=[]
 for c in cases():
  o=execute(original,**c);n=execute(a.candidate,**c);diff=[k for k in o if k!='logs' and o[k]!=n[k]];rows.append(dict(c,different_fields=diff,original=o,candidate=n))
 assert provenance=={str(p):sha(p) for p in [original,a.candidate,pathlib.Path(__file__),R/'evidence/upstream/pump.json']}
 report={'scope':'Synthetic offline normally signed transactions; full binaries are unequal. No captured binary used as compiler input.','original_sha256':provenance[str(original)],'candidate_sha256':provenance[str(a.candidate)],'provenance':provenance,'case_count':len(rows),'mismatches':[i for i,c in enumerate(rows) if c['different_fields']],'cases':rows}
 publisher.write(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(json.dumps({k:report[k] for k in ['case_count','mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
