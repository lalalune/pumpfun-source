"""Offline AMM legacy sell with synthetic test-owned signer/state and captured CPIs."""
import sys,base64,os,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
_CALLER_CWD=pathlib.Path.cwd()
sys.path.insert(0,str(ROOT/'scripts'))
# Imported legacy harnesses read their captured fixtures relative to the repository.
os.chdir(ROOT)
from pump_amm_trade_v2_differential import *
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
PROTOCOL=Pubkey.from_bytes(bytes(RAW[57:89]));PROTOCOL_ATA=Pubkey.find_program_address([bytes(PROTOCOL),bytes(TOKEN),bytes(quote)],ATA)[0]
CREATOR=Pubkey.from_bytes(bytes(poolraw[211:243]));CREATOR_VAULT=Pubkey.find_program_address([b'creator_vault',bytes(CREATOR)],PROGRAM)[0];CREATOR_ATA=Pubkey.find_program_address([bytes(CREATOR_VAULT),bytes(TOKEN),bytes(quote)],ATA)[0]
def legacy(amount=10**10,limit=0,overrides=None,candidate=None,unsigned=False,payload_length=None,remaining=True):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,filepath in [(TOKEN,'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,'evidence/dependencies/spl_token_2022/deployed.so'),(FEES,'evidence/original/pump_fees/deployed.so'),(ATA,'evidence/dependencies/associated_token/deployed.so')]:h.vm.add_program_from_file(pid,ROOT/filepath)
 for n,row in f['accounts'].items():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 glob=bytearray(RAW);glob[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(glob),PROGRAM))
 for k,m,owner,native in [(userbase,base,PAYER.pubkey(),False),(userquote,quote,PAYER.pubkey(),True),(PROTOCOL_ATA,quote,PROTOCOL,True),(CREATOR_ATA,quote,CREATOR_VAULT,True)]:h.vm.set_account(k,Account(10**15+2039280 if native else 10**9,token(m,owner,10**15 if k in [userbase,userquote] else 0,native),TOKEN))
 for k in [PROTOCOL,CREATOR_VAULT]:h.vm.set_account(k,Account(10**9,b'',Pubkey.default()))
 h.vm.set_account(volume,Account(0,b'',Pubkey.default()))
 keys=[pool,PAYER.pubkey(),CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,PROTOCOL,PROTOCOL_ATA,TOKEN,TOKEN,Pubkey.default(),ATA,EVENT,PROGRAM,CREATOR_ATA,CREATOR_VAULT,feeconfig,FEES]
 ix=next(x for x in IDL['instructions'] if x['name']=='sell');metas=[AccountMeta(k,bool(row.get('signer')),bool(row.get('writable'))) for k,row in zip(keys,ix['accounts'])]
 if remaining:
  owner=Pubkey.from_bytes(base64.b64decode(f['accounts']['buyback_fee_recipient']['data_base64'])[32:64]);poolv2=Pubkey.find_program_address([b'pool-v2',bytes(base)],PROGRAM)[0]
  for key in [poolv2,owner]:h.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
  metas+=[AccountMeta(poolv2,False,False),AccountMeta(owner,False,False),AccountMeta(buyback,False,True)]
 if overrides:overrides(h,metas)
 data=bytes(ix['discriminator'])+struct.pack('<QQ',amount,limit)
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

def legacy_transferfee(key,bps=100,maximum=2**64-1):
 def ov(h,m):
  transferfee(key,bps,maximum)(h,m);m[11 if key==base else 12]=AccountMeta(TOKEN22,False,False)
  if key==quote:
   for idx,old in [(10,PROTOCOL_ATA),(17,CREATOR_ATA),(23,buyback)]:
    a=h.vm.get_account(old);owner=Pubkey.from_bytes(a.data[32:64]);new=Pubkey.find_program_address([bytes(owner),bytes(TOKEN22),bytes(quote)],ATA)[0];d=bytearray(a.data[:165])+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(new,Account(a.lamports,bytes(d),TOKEN22));m[idx]=AccountMeta(new,False,True)
 return ov
def legacy_rekey(quote_key,canonical=True,index=0):
 def ov(h,m):
  old=h.vm.get_account(pool);data=bytearray(old.data);creator=Pubkey.find_program_address([b'pool-authority',bytes(base)],PUMP)[0] if canonical else OUTSIDER.pubkey();new,bump=Pubkey.find_program_address([b'pool',struct.pack('<H',index),bytes(creator),bytes(base),bytes(quote_key)],PROGRAM);data[8]=bump;data[9:11]=struct.pack('<H',index);data[11:43]=bytes(creator);data[75:107]=bytes(quote_key);h.vm.set_account(new,Account(old.lamports,bytes(data),old.owner));m[0]=AccountMeta(new,False,True);h.vm.set_account(quote_key,h.vm.get_account(quote));m[4]=AccountMeta(quote_key,False,False)
  for key in [vaultbase,vaultquote,userquote]:
   a=h.vm.get_account(key);d=bytearray(a.data)
   if key!=vaultbase:d[:32]=bytes(quote_key)
   if key!=userquote:d[32:64]=bytes(new)
   h.vm.set_account(key,Account(a.lamports,bytes(d),a.owner))
  for idx,old in [(10,PROTOCOL_ATA),(17,CREATOR_ATA),(23,buyback)]:
   a=h.vm.get_account(old);owner=Pubkey.from_bytes(a.data[32:64]);new=Pubkey.find_program_address([bytes(owner),bytes(TOKEN),bytes(quote_key)],ATA)[0];d=bytearray(a.data);d[:32]=bytes(quote_key);h.vm.set_account(new,Account(a.lamports,bytes(d),a.owner));m[idx]=AccountMeta(new,False,True)
 return ov

owner=Pubkey.from_bytes(base64.b64decode(f['accounts']['buyback_fee_recipient']['data_base64'])[32:64]);p2=Pubkey.find_program_address([b'pool-v2',bytes(base)],PROGRAM)[0];uvata=Pubkey.find_program_address([bytes(volume),bytes(TOKEN),bytes(quote)],ATA)[0]
def cash(present=True,change=None):
 def ov(h,m):
  mutate(pool,244,b'\1')(h,m);del m[21:]
  for key in [p2,owner]:h.vm.set_account(key,Account(10**9,b'',Pubkey.default()))
  if present:
   disc=bytes(next(x for x in IDL['accounts'] if x['name']=='UserVolumeAccumulator')['discriminator']);h.vm.set_account(volume,Account(10**9,(disc+bytes(PAYER.pubkey())+bytes(97)),PROGRAM));h.vm.set_account(uvata,Account(2039280,token(quote,volume,0,True),TOKEN))
  m.extend([AccountMeta(uvata,False,True),AccountMeta(volume,False,True),AccountMeta(p2,False,False),AccountMeta(owner,False,False),AccountMeta(buyback,False,True)])
  if change:change(h,m)
 return ov

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();a.candidate=(_CALLER_CWD/a.candidate).resolve();a.output=(_CALLER_CWD/a.output).resolve();rows=[]
 def test(label,**kw):
  x,y=legacy(**kw),legacy(candidate=a.candidate,**kw);diff=[k for k in x if k!='logs' and x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'diff':diff})
 def tail(count,skip=False):
  def ov(h,m):
   if skip:del m[21]
   del m[21+count:]
  return ov
 for amount in [0,1,1000,10**6,10**10,2**64-1]:
  for count in [0,1,2,3]:
   for skip in [False,True]:test('amount-tail='+str((amount,count,skip)),amount=amount,overrides=tail(count,skip))
 for limit in [0,1,1802114,1802115,1802116,2**64-1]:test('limit='+str(limit),limit=limit)
 test('unsigned',unsigned=True)
 for length in range(24):test('payload='+str(length),payload_length=length)
 for idx in range(24):
  if idx!=1:test('substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
 for idx in [0,5,6,7,8,10,17,23]:test('readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
 for key in [pool,CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,feeconfig,PROTOCOL_ATA,CREATOR_ATA,buyback]:
  for owner in [Pubkey.default(),TOKEN22]:test('owner='+str((key,owner)),overrides=mutate(key,0,b'',owner=owner))
 for off,v in [(243,b'\1'),(244,b'\1'),(270,b'\1'),(261,struct.pack('<Q',100)),(245,(10**9).to_bytes(16,'little',signed=True))]:test('pool-field='+str((off,v.hex())),overrides=mutate(pool,off,v))
 for key,offset in [(vaultbase,64),(vaultquote,64),(userbase,64),(userquote,64),(base,36)]:
  for value in [0,1,2**64-1]:test('amount-field='+str((key,offset,value)),overrides=mutate(key,offset,struct.pack('<Q',value)))
 for v in [-2**127,-10**13,-125882,0,1,10**9,2**64,2**127-1]:test('virtual='+str(v),overrides=mutate(pool,245,v.to_bytes(16,'little',signed=True)))
 for flags in [0,1,2,4,8,16,31,255]:test('disable='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
 for length in [0,7,8,210,211,243,244,245,261,270,271,286,287,300]:test('pool-layout='+str(length),overrides=mutate(pool,0,b'',length))
 for length in [0,7,8,65,69,1068,1069,2511,2512,3000,4072,4073,4096,4097]:test('fee-layout='+str(length),overrides=mutate(feeconfig,0,b'',length))
 for off in [261,271,279]:
  for v in [0,1,10**9,2**64-1]:test('pool-fees='+str((off,v)),overrides=mutate(pool,off,struct.pack('<Q',v)))
 for v in [0,1,9999,10000,10001,2**64-1]:test('buyback-bps='+str(v),overrides=mutate(CONFIG_KEY,899,struct.pack('<Q',v)))
 for key in [userbase,userquote,vaultbase,vaultquote,PROTOCOL_ATA,CREATOR_ATA,buyback]:
  for off,v in [(0,bytes(32)),(32,bytes(OUTSIDER.pubkey())),(108,b'\0'),(108,b'\2')]:test('token-field='+str((key,off,v.hex())),overrides=mutate(key,off,v))
  def missing(h,m,key=key):h.vm.set_account(key,Account(0,b'',Pubkey.default()))
  test('missing-token='+str(key),overrides=missing)

 for amount in [1,1000,10**6,10**10]:
  for present in [False,True]:test('cashback='+str((amount,present)),amount=amount,overrides=cash(present))
 for key in [volume,uvata]:
  for owner in [Pubkey.default(),TOKEN,PROGRAM]:test('cash-owner='+str((key,owner)),overrides=cash(change=mutate(key,0,b'',owner=owner)))
 for length in [0,7,8,40,73,74,81,82,89,90,136,137]:test('cash-length='+str(length),overrides=cash(change=mutate(volume,0,b'',length)))
 for off,val in [(0,bytes(8)),(8,bytes(32)),(8,bytes(OUTSIDER.pubkey())),(40,b'\2'),(74,struct.pack('<Q',2**64-1))]:test('cash-field='+str((off,val.hex())),overrides=cash(change=mutate(volume,off,val)))
 for idx in [21,22,23]:
  for mode in ['readonly','substitute']:test('cash-meta='+str((idx,mode)),overrides=cash(change=meta_mutation(idx,mode)))
 for off,val in [(0,bytes(32)),(32,bytes(OUTSIDER.pubkey())),(108,b'\0'),(108,b'\2')]:test('cash-token-field='+str((off,val.hex())),overrides=cash(change=mutate(uvata,off,val)))
 for count in range(6):
  def trim(h,m,count=count):del m[21+count:]
  test('cash-tail='+str(count),overrides=cash(change=trim))
 for lamports in [1,1844399,1844400,10**9]:
  def prefund(h,m,lamports=lamports):h.vm.set_account(volume,Account(lamports,b'',Pubkey.default()))
  test('cash-prefund='+str(lamports),overrides=cash(False,prefund))
 for key in [base,quote]:
  for bps in [0,1,100,9999,10000]:
   for maximum in [0,1,123,2**64-1]:test('transfer-fee='+str((key,bps,maximum)),overrides=legacy_transferfee(key,bps,maximum))
 for key in [quote,Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v'),Pubkey.from_bytes(bytes([90])*32)]:
  for canonical in [False,True]:
   for length in [65,69,1068,1069,2511,2512,3000,4072,4073,4096,4097]:test('quote-layout='+str((key,canonical,length)),overrides=combine(legacy_rekey(key,canonical),mutate(feeconfig,0,b'',length)))
 for tiers in [[],[(0,(0,0,0))],[(0,(10,20,30))],[(2**120,(10,20,30)),(0,(40,50,60))],[(0,(10,20,30)),(0,(40,50,60))],[(0,(10000,10000,10000))],[(0,(2**64-1,0,0))]]:test('fee-table='+str(tiers),overrides=custom_fee_table(tiers))

 def mayhem(h,m):
  mutate(pool,243,b'\1')(h,m);mutate(CONFIG_KEY,385,bytes(PROTOCOL))(h,m)
 for amount in [1,10**6,10**10]:test('mayhem='+str(amount),amount=amount,overrides=mayhem)
 for amount in [1,10**6,10**10,10**15]:
  for q in [1,10**8,10**9]:
   for virtual in [-1,0,10**10]:test('cap='+str((amount,q,virtual)),amount=amount,overrides=combine(mutate(vaultquote,64,struct.pack('<Q',q)),mutate(pool,245,virtual.to_bytes(16,'little',signed=True)),mutate(pool,271,bytes(16))))
 for source,dest in [(5,7),(6,8),(10,8),(17,8),(23,8)]:
  def alias(h,m,source=source,dest=dest):m[source]=m[dest]
  test('alias='+str((source,dest)),overrides=alias)

 # Additional crossed cases bind validation precedence and fee-account behavior.
 for qtotal in [10**9,10**10]:
  b=int(f['pool_base_vault_amount_raw']);curve=qtotal*10**10//(b+10**10);lpfee=(curve*2+9999)//10000;protocolfee=(curve*93+9999)//10000;creatorfee=(curve*30+9999)//10000
  for real in [0,curve-lpfee-protocolfee-creatorfee-1,curve-lpfee-protocolfee-creatorfee,curve-lpfee-1,curve-lpfee,curve,curve+1]:
   for accrued in [0,12345]:
    for limit in [0,2**64-1]:test('real-boundary='+str((qtotal,real,accrued,limit)),limit=limit,overrides=combine(mutate(vaultquote,64,struct.pack('<Q',real+accrued)),mutate(pool,245,(qtotal-real-accrued).to_bytes(16,'little',signed=True)),mutate(pool,271,struct.pack('<QQ',accrued,0))))
 for present in [False,True]:
  for bps in [1,100,10000]:
   for maximum in [1,2**64-1]:
    def cash_tf(h,m,present=present,bps=bps,maximum=maximum):
     legacy_transferfee(quote,bps,maximum)(h,m);buy=m[23];cash(present)(h,m);m[25]=buy;new=Pubkey.find_program_address([bytes(volume),bytes(TOKEN22),bytes(quote)],ATA)[0];m[21]=AccountMeta(new,False,True)
     if present:h.vm.set_account(new,Account(2039280,token(quote,volume,0,True)+bytes([2])+struct.pack('<HHQ',2,8,0),TOKEN22))
    test('cash-transfer-fee='+str((present,bps,maximum)),overrides=cash_tf)
 for idx in [21,22,23]:
  for owner in [Pubkey.default(),TOKEN,PROGRAM]:
   def own(h,m,idx=idx,owner=owner):mutate(m[idx].pubkey,0,b'',owner=owner)(h,m)
   test('remaining-owner='+str((idx,owner)),overrides=own)
 for count in range(4):test('mayhem-tail='+str(count),overrides=combine(mayhem,tail(count)))
 for length in [0,1,8,90,287]:
  def lengthp2(h,m,length=length):mutate(m[21].pubkey,0,b'',length)(h,m)
  test('pool-v2-layout='+str(length),overrides=lengthp2)
 for idx in [17,10,23]:
  for amount in [1,1000,10**6]:
   def remove(h,m,idx=idx,amount=amount):
    if amount<10**6:del m[21]
    target=idx if idx!=23 or amount>=10**6 else 22;h.vm.set_account(m[target].pubkey,Account(0,b'',Pubkey.default()))
   test('zero-fee-ata='+str((idx,amount)),amount=amount,overrides=remove)
 for flag in [243,244,270]:
  for other in [243,244,270]:
   if flag<other:test('flags='+str((flag,other)),overrides=combine(mayhem if flag==243 else cash(),mutate(pool,other,b'\1')))
 for value in [Pubkey.default(),OUTSIDER.pubkey()]:
  def creator_override(h,m,value=value):
   mutate(pool,211,bytes(value))(h,m);vault=Pubkey.find_program_address([b'creator_vault',bytes(value)],PROGRAM)[0];ata=Pubkey.find_program_address([bytes(vault),bytes(TOKEN),bytes(quote)],ATA)[0];h.vm.set_account(vault,Account(10**9,b'',Pubkey.default()));h.vm.set_account(ata,Account(2039280,token(quote,vault,0,True),TOKEN));m[17]=AccountMeta(ata,False,True);m[18]=AccountMeta(vault,False,False)
   if value==Pubkey.default():del m[21]
  test('creator='+str(value),overrides=creator_override)

 for amount in [1,2,100,1000]:
  for zero_creator in [False,True]:
   for holder in [False,True]:
    def zero_cashback(h,m,zero_creator=zero_creator,holder=holder):
     mutate(pool,244,b'\1')(h,m);mutate(pool,270,bytes([holder]))(h,m);del m[21]
     if zero_creator:
      creator=Pubkey.default();mutate(pool,211,bytes(creator))(h,m);vault=Pubkey.find_program_address([b'creator_vault',bytes(creator)],PROGRAM)[0];ata=Pubkey.find_program_address([bytes(vault),bytes(TOKEN),bytes(quote)],ATA)[0];h.vm.set_account(vault,Account(10**9,b'',Pubkey.default()));h.vm.set_account(ata,Account(2039280,token(quote,vault,0,True),TOKEN));m[17]=AccountMeta(ata,False,True);m[18]=AccountMeta(vault,False,False)
    test('zero-fee-cashback-event='+str((amount,zero_creator,holder)),amount=amount,overrides=zero_cashback)
 failures=[i for i,r in enumerate(rows) if r['diff']];sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();report={'scope':'AMM legacy sell scratch differential; ordinary verified signatures, synthetic signer/state fixtures and actual captured token/ATA/Fees CPI. Not whole-program equality.','candidate_sha256':sha(pin_program(a.candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':failures,'cases':rows};a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatches':failures}));raise SystemExit(bool(failures))
if __name__=='__main__':main()
