import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
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

PUMP=Pubkey.from_string(json.load(open('evidence/upstream/pump.json'))['address']);PUMPVAULT=Pubkey.find_program_address([b'creator-vault',bytes(CREATOR)],PUMP)[0];PUMPATA=Pubkey.find_program_address([bytes(PUMPVAULT),bytes(TOKEN),bytes(quote)],ATA)[0]
def transfer(name='transfer_creator_fees_to_pump',amount=1000,candidate=None,overrides=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:h.vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 row=f['accounts']['quote_mint'];h.vm.set_account(quote,Account(row['lamports'],base64.b64decode(row['data_base64']),TOKEN));h.vm.set_account(VAULT,Account(min(2**64-1,amount+2039280),token(quote,AUTH,amount,True),TOKEN));h.vm.set_account(AUTH,Account(10**9,b'',Pubkey.default()));h.vm.set_account(PUMPVAULT,Account(10**9,b'',Pubkey.default()));h.vm.set_account(PUMPATA,Account(0,b'',Pubkey.default()))
 ix=next(x for x in IDL['instructions'] if x['name']==name)
 if name.endswith('_v2'):keys=[PAYER.pubkey(),quote,TOKEN,Pubkey.default(),ATA,CREATOR,AUTH,VAULT,PUMPVAULT,PUMPATA,EVENT,PROGRAM]
 else:keys=[quote,TOKEN,Pubkey.default(),ATA,CREATOR,AUTH,VAULT,PUMPVAULT,EVENT,PROGRAM]
 metas=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable'))) for k,a in zip(keys,ix['accounts'])]
 if overrides:overrides(h,metas)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,bytes(ix['discriminator']),metas)],PAYER.pubkey(),[PAYER],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 states={}
 for m in metas:
  a=h.vm.get_account(m.pubkey)
  if a is None or not a.executable:states[str(m.pubkey)]=None if a is None else {'data':bytes(a.data).hex(),'lamports':a.lamports,'owner':str(a.owner)}
 return {'error':str(r.err()) if failed else None,'states':states,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions']}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();candidate=args.candidate;rows=[]
 def test(name,label,**kw):
  x=transfer(name,**kw);y=transfer(name,candidate=candidate,**kw)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diff=[k for k in x if x[k]!=y[k]];rows.append({'instruction':name,'case':label,'original':x,'candidate':y,'diff':diff})
 for name in ['transfer_creator_fees_to_pump','transfer_creator_fees_to_pump_v2']:
  v2=name.endswith('_v2')
  for amount in [0,1,1000,10**9,2**64-2039281,2**64-1]:test(name,'amount='+str(amount),amount=amount)
  for idx in range(1 if v2 else 0,12 if v2 else 10):test(name,'substitute='+str(idx),overrides=meta_mutation(idx,'substitute'))
  for idx in ([0,6,7,8,9] if v2 else [5,6,7]):test(name,'readonly='+str(idx),overrides=meta_mutation(idx,'readonly'))
  for key in [AUTH,PUMPVAULT]:
   for lamports in [0,1,2039280,10**9]:
    def balance(h,m,key=key,lamports=lamports):h.vm.set_account(key,Account(lamports,b'',Pubkey.default()))
    test(name,'balance='+str((key,lamports)),overrides=balance)
   for owner in [Pubkey.default(),PROGRAM,TOKEN]:test(name,'owner='+str((key,owner)),overrides=mutate(key,0,b'',owner=owner))
   test(name,'authority-data='+str(key),overrides=mutate(key,0,b'123'))
  for key in [VAULT]:
   for off,val in [(0,bytes(32)),(32,bytes(32)),(64,bytes(8)),(108,b'\2'),(108,b'\0'),(109,bytes(4))]:test(name,'vault-field='+str(off),overrides=mutate(key,off,val))
   for size in [0,1,164,165,166]:test(name,'vault-size='+str(size),overrides=mutate(key,0,b'',size))
   for owner in [Pubkey.default(),PROGRAM,TOKEN22]:test(name,'vault-owner='+str(owner),overrides=mutate(key,0,b'',owner=owner))
  for owner in [Pubkey.default(),PROGRAM,TOKEN22]:test(name,'mint-owner='+str(owner),overrides=mutate(quote,0,b'',owner=owner))
  fee=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ');test(name,'creator-fees-owned',overrides=mutate(CREATOR,0,b'',owner=fee))

 def non_sol(amount=1000,program=TOKEN,fee=None,dest_field=None,dest_owner=None):
  def apply(h,m):
   row=f['accounts']['base_mint'];data=base64.b64decode(row['data_base64']);tail=b''
   if fee is not None:
    bps,maximum=fee;conf=bytes(72)+struct.pack('<QQH',0,maximum,bps)*2;data=data[:82]+bytes(83)+b'\1'+struct.pack('<HH',1,len(conf))+conf;tail=b'\2'+struct.pack('<HHQ',2,8,0)
   h.vm.set_account(base,Account(row['lamports'],data,program));m[1]=AccountMeta(base,False,False);m[2]=AccountMeta(program,False,False)
   vault=Pubkey.find_program_address([bytes(AUTH),bytes(program),bytes(base)],ATA)[0];h.vm.set_account(vault,Account(10**9,token(base,AUTH,amount)+tail,program));m[7]=AccountMeta(vault,False,True);dest=Pubkey.find_program_address([bytes(PUMPVAULT),bytes(program),bytes(base)],ATA)[0];m[9]=AccountMeta(dest,False,True)
   if dest_field is not None or dest_owner is not None:
    data=bytearray(token(base,PUMPVAULT,0)+tail)
    if dest_field is not None:
     off,val=dest_field;data[off:off+len(val)]=val
    h.vm.set_account(dest,Account(10**9,bytes(data),dest_owner or program))
  return apply
 name='transfer_creator_fees_to_pump_v2'
 for program in [TOKEN,TOKEN22]:
  for amount in [0,1,1000,2**64-1]:test(name,'non-sol='+str((program,amount)),amount=amount,overrides=non_sol(amount,program))
  for off,val in [(0,b''),(0,bytes(32)),(32,bytes(32)),(108,b'\2')]:test(name,'non-sol-dest='+str((program,off,val.hex())),overrides=non_sol(program=program,dest_field=(off,val)))
  for owner in [Pubkey.default(),PROGRAM,TOKEN22]:test(name,'non-sol-dest-owner='+str((program,owner)),overrides=non_sol(program=program,dest_owner=owner))
 for bps in [0,1,100,10000]:
  for maximum in [0,1,2**64-1]:test(name,'non-sol-transferfee='+str((bps,maximum)),overrides=non_sol(program=TOKEN22,fee=(bps,maximum)))
 for name in ['transfer_creator_fees_to_pump','transfer_creator_fees_to_pump_v2']:
  for destination_balance in [0,1,890879,890880,890881]:
   for amount in [0,1,890879,890880,890881]:
    for authority_balance in [0,10**9]:
     def edge(h,m,destination_balance=destination_balance,authority_balance=authority_balance):
      h.vm.set_account(PUMPVAULT,Account(destination_balance,b'',Pubkey.default()));h.vm.set_account(AUTH,Account(authority_balance,b'',Pubkey.default()))
     test(name,'rent-edge='+str((destination_balance,amount,authority_balance)),amount=amount,overrides=edge)
  for size in [1,8,165,1000]:
   for amount in [0,890880,10**9]:
    def destination_data(h,m,size=size):h.vm.set_account(PUMPVAULT,Account(0,bytes(size),PROGRAM))
    test(name,'destination-data-rent='+str((size,amount)),amount=amount,overrides=destination_data)
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'SBF transfer_creator_fees_to_pump and v2: signed local transactions, WSOL close/recreate/System transfers and quote token CPI state/error boundaries. Bounded recovery, not whole-program or byte equivalence.','candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
