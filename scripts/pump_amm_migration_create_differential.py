#!/usr/bin/env python3
"""Saved signed migration replay using original Pump and captured dependencies."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from solders.litesvm import LiteSVM
from pump_amm_reusable_harness import pin_program
PUMP=Pubkey.from_string(json.load(open('evidence/upstream/pump.json', encoding='utf-8'))['address']);ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
p=json.load(open('research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json'))
def run_migration(candidate=None,label='missing_boost',overrides=None):
 row=p[label];tx=Transaction.from_bytes(base64.b64decode(row['transaction_base64']));assert all(tx.verify_with_results())
 vm=LiteSVM().with_transaction_history(0).with_blockhash_check(False);vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,path in [(PROGRAM,candidate or pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),(PUMP,ROOT/'evidence/original/pump/deployed.so'),(TOKEN,ROOT/'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,ROOT/'evidence/dependencies/spl_token_2022/deployed.so'),(ATA,ROOT/'evidence/dependencies/associated_token/deployed.so')]:vm.add_program_from_file(pid,path)
 ix=tx.message.instructions[-1];spec=next(x for x in json.load(open('evidence/upstream/pump.json', encoding='utf-8'))['instructions'] if x['name']=='migrate_v2');keys={a['name']:tx.message.account_keys[i] for a,i in zip(spec['accounts'],ix.accounts)}
 aliases={'mint':'base_mint','curve':'bonding_curve','curve_base':'associated_base_bonding_curve','pool_authority_mint':'pool_authority_mint_account','pool_authority_quote':'pool_authority_quote_account','pool_base':'pool_base_token_account','pool_quote':'pool_quote_token_account','user_lp':'user_pool_token_account'}
 for name,account in row['before'].items():
  key=keys.get(aliases.get(name,name))
  if name in ['boost_authority','boost_vault']:key=Pubkey.from_string(p[name])
  if key is not None and account:vm.set_account(key,Account(account['lamports'],base64.b64decode(account['data_base64']),Pubkey.from_string(account['owner'])))
 q=f['accounts']['quote_mint'];vm.set_account(keys['quote_mint'],Account(q['lamports'],base64.b64decode(q['data_base64']),Pubkey.from_string(q['owner'])))
 if overrides:overrides(vm,keys)
 r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 states={}
 for key in tx.message.account_keys:
  a=vm.get_account(key)
  if a is None or not a.executable:states[str(key)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'states':states,'error':str(r.err()) if failed else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();args.candidate=pin_program(args.candidate);rows=[]
 def test(label,curve=None,config=None):
  def mutation(vm,k):
   for key,changes in [(k['bonding_curve'],curve or []),(k['amm_global_config'],config or [])]:
    a=vm.get_account(key);d=bytearray(a.data)
    for off,value,size in changes:d[off:off+size]=value.to_bytes(size,'little')
    vm.set_account(key,Account(a.lamports,bytes(d),a.owner))
  x=run_migration(overrides=mutation);y=run_migration(args.candidate,overrides=mutation)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diff=[k for k in x if x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'mismatched_fields':diff,'match':not diff})
 test('saved-signed-missing-boost')
 for mayhem in [0,1]:
  for offset,values,size in [(115,[0,1,100,10000,2**64-1],8),(123,[0,1],1),(82,[0,1],1),(124,[0,1],1)]:
   for value in values:test('canonical-curve='+str((mayhem,offset,value)),curve=[(81,mayhem,1),(offset,value,size)])
 for off,values,size in [(417,[0,1],1),(642,[0,1],1),(940,[0,1],1),(941,[0,1,10000,2**64-1],8),(56,[0,1,2,255],1)]:
  for value in values:test('canonical-config='+str((off,value)),curve=[(81,1,1),(82,1,1),(115,100,8),(123,1,1)],config=[(off,value,size)])
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'Original signed saved Pump migrate_v2 transactions through genuine Pump PDA signer. Historical blockhash freshness disabled; signature verification retained. Synthetic before-account mutations documented per case. Missing-boost cases roll back after successful create_pool; mayhem cases commit and bypass boost. No source or whole-program equality claim.','candidate_sha256':sha(args.candidate),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if not r['match']],'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)
if __name__=='__main__':main()
