#!/usr/bin/env python3
"""Local original/candidate SBF liquidity differential with captured SPL dependency ELFs."""
import sys,json,base64,struct,argparse,hashlib,pathlib,random
from solders.clock import Clock
sys.path.insert(0,'scripts')
from pump_amm_admin_differential import *
from pump_amm_reusable_harness import acquire_harness, pin_program
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
f=json.load(open('research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json'));pool=Pubkey.from_string(f['pool']);poolraw=bytearray(base64.b64decode(f['accounts']['pool']['data_base64']));lp=Pubkey.from_bytes(bytes(poolraw[107:139]));supply=struct.unpack_from('<Q',poolraw,203)[0]
base=Pubkey.from_string(f['keys']['base_mint']);quote=Pubkey.from_string(f['keys']['quote_mint']);vaultbase=Pubkey.from_string(f['keys']['pool_base_token_account']);vaultquote=Pubkey.from_string(f['keys']['pool_quote_token_account'])
userbase=Pubkey.from_bytes(bytes([70])*32);userquote=Pubkey.from_bytes(bytes([71])*32);userlp=Pubkey.from_bytes(bytes([72])*32)
def token(mint,owner,amount,native=False):
 data=bytearray(165);data[:32]=bytes(mint);data[32:64]=bytes(owner);struct.pack_into('<Q',data,64,amount);data[108]=1
 if native:struct.pack_into('<IQ',data,109,1,2039280)
 return bytes(data)
