"""Local captured-dependency sell-v3 fixture; initialization performs no RPC."""
import json,base64,pathlib,struct
from solders.account import Account
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.instruction import Instruction,AccountMeta
from solders.keypair import Keypair
from solders.transaction_metadata import FailedTransactionMetadata
R=pathlib.Path(__file__).resolve().parents[1]
# Every file read while constructing this shared fixture or its program set.
# Report writers must protect these paths as well as their public candidate.
REPORT_INPUTS = (
 pathlib.Path(__file__),
 R/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
 *(R/'evidence'/group/name/filename
   for group,names in [('original',('pump','pump_fees')),
                       ('dependencies',('spl_token','spl_token_2022','associated_token'))]
   for name in names for filename in ('capture.json','deployed.so')),
)
x=json.load(open(R/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',encoding='utf-8'))
s=x['steps'][4]
t=Transaction.from_bytes(base64.b64decode(s['transaction_base64']));msg=t.message
vm=LiteSVM().with_transaction_history(0)
for name in ['pump','pump_fees']:
 cap=json.load(open(R/f'evidence/original/{name}/capture.json',encoding='utf-8'));vm.add_program_from_file(Pubkey.from_string(cap['program']),R/f'evidence/original/{name}/deployed.so')
for name in ['spl_token','spl_token_2022','associated_token']:
 cap=json.load(open(R/f'evidence/dependencies/{name}/capture.json',encoding='utf-8'));vm.add_program_from_file(Pubkey.from_string(cap['program']),R/f'evidence/dependencies/{name}/deployed.so')
for k in msg.account_keys:
 if vm.get_account(k) is None: vm.set_account(k, Account(10**10,b'',Pubkey.default()))
for name,r in s['before'].items():
 if r:vm.set_account(Pubkey.from_string(x['accounts'][name]),Account(r['lamports'],base64.b64decode(r['data_base64']),Pubkey.from_string(r['owner'])))
ixs=[];n=len(msg.account_keys);h=msg.header
for ix in msg.instructions:
 metas=[]
 for j in ix.accounts:
  signer=j<h.num_required_signatures
  writable=j < (h.num_required_signatures-h.num_readonly_signed_accounts) if signer else j < n-h.num_readonly_unsigned_accounts
  metas.append(AccountMeta(msg.account_keys[j],signer,writable))
 ixs.append(Instruction(msg.account_keys[ix.program_id_index],ix.data,metas))
