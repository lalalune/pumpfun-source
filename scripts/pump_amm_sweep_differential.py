#!/usr/bin/env python3
"""Local protocol and creator fee sweep differential."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
def sweep(name='sweep_protocol_fee',amount=1000,candidate=None,recipient=None,overrides=None,unsigned=False,payload_length=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 for row in f['accounts'].values():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(RAW),PROGRAM))
 d=bytearray(poolraw);d[245:261]=bytes(16);d[271:287]=bytes(16);struct.pack_into('<Q',d,271 if name=='sweep_protocol_fee' else 279,amount);h.vm.set_account(pool,Account(10**9,bytes(d),PROGRAM))
 recipient=recipient or (Pubkey.from_bytes(bytes(RAW[57:89])) if name=='sweep_protocol_fee' else Pubkey.find_program_address([b'creator_vault',bytes(poolraw[211:243])],PROGRAM)[0])
 ata=Pubkey.find_program_address([bytes(recipient),bytes(TOKEN),bytes(quote)],ATA)[0];keys=[PAYER.pubkey(),CONFIG_KEY,pool,quote,TOKEN,vaultquote,recipient,ata,Pubkey.default(),ATA,EVENT,PROGRAM];ix=next(x for x in IDL['instructions'] if x['name']==name);metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 data=bytes(ix['discriminator'])
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[0]=AccountMeta(PAYER.pubkey(),False,True)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 states={}
 for m in metas:
  a=h.vm.get_account(m.pubkey)
  if a is None or not a.executable:states[str(m.pubkey)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'error':str(r.err()) if failed else None,'states':states,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();candidate=args.candidate;rows=[]
 def test(name,label,**kw):
  x=sweep(name,**kw);y=sweep(name,candidate=candidate,**kw)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diffs=[k for k in x if x[k]!=y[k]];rows.append({'instruction':name,'case':label,'original':x,'candidate':y,'diff':diffs})
 q=int.from_bytes(base64.b64decode(f['accounts']['pool_quote_token_account']['data_base64'])[64:72],'little')
 for name in ['sweep_protocol_fee','sweep_creator_fee']:
  for amount in [0,1,1000,q-1,q,q+1,2**64-1]:test(name,'amount='+str(amount),amount=amount)
  for idx in range(1,12):test(name,'substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
  for idx in [0,2,5,7]:test(name,'readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
  for size in [0,8,210,211,243,245,261,271,286,287,300]:test(name,'pool-size='+str(size),overrides=mutate(pool,0,b'',size))
  for off in [271,279]:
   for value in [0,1,q,2**64-1]:
    for amount in [0,1000]:test(name,'fee-field='+str((off,value,amount)),amount=amount,overrides=mutate(pool,off,struct.pack('<Q',value)))
  for value in [-2**127,-1000,-1,0,1,2**127-1000,2**127-1]:test(name,'virtual='+str(value),overrides=mutate(pool,245,value.to_bytes(16,'little',signed=True)))
  for idx in [5,7]:
   for off,val in [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\2')]:
    def field(h,m,idx=idx,off=off,val=val):
     if idx==7:h.vm.set_account(m[7].pubkey,Account(2039280,token(quote,m[6].pubkey,0,True),TOKEN))
     a=h.vm.get_account(m[idx].pubkey);d=bytearray(a.data);d[off:off+len(val)]=val;h.vm.set_account(m[idx].pubkey,Account(a.lamports,bytes(d),a.owner))
    test(name,'token-field='+str((idx,off)),overrides=field)
  for flags in [0,1,2,4,8,16,255]:test(name,'disable='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
  for off,value in [(243,b'\1'),(244,b'\1'),(211,bytes(32)),(8,b'\0')]:test(name,'pool-field='+str(off),overrides=mutate(pool,off,value))
  for recipient in [PAYER.pubkey(),Pubkey.default(),Pubkey.from_bytes(bytes(RAW[385:417])),Pubkey.from_bytes(bytes(RAW[418:450]))]:
   for mayhem in [0,1]:test(name,'recipient='+str((recipient,mayhem)),recipient=recipient,overrides=mutate(pool,243,bytes([mayhem])))
  for bps in [0,1,100,10000]:
   def fee(h,m,bps=bps):
    a=h.vm.get_account(quote);d=a.data[:82]+bytes(83)+b'\1';conf=bytes(72)+struct.pack('<QQH',0,2**64-1,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(quote,Account(a.lamports,d,TOKEN22));a=h.vm.get_account(vaultquote);d=a.data[:165]+b'\2'+struct.pack('<HHQ',2,8,0);h.vm.set_account(vaultquote,Account(a.lamports,d,TOKEN22));m[4]=AccountMeta(TOKEN22,False,False);ata=Pubkey.find_program_address([bytes(m[6].pubkey),bytes(TOKEN22),bytes(quote)],ATA)[0];m[7]=AccountMeta(ata,False,True)
   test(name,'quote-fee='+str(bps),overrides=fee)

 for name in ['sweep_protocol_fee','sweep_creator_fee']:
  test(name,'unsigned',unsigned=True)
  for length in range(8):test(name,'short-payload='+str(length),payload_length=length)
  for size in [243,271,286,287]:
   for rent in [1,1000000,2888400]:
    def resize(h,m,size=size,rent=rent):
     a=h.vm.get_account(pool);h.vm.set_account(pool,Account(rent,a.data[:size],a.owner))
    test(name,'rent-resize='+str((size,rent)),overrides=resize)
  for owner in [Pubkey.default(),PROGRAM,TOKEN22]:
   for size in [0,165]:
    def existing(h,m,owner=owner,size=size):h.vm.set_account(m[7].pubkey,Account(2039280,token(quote,m[6].pubkey,0,True)[:size],owner))
    test(name,'recipient-token-owner='+str((owner,size)),overrides=existing)
  for amount in [0,1000]:
   def existing(h,m):h.vm.set_account(m[7].pubkey,Account(2039280,token(quote,m[6].pubkey,0,True),TOKEN))
   test(name,'existing-ATA='+str(amount),amount=amount,overrides=existing)

 for offset,mayhem in [(57,0),(385,1),(418,1),(450,1)]:
  for key in [PAYER.pubkey(),OUTSIDER.pubkey(),pool,Pubkey.default()]:
   test('sweep_protocol_fee','mutated-recipient='+str((offset,key)),recipient=key,overrides=combine(mutate(CONFIG_KEY,offset,bytes(key)),mutate(pool,243,bytes([mayhem]))))
 for owner in [pool,OUTSIDER.pubkey()]:
  for amount in [0,1000]:test('sweep_protocol_fee','self-transfer='+str((owner,amount)),amount=amount,recipient=pool,overrides=combine(mutate(CONFIG_KEY,57,bytes(pool)*8),mutate(vaultquote,32,bytes(owner))))
 for amount in [0,1000]:
  key=Pubkey.find_program_address([b'creator_vault',bytes(32)],PROGRAM)[0]
  test('sweep_creator_fee','zero-coin-creator='+str(amount),amount=amount,recipient=key,overrides=mutate(pool,211,bytes(32)))
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'SBF protocol/creator fee sweeps: ordinary local signed transactions, exact token/ATA/System/event CPIs, full committed states and errors. Captured SPL/Token2022/ATA; bounded synthetic account and transfer-fee variations, not whole-program equivalence.','candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