def run(name,amount,maxbase=2**64-1,maxquote=2**64-1,virtual=0,mint_supply=None, overrides=None, candidate=None,unsigned=False,payload_length=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'))
 h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 h.vm.add_program_from_file(TOKEN,ROOT/'evidence/dependencies/spl_token/deployed.so');h.vm.add_program_from_file(TOKEN22,ROOT/'evidence/dependencies/spl_token_2022/deployed.so')
 glob=bytearray(RAW);glob[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(glob),PROGRAM))
 for n in ['base_mint','quote_mint','pool_base_token_account','pool_quote_token_account']:
  row=f['accounts'][n];key=Pubkey.from_string(f['keys'][n]);h.vm.set_account(key,Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 data=bytearray(poolraw);data[245:261]=virtual.to_bytes(16,'little',signed=True);data[271:287]=bytes(16);h.vm.set_account(pool,Account(f['accounts']['pool']['lamports'],bytes(data),PROGRAM))
 mint=struct.pack('<I',1)+bytes(pool)+struct.pack('<Q',supply if mint_supply is None else mint_supply)+bytes([9,1])+bytes(36);h.vm.set_account(lp,Account(10**9,mint,TOKEN22))
 for k,m,own,amt,nat in [(userbase,base,TOKEN,10**15,False),(userquote,quote,TOKEN,10**15,True),(userlp,lp,TOKEN22,supply//2,False)]:h.vm.set_account(k,Account(amt+2039280 if nat else 10**9,token(m,PAYER.pubkey(),amt,nat),own))
 metas=[AccountMeta(k,sign,w) for k,sign,w in [(pool,False,True),(CONFIG_KEY,False,False),(PAYER.pubkey(),True,False),(base,False,False),(quote,False,False),(lp,False,True),(userbase,False,True),(userquote,False,True),(userlp,False,True),(vaultbase,False,True),(vaultquote,False,True),(TOKEN,False,False),(TOKEN22,False,False),(EVENT,False,False),(PROGRAM,False,False)]]
 if overrides: overrides(h,metas)
 ix=next(x for x in IDL['instructions'] if x['name']==name);args=bytes(ix['discriminator'])+struct.pack('<QQQ',amount,maxbase,maxquote)
 if payload_length is not None:args=args[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[2]=AccountMeta(PAYER.pubkey(),False,False)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,args,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 keys=[pool,CONFIG_KEY,base,quote,lp,userbase,userquote,userlp,vaultbase,vaultquote]
 states={str(k):{'data_hex':bytes(h.vm.get_account(k).data).hex(),'owner':str(h.vm.get_account(k).owner),'lamports':h.vm.get_account(k).lamports} for k in keys}
 return {'accounts':states,'pool_data':bytes(h.vm.get_account(pool).data).hex(),'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'error':str(r.err()) if failed else None,'logs':meta.logs(),'amounts':{str(k):struct.unpack_from('<Q',h.vm.get_account(k).data,64)[0] for k in [userbase,userquote,userlp,vaultbase,vaultquote]},'pool_supply':int.from_bytes(h.vm.get_account(pool).data[203:211],'little'),'lp_supply':struct.unpack_from('<Q',h.vm.get_account(lp).data,36)[0]}
def mutate(key,offset,value,length=None,owner=None):
 def apply(h,metas):
  a=h.vm.get_account(key);d=bytearray(a.data);d[offset:offset+len(value)]=value
  if length is not None:d=d[:length]+bytes(max(0,length-len(d)))
  h.vm.set_account(key,Account(a.lamports,bytes(d),owner or a.owner))
 return apply

def transferfee(key,fee_bps=100,maxfee=2**64-1):
 def apply(h,m):
  mint=h.vm.get_account(key);d=bytearray(mint.data[:82]);d+=bytes(83)+bytes([1]);conf=bytes(72)+struct.pack('<QQH',0,maxfee,fee_bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(key,Account(mint.lamports,bytes(d),TOKEN22))
  for k in ([userbase,vaultbase] if key==base else [userquote,vaultquote]):
   a=h.vm.get_account(k);d=bytearray(a.data[:165]);d+=bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(k,Account(a.lamports,bytes(d),TOKEN22))
 return apply

def combine(*mutations):
 def apply(h,metas):
  for mutation in mutations:mutation(h,metas)
 return apply

def meta_mutation(index,kind):
 def apply(h,metas):
  old=metas[index]
  if kind=='readonly':metas[index]=AccountMeta(old.pubkey,old.is_signer,False)
  elif kind=='substitute':
   key=Pubkey.from_bytes(bytes([89])*32);account=h.vm.get_account(old.pubkey)
   if account:h.vm.set_account(key,account)
   metas[index]=AccountMeta(key,old.is_signer,old.is_writable)
 return apply

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args();rows=[]
 def test(name,label,**kwargs):
  parameters=dict(amount=1000000,maxbase=0 if name=='withdraw' else 2**64-1,maxquote=0 if name=='withdraw' else 2**64-1);parameters.update(kwargs)
  x=run(name,**parameters);y=run(name,candidate=args.candidate,**parameters)
  x['events']=[l for l in x['logs'] if l.startswith('Program data: ')];y['events']=[l for l in y['logs'] if l.startswith('Program data: ')]
  diffs=[k for k in x if k!='logs' and x[k]!=y[k]]
  rows.append({'instruction':name,'case':label,'original':x,'candidate':y,'mismatched_fields':diffs,'match':not diffs})
 for n in ['deposit','withdraw']:
  test(n,'unsigned-user',unsigned=True)
  for length in range(32):test(n,'payload-length='+str(length),payload_length=length)
  for amount in [0,1,2,1000,1000000,supply//2,supply,supply+1,2**64-1]:test(n,'amount='+str(amount),amount=amount)
  for virtual in [-2**127,-10**9,-1,0,1,10**9,10**15,2**64,2**100,2**127-1]:test(n,'virtual='+str(virtual),virtual=virtual)
  for mint_supply in [0,1,supply//2,supply-1,supply,supply+1,2**64-1]:test(n,'mint-supply='+str(mint_supply),mint_supply=mint_supply)
  for off in [261,271,279]:
   for x in [0,1,10**9,2**64-1]:test(n,'pool-field='+str((off,x)),overrides=mutate(pool,off,struct.pack('<Q',x)))
  for v in [-10**9,-1,0,1,10**9]:
   for fees in [0,1,10**9]:test(n,'effective-virtual='+str((v,fees)),virtual=v,overrides=mutate(pool,271,struct.pack('<Q',fees)))
  for k in [base,quote]:
   for bps in [0,1,100,9999,10000]:
    for maximum in [0,1,123,2**64-1]:test(n,'transfer-fee='+str((k,bps,maximum)),overrides=transferfee(k,bps,maximum))
  for size in [0,7,8,210,211,242,243,244,245,260,261,268,269,270,271,278,279,286,287,299,300,301]:test(n,'pool-size='+str(size),overrides=mutate(pool,0,b'',size))
  for k,off,val in [(pool,0,bytes(8)),(pool,243,b'\x02'),(pool,244,b'\x02'),(pool,269,b'\x02'),(pool,270,b'\x02'),(userbase,32,bytes(32)),(userbase,0,bytes(32)),(userquote,32,bytes(32)),(userlp,32,bytes(32)),(vaultbase,32,bytes(32)),(vaultquote,32,bytes(32)),(lp,4,bytes(32)),(pool,8,b'\x00'),(pool,11,bytes(32))]:test(n,'field='+str((k,off,val.hex())),overrides=mutate(k,off,val))
  for index in [0,5,6,7,8,9,10]:test(n,'readonly='+str(index),overrides=meta_mutation(index,'readonly'))
  for index in [0,1,3,4,5,6,7,8,9,10,11,12,13,14]:test(n,'substitute='+str(index),overrides=meta_mutation(index,'substitute'))
  for flags in [0,1,2,4,8,16,31,255]:test(n,'disable-flags='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
  for amount in [0,1,1000000]:
   for pool_supply in [0,1,supply,2**64-1]:test(n,'pool-supply='+str((amount,pool_supply)),amount=amount,mint_supply=0,overrides=mutate(pool,203,struct.pack('<Q',pool_supply)))
  for limit in [0,1,29312,29313,29609,29610,2**64-1]:
   test(n,'quote-slippage='+str(limit),maxquote=limit)
   test(n,'quote-fee-slippage='+str(limit),maxquote=limit,overrides=transferfee(quote))
  for limit in [0,160619894,160619895,160619896,2**64-1]:test(n,'base-slippage='+str(limit),maxbase=limit)
  for user_index,vault_index in [(6,9),(7,10)]:
   for amount in [0,1,1000000]:
    def alias(h,metas,ui=user_index,vi=vault_index):metas[ui]=AccountMeta(metas[vi].pubkey,False,True)
    test(n,'self-transfer='+str((user_index,amount)),amount=amount,overrides=alias)
  for key in [pool,CONFIG_KEY,base,quote,lp,userbase,userquote,userlp,vaultbase,vaultquote]:
   test(n,'wrong-owner='+str(key),overrides=mutate(key,0,b'',owner=Pubkey.default()))
  for key in [lp,userlp]:test(n,'classic-lp-owner='+str(key),overrides=mutate(key,0,b'',owner=TOKEN))
  for key in [userbase,userquote,userlp,vaultbase,vaultquote]:
   for offset,value in [(0,bytes(32)),(32,bytes(OUTSIDER.pubkey())),(64,bytes(8)),(108,b'\x02')]:test(n,'token-field='+str((key,offset,value.hex())),overrides=mutate(key,offset,value))
  rng=random.Random(20261024)
  for i in range(80):
   amount=rng.choice([0,1,1000,1000000,supply//2,supply])
   virtual=rng.choice([0,1,2**32,2**64,2**80,2**100,2**120,-10**9])+rng.randrange(-100,100)
   fee=rng.choice([0,1,10**9,10**11])
   test(n,'seeded-math='+str((i,amount,virtual,fee)),amount=amount,virtual=virtual,overrides=mutate(pool,271,struct.pack('<Q',fee)))
 failures=[i for i,r in enumerate(rows) if not r['match']];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 report={'scope':'SBF deposit/withdraw: committed account bytes, lamports, errors, event bytes, exact inner CPI instructions. Captured classic SPL and Token2022 ELFs; synthetic transfer-fee extension cases. Not whole-program equivalence or exhaustive extension coverage.','original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'candidate_sha256':sha(pin_program(args.candidate)),'script_sha256':sha(pathlib.Path(__file__)),'harness_sha256':sha(ROOT/'scripts/pump_amm_reusable_harness.py'),'dependencies':{name:sha(ROOT/'evidence/dependencies'/name/'deployed.so') for name in ['spl_token','spl_token_2022']},'case_count':len(rows),'mismatches':failures,'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(failures),'mismatches':failures[:40]}))
 if failures:raise SystemExit(1)
if __name__=='__main__':main()
