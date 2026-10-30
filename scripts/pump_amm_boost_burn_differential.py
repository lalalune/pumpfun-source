"""Offline original boost handler probes; synthetic state, normal test-owned signer."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,pathlib,base64,os
_CALLER_CWD=pathlib.Path.cwd()
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));os.chdir(ROOT)
from pump_amm_legacy_sell_differential import *
BOOST=Pubkey.find_program_address([b'boost_vault',bytes(pool)],PROGRAM)[0]
BOOST_ATA=Pubkey.find_program_address([bytes(BOOST),bytes(TOKEN),bytes(quote)],ATA)[0]
def run(amount=10**9,limit=0,overrides=None,candidate=None,unsigned=False,payload_length=None,separate_payer=False):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,name in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/name/'deployed.so')
 for row in f['accounts'].values():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 raw=bytearray(RAW);raw[907:939]=bytes(PAYER.pubkey());raw[939]=1;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(raw),PROGRAM))
 mutate(pool,245,(10**9).to_bytes(16,'little',signed=True))(h,[])
 h.vm.set_account(BOOST,Account(10**9,b'',Pubkey.default()));h.vm.set_account(BOOST_ATA,Account(10**12+2039280,token(quote,BOOST,10**12,True),TOKEN))
 keys=[pool,PAYER.pubkey(),CONFIG_KEY,base,quote,vaultbase,vaultquote,BOOST,BOOST_ATA,TOKEN,TOKEN,EVENT,PROGRAM]
 ix=next(i for i in IDL['instructions'] if i['name']=='boost_buy_and_burn');m=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable')))for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,m)
 data=bytes(ix['discriminator'])+struct.pack('<QQ',amount,limit)
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned or separate_payer else PAYER
 if unsigned:m[1]=AccountMeta(PAYER.pubkey(),False,True)
 def snap():
  out={}
  for key in sorted(set(k.pubkey for k in m),key=str):
   a=h.vm.get_account(key)
   if not a or not a.executable:out[str(key)]=None if not a else {'data_hex':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
  return out
 before=snap();tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,m)],payer.pubkey(),[payer,PAYER] if separate_payer and not unsigned else [payer],h.vm.latest_blockhash());assert all(tx.verify_with_results());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 return {'error':str(r.err())if failed else None,'logs':meta.logs(),'events':[x for x in meta.logs()if x.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'before':before,'after':snap(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}

def boost_transferfee(key,bps=100,maximum=2**64-1,withheld=0,writable=False):
 def ov(h,m):
  mint=h.vm.get_account(key);d=bytearray(mint.data[:82]);d+=bytes(83)+bytes([1]);conf=bytes(72)+struct.pack('<QQH',0,maximum,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(key,Account(10**9,bytes(d),TOKEN22));m[9 if key==base else 10]=AccountMeta(TOKEN22,False,False)
  for k in ([vaultbase]if key==base else [vaultquote]):
   a=h.vm.get_account(k);d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(k,Account(a.lamports,bytes(d),TOKEN22))
  if key==quote:
   a=h.vm.get_account(BOOST_ATA);new=Pubkey.find_program_address([bytes(BOOST),bytes(TOKEN22),bytes(quote)],ATA)[0];d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,withheld);h.vm.set_account(new,Account(10**12+10**9,bytes(d),TOKEN22));m[8]=AccountMeta(new,False,True);m[4]=AccountMeta(quote,False,writable)
 return ov

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args();args.candidate=(_CALLER_CWD/args.candidate).resolve();args.output=(_CALLER_CWD/args.output).resolve();rows=[]
 def test(label,**kw):
  x=run(**kw);y=run(candidate=args.candidate,**kw);diff=[k for k in x if k!='logs' and x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'diff':diff})
 for amount in [0,1,2,3,4,10,100,1000,10**6,10**9,10**12-1,10**12,10**12+1,2**64-1]:
  for limit in [0,1,2**64-1]:test('amount-limit='+str((amount,limit)),amount=amount,limit=limit)
 test('unsigned',unsigned=True)
 test('separate-fee-payer',separate_payer=True)
 test('readonly-authority-separate-payer',separate_payer=True,overrides=meta_mutation(1,'readonly'))
 test('full-drain-separate-payer',amount=10**12,separate_payer=True)
 for length in range(24):test('payload='+str(length),payload_length=length)
 for idx in range(13):
  if idx!=1:test('substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
 for idx in [1,3,5,6,8]:test('readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
 for key in [pool,CONFIG_KEY,base,quote,vaultbase,vaultquote,BOOST_ATA]:
  for owner in [Pubkey.default(),TOKEN22,PROGRAM]:test('owner='+str((key,owner)),overrides=mutate(key,0,b'',owner=owner))
 for key in [vaultbase,vaultquote,BOOST_ATA]:
  for off,val in [(0,bytes(32)),(32,bytes(32)),(108,b'\0'),(108,b'\2')]:test('token-field='+str((key,off,val.hex())),overrides=mutate(key,off,val))
  for length in [0,8,164,165,166,183]:test('token-length='+str((key,length)),overrides=mutate(key,0,b'',length))
  for amount in [0,1,10**9,2**64-1]:test('token-amount='+str((key,amount)),overrides=mutate(key,64,struct.pack('<Q',amount)))
 for length in [0,7,8,82,165,166,278]:
  for key in [base,quote]:test('mint-length='+str((key,length)),overrides=mutate(key,0,b'',length))
 for off,val in [(907,bytes(32)),(907,bytes(OUTSIDER.pubkey())),(939,b'\0')]:test('config='+str((off,val.hex())),overrides=mutate(CONFIG_KEY,off,val))
 for flag in [0,1,2,4,8,16,31,255]:test('disabled='+str(flag),overrides=mutate(CONFIG_KEY,56,bytes([flag])))
 for off,val in [(243,b'\1'),(244,b'\1'),(270,b'\1'),(261,struct.pack('<Q',10000)),(271,bytes(16)),(11,bytes(32)),(8,b'\0')]:test('pool='+str(off),overrides=mutate(pool,off,val))
 for v in [-2**127,-10**13,-125882,-125881,0,1,10**9,2**64,2**127-1]:test('virtual='+str(v),overrides=mutate(pool,245,v.to_bytes(16,'little',signed=True)))
 for off in [271,279]:
  for n in [0,1,10**9,2**64-1]:test('fees='+str((off,n)),overrides=mutate(pool,off,struct.pack('<Q',n)))
 for n in [0,1,1000,10**12,2**64-1]:test('supply='+str(n),overrides=mutate(base,36,struct.pack('<Q',n)))
 for length in [0,7,8,210,211,243,244,245,261,270,271,286,287,300]:test('pool-length='+str(length),overrides=mutate(pool,0,b'',length))
 for key in [base,quote]:
  for bps in [0,1,100,9999,10000]:
   for maximum in [0,1,123,2**64-1]:
    for amount in [1,1000,10**9,10**12]:test('transfer-fee='+str((key,bps,maximum,amount)),amount=amount,overrides=boost_transferfee(key,bps,maximum))
 for bps in [0,1,100,10000]:
  for withheld in [0,1,10**9]:
   for amount in [10**9,10**12]:test('writable-harvest='+str((bps,withheld,amount)),amount=amount,overrides=boost_transferfee(quote,bps,123,withheld,True))
 for amount in [1,2,1000,10**9]:
  for virtual in [0,1,-1]:
   for q in [0,1,10**9]:test('price-boundary='+str((amount,virtual,q)),amount=amount,overrides=combine(mutate(pool,245,virtual.to_bytes(16,'little',signed=True)),mutate(pool,271,bytes(16)),mutate(vaultquote,64,struct.pack('<Q',q))))
 for v,fees in [(0,0),(-1,1),(-2,1),(2**127-1,0),(2**127-1,1)]:test('canboost-boundary='+str((v,fees)),overrides=combine(mutate(pool,245,v.to_bytes(16,'little',signed=True)),mutate(pool,271,struct.pack('<QQ',fees,0))))
 for aoff,aval in [(907,bytes(32)),(939,b'\0'),(56,b'\xff')]:
  for amount in [0,1]:test('precedence='+str((aoff,amount)),amount=amount,overrides=combine(mutate(CONFIG_KEY,aoff,aval),mutate(pool,245,(-125882).to_bytes(16,'little',signed=True))))
 for idx in [0,2,3,4,5,6,7,8]:
  for amount in [0,1]:test('constraint-before-amount='+str((idx,amount)),amount=amount,overrides=meta_mutation(idx,'substitute'))
 # Exact rounding/slippage boundaries and drained-vault close/harvest constraints.
 for amount in [2,1000,10**9,10**12]:
  out=int(f['pool_base_vault_amount_raw'])*(amount-1)//(int(f['pool_quote_vault_amount_raw'])+10**9+amount-1)
  for minimum in [max(0,out-1),out,out+1]:test('slippage-boundary='+str((amount,minimum)),amount=amount,limit=minimum)
 for length in [0,7,8,56,642,907,939,940,948,949,1000]:test('global-length='+str(length),overrides=mutate(CONFIG_KEY,0,b'',length))
 for off in [243,244,269,270]:test('invalid-pool-bool='+str(off),overrides=mutate(pool,off,b'\2'))
 for idx in [9,10]:
  def mismatch_program(h,m,idx=idx):m[idx]=AccountMeta(TOKEN22,False,False)
  test('token-program-mismatch='+str(idx),overrides=mismatch_program)
 for amount in [10**9,10**12]:
  for close_owner in [Pubkey.default(),BOOST,OUTSIDER.pubkey()]:test('close-authority='+str((amount,close_owner)),amount=amount,overrides=mutate(BOOST_ATA,129,struct.pack('<I',1)+bytes(close_owner)))
 for withheld in [0,1,2**64-1]:
  for mint_writable in [False,True]:test('full-drain-withheld='+str((withheld,mint_writable)),amount=10**12,overrides=boost_transferfee(quote,100,123,withheld,mint_writable))
 failures=[i for i,r in enumerate(rows) if r['diff']];sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();report={'scope':'AMM boost_buy_and_burn with ordinary verified test-owned authority signatures, synthetic state and captured token dependencies. Full states, exact CPI/event bytes, errors and return data. Not full-program or exhaustive equivalence.','candidate_sha256':sha(pin_program(args.candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':failures,'cases':rows};args.output.parent.mkdir(exist_ok=True,parents=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
if __name__=='__main__':main()
