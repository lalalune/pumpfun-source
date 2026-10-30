#!/usr/bin/env python3
"""Differential-test the compiled Rust fragment against captured Pump Fees locally."""
import argparse,hashlib,json,pathlib,random,struct,subprocess
from solders.litesvm import LiteSVM
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.account import Account
from solders.instruction import Instruction,AccountMeta
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--host',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);args=ap.parse_args()
idl=json.loads((ROOT/'evidence/upstream/pump_fees.json').read_text());prog=Pubkey.from_string(idl['address']);configprog=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P');key,bump=Pubkey.find_program_address([b'fee_config',bytes(configprog)],prog)
disc=bytes(next(a for a in idl['accounts'] if a['name']=='FeeConfig')['discriminator']);ixdisc=bytes(next(a for a in idl['instructions'] if a['name']=='get_fees')['discriminator'])
fees=lambda x:struct.pack('<QQQ',*x)
def encode_tiers(xs):return struct.pack('<I',len(xs))+b''.join(t.to_bytes(16,'little')+fees(f) for t,f in xs)
s=LiteSVM().with_transaction_history(0);payer=Keypair.from_seed(bytes(32));s.airdrop(payer.pubkey(),10**10);s.add_program_from_file(prog,ROOT/'evidence/original/pump_fees/deployed.so');s.set_account(configprog,Account(10**9,b'',Pubkey.default()))
def invoke(tiers,stable,cap,flag,pool=True,trade_size=0,allocation=4097):
 data=disc+bytes([bump])+bytes(32)+fees((1,2,3))+encode_tiers(tiers)+encode_tiers(stable)+fees((1000,2000,3000));data=data.ljust(allocation,b'\0')[:allocation]
 s.set_account(key,Account(10**9,data,prog));payload=ixdisc+bytes([pool])+cap.to_bytes(16,'little')+trade_size.to_bytes(8,'little')+flag
 tx=Transaction.new_signed_with_payer([Instruction(prog,payload,[AccountMeta(key,False,False),AccountMeta(configprog,False,False)])],payer.pubkey(),[payer],s.latest_blockhash());r=s.send_transaction(tx)
 return {'error':str(r.err()),'logs':r.meta().logs()} if isinstance(r,FailedTransactionMetadata) else {'fees':list(struct.unpack('<QQQ',r.return_data().data))}
rng=random.Random(10424);configs=[[(0,(10,20,30)),(100,(40,50,60)),(1000,(70,80,90))],[(500,(1,2,3)),(0,(4,5,6)),(100,(7,8,9))],[(0,(1,2,3)),(100,(4,5,6)),(100,(7,8,9))]]
for _ in range(15): configs.append([(rng.randrange(1<<100),tuple(rng.randrange(1000) for _ in range(3))) for _ in range(rng.randrange(1,12))])
rows=[];stdin=[];expected=[]
for tiers in configs:
 stable=list(reversed(tiers));caps={0,2**128-1}
 for threshold,_ in tiers: caps.update((max(0,threshold-1),threshold,min(2**128-1,threshold+1)))
 for cap in sorted(caps):
  for flag in [b'',b'\0',b'\1']:
   selected=stable if flag==b'\1' else tiers
   trade_size=rng.choice([0,1,2**64-1]);r=invoke(tiers,stable,cap,flag,trade_size=trade_size)
   if 'fees' not in r: raise RuntimeError(f'unexpected original fee-query failure: {r}')
   stdin.append(';'.join([str(cap)]+[','.join(map(str,[t,*f])) for t,f in selected]));expected.append(r['fees'])
   rows.append({'tiers':tiers,'stable_tiers':stable,'market_cap':cap,'option_bool_hex':flag.hex(),'trade_size':trade_size,'original_fees':r['fees']})
run=subprocess.run([str(args.host.resolve())],input='\n'.join(stdin)+'\n',text=True,capture_output=True,check=True);native=[list(map(int,l.split(','))) for l in run.stdout.splitlines()]
if native!=expected:
 mismatch=next((i for i,(actual,wanted) in enumerate(zip(native,expected)) if actual!=wanted),min(len(native),len(expected)))
 raise ValueError(f'native fee selector mismatch at result {mismatch}: expected {len(expected)} results, received {len(native)}')
boundary=[]
for size in [296,297,300,512,1024,2048,4095,4096,4097]: boundary.append({'allocation':size,'result':invoke(configs[0],configs[0],100,b'',allocation=size)})
lo,hi=2048,4095
while lo+1<hi:
 mid=(lo+hi)//2
 if 'fees' in invoke(configs[0],configs[0],100,b'',allocation=mid): hi=mid
 else: lo=mid
boundary.extend({'allocation':n,'result':invoke(configs[0],configs[0],100,b'',allocation=n)} for n in [lo,hi])
negative=[{'case':'empty_normal_tiers','result':invoke([],configs[0],0,b'')},{'case':'empty_stable_tiers','result':invoke(configs[0],[],0,b'\1')},{'case':'invalid_option_bool','result':invoke(configs[0],configs[0],0,b'\2')},{'case':'non_pump_pool','result':invoke([],[],0,b'\1',pool=False)}]
report={'scope':'Recovered selector native Rust versus captured original get_fees; not a rebuilt SBF program. Synthetic accounts only.','original_sha256':hashlib.sha256((ROOT/'evidence/original/pump_fees/deployed.so').read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((ROOT/'programs/pump-fees/recovered/fee_selection.rs').read_bytes()).hexdigest(),'host_sha256':hashlib.sha256(args.host.read_bytes()).hexdigest(),'differential_cases':len(rows),'all_matched':native==expected,'allocation_boundary_probes':boundary,'negative_probes':negative,'cases':rows}
args.output.write_text(json.dumps(report,indent=2)+'\n');print('Matched',len(rows),'cases');print(json.dumps(boundary+negative,indent=2))
