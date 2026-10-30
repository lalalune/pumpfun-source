#!/usr/bin/env python3
"""Independent SBF fee-schedule mutations using synthetic authorized local state."""
from fees_admin_differential import *
from fee_recovery_fixture import FeeFixture
import random
CONFIG_PROGRAM=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
CONFIG,BUMP=Pubkey.find_program_address([b'fee_config',bytes(CONFIG_PROGRAM)],PROGRAM)
CONFIG_DISC=bytes(next(x['discriminator'] for x in IDL['accounts'] if x['name']=='FeeConfig'))
def fees(xs):return struct.pack('<QQQ',*xs)
def tiers(xs):return struct.pack('<I',len(xs))+b''.join(t.to_bytes(16,'little')+fees(f) for t,f in xs)
def encode(normal,stable,flat=(11,22,33),exotic=(44,55,66)):
 return CONFIG_DISC+bytes([BUMP])+bytes(AUTH.pubkey())+fees(flat)+tiers(normal)+tiers(stable)+fees(exotic)
class ConfigFixture(Fixture):
 def run(self,c):
  mutation=c.get('mutation','none');normal=c.get('old_normal',[(0,(1,2,3)),(100,(4,5,6))]);stable=c.get('old_stable',[(0,(7,8,9))])
  data=bytearray(encode(normal,stable).ljust(c.get('allocation',2512),b'\x00'));owner=PROGRAM;key=CONFIG;config_program=CONFIG_PROGRAM;admin=AUTH;event=EVENT;program=PROGRAM;system=Pubkey.default()
  if mutation=='owner':owner=Pubkey.default()
  if mutation=='key':key=Pubkey.from_bytes(bytes([44])*32)
  if mutation=='bump':data[8]^=1
  if mutation=='discriminator':data[0]^=1
  if mutation=='admin':admin=OTHER
  if mutation=='config_program':config_program=OTHER.pubkey()
  if mutation=='event':event=OTHER.pubkey()
  if mutation=='program':program=Pubkey.default()
  if mutation=='system':system=OTHER.pubkey()
  if mutation.startswith('length:'):data=data[:int(mutation.split(':')[1])]
  if mutation.startswith('normal_count:'):data[65:69]=int(mutation.split(':')[1]).to_bytes(4,'little')
  self.vm.set_account(key,Account(c.get('lamports',10**9),bytes(data),owner));self.vm.set_account(CONFIG_PROGRAM,Account(10**9,b'',Pubkey.default()))
  if c['instruction']=='set_exotic_flat_fees':metas=[AccountMeta(key,False,mutation!='readonly'),AccountMeta(admin.pubkey(),mutation!='unsigned',mutation!='admin_readonly'),AccountMeta(config_program,False,False),AccountMeta(system,False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  else:metas=[AccountMeta(key,False,mutation!='readonly'),AccountMeta(admin.pubkey(),mutation!='unsigned',False),AccountMeta(config_program,False,False),AccountMeta(event,False,False),AccountMeta(program,False,False)]
  if mutation.startswith('accounts:'):metas=metas[:int(mutation.split(':')[1])]
  disc=bytes(next(x['discriminator'] for x in IDL['instructions'] if x['name']==c['instruction']))
  arg=bytes.fromhex(c['arg']);before=[self.vm.get_account(k.pubkey()).lamports for k in [AUTH,OTHER,PAYER]]
  signers=[PAYER,admin] if mutation!='unsigned' and any(m.pubkey==admin.pubkey() and m.is_signer for m in metas) else [PAYER]
  tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,disc+arg,metas)],PAYER.pubkey(),signers,self.vm.latest_blockhash())
  result=self.vm.send_transaction(tx);failed=isinstance(result,FailedTransactionMetadata);meta=result.meta() if failed else result;after=self.vm.get_account(key)
  balances=[self.vm.get_account(k.pubkey()).lamports for k in [AUTH,OTHER,PAYER]]
  return {'error':str(result.err()) if failed else None,'data_hex':after.data.hex() if after else None,'lamports':after.lamports if after else None,'owner':str(after.owner) if after else None,'balance_deltas':[a-b for a,b in zip(balances,before)],'events':[l for l in meta.logs() if l.startswith('Program data:')],'inner_instructions':json.loads(meta.to_json())['inner_instructions'],'logs':meta.logs()}
