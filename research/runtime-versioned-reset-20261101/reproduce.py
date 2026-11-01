"""Real signed local transfers through the reusable AMM VM API."""
if not __debug__:
 raise SystemExit('research evidence requires normal Python (assertions enabled)')
def signatures_verified(tx):
 """True only for every signature required by the message header."""
 required = tx.message.header.num_required_signatures
 if required <= 0 or len(tx.signatures) != required:return False
 results = tx.verify_with_results()
 return bool(results) and len(results) == required and all(results)

import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();repo=a.repo.resolve();sys.path.insert(0,str(repo/'scripts'))
os.environ['PUMP_AMM_FRESH_VM']='0'
import pump_amm_reusable_harness as reusable
from pump_amm_admin_differential import PAYER,OUTSIDER,EVENT
from solders.address_lookup_table_account import AddressLookupTableAccount,LookupTableMeta,ADDRESS_LOOKUP_TABLE_ID
from solders.account import Account
from solders.pubkey import Pubkey
from solders.instruction import Instruction,AccountMeta
from solders.message import MessageV0,MessageAddressTableLookup
from solders.transaction import VersionedTransaction,Transaction
from solders.system_program import transfer,TransferParams
from solders.transaction_metadata import FailedTransactionMetadata
binary=repo/'evidence/original/pump_amm/deployed.so';table_key=Pubkey(bytes([73])*32)
rows=[]
for kind in ('legacy','v0-static','v0-alt','v0-alt-readonly','v0-alt-missing','v0-alt-invalid','v0-alt-index','v0-alt-owner'):
 reusable._cached.clear() # each scenario starts with an independent production Harness
 h=reusable.acquire_harness(binary);vm=h.vm;vm.warp_to_slot(1)
 def snapshot():return {str(key):json.loads(vm.get_account(key).to_json()) for key in (PAYER.pubkey(),OUTSIDER.pubkey(),EVENT)}
 before=snapshot();ix=transfer(TransferParams(from_pubkey=PAYER.pubkey(),to_pubkey=OUTSIDER.pubkey(),lamports=123))
 if kind=='v0-alt-readonly':ix=Instruction(ix.program_id,ix.data,[ix.accounts[0],AccountMeta(OUTSIDER.pubkey(),False,False)])
 if kind.startswith('v0-alt'):
  raw=((1).to_bytes(4,'little')+bytes(LookupTableMeta())).ljust(56,b'\0')+bytes(OUTSIDER.pubkey())
  if kind=='v0-alt-invalid':raw=b'\x01'
  if kind!='v0-alt-missing':vm.set_account(table_key,Account(10**9,raw,Pubkey.default() if kind=='v0-alt-owner' else ADDRESS_LOOKUP_TABLE_ID))
  tables=[AddressLookupTableAccount(table_key,[OUTSIDER.pubkey()])]
 else:tables=[]
 if kind=='legacy':tx=Transaction.new_signed_with_payer([ix],PAYER.pubkey(),[PAYER],vm.latest_blockhash())
 else:
  message=MessageV0.try_compile(PAYER.pubkey(),[ix],tables,vm.latest_blockhash())
  if kind=='v0-alt-index':message=MessageV0(message.header,message.account_keys,message.recent_blockhash,message.instructions,[MessageAddressTableLookup(table_key,b'\x01',b'')])
  tx=VersionedTransaction(message,[PAYER])
 verified=signatures_verified(tx)
 if not verified:raise AssertionError('transaction signature verification failed')
 result=vm.send_transaction(tx);error=str(result.err()) if isinstance(result,FailedTransactionMetadata) else None;after=snapshot()
 reused=reusable.acquire_harness(binary);assert reused is h;reset=snapshot()
 rows.append({'kind':kind,'error':error,'signatures_verified':verified,'recipient_before':before[str(OUTSIDER.pubkey())]['lamports'],'recipient_after':after[str(OUTSIDER.pubkey())]['lamports'],'recipient_reset':reset[str(OUTSIDER.pubkey())]['lamports'],'complete_watched_accounts_restored':reset==before})
 print(rows[-1],flush=True)
a.output.write_text(json.dumps({'base':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'captured_amm_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'rows':rows},indent=2)+'\n')
