#!/usr/bin/env python3
"""Execute recovered query handlers and captured original independently in LiteSVM."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import argparse,gzip,hashlib,json,pathlib,struct
from fee_recovery_fixture import *
from pump_differential_output import PumpReport
p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);args=p.parse_args();publisher=PumpReport(args.output,ROOT,args.candidate,__file__,extra_inputs=[ROOT/'research/fees-query-inputs/quote-selector-cases.json.gz',ROOT/'research/fees-query-inputs/fee-selector-cases.json.gz'])
original=FeeFixture();candidate=FeeFixture(args.candidate);fixtures=[original,candidate]
rows=[];failures=[]
def outcome(r):return {'fees':r['fees']} if 'fees' in r else {'error':r['error']}
def record(name,results):
 row={'name':name,'original':outcome(results[0]),'candidate':outcome(results[1])};rows.append(row)
 if row['original']!=row['candidate']:failures.append(row)
def run(name,data,raw=None,owner=None,key=None,count=2):
 results=[]
 for f in fixtures:
  actual_key=key or f.key
  f.vm.set_account(actual_key,Account(10**9,data,owner or f.program))
  before=f.vm.get_account(actual_key)
  ix=next(i for i in f.idl['instructions'] if i['name']=='get_fees_with_quote_mint')
  payload=raw if raw is not None else bytes(ix['discriminator'])+b'\1'+(100).to_bytes(16,'little')+bytes(32)
  accounts=[AccountMeta(actual_key,False,False),AccountMeta(f.config_program,False,False)][:count]
  tx=Transaction.new_signed_with_payer([Instruction(f.program,payload,accounts)],f.payer.pubkey(),[f.payer],f.vm.latest_blockhash())
  r=f.vm.send_transaction(tx)
  if isinstance(r,FailedTransactionMetadata):results.append({'error':str(r.err())})
  else:results.append({'fees':list(struct.unpack('<QQQ',r.return_data().data))})
  after=f.vm.get_account(actual_key)
  assert before.data==after.data and before.lamports==after.lamports,(name,'query mutated account')
 record(name,results)
receipt=ROOT/'research/fees-query-inputs/quote-selector-cases.json.gz'
cases=json.loads(gzip.decompress(receipt.read_bytes()))['cases']
for i,c in enumerate(cases):
 results=[]
 for f in fixtures:
  f.config(c['normal'],c['stable'],c['flat'],c['exotic'])
  before=f.vm.get_account(f.key)
  results.append(f.query(c['is_pump_pool'],c['market_cap'],bytes.fromhex(c['quote_hex'])))
  after=f.vm.get_account(f.key)
  assert before.data==after.data and before.lamports==after.lamports
 record('quote-'+str(i),results)
tier_receipt=ROOT/'research/fees-query-inputs/fee-selector-cases.json.gz'
tier_cases=json.loads(gzip.decompress(tier_receipt.read_bytes()))['cases']
tier_disc=bytes(next(i['discriminator'] for i in original.idl['instructions'] if i['name']=='get_fees'))
for i,c in enumerate(tier_cases):
 original.config(c['tiers'],c['stable_tiers'],(1,2,3),(1000,2000,3000))
 data=original.vm.get_account(original.key).data
 payload=tier_disc+b'\1'+c['market_cap'].to_bytes(16,'little')+c['trade_size'].to_bytes(8,'little')+bytes.fromhex(c['option_bool_hex'])
 run('get-fees-tier-'+str(i),data,raw=payload)
original.config([(0,(1,2,3))],[(0,(4,5,6))],(7,8,9),(10,11,12));base=original.vm.get_account(original.key).data
run('wrong-owner',base,owner=Pubkey.default())
run('wrong-disc',bytes(8)+base[8:])
run('wrong-bump',base[:8]+bytes([base[8]^1])+base[9:])
run('wrong-key',base,key=Pubkey.from_bytes(bytes([21])*32))
for n in [0,7,8,9,100,150,200,2511,2512,2513,4097]:run('account-len-'+str(n),base[:n])
for offset in [65,109]:
 for count in [0,1,2,29,30,31,60,61,62,100,1024,2**32-1]:
  altered=base[:offset]+count.to_bytes(4,'little')+base[offset+4:]
  run('vector-count-'+str(offset)+'-'+str(count),altered)
for n in [0,1]:run('account-count-'+str(n),base,count=n)
for name in ['get_fees','get_fees_with_quote_mint']:
 disc=bytes(next(i['discriminator'] for i in original.idl['instructions'] if i['name']==name))
 valid=disc+b'\1'+(100).to_bytes(16,'little')+(bytes(8)+b'\0' if name=='get_fees' else bytes(32))
 for n in range(len(valid)+1):run(name+'-payload-length-'+str(n),base,raw=valid[:n])
 run(name+'-invalid-pool-bool',base,raw=valid[:8]+b'\2'+valid[9:])
 run(name+'-extra-data',base,raw=valid+b'\xff'*16)
 if name=='get_fees':
  for pool in [0,1]:
   for flag in [b'',b'\0',b'\1',b'\2']:
    run('get_fees-pool-'+str(pool)+'-flag-'+flag.hex(),base,raw=disc+bytes([pool])+(100).to_bytes(16,'little')+bytes(8)+flag)
# Allocation-gated legacy layouts: stable schedule begins at4073, exotic at4097.
original.config([(0,(1,2,3))],[(0,(4,5,6))],(7,8,9),(10,11,12),allocation=5000)
legacy_base=original.vm.get_account(original.key).data
quote_disc=bytes(next(i['discriminator'] for i in original.idl['instructions'] if i['name']=='get_fees_with_quote_mint'))
for size in [2511,2512,4072,4073,4096,4097,5000]:
 for quote in [bytes(32),bytes(Pubkey.from_string('So11111111111111111111111111111111111111112')),bytes(Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')),bytes([45])*32]:
  payload=quote_disc+b'\1'+(100).to_bytes(16,'little')+quote
  run('legacy-allocation-'+str(size)+'-'+quote.hex(),legacy_base[:size],raw=payload)
 for count in [0,61,2**32-1]:
  data=legacy_base[:109]+count.to_bytes(4,'little')+legacy_base[113:]
  run('legacy-stable-count-'+str(size)+'-'+str(count),data[:size])
report={'scope':'Two independently executing full query handlers only; other handlers unsupported. Error numbers/return bytes and read-only state tested; logs, compute, full byte identity not asserted.','original_sha256':hashlib.sha256((ROOT/'evidence/original/pump_fees/deployed.so').read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(args.candidate.read_bytes()).hexdigest(),'input_receipt_sha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'tier_input_receipt_sha256':hashlib.sha256(tier_receipt.read_bytes()).hexdigest(),'case_count':len(rows),'mismatch_count':len(failures),'failures':failures,'cases':rows}
publisher.write((json.dumps(report,indent=2)+'\n').encode('utf-8'));print('Cases',len(rows),'mismatches',len(failures));print(json.dumps(failures[:10],indent=2))
if failures:raise SystemExit(1)