def cases():
 out=[];rng=random.Random(771)
 for name in ['update_fee_config','update_stable_fee_config','set_exotic_flat_fees']:
  def add(label,ts=None,flat=(11,22,33),**kw):
   arg=fees(flat) if name=='set_exotic_flat_fees' else tiers(ts if ts is not None else [(0,(1,2,3)),(100,(4,5,6))])+(fees(flat) if name=='update_fee_config' else b'')
   out.append({'name':name+'-'+label,'instruction':name,'arg':arg.hex(),**kw})
  for n in [0,1,2,29,30,31,32,49,50,51,59,60,61]:add('count-'+str(n),[(i,(1,2,3)) for i in range(n)])
  for ts in [[(1,(1,2,3)),(0,(1,2,3))],[(0,(1,2,3)),(0,(4,5,6))],[(2**128-1,(1,2,3))]]:add('tiers-'+str(ts),ts)
  for f in [(0,0,0),(10000,0,0),(10001,0,0),(5000,5000,0),(5000,5000,1),(2**64-1,0,0),(2**64-1,1,0),(2**64-1,2**64-1,2**64-1)]:
   add('flat-'+str(f),flat=f);add('tierfee-'+str(f),[(0,f)])
  for mutation in ['owner','key','bump','discriminator','admin','config_program','event','program','unsigned','readonly','admin_readonly','system']+['length:'+str(n) for n in [0,7,8,9,40,97,136,217,2511,2512,4097]]+['accounts:'+str(n) for n in range(6 if name=='set_exotic_flat_fees' else 5)]+['normal_count:'+str(n) for n in [0,1,30,31,61,2**32-1]]:add(mutation,mutation=mutation)
  for n in [0,1,2,3,4,15,16,23,24,27,28,43,44,47,48,67,68,83,84,107,108]:
   add('arglength-'+str(n));out[-1]['arg']=out[-1]['arg'][:n*2]
  for n in [1,3,30]:add('replace-normal-'+str(n),old_normal=[(i,(11,22,33)) for i in range(n)],old_stable=[(i,(44,55,66)) for i in range(30)])
  for allocation in [2512,3000,4072,4073,4096,4097,5000]:
   for lamports in [1,10**9]:
    add('allocation-'+str(allocation)+'-'+str(lamports),allocation=allocation,lamports=lamports)
  for invalid_flat,ts in [((10001,0,0),[]),((1,2,3),[(1,(10001,0,0)),(0,(1,2,3))]),((1,2,3),[(1,(1,2,3)),(0,(10001,0,0))]),((10001,0,0),[(0,(10001,0,0))]*60)]:
   add('precedence-'+str(invalid_flat)+'-'+str(len(ts)),ts,flat=invalid_flat)
  for i in range(100):
   n=rng.randrange(1,32);ts=[(rng.randrange(2**128),(rng.randrange(11000),rng.randrange(500),rng.randrange(500))) for _ in range(n)];ts.sort();add('random-'+str(i),ts,flat=tuple(rng.randrange(4000) for _ in range(3)))
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();o=ConfigFixture(ROOT/'evidence/original/pump_fees/deployed.so');b=ConfigFixture(a.candidate) if a.candidate else None;rows=[];failures=[]
 for c in cases():
  x=o.run(c);y=b.run(c) if b else None;match=all(x[k]==y[k] for k in ['error','data_hex','lamports','owner','balance_deltas','events','inner_instructions']) if b else None
  rows.append({'case':c,'original':x,'candidate':y,'match':match})
  if match is False:failures.append(c['name'])
 report={'scope':'Three fee configuration setters: synthetic authorized state; state/errors/lamports/events/inner instructions. No complete source identity or security finding.','original_sha256':o.program_sha256,'candidate_sha256':b.program_sha256 if b else None,'case_count':len(rows),'mismatches':failures,'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'case_count':len(rows),'mismatches':failures[:30]}));assert not failures
if __name__=='__main__':main()
