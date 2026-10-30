"""Bounded AMM legacy buy/exact-quote with normal signed synthetic fixtures and captured CPIs."""
import sys,pathlib,os
ROOT=pathlib.Path(__file__).resolve().parents[1]
_CALLER_CWD=pathlib.Path.cwd()
sys.path.insert(0,str(ROOT/'scripts'))
os.chdir(ROOT)
from pump_amm_legacy_sell_differential import *
GLOBAL_VOLUME=Pubkey.find_program_address([b'global_volume_accumulator'],PROGRAM)[0]
GDISC=bytes(next(x for x in IDL['accounts'] if x['name']=='GlobalVolumeAccumulator')['discriminator'])
def legacy_buy(name='buy',amount=10**10,limit=10**12,track=b'\0',overrides=None,candidate=None,unsigned=False,payload_length=None,remaining=True):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,filepath in [(TOKEN,'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,'evidence/dependencies/spl_token_2022/deployed.so'),(FEES,'evidence/original/pump_fees/deployed.so'),(ATA,'evidence/dependencies/associated_token/deployed.so')]:h.vm.add_program_from_file(pid,ROOT/filepath)
 for n,row in f['accounts'].items():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 glob=bytearray(RAW);glob[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(glob),PROGRAM))
 for k,m,owner,native in [(userbase,base,PAYER.pubkey(),False),(userquote,quote,PAYER.pubkey(),True),(PROTOCOL_ATA,quote,PROTOCOL,True),(CREATOR_ATA,quote,CREATOR_VAULT,True)]:h.vm.set_account(k,Account(10**15+2039280 if native else 10**9,token(m,owner,10**15 if k in [userbase,userquote] else 0,native),TOKEN))
 for k in [PROTOCOL,CREATOR_VAULT]:h.vm.set_account(k,Account(10**9,b'',Pubkey.default()))
 h.vm.set_account(volume,Account(0,b'',Pubkey.default()));h.vm.set_account(GLOBAL_VOLUME,Account(10**9,GDISC+struct.pack('<qqq',0,0,86400)+bytes(base)+bytes(480),PROGRAM))
 keys=[pool,PAYER.pubkey(),CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,PROTOCOL,PROTOCOL_ATA,TOKEN,TOKEN,Pubkey.default(),ATA,EVENT,PROGRAM,CREATOR_ATA,CREATOR_VAULT,GLOBAL_VOLUME,volume,feeconfig,FEES]
 ix=next(x for x in IDL['instructions'] if x['name']==name);metas=[AccountMeta(k,bool(row.get('signer')),bool(row.get('writable'))) for k,row in zip(keys,ix['accounts'])]
 if remaining:
  owner=Pubkey.from_bytes(base64.b64decode(f['accounts']['buyback_fee_recipient']['data_base64'])[32:64]);poolv2=Pubkey.find_program_address([b'pool-v2',bytes(base)],PROGRAM)[0]
  for key in [poolv2,owner]:h.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
  metas+=[AccountMeta(poolv2,False,False),AccountMeta(owner,False,False),AccountMeta(buyback,False,True)]
 if overrides:overrides(h,metas)
 data=bytes(ix['discriminator'])+struct.pack('<QQ',amount,limit)+track
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[1]=AccountMeta(PAYER.pubkey(),False,True)
 watch=set(m.pubkey for m in metas)|{volume}
 def snapshot():
  rows={}
  for k in sorted(watch,key=str):
   a=h.vm.get_account(k)
   if not a or not a.executable:rows[str(k)]=None if not a else {'data_hex':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
  return rows
 before=snapshot();tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 return {'error':str(r.err()) if failed else None,'logs':meta.logs(),'events':[x for x in meta.logs() if x.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'before':before,'after':snapshot(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}

def adapt_sell_helper(fn):
 def ov(h,m):
  volumes=m[19:21];shadow=m[:19]+m[21:];fn(h,shadow);m[:]=shadow[:19]+volumes+shadow[19:]
 return ov
def cashback_buy(present=False):
 def ov(h,m):
  mutate(pool,244,b'\1')(h,m);m.insert(23,AccountMeta(uvata,False,True))
  if present:h.vm.set_account(uvata,Account(2039280,token(quote,volume,0,True),TOKEN))
 return ov
def existing_volume(length=137,offset=8,value=None):
 def ov(h,m):
  raw=bytearray(bytes(next(x for x in IDL['accounts'] if x['name']=='UserVolumeAccumulator')['discriminator'])+bytes(PAYER.pubkey())+bytes(97))
  if value is not None:raw[offset:offset+len(value)]=value
  h.vm.set_account(volume,Account(10**9,bytes(raw[:length]).ljust(length,b'\0'),PROGRAM))
 return ov
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.candidate=(_CALLER_CWD/a.candidate).resolve();a.output=(_CALLER_CWD/a.output).resolve();rows=[]
 def test(name,label,**kw):
  params=dict(name=name,amount=10**10 if name=='buy' else 10**7,limit=10**12 if name=='buy' else 1);params.update(kw);x=legacy_buy(**params);y=legacy_buy(candidate=a.candidate,**params);diff=[k for k in x if k!='logs' and x[k]!=y[k]];rows.append({'instruction':name,'case':label,'original':x,'candidate':y,'diff':diff})
 for name in ['buy','buy_exact_quote_in']:
  for amount in [0,1,2,3,4,5,1000,10**7,10**10,int(f['pool_base_vault_amount_raw']),int(f['pool_base_vault_amount_raw'])+1,2**64-1]:test(name,'amount='+str(amount),amount=amount)
  for limit in [0,1,1847795,1847796,1847797,2**64-1]:test(name,'limit='+str(limit),limit=limit)
  for track in [b'',b'\0',b'\1',b'\2',b'\xff',b'\1\1']:test(name,'track='+track.hex(),track=track)
  for length in range(26):test(name,'payload='+str(length),payload_length=length)
  test(name,'unsigned',unsigned=True)
  for idx in range(26):
   if idx!=1:test(name,'substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
  for idx in [0,5,6,7,8,10,17,20,25]:test(name,'readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
  for key in [pool,CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,PROTOCOL_ATA,CREATOR_ATA,GLOBAL_VOLUME,feeconfig,buyback]:
   for owner in [Pubkey.default(),TOKEN22]:test(name,'owner='+str((key,owner)),overrides=mutate(key,0,b'',owner=owner))
  for key,off in [(vaultbase,64),(vaultquote,64),(userbase,64),(userquote,64),(base,36)]:
   for value in [0,1,2**64-1]:test(name,'amount-field='+str((key,value)),overrides=mutate(key,off,struct.pack('<Q',value)))
  for value in [-2**127,-10**13,-125882,0,1,10**9,2**64,2**127-1]:test(name,'virtual='+str(value),overrides=mutate(pool,245,value.to_bytes(16,'little',signed=True)))
  for flags in [0,1,2,4,8,16,31,255]:test(name,'disable='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
  for length in [0,7,8,210,211,243,244,245,261,270,271,286,287,300]:test(name,'pool-layout='+str(length),overrides=mutate(pool,0,b'',length))
  for length in [0,7,8,65,69,1068,1069,2511,2512,3000,4072,4073,4096,4097]:test(name,'fee-layout='+str(length),overrides=mutate(feeconfig,0,b'',length))
  for off in [261,271,279]:
   for value in [0,1,10**9,2**64-1]:test(name,'pool-fees='+str((off,value)),overrides=mutate(pool,off,struct.pack('<Q',value)))
  for value in [0,1,9999,10000,10001,2**64-1]:test(name,'buyback-bps='+str(value),overrides=mutate(CONFIG_KEY,899,struct.pack('<Q',value)))
  for key in [base,quote]:
   for bps in [0,1,100,9999,10000]:
    for maximum in [0,1,123,2**64-1]:test(name,'transfer-fee='+str((key,bps,maximum)),overrides=adapt_sell_helper(legacy_transferfee(key,bps,maximum)))
  for key in [quote,Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),Pubkey.from_bytes(bytes([90])*32)]:
   for canonical in [False,True]:
    for length in [2511,2512,4072,4073,4096,4097]:test(name,'quote='+str((key,canonical,length)),overrides=combine(adapt_sell_helper(legacy_rekey(key,canonical)),mutate(feeconfig,0,b'',length)))
  for tiers in [[],[(0,(0,0,0))],[(0,(10,20,30))],[(2**120,(10,20,30)),(0,(40,50,60))],[(0,(10,20,30)),(0,(40,50,60))],[(0,(10000,10000,10000))],[(0,(2**64-1,0,0))]]:test(name,'fee-table='+str(tiers),overrides=custom_fee_table(tiers))
  for key in [userbase,userquote,vaultbase,vaultquote,PROTOCOL_ATA,CREATOR_ATA,buyback]:
   for off,val in [(0,bytes(32)),(32,bytes(OUTSIDER.pubkey())),(108,b'\0'),(108,b'\2')]:test(name,'token-field='+str((key,off,val.hex())),overrides=mutate(key,off,val))
   def missing(h,m,key=key):h.vm.set_account(key,Account(0,b'',Pubkey.default()))
   test(name,'missing-token='+str(key),overrides=missing)
  for off in [243,244,270]:test(name,'pool-flag='+str(off),overrides=mutate(pool,off,b'\1'))
  for length in [0,7,8,40,73,89,90,136,137,138]:test(name,'volume-layout='+str(length),overrides=existing_volume(length))
  for off,val in [(8,bytes(32)),(8,bytes(OUTSIDER.pubkey())),(40,b'\1'),(41,struct.pack('<Q',123)),(49,struct.pack('<Q',456)),(57,struct.pack('<Q',789)),(65,struct.pack('<q',123)),(73,b'\1'),(74,struct.pack('<Q',123)),(82,struct.pack('<Q',456))]:test(name,'volume-field='+str((off,val.hex())),track=b'\1',overrides=existing_volume(offset=off,value=val))
  for length in [0,7,8,32,64,543,544,1024]:test(name,'global-volume-layout='+str(length),overrides=mutate(GLOBAL_VOLUME,0,b'',length))
  for times in [(0,0,0),(0,2**63-1,1),(1234500000,1234600000,86400),(-2**63,2**63-1,0)]:test(name,'global-volume-times='+str(times),track=b'\1',overrides=mutate(GLOBAL_VOLUME,8,struct.pack('<qqq',*times)))
  for count in range(4):
   def trim(h,m,count=count):del m[23+count:]
   test(name,'tail='+str(count),overrides=trim)
  for present in [False,True]:
   for track in [b'',b'\0',b'\1']:test(name,'cash='+str((present,track.hex())),track=track,overrides=cashback_buy(present))
  for idx in [23,24]:
   for mode in ['substitute','readonly']:test(name,'cash-meta='+str((idx,mode)),overrides=combine(cashback_buy(True),meta_mutation(idx,mode)))
  test(name,'cash-overflow',overrides=combine(existing_volume(offset=74,value=struct.pack('<Q',2**64-1)),cashback_buy(True)))
  for source,dest in [(5,7),(6,8),(10,8),(17,8),(25,8)]:
   def alias(h,m,source=source,dest=dest):m[source]=m[dest]
   test(name,'alias='+str((source,dest)),overrides=alias)

 for name in ['buy','buy_exact_quote_in']:
  for amount in [1,1000,10**6,10**10]:
   for count in range(4):
    for skip in [False,True]:
     def tails(h,m,count=count,skip=skip):
      if skip:del m[23]
      del m[23+count:]
     test(name,'amount-tail='+str((amount,count,skip)),amount=amount,overrides=tails)
  for present in [False,True]:
   for bps in [1,100,10000]:
    for maximum in [1,2**64-1]:
     def cash_tf(h,m,present=present,bps=bps,maximum=maximum):
      adapt_sell_helper(legacy_transferfee(quote,bps,maximum))(h,m);cashback_buy(False)(h,m);ata=Pubkey.find_program_address([bytes(volume),bytes(TOKEN22),bytes(quote)],ATA)[0];m[23]=AccountMeta(ata,False,True)
      if present:h.vm.set_account(ata,Account(2039280,token(quote,volume,0,True)+bytes([2])+struct.pack('<HHQ',2,8,0),TOKEN22))
     test(name,'cash-transfer-fee='+str((present,bps,maximum)),overrides=cash_tf)
  for key in [volume,uvata]:
   for owner in [Pubkey.default(),TOKEN,PROGRAM]:test(name,'cash-owner='+str((key,owner)),overrides=combine(existing_volume(),cashback_buy(True),mutate(key,0,b'',owner=owner)))
  for off,val in [(0,bytes(32)),(32,bytes(OUTSIDER.pubkey())),(108,b'\0'),(108,b'\2')]:test(name,'cash-token-field='+str((off,val.hex())),overrides=combine(cashback_buy(True),mutate(uvata,off,val)))
  for count in range(5):
   def trim(h,m,count=count):del m[23+count:]
   test(name,'cash-tail='+str(count),overrides=combine(cashback_buy(True),trim))
  def mayhem(h,m):mutate(pool,243,b'\1')(h,m);mutate(CONFIG_KEY,385,bytes(PROTOCOL))(h,m)
  for count in range(4):
   def trim(h,m,count=count):del m[23+count:]
   test(name,'mayhem-tail='+str(count),overrides=combine(mayhem,trim))
  for flag in [243,244,270]:
   for other in [243,244,270]:
    if flag<other:test(name,'flags='+str((flag,other)),overrides=combine(mayhem if flag==243 else cashback_buy(True),mutate(pool,other,b'\1')))
  for value in [Pubkey.default(),OUTSIDER.pubkey()]:
   def creator_override(h,m,value=value):
    mutate(pool,211,bytes(value))(h,m);vault=Pubkey.find_program_address([b'creator_vault',bytes(value)],PROGRAM)[0];ata=Pubkey.find_program_address([bytes(vault),bytes(TOKEN),bytes(quote)],ATA)[0];h.vm.set_account(vault,Account(10**9,b'',Pubkey.default()));h.vm.set_account(ata,Account(2039280,token(quote,vault,0,True),TOKEN));m[17]=AccountMeta(ata,False,True);m[18]=AccountMeta(vault,False,False)
    if value==Pubkey.default():del m[23]
   for cashback in [False,True]:test(name,'creator='+str((value,cashback)),overrides=combine(creator_override,mutate(pool,244,bytes([cashback]))))
  for idx in [17,10,25]:
   for value in [1,1844399,1844400,10**9]:
    def prefund(h,m,idx=idx,value=value):h.vm.set_account(m[idx].pubkey,Account(value,b'',Pubkey.default()))
    test(name,'prefunded-ata='+str((idx,value)),overrides=prefund)
  for value in [1,1844399,1844400,10**9]:
   def prefund(h,m,value=value):h.vm.set_account(volume,Account(value,b'',Pubkey.default()))
   test(name,'prefunded-volume='+str(value),overrides=prefund)
  for length in [211,245,287,300]:
   def lowrent(h,m,length=length):a=h.vm.get_account(pool);h.vm.set_account(pool,Account(1,a.data[:length].ljust(length,b'\0'),a.owner))
   test(name,'low-rent-pool='+str(length),overrides=lowrent)
  for idx in [23,24,25]:
   for owner in [Pubkey.default(),TOKEN,PROGRAM]:
    def own(h,m,idx=idx,owner=owner):mutate(m[idx].pubkey,0,b'',owner=owner)(h,m)
    test(name,'remaining-owner='+str((idx,owner)),overrides=own)
  for length in [0,1,8,90,287]:
   def p2data(h,m,length=length):mutate(m[23].pubkey,0,b'',length)(h,m)
   test(name,'pool-v2-data='+str(length),overrides=p2data)
 for bps in [1,100,10000]:
  for maximum in [1,123,2**64-1]:
   for limit in [1847795,1847796,1847797,1847918,1847919,1847920,1866233,1866234,1866235]:test('buy','transferfee-limit='+str((bps,maximum,limit)),limit=limit,overrides=adapt_sell_helper(legacy_transferfee(quote,bps,maximum)))
 failures=[i for i,x in enumerate(rows) if x['diff']];sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();report={'scope':'Isolated AMM buy/exact-quote reconstruction with synthetic state, normal verified test-owned signatures, and actual captured dependencies. No full ELF identity or exhaustive equivalence.','candidate_sha256':sha(pin_program(a.candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':failures,'cases':rows};a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
if __name__=='__main__':main()
