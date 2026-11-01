"""Bounded native/legacy fixtures via captured AMM's genuine CPI signer.

Synthetic local accounts; ordinary test-owned verified outer signatures.
No live traffic, fabricated PDA signatures or executable modification.
"""
if not __debug__:
    raise SystemExit('research evidence requires normal Python (assertions enabled)')

from pathlib import Path
import argparse,hashlib,json,sys
P=Path(__file__).resolve().parent;ROOT=next(p for p in P.parents if (p/'evidence/original/pump/deployed.so').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
import pump_amm_multi_hop_differential as h
from pump_amm_admin_differential import Harness

def require_signed(tx):
    """Require the complete nonempty header signature vector, also under -O."""
    required = tx.message.header.num_required_signatures
    if required <= 0 or len(tx.signatures) != required:
        raise AssertionError('incomplete transaction signature vector')
    results = tx.verify_with_results()
    if not results or len(results) != required or not all(results):
        raise AssertionError('transaction signature verification failed')


def legacy_curve(sell,mutation=None):
 def setup(vm,metas):
  h.curve_route(sell)(vm,metas)
  # The fixture is deliberately re-owned and truncated to the ordinary legacy
  # mint/account layouts. This is synthetic state, not a historical creation.
  mint=vm.vm.get_account(h.CM)
  vm.vm.set_account(h.CM,h.Account(mint.lamports,bytes(mint.data[:82]),h.TOKEN))
  vault=h.Pubkey.find_program_address([bytes(h.CURVE),bytes(h.TOKEN),bytes(h.CM)],h.ATA)[0]
  old=vm.vm.get_account(h.CB)
  vm.vm.set_account(vault,h.Account(old.lamports,bytes(old.data[:165]),h.TOKEN))
  user=vm.vm.get_account(h.CU)
  vm.vm.set_account(h.CU,h.Account(user.lamports,bytes(user.data[:165]),h.TOKEN))
  metas[19]=h.AccountMeta(vault,False,True)
  if mutation:mutation(vm,metas)
 return setup

def invoke(sell,amount,candidate=None,mutation=None,limit=1):
 # A fresh VM on every side avoids stale nested-program caches. Exactly one
 # chosen Pump ELF is loaded; the AMM and dependency ELFs are always captured.
 vm=Harness(ROOT/'evidence/original/pump_amm/deployed.so')
 vm.vm.set_clock(h.Clock(100,1234567890,0,0,1234567890))
 programs=[(h.TOKEN,ROOT/'evidence/dependencies/spl_token/deployed.so'),(h.TOKEN22,ROOT/'evidence/dependencies/spl_token_2022/deployed.so'),(h.FEES,ROOT/'evidence/original/pump_fees/deployed.so'),(h.ATA,ROOT/'evidence/dependencies/associated_token/deployed.so'),(h.PUMP,candidate or ROOT/'evidence/original/pump/deployed.so')]
 for pid,path in programs:vm.vm.add_program_from_file(pid,path)
 for row in h.f['accounts'].values():vm.vm.set_account(h.Pubkey.from_string(row['address']),h.Account(row['lamports'],h.base64.b64decode(row['data_base64']),h.Pubkey.from_string(row['owner'])))
 raw=bytearray(h.RAW);raw[56]=0;vm.vm.set_account(h.CONFIG_KEY,h.Account(h.CONFIG['lamports'],bytes(raw),h.PROGRAM))
 for key,mint,native in [(h.userbase,h.base,False),(h.userquote,h.quote,True)]:vm.vm.set_account(key,h.Account(10**15+2039280 if native else 10**9,h.token(mint,h.PAYER.pubkey(),10**15,native),h.TOKEN))
 vm.vm.set_account(h.volume,h.Account(0,b'',h.Pubkey.default()))
 for key in [h.PUMP_GLOBAL,h.PUMP_FEES,h.PUMP_EVENT]:vm.vm.set_account(key,h.Account(10**9,b'',h.Pubkey.default()))
 ix=next(i for i in h.IDL['instructions']if i['name']=='multi_hop_swap')
 keys=[h.PAYER.pubkey(),h.userbase if sell else h.userquote,h.userquote if sell else h.userbase,h.CONFIG_KEY,h.feeconfig,h.volume,h.buyback,h.TOKEN,h.TOKEN22,h.Pubkey.default(),h.EVENT,h.PROGRAM,h.PUMP,h.PUMP_GLOBAL,h.PUMP_FEES,h.PUMP_EVENT]
 metas=[h.AccountMeta(k,bool(a.get('signer')),bool(a.get('writable')))for k,a in zip(keys,ix['accounts'])]
 legacy_curve(sell,mutation)(vm,metas)
 def snapshot():
  out={}
  for key in sorted(set([m.pubkey for m in metas]+[h.PAYER.pubkey()]),key=str):
   account=vm.vm.get_account(key)
   if not account or not account.executable:out[str(key)]=None if not account else {'lamports':account.lamports,'owner':str(account.owner),'data_hex':bytes(account.data).hex()}
  return out
 before=snapshot();data=bytes(ix['discriminator'])+h.struct.pack('<QQ',amount,limit)
 tx=h.Transaction.new_signed_with_payer([h.Instruction(h.PROGRAM,data,metas)],h.PAYER.pubkey(),[h.PAYER],vm.vm.latest_blockhash())
 require_signed(tx)
 result=vm.vm.send_transaction(tx);failed=isinstance(result,h.FailedTransactionMetadata);meta=result.meta()if failed else result;encoded=json.loads(meta.to_json())
 return {'error':str(result.err())if failed else None,'logs':meta.logs(),'events':[line for line in meta.logs()if line.startswith('Program data: ')],'inner':encoded['inner_instructions'],'return_data':encoded.get('return_data'),'before':before,'after':snapshot(),'transaction_base64':h.base64.b64encode(bytes(tx)).decode(),'program_sha256':{str(pid):hashlib.sha256(path.read_bytes()).hexdigest()for pid,path in programs},'fresh_vm':True}

def compare(a,b):
 return [k for k in ['error','events','inner','return_data','before','after'] if a[k]!=b[k]]

def mutate(index,offset,value):
 def action(vm,metas):
  key=metas[index].pubkey;account=vm.vm.get_account(key);data=bytearray(account.data);data[offset:offset+len(value)]=value
  vm.vm.set_account(key,h.Account(account.lamports,bytes(data),account.owner))
 return action

def readonly(index):
 def action(vm,metas):
  old=metas[index];metas[index]=h.AccountMeta(old.pubkey,old.is_signer,False)
 return action

def fixture_cases():
 for sell in [False,True]:
  for amount in [0,1,2,3,10,99,100,101,10000,1000000,1000000000,10000000000]:
   yield f'native-legacy-{sell}-{amount}',sell,amount,None,1
  for amount in [100,1000000000]:
   for limit in [0,2**64-1]:yield f'slippage-{sell}-{amount}-{limit}',sell,amount,None,limit
  for label,mutation in [
   ('complete',mutate(18,48,b'\1')),('mayhem',mutate(18,81,b'\1')),
   ('cashback',mutate(18,82,b'\1')),('quote-mismatch',mutate(18,83,bytes([7])*32)),
   ('curve-readonly',readonly(18)),('base-vault-readonly',readonly(19)),('quote-vault-readonly',readonly(20)),
   ('base-vault-mint',mutate(19,0,bytes([7])*32)),('source-balance-zero',mutate(1,64,bytes(8))),
   ('fee-discriminator',mutate(14,0,bytes(8))),('global-discriminator',mutate(13,0,bytes(8))),
   ('buyback-owner',mutate(6,32,bytes([7])*32)),
  ]:yield f'{label}-{sell}',sell,1000000000,mutation,1

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 cases=[]
 for name,sell,amount,mutation,limit in fixture_cases():
  original=invoke(sell,amount,mutation=mutation,limit=limit)
  candidate=invoke(sell,amount,args.candidate.resolve(),mutation,limit) if args.candidate else None
  mismatches=compare(original,candidate) if candidate else []
  cases.append({'case':name,'mismatches':mismatches,'original':original,'candidate':candidate})
 result={'scope':__doc__,'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest()if args.candidate else None,'original_pump_sha256':hashlib.sha256((ROOT/'evidence/original/pump/deployed.so').read_bytes()).hexdigest(),'captured_amm_sha256':hashlib.sha256((ROOT/'evidence/original/pump_amm/deployed.so').read_bytes()).hexdigest(),'case_count':len(cases),'passed':sum(not r['mismatches']for r in cases)if args.candidate else None,'cases':cases}
 args.output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({'cases':len(cases),'passed':result['passed'],'results':[(r['case'],r['original']['error'],r['mismatches'])for r in cases]},indent=2))

 raise SystemExit(result['passed'] != len(cases))
