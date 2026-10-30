if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,json,pathlib,gzip,hashlib
from solders.account import Account
from solders.instruction import AccountMeta,Instruction
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from pump_amm_reusable_harness import pin_program
R=pathlib.Path(__file__).resolve().parents[1];J=json.load(open(R/'evidence/upstream/pump.json',encoding='utf-8'));P=Pubkey.from_string(J['address']);U=Keypair.from_seed(bytes([222])*32);PAY=Keypair.from_seed(bytes([223])*32);V=Pubkey.find_program_address([b'user_volume_accumulator',bytes(U.pubkey())],P)[0];E=Pubkey.find_program_address([b'__event_authority'],P)[0];D=bytes(next(a['discriminator'] for a in J['accounts'] if a['name']=='UserVolumeAccumulator'))
def execute(binary,name,mutation):
 vm=LiteSVM().with_transaction_history(0);vm.add_program_from_file(P,binary);vm.airdrop(PAY.pubkey(),10**12);vm.airdrop(U.pubkey(),10**12)
 key=V if mutation!='pda_wrong' else Pubkey(bytes([224])*32);user=Pubkey.default() if mutation=='user_zero' else U.pubkey()
 if mutation=='user_zero':key=Pubkey.find_program_address([b'user_volume_accumulator',bytes(user)],P)[0]
 if name.startswith('close') or mutation.startswith('existing_') or mutation in ['already_exists','prefunded','prefunded_rent']:
  data=bytearray((D+bytes(U.pubkey())+bytes(97)));owner=P
  mutation=mutation.removeprefix('existing_')
  offsets={'needs_claim':40,'unclaimed':41,'claimed':49,'volume':57,'last_timestamp':65,'has_claimed':73,'cashback':74,'stable_cashback':90}
  if mutation in offsets:data[offsets[mutation]]=1
  if mutation=='bool_invalid':data[40]=2
  if mutation=='stored_user_wrong':data[8:40]=bytes(32)
  if mutation=='wrong_discriminator':data[0]^=1
  if mutation=='wrong_owner':owner=Pubkey.default()
  if mutation.startswith('length_'):data=data[:int(mutation[7:])]
  if mutation in ['prefunded','prefunded_rent']:data=bytearray();owner=Pubkey.default()
  vm.set_account(key,Account(1 if mutation=='prefunded' else 1844400,bytes(data),owner))
 keys=[PAY.pubkey(),user,key,Pubkey.default(),E,P] if name.startswith('init') else [user,key,E,P];idef=next(i for i in J['instructions'] if i['name']==name)
 metas=[AccountMeta(k,a.get('signer',False),a.get('writable',False)) for k,a in zip(keys,idef['accounts'])]
 for i,a in enumerate(idef['accounts']):
  if mutation==a['name']+'_readonly':metas[i]=AccountMeta(keys[i],metas[i].is_signer,False)
  if mutation==a['name']+'_unsigned':metas[i]=AccountMeta(keys[i],False,metas[i].is_writable)
  if mutation==a['name']+'_wrong':metas[i]=AccountMeta(Pubkey.default(),metas[i].is_signer,metas[i].is_writable)
 if mutation.startswith('missing_'):metas=metas[:int(mutation[8:])]
 fee_payer=U.pubkey() if mutation=='payer_unsigned' else PAY.pubkey()
 signerkeys={m.pubkey for m in metas if m.is_signer}|{fee_payer};signers=[k for k in [PAY,U] if k.pubkey() in signerkeys]
 payload=bytes(idef['discriminator'])+(b'\xff' if mutation=='trailing_data' else b'')
 tx=Transaction.new_signed_with_payer([Instruction(P,payload,metas)],fee_payer,signers,vm.latest_blockhash());r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r;a=vm.get_account(key)
 return {'error':str(r.err()) if failed else None,'account':json.loads(a.to_json()) if a else None,'payer_lamports':vm.get_account(PAY.pubkey()).lamports,'user_lamports':vm.get_account(U.pubkey()).lamports,'logs':meta.logs(),'events':[s[14:] for s in meta.logs() if s.startswith('Program data: ')],'inner_instructions':json.loads(meta.to_json())['inner_instructions']}
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.candidate=pin_program(a.candidate);cases=[]
common=['none','pda_wrong','event_authority_wrong','program_wrong','user_volume_accumulator_readonly','trailing_data']
for name,mutations in [('init_user_volume_accumulator',common+['existing_'+m for m in ['stored_user_wrong','needs_claim','unclaimed','claimed','cashback','stable_cashback','wrong_owner','wrong_discriminator','length_106','length_136']]+['user_zero','already_exists','prefunded','prefunded_rent','payer_readonly','payer_unsigned','system_program_wrong']+['missing_'+str(i) for i in range(6)]),('close_user_volume_accumulator',common+['stored_user_wrong','needs_claim','unclaimed','claimed','volume','last_timestamp','has_claimed','cashback','stable_cashback','bool_invalid','wrong_owner','wrong_discriminator','user_readonly','user_unsigned']+['length_'+str(n) for n in [0,8,40,73,74,82,90,98,105,106,107,136,137]]+['missing_'+str(i) for i in range(4)])]:
 for m in mutations:
  o=execute(R/'evidence/original/pump/deployed.so',name,m);n=execute(a.candidate,name,m);diff=[k for k in o if k!='logs' and o[k]!=n[k]];cases.append({'instruction':name,'mutation':m,'different_fields':diff,'original':o,'candidate':n})
sources={str(p.relative_to(R/'programs/pump')):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((R/'programs/pump').rglob('*')) if p.is_file() and 'target' not in p.parts and (p.suffix=='.rs' or p.name in ['Cargo.toml','Cargo.lock'])}
report={'scope':'Two volume account lifecycle handlers; synthetic local signed transactions compare complete account state, balances, errors, raw events and inner CPI instructions.', 'candidate_sha256':hashlib.sha256(a.candidate.read_bytes()).hexdigest(),'original_sha256':hashlib.sha256((R/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'source_sha256':sources,'case_count':len(cases),'mismatches':[i for i,c in enumerate(cases) if c['different_fields']],'cases':cases};a.output.write_bytes(gzip.compress(json.dumps(report,indent=2).encode(),mtime=0));print(len(cases),[(c['instruction'],c['mutation'],c['different_fields'],c['original']['error'],c['candidate']['error']) for c in cases if c['different_fields']])
assert not report['mismatches'], report['mismatches']
