#!/usr/bin/env python3
"""Local SBF pool creation differential; no RPC or network transactions."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
def create(base_amount=10**9,quote_amount=10**9,index=0,creator=None,mayhem=False,optional=b'',candidate=None,overrides=None,payload_length=None,unsigned=False):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,name in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/name/'deployed.so')
 glob=bytearray(RAW);glob[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(glob),PROGRAM))
 for n in ['base_mint','quote_mint']:
  row=f['accounts'][n];h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 for key,mint,native in [(userbase,base,False),(userquote,quote,True)]:h.vm.set_account(key,Account(10**15+2039280 if native else 10**9,token(mint,PAYER.pubkey(),10**15,native),TOKEN))
 pool=Pubkey.find_program_address([b'pool',struct.pack('<H',index),bytes(PAYER.pubkey()),bytes(base),bytes(quote)],PROGRAM)[0]
 lp=Pubkey.find_program_address([b'pool_lp_mint',bytes(pool)],PROGRAM)[0]
 ata=lambda owner,mint,program:Pubkey.find_program_address([bytes(owner),bytes(program),bytes(mint)],ATA)[0]
 userlp=ata(PAYER.pubkey(),lp,TOKEN22);vaultbase=ata(pool,base,TOKEN);vaultquote=ata(pool,quote,TOKEN)
 keys=[pool,CONFIG_KEY,PAYER.pubkey(),base,quote,lp,userbase,userquote,userlp,vaultbase,vaultquote,Pubkey.default(),TOKEN22,TOKEN,TOKEN,ATA,EVENT,PROGRAM]
 ix=next(x for x in IDL['instructions'] if x['name']=='create_pool');metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 args=struct.pack('<HQQ',index,base_amount,quote_amount)+bytes(PAYER.pubkey() if creator is None else creator)+bytes([mayhem])+optional
 data=bytes(ix['discriminator'])+args
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[2]=AccountMeta(PAYER.pubkey(),False,True)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 watch=[m.pubkey for m in metas[:11]];states={}
 for k in watch:
  a=h.vm.get_account(k);states[str(k)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'error':str(r.err()) if failed else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions'],'states':states}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();candidate=args.candidate;rows=[]
 def test(label,**kw):
  x=create(**kw);y=create(candidate=candidate,**kw)
  for r in [x,y]:r['events']=[a for a in r['logs'] if a.startswith('Program data: ')];r.pop('logs')
  diff=[k for k in x if x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'diff':diff})
 for b,q in [(0,0),(0,1),(1,0),(1,1),(99,99),(100,100),(101,101),(1,10000),(10000,1),(10**9,10**9),(10**15,10**15),(2**64-1,2**64-1)]:test('amounts='+str((b,q)),base_amount=b,quote_amount=q)
 for index in [0,1,255,256,65535]:test('index='+str(index),index=index)
 for creator in [Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey()]:test('creator='+str(creator),creator=creator)
 for opt in [b'',b'\0',b'\1',b'\2',b'\0\1',b'\0'+bytes(7),b'\0'+bytes(8),b'\0'+bytes(8)+b'\0',b'\0'+bytes(8)+b'\1',b'\0'+bytes(8)+b'\0\1',b'\0'+bytes(8)+b'\0\2']:
  test('optional='+opt.hex(),optional=opt)
 for flags in [0,1,2,4,8,16,255]:test('disable='+str(flags),overrides=mutate(CONFIG_KEY,56,bytes([flags])))
 for off,val in [(417,0),(417,1),(642,0),(642,1),(940,0),(940,1)]:test('globalbool='+str((off,val)),overrides=mutate(CONFIG_KEY,off,bytes([val])))
 test('mayhem',mayhem=True)
 for idx in [i for i in range(18) if i!=2]:test('substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
 for idx in [0,2,5,6,7,8,9,10]:test('readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
 for key in [userbase,userquote]:
  for off,val in [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\2')]:test('tokenfield='+str((key,off)),overrides=mutate(key,off,val))
 for key in [base,quote]:
  for off,val in [(0,bytes(4)),(36,bytes(8)),(44,b'\0'),(44,b'\xff'),(45,b'\0'),(46,struct.pack('<I',1))]:test('mintfield='+str((key,off,val.hex())),overrides=mutate(key,off,val))
 
 for idx in [9,10]:
  for amt in [0,1,100,10**9]:
   def existing(h,m,idx=idx,amt=amt):
    mint=base if idx==9 else quote;native=idx==10
    h.vm.set_account(m[idx].pubkey,Account(amt+2039280 if native else 2039280,token(mint,m[0].pubkey,amt,native),TOKEN))
   test('existing-vault='+str((idx,amt)),overrides=existing)
 for mintkey,programidx,vaultidx,userkey in [(base,13,9,userbase),(quote,14,10,userquote)]:
  for bps in [0,1,100,9999,10000]:
   for maxfee in [0,1,123,2**64-1]:
    def fee(h,m,mintkey=mintkey,programidx=programidx,vaultidx=vaultidx,userkey=userkey,bps=bps,maxfee=maxfee):
     mint=h.vm.get_account(mintkey);d=bytearray(mint.data[:82])+bytes(83)+bytes([1]);conf=bytes(72)+struct.pack('<QQH',0,maxfee,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(mintkey,Account(mint.lamports,bytes(d),TOKEN22))
     a=h.vm.get_account(userkey);d=bytearray(a.data[:165])+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(userkey,Account(a.lamports,bytes(d),TOKEN22));m[programidx]=AccountMeta(TOKEN22,False,False)
     vault=Pubkey.find_program_address([bytes(m[0].pubkey),bytes(TOKEN22),bytes(mintkey)],ATA)[0];m[vaultidx]=AccountMeta(vault,False,True)
    test('transferfee='+str((mintkey,bps,maxfee)),overrides=fee)
 
 for length in range(71):test('payload-length='+str(length),payload_length=length,optional=bytes(11))
 test('unsigned',unsigned=True)
 for typ,size in [(3,32),(6,1),(9,0),(10,52),(12,32),(14,64),(18,64),(20,64),(22,64)]:
  for mintkey,pi,vi,uk in [(base,13,9,userbase),(quote,14,10,userquote)]:
   def ext(h,m,typ=typ,size=size,mintkey=mintkey,pi=pi,vi=vi,uk=uk):
    a=h.vm.get_account(mintkey);body=b'\1' if typ==6 else bytes(size);d=a.data[:82]+bytes(83)+b'\1'+struct.pack('<HH',typ,size)+body;h.vm.set_account(mintkey,Account(a.lamports,d,TOKEN22));a=h.vm.get_account(uk);h.vm.set_account(uk,Account(a.lamports,a.data,TOKEN22));m[pi]=AccountMeta(TOKEN22,False,False);v=Pubkey.find_program_address([bytes(m[0].pubkey),bytes(TOKEN22),bytes(mintkey)],ATA)[0];m[vi]=AccountMeta(v,False,True)
   test('extension='+str((typ,mintkey)),overrides=ext)
   test('extension-zero='+str((typ,mintkey)),base_amount=0,quote_amount=0,overrides=ext)
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'Direct signed local create_pool cases; captured SPL/Token2022/ATA dependencies. Committed account data/lamports/owners, event bytes, errors and exact CPIs. Canonical migration cases are covered separately.','candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
