#!/usr/bin/env python3
"""Compare recovered native quote-selection Rust against original SBF queries."""
import argparse,hashlib,json,pathlib,random,subprocess
from pump_differential_output import PumpReport
from solders.pubkey import Pubkey
from fee_recovery_fixture import FeeFixture,ROOT
ap=argparse.ArgumentParser();ap.add_argument('--host',type=pathlib.Path,required=True);ap.add_argument('--output',type=pathlib.Path,required=True);args=ap.parse_args();report_output=PumpReport(args.output,ROOT,None,__file__,extra_inputs=(args.host,ROOT/'programs/pump-fees/recovered'))
f=FeeFixture();rng=random.Random(10425)
quotes=[bytes(32)]+[bytes(Pubkey.from_string(s)) for s in ['So11111111111111111111111111111111111111112','9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP','EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v']]+[bytes([1])*32]
configs=[([],[]),([(100,(10,20,30)),(1000,(40,50,60))],[(50,(70,80,90)),(100,(100,200,300))]),([(200,(1,2,3)),(0,(4,5,6)),(100,(7,8,9))],[(0,(20,30,40)),(0,(50,60,70))])]
for _ in range(5):configs.append(([(rng.randrange(2**100),tuple(rng.randrange(500) for _ in range(3))) for _ in range(4)],[(rng.randrange(2**100),tuple(rng.randrange(500) for _ in range(3))) for _ in range(4)]))
rows=[];lines=[];expected=[]
def case(normal,stable,flat,exotic,cap,pool,quote):
 f.config(normal,stable,flat,exotic);r=f.query(pool,cap,quote)
 if 'fees' in r:answer=','.join(map(str,r['fees']))
 else:
  if 'ProgramFailedToComplete' not in r['error']: raise RuntimeError(f'unexpected original quote-query failure: {r}')
  answer='PANIC'
 def encode(ts):return '|'.join(','.join(map(str,[t,*fees])) for t,fees in ts)
 lines.append(';'.join([str(cap),str(int(pool)),quote.hex(),','.join(map(str,flat)),','.join(map(str,exotic)),encode(normal),encode(stable)]));expected.append(answer)
 rows.append({'normal':normal,'stable':stable,'flat':flat,'exotic':exotic,'market_cap':cap,'is_pump_pool':pool,'quote_hex':quote.hex(),'original':r})
for normal,stable in configs:
 caps={0,99,100,101,2**64-1,2**64,2**128-1}
 for t,_ in normal+stable:caps.update([max(0,t-1),t,min(2**128-1,t+1)])
 for cap in sorted(caps):
  for pool in [False,True]:
   for q in quotes:
    for exotic in [(0,0,0),(0,0,1),(2,0,0),(0,3,0),(4,5,6)]:case(normal,stable,(11,22,33),exotic,cap,pool,q)
# Mutate every byte of each recognized quote constant; all 32 bytes matter.
for q in quotes[:4]:
 for i in range(32):
  altered=bytearray(q);altered[i]^=1;case(configs[1][0],configs[1][1],(11,22,33),(4,5,6),100,True,bytes(altered))
r=subprocess.run([str(args.host.resolve())],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True);actual=r.stdout.splitlines()
if len(actual)!=len(expected): raise ValueError(f'native quote host result count mismatch: expected {len(expected)}, received {len(actual)}')
failures=[i for i,(a,b) in enumerate(zip(actual,expected)) if a!=b]
report={'original_sha256':hashlib.sha256((ROOT/'evidence/original/pump_fees/deployed.so').read_bytes()).hexdigest(),'source_sha256':{p:hashlib.sha256((ROOT/'programs/pump-fees/recovered'/p).read_bytes()).hexdigest() for p in ['fee_selection.rs','quote_fees.rs','quote_fees_host.rs','memory_compare.rs']},'host_sha256':hashlib.sha256(args.host.read_bytes()).hexdigest(),'case_count':len(rows),'mismatches':failures,'scope':'Native recovered quote routing versus original get_fees_with_quote_mint. Synthetic state including unreachable candidates; not complete handler or SBF byte identity.','cases':rows}
report_output.write((json.dumps(report,separators=(',',':'))+'\n').encode("utf-8"));print('Cases',len(rows),'mismatches',len(failures))
if failures: raise ValueError(f'native quote host mismatches at results {failures[:10]}')
