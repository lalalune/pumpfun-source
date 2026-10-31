#!/usr/bin/env python3
"""Local boost initialization and authentic signed migration differential."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys
sys.path.insert(0,'scripts')
from pump_amm_create_differential import *
from pump_amm_reusable_harness import pin_program
from pump_differential_output import PumpReport
def boost(candidate=None,overrides=None,fixture=False):
 r=create();h=Harness(candidate or pin_program(ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 for k,a in r['states'].items():
  if a:h.vm.set_account(Pubkey.from_string(k),Account(a['lamports'],bytes.fromhex(a['data']),Pubkey.from_string(a['owner'])))
 pool=next(Pubkey.from_string(k) for k,a in r['states'].items() if a and a['owner']==str(PROGRAM) and len(bytes.fromhex(a['data']))==287);d=h.vm.get_account(pool).data
 if fixture:
  for row in f['accounts'].values():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
  pool=Pubkey.from_string(f['pool']);d=h.vm.get_account(pool).data
 vaultbase=Pubkey.from_bytes(d[139:171]);vaultquote=Pubkey.from_bytes(d[171:203]);authority=Pubkey.find_program_address([b"boost_vault",bytes(pool)],PROGRAM)[0];vault=Pubkey.find_program_address([bytes(authority),bytes(TOKEN),bytes(quote)],ATA)[0]
 keys=[pool,CONFIG_KEY,PAYER.pubkey(),base,quote,vaultbase,vaultquote,authority,vault,TOKEN,Pubkey.default(),ATA,EVENT,PROGRAM];ix=next(x for x in IDL['instructions'] if x['name']=='init_boost');metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,bytes(ix['discriminator']),metas)],PAYER.pubkey(),[PAYER],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);meta=r.meta() if fail else r
 states={}
 for m in metas:
  a=h.vm.get_account(m.pubkey)
  if a is None or not a.executable:states[str(m.pubkey)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'states':states,'error':str(r.err()) if fail else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}

PUMP_IDL_PATH=pathlib.Path('evidence/upstream/pump.json').resolve()
MIGRATION_FIXTURE_PATH=pathlib.Path('research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json').resolve()
REPORT_INPUTS=(TRADE_FIXTURE_PATH,PUMP_IDL_PATH,MIGRATION_FIXTURE_PATH)
PUMP=Pubkey.from_string(json.load(open(PUMP_IDL_PATH, encoding='utf-8'))['address']);ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
p=json.load(open(MIGRATION_FIXTURE_PATH,encoding='utf-8'))
def run_migration(candidate=None,label='missing_boost',overrides=None):
 row=p[label];tx=Transaction.from_bytes(base64.b64decode(row['transaction_base64']));assert all(tx.verify_with_results())
 vm=LiteSVM().with_transaction_history(0).with_blockhash_check(False).with_log_bytes_limit(None);vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,path in [(PROGRAM,candidate or pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),(PUMP,ROOT/'evidence/original/pump/deployed.so'),(TOKEN,ROOT/'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,ROOT/'evidence/dependencies/spl_token_2022/deployed.so'),(ATA,ROOT/'evidence/dependencies/associated_token/deployed.so')]:vm.add_program_from_file(pid,path)
 ix=tx.message.instructions[-1];spec=next(x for x in json.load(open(PUMP_IDL_PATH, encoding='utf-8'))['instructions'] if x['name']=='migrate_v2');keys={a['name']:tx.message.account_keys[i] for a,i in zip(spec['accounts'],ix.accounts)}
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
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();publisher=PumpReport(args.output,ROOT,args.candidate,__file__,extra_inputs=[ROOT/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',ROOT/'research/imported-lab/analysis/pump_fun/curve-migrate-v2-signed-surfpool.json']);candidate=pin_program(args.candidate);rows=[]
 def test(case,kind='direct',overrides=None,**kw):
  fn=boost if kind=='direct' else run_migration
  x=fn(overrides=overrides,**kw);y=fn(candidate=candidate,overrides=overrides,**kw)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diffs=[k for k in x if x[k]!=y[k]];rows.append({'label':case,'original':x,'candidate':y,'diff':diffs})
 for fixture in [False,True]:
  test('direct='+str(fixture),fixture=fixture)
  for idx in [i for i in range(14) if i!=2]:test('substitute='+str((fixture,idx)),fixture=fixture,overrides=meta_mutation(idx,'substitute'))
  for idx in [0,2,6,8]:test('readonly='+str((fixture,idx)),fixture=fixture,overrides=meta_mutation(idx,'readonly'))
  for size in [0,8,210,211,243,245,261,271,286,287,300]:
   def sz(h,m,size=size):a=h.vm.get_account(m[0].pubkey);h.vm.set_account(m[0].pubkey,Account(a.lamports,a.data[:size]+bytes(max(0,size-len(a.data))),a.owner))
   test('pool-size='+str((fixture,size)),fixture=fixture,overrides=sz)
 for field,offset,values in [('boostflag',939,[0,1]),('disableflag',56,[0,1,255])]:
  for value in values:test(field+'='+str(value),overrides=mutate(CONFIG_KEY,offset,bytes([value])))
 test('canonical-signed-migration',kind='migration',label='migration')
 for value in [0,1]:
  def change(vm,k,value=value):
   a=vm.get_account(k['amm_global_config']);d=bytearray(a.data);d[939]=value;vm.set_account(k['amm_global_config'],Account(a.lamports,bytes(d),a.owner))
  test('canonical-boost='+str(value),kind='migration',label='migration',overrides=change)
 for amount in [1,100,10**9,10**12,206900000000000,10**15-1,10**15,10**15+1,2**64-1]:
  def change(vm,k,amount=amount):
   a=vm.get_account(k['associated_base_bonding_curve']);d=bytearray(a.data);d[64:72]=struct.pack('<Q',amount);vm.set_account(k['associated_base_bonding_curve'],Account(a.lamports,bytes(d),a.owner))
  test('canonical-base='+str(amount),kind='migration',label='migration',overrides=change)

 for value in [0,1,10**9,10**15,2**64-1]:
  def change(vm,k,value=value):
   a=vm.get_account(k['base_mint']);d=bytearray(a.data);d[36:44]=struct.pack('<Q',value);vm.set_account(k['base_mint'],Account(a.lamports,bytes(d),a.owner))
  test('canonical-mint-supply='+str(value),kind='migration',label='migration',overrides=change)
 for lamports in [1,10**6,10**9,10**10,10**11,10**12,10**15,2**64-1]:
  def change(vm,k,lamports=lamports):
   a=vm.get_account(k['bonding_curve']);vm.set_account(k['bonding_curve'],Account(lamports,a.data,a.owner))
  test('canonical-curve-lamports='+str(lamports),kind='migration',label='migration',overrides=change)
 for amount in [0,1,10**9]:
  def existing(h,m,amount=amount):h.vm.set_account(m[8].pubkey,Account(amount+2039280,token(quote,m[7].pubkey,amount,True),TOKEN))
  test('existing-boost-vault='+str(amount),overrides=existing)
 for idx in [5,6,8]:
  for off,val in [(0,bytes(32)),(32,bytes(32)),(108,b'\2')]:
   def field(h,m,idx=idx,off=off,val=val):
    if idx==8:h.vm.set_account(m[8].pubkey,Account(2039280,token(quote,m[7].pubkey,0,True),TOKEN))
    a=h.vm.get_account(m[idx].pubkey);d=bytearray(a.data);d[off:off+len(val)]=val;h.vm.set_account(m[idx].pubkey,Account(a.lamports,bytes(d),a.owner))
   test('vault-field='+str((idx,off)),overrides=field)
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'init_boost: direct signed constraints and fully committed saved signed Pump migrate_v2 through original PDA caller, with documented synthetic account variations. Historical blockhash freshness disabled, signatures retained. Full states, exact inner CPI/event bytes, errors; not full-program equivalence.','candidate_sha256':sha(candidate),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
