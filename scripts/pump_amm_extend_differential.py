#!/usr/bin/env python3
"""Local raw-account extension differential."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from pump_differential_output import PumpReport
TARGET=Pubkey.from_bytes(bytes([91])*32)
def extend(kind='Pool',size=8,lamports=1,candidate=None,overrides=None,unsigned=False,payload_length=None):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890));disc=bytes(next(x for x in IDL['accounts'] if x['name']==kind)['discriminator']);data=(disc+bytes(max(0,size-8)))[:size];h.vm.set_account(TARGET,Account(lamports,data,PROGRAM));metas=[AccountMeta(TARGET,False,True),AccountMeta(PAYER.pubkey(),True,True),AccountMeta(Pubkey.default(),False,False),AccountMeta(EVENT,False,False),AccountMeta(PROGRAM,False,False)]
 if overrides:overrides(h,metas)
 ix=next(x for x in IDL['instructions'] if x['name']=='extend_account');data=bytes(ix['discriminator'])
 if payload_length is not None:data=data[:payload_length]
 payer=OUTSIDER if unsigned else PAYER
 if unsigned:metas[1]=AccountMeta(PAYER.pubkey(),False,True)
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),[payer],h.vm.latest_blockhash());r=h.vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);meta=r.meta() if fail else r;a=h.vm.get_account(TARGET)
 states={}
 for m in metas:
  v=h.vm.get_account(m.pubkey)
  if v is None or not v.executable:states[str(m.pubkey)]=None if v is None else {'data':bytes(v.data).hex(),'lamports':v.lamports,'owner':str(v.owner)}
 return {'states':states,'error':str(r.err()) if fail else None,'logs':meta.logs(),'inner':json.loads(meta.to_json())['inner_instructions'],'size':len(a.data) if a else None,'data':bytes(a.data).hex() if a else None,'lamports':a.lamports if a else 0}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();publisher=PumpReport(args.output,ROOT,args.candidate,__file__,extra_inputs=[TRADE_FIXTURE_PATH]);candidate=args.candidate;rows=[]
 def test(label,**kw):
  x=extend(**kw);y=extend(candidate=candidate,**kw)
  for r in [x,y]:r['events']=[v for v in r.pop('logs') if v.startswith('Program data: ')]
  diffs=[k for k in x if x[k]!=y[k]];rows.append({'case':label,'original':x,'candidate':y,'diff':diffs})
 for kind in ['Pool','GlobalConfig','UserVolumeAccumulator','GlobalVolumeAccumulator','FeeConfig','SharingConfig','BondingCurve']:
  for size in [0,1,7,8,89,90,136,137,138,210,211,286,287,300,301,302,599,600,601,948,949,950,10000]:
   test('kind-size='+str((kind,size)),kind=kind,size=size,lamports=10**9)
 for kind,target in [('Pool',301),('GlobalConfig',949),('UserVolumeAccumulator',137),('GlobalVolumeAccumulator',600)]:
  for size in [8,target-1,target,target+1]:
   for lamports in [0,1,946560,(size+128)*6960,10**9]:test('rent='+str((kind,size,lamports)),kind=kind,size=size,lamports=lamports)
  for idx in [0,2,3,4]:test('substitute='+str((kind,idx)),kind=kind,lamports=10**9,overrides=meta_mutation(idx,'substitute'))
  for idx in [0,1]:test('readonly='+str((kind,idx)),kind=kind,lamports=10**9,overrides=meta_mutation(idx,'readonly'))
  test('unsigned='+kind,kind=kind,lamports=10**9,unsigned=True)
  for owner in [Pubkey.default(),TOKEN]:test('owner='+str((kind,owner)),kind=kind,lamports=10**9,overrides=mutate(TARGET,0,b'',owner=owner))
  for payload in range(8):test('payload='+str((kind,payload)),kind=kind,lamports=10**9,payload_length=payload)
  for off,val in [(0,bytes(8)),(8,b'\xff'*16)]:test('body='+str((kind,off)),kind=kind,size=50,lamports=10**9,overrides=mutate(TARGET,off,val))
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'SBF extend_account: four recognized raw account types, exact System/event CPIs, committed states, runtime rent outcomes and errors. Ordinary signed local transactions only; not whole-program equivalence.','candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'script_sha256':sha(__file__),'case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'cases':rows}
 publisher.write((json.dumps(report,separators=(',',':'))+'\n').encode('utf-8'));print(json.dumps({'case_count':len(rows),'mismatch_count':len(report['mismatches']),'mismatches':report['mismatches']}))
 if report['mismatches']:raise SystemExit(1)

if __name__=='__main__':main()
