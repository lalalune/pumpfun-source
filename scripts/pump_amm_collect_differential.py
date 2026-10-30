import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from pump_differential_output import PumpReport
ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL');CREATOR=OUTSIDER.pubkey();AUTH,BUMP=Pubkey.find_program_address([b'creator_vault',bytes(CREATOR)],PROGRAM);VAULT=Pubkey.find_program_address([bytes(AUTH),bytes(TOKEN),bytes(quote)],ATA)[0];DEST=Pubkey.from_bytes(bytes([94])*32)
def collect(amount=1000,candidate=None,overrides=None,payload_length=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 row=f['accounts']['quote_mint'];h.vm.set_account(quote,Account(row['lamports'],base64.b64decode(row['data_base64']),TOKEN));h.vm.set_account(VAULT,Account(min(2**64-1,amount+2039280),token(quote,AUTH,amount,True),TOKEN));h.vm.set_account(DEST,Account(2039280,token(quote,CREATOR,0,True),TOKEN))
 ix=next(x for x in IDL['instructions'] if x['name']=='collect_coin_creator_fee');keys=[quote,TOKEN,CREATOR,AUTH,VAULT,DEST,EVENT,PROGRAM];metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 data=bytes(ix['discriminator']);data=data if payload_length is None else data[:payload_length]
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],PAYER.pubkey(),[PAYER],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 states={}
 for m in metas:
  a=h.vm.get_account(m.pubkey)
  if a is None or not a.executable:states[str(m.pubkey)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'error':str(r.err()) if failed else None,'states':states,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();candidate=args.candidate;output=PumpReport(args.output,ROOT,candidate,__file__,extra_inputs=[ROOT/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json']);rows=[]
 def test(label,**kw):
  x=collect(**kw);y=collect(candidate=candidate,**kw)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diff=[k for k in x if x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'diff':diff})
 for amount in [0,1,1000,10**12,2**64-2039281,2**64-1]:test('amount='+str(amount),amount=amount)
 for idx in range(8):test('substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
 for idx in [4,5]:test('readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
 for length in range(8):test('payload='+str(length),payload_length=length)
 for amount in [0,1000]:
  for key in [VAULT,DEST]:
   for off,val in [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\2'),(108,b'\0')]:test('token-field='+str((amount,key,off,val.hex())),amount=amount,overrides=mutate(key,off,val))
   for size in [0,1,164,165,166,200]:test('token-length='+str((amount,key,size)),amount=amount,overrides=mutate(key,0,b'',size))
   for owner in [Pubkey.default(),PROGRAM,TOKEN22]:test('token-owner='+str((amount,key,owner)),amount=amount,overrides=mutate(key,0,b'',owner=owner))
  for key in [quote]:
   for off,val in [(0,bytes(4)),(36,bytes(8)),(44,b'\0'),(44,b'\xff'),(45,b'\0')]:test('mint-field='+str((amount,off,val.hex())),amount=amount,overrides=mutate(key,off,val))
   test('quote-owner-token22='+str(amount),amount=amount,overrides=mutate(quote,0,b'',owner=TOKEN22))
  fee=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ');disc=bytes(next(x for x in IDL['accounts'] if x['name']=='SharingConfig')['discriminator'])
  for owner in [Pubkey.default(),fee,PROGRAM,TOKEN]:
   for data in [b'',disc,disc+bytes(200),bytes(200)]:
    def creator(h,m,owner=owner,data=data):h.vm.set_account(CREATOR,Account(10**9,data,owner))
    test('creator-state='+str((amount,owner,len(data),data[:8].hex())),amount=amount,overrides=creator)
  for bps in [0,1,100,10000]:
   for maximum in [0,1,2**64-1]:
    def transferfee(h,m,bps=bps,maximum=maximum):
     a=h.vm.get_account(quote);d=a.data[:82]+bytes(83)+b'\1';conf=bytes(72)+struct.pack('<QQH',0,maximum,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(quote,Account(a.lamports,d,TOKEN22));m[1]=AccountMeta(TOKEN22,False,False)
     v=Pubkey.find_program_address([bytes(AUTH),bytes(TOKEN22),bytes(quote)],ATA)[0];a=h.vm.get_account(VAULT);d=a.data[:165]+b'\2'+struct.pack('<HHQ',2,8,0);h.vm.set_account(v,Account(a.lamports,d,TOKEN22));m[4]=AccountMeta(v,False,True);a=h.vm.get_account(DEST);d=a.data[:165]+b'\2'+struct.pack('<HHQ',2,8,0);h.vm.set_account(DEST,Account(a.lamports,d,TOKEN22))
    test('transfer-fee='+str((amount,bps,maximum)),amount=amount,overrides=transferfee)
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'SBF collect_coin_creator_fee: signed local transactions, token CPI, events, committed states and error constraints. Bounded recovery, not whole-program or byte equivalence.','candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 output.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
