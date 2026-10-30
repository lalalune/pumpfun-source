#!/usr/bin/env python3
"""Synthetic AMM-owned fixtures, ordinary verified local transaction signatures; no RPC."""
import sys,base64,struct,json,pathlib,hashlib,argparse,itertools
sys.path.insert(0,'scripts')
from pump_amm_admin_differential import *
from pump_amm_reusable_harness import acquire_harness, pin_program
from solders.clock import Clock
TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
MINT=Pubkey.from_bytes(bytes([226])*32);USER=OUTSIDER.pubkey();G=Pubkey.find_program_address([b'global_volume_accumulator'],PROGRAM)[0];U=Pubkey.find_program_address([b'user_volume_accumulator',bytes(USER)],PROGRAM)[0]
ORIGINAL=ROOT/'evidence/original/pump_amm/deployed.so'
def disc(name):return bytes(next(x for x in IDL['accounts'] if x['name']==name)['discriminator'])
def token_data(owner,amount):
 d=bytearray(165);d[:32]=bytes(MINT);d[32:64]=bytes(owner);struct.pack_into('<Q',d,64,amount);d[108]=1;return bytes(d)
def run(c,program=ORIGINAL):
 h=acquire_harness(pin_program(program));vm=h.vm;vm.with_sigverify(True);vm.set_clock(Clock(100,0,0,0,c.get('now',10)))
 for pid,n in [(TOKEN,'spl_token'),(TOKEN22,'spl_token_2022'),(ATA,'associated_token')]:vm.add_program_from_file(pid,ROOT/'evidence/dependencies'/n/'deployed.so')
 token=TOKEN22 if c.get('token22') else TOKEN
 ga=Pubkey.find_program_address([bytes(G),bytes(token),bytes(MINT)],ATA)[0];ua=Pubkey.find_program_address([bytes(USER),bytes(token),bytes(MINT)],ATA)[0]
 cfg=bytearray(RAW);cfg[8:40]=bytes(PAYER.pubkey())
 g=disc('GlobalVolumeAccumulator')+struct.pack('<qqq',c.get('start',20),c.get('end',49),c.get('period',1))+bytes(MINT if not c.get('wrong_mint') else USER)+struct.pack('<30Q',*c.get('supplies',[1000]*30))+struct.pack('<30Q',*c.get('volumes',[100]*30))
 u=disc('UserVolumeAccumulator')+bytes(USER if not c.get('stored_other_user') else PAYER.pubkey())+struct.pack('<BQQQqBQQ',c.get('needs',1),c.get('unclaimed',5),c.get('claimed',7),c.get('volume',20),c.get('last',0),c.get('has_claimed',1),c.get('cashback',11),c.get('cashback_claimed',13))
 states={'global_config':(CONFIG_KEY,bytes(cfg),PROGRAM),'global_volume_accumulator':(G,g.ljust(600,b'\0'),PROGRAM),'user_volume_accumulator':(U,u.ljust(137,b'\0'),PROGRAM),'mint':(MINT,struct.pack('<I',0)+bytes(32)+struct.pack('<Q',10**12)+bytes([6,1])+bytes(36),token),'global_incentive_token_account':(ga,token_data(G,c.get('vault_amount',10**9)),token),'user_ata':(ua,token_data(USER,c.get('user_amount',17)),token)}
 for name,(key,data,owner) in states.items():
  if c.get('mutate')==name:
   if 'offset' in c:
    b=bytearray(data);v=bytes.fromhex(c['value']);b[c['offset']:c['offset']+len(v)]=v;data=bytes(b)
   if 'length' in c:data=data[:c['length']].ljust(c['length'],b'\0')
   if 'owner' in c:owner=Pubkey.from_string(c['owner'])
  if name in c.get('missing',[]):vm.set_account(key,Account(0,b'',Pubkey.default()))
  else:vm.set_account(key,Account(10**9,data,owner))
 names={'admin':PAYER.pubkey(),'user':USER,'payer':PAYER.pubkey(),'system_program':Pubkey.default(),'token_program':token,'associated_token_program':ATA,'event_authority':EVENT,'program':PROGRAM,**{n:v[0] for n,v in states.items()}}
 name=c.get('instruction','sync_user_volume_accumulator');ix=next(x for x in IDL['instructions'] if x['name']==name)
 metas=[]
 for a in ix['accounts']:
  n=a['name'];key=names[n];signer=bool(a.get('signer'));writable=bool(a.get('writable'))
  if c.get('wrong_account')==n:
   old=vm.get_account(key);key=Pubkey.from_bytes(bytes([228])*32)
   if old:vm.set_account(key,old)
  if c.get('readonly')==n:writable=False
  if c.get('unsigned')==n:signer=False
  metas.append(AccountMeta(key,signer,writable))
 if 'account_count' in c:metas=metas[:c['account_count']]
 args=b''
 if name=='admin_update_token_incentives':args=struct.pack('<qqqQQ',c.get('new_start',30),c.get('new_end',59),c.get('new_period',1),c.get('day',0),c.get('supply',1000))
 data=bytes(ix['discriminator'])+args+bytes.fromhex(c.get('trailing',''))
 if 'payload_length' in c:data=data[:c['payload_length']]
 payer=OUTSIDER if c.get('unsigned') or c.get('readonly') in ['admin','payer'] else PAYER
 # No known production signer is requested: synthetic config assigns the locally owned admin.
 signers=[payer]
 if any(m.is_signer and m.pubkey==PAYER.pubkey() for m in metas) and payer!=PAYER:signers.append(PAYER)
 keys=set(names.values())|{m.pubkey for m in metas}
 def snapshot():
  out={}
  for key in sorted(keys,key=str):
   a=vm.get_account(key)
   if a is None:out[str(key)]=None
   elif not a.executable:out[str(key)]={'data':bytes(a.data).hex(),'owner':str(a.owner),'lamports':a.lamports}
  return out
 before=snapshot();tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],payer.pubkey(),signers,vm.latest_blockhash());verified=all(tx.verify_with_results());assert verified;r=vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta() if failed else r
 result={'signature_verification':verified,'sigverify_runtime_enabled':True,'error':str(r.err()) if failed else None,'before':before,'after':snapshot(),'events':[l for l in meta.logs() if l.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'logs':meta.logs()}
 return result
def decoded(r):
 u=r['after'].get(str(U));g=r['after'].get(str(G));return {'error':r['error'],'u':None if not u or len(u['data'])<180 else struct.unpack_from('<BQQQqBQQ',bytes.fromhex(u['data']),40),'g':None if not g or len(g['data'])<1088 else [struct.unpack_from('<qqq',bytes.fromhex(g['data']),8),struct.unpack_from('<30Q',bytes.fromhex(g['data']),64)],'events':len(r['events'])}
def cases(family):
 n={'sync':'sync_user_volume_accumulator','admin':'admin_update_token_incentives','claim':'claim_token_incentives'}[family]
 out=[]
 def add(**kw):out.append({'instruction':n,**kw})
 add()
 if family=='sync':
  for now,last,start in itertools.product([-1,0,10,20,21,50],[-1,0,10,20,21,50],[-1,0,20,50]):add(now=now,last=last,start=start)
  for field,values in [('claimed',[0,1,2**64-1]),('has_claimed',[0,1,2]),('needs',[0,1,2]),('period',[0,-1,2**63-1]),('end',[-2**63,0,2**63-1]),('now',[-2**63,2**63-1]),('last',[-2**63,2**63-1]),('start',[-2**63,2**63-1])]:
   for value in values:add(**{field:value})
 if family=='claim':
  for now,last in itertools.product([0,19,20,21,29,49,50,60],[0,19,20,21,29,49,50,60]):
   for unclaimed in [0,5]:add(now=now,last=last,unclaimed=unclaimed)
  for base in [{},{'now':21,'last':20},{'now':22,'last':21,'period':10}]:
   for field,values in [('needs',[0,1,2]),('has_claimed',[0,1,2]),('unclaimed',[0,1,2**64-1]),('claimed',[0,1,2**64-1]),('volume',[0,1,99,100,101,2**64-1]),('period',[0,-1,2,10]),('vault_amount',[0,1,4,5,204,205,2**64-1]),('supplies',[[0]*30,[1]*30,[2**64-1]*30,list(range(30))]),('volumes',[[0]*30,[1]*30,[2**64-1]*30,list(range(30))]),('end',[0,19,20,21,49,50,100])]:
    for value in values:add(**{**base,field:value})
  for field in ['now','last','start','end','period']:
   for value in [-2**63,-1,0,2**63-1]:add(now=21,last=20,**{field:value}) if field not in ['now','last'] else add(**{'now':21,'last':20,field:value})
  for d in [{'unclaimed':0,'volume':0,'has_claimed':0},{'unclaimed':0,'volume':0},{'now':21,'last':20,'unclaimed':0,'volume':0,'has_claimed':0},{'now':21,'last':20,'unclaimed':0,'supplies':[0]*30},{'now':21,'last':20,'unclaimed':0,'volumes':[0]*30},{'wrong_mint':True}]:add(**d)
 if family=='admin':
  for field,values in [('new_start',[-2**63,-1,0,9,10,11,20,30,59,60,2**63-1]),('new_end',[-2**63,-1,0,9,10,11,20,29,30,31,59,60,2**63-1]),('new_period',[-2**63,-1,0,1,2,29,30,2**63-1]),('day',[0,1,28,29,30,31,2**64-1]),('supply',[0,1,2**64-1])]:
   for value in values:add(**{field:value})
  for now,start,end in itertools.product([0,19,20,21,49,50,60],[0,20,30],[0,21,49,59]):
   for day in [0,1,29,30]:add(now=now,new_start=start,new_end=end,day=day)
  for period in [-1,0,1,2,10]:
   for supply in [0,1]:
    for day in [0,29,30]:add(new_start=0,new_end=0,new_period=period,supply=supply,day=day)
  add(mutate='global_config',offset=8,value=bytes(USER).hex())
 if family!='admin':add(stored_other_user=True)
 if family!='sync':
  for token22 in [False,True]:
   for missing in [[],['user_ata'],['global_incentive_token_account'],['global_volume_accumulator']]:add(token22=token22,missing=missing)
  for name in ['mint','user_ata','global_incentive_token_account']:
   for length in [0,7,81,82,83,164,165,166]:add(mutate=name,length=length)
   for owner in [Pubkey.default(),PROGRAM,TOKEN22]:add(mutate=name,owner=str(owner))
   for off,value in ([(0,bytes(4)),(44,b'\xff'),(45,b'\0')] if name=='mint' else [(0,bytes(32)),(32,bytes(32)),(108,b'\0'),(108,b'\2')]):add(mutate=name,offset=off,value=value.hex())
 for name,lengths in [('global_volume_accumulator',[0,7,8,31,32,63,64,303,304,543,544,599,600,601]),('user_volume_accumulator',[0,7,8,40,41,72,73,74,89,90,136,137,138]),('global_config',[0,7,8,906,907,939,940,948,949,950])]:
  if name=='global_config' and family!='admin' or name=='user_volume_accumulator' and family=='admin':continue
  for length in lengths:add(mutate=name,length=length)
  for owner in [Pubkey.default(),TOKEN]:add(mutate=name,owner=str(owner))
  add(mutate=name,offset=0,value=bytes(8).hex());add(missing=[name])
 ix=next(x for x in IDL['instructions'] if x['name']==n)
 for a in ix['accounts']:
  if not a.get('signer'):add(wrong_account=a['name'])
  else:add(unsigned=a['name'])
  if a.get('writable'):add(readonly=a['name'])
 for count in range(len(ix['accounts'])):add(account_count=count)
 for length in range(48 if family=='admin' else 8):add(payload_length=length)
 add(trailing='010203')
 if family=='claim':
  for field in ['now','last','start','end','period']:
   for value in [-1,0,1,19,20,21,49,50,100]:
    for now,last in [(10,0),(10,20),(21,0),(21,20),(60,50)]:
     add(**{'now':now,'last':last,'unclaimed':0,field:value})
  for period,now,last in itertools.product([1,2,10],[20,21,22,30,49,50,60],[0,19,20,21,22,30,49,50]):add(period=period,now=now,last=last,unclaimed=0)
  for d in [{'stored_other_user':True,'unclaimed':0},{'stored_other_user':True,'now':21,'last':20,'volume':0,'unclaimed':0}]:add(**d)
 if family=='admin':
  for period,now,end in itertools.product([1,2,10],[0,19,20,21,22,30,49,50],[21,49,59,60]):
   add(new_start=20,new_end=end,new_period=period,now=now,day=30,supply=101)
  for supply in [0,1000]:
   for end in [21,25,49]:add(new_start=20,new_end=end,now=21,supply=supply,day=1)
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path,required=True);p.add_argument('--output',type=pathlib.Path,required=True);p.add_argument('--family',choices=['sync','claim','admin'],required=True);a=p.parse_args();rows=[]
 for c in cases(a.family):
  x,y=run(c),run(c,a.candidate);diff=[k for k in x if k!='logs' and x[k]!=y[k]];rows.append({'input':c,'original':x,'candidate':y,'diff':diff})
 sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
 report={'scope':'Bounded offline AMM '+a.family+' recovery with synthetic local state and ordinary verified signatures. Full committed state, event, inner CPI, return, transaction and error comparison; not binary identity or whole program equivalence.','case_count':len(rows),'mismatches':[i for i,r in enumerate(rows) if r['diff']],'original_sha256':sha(pin_program(ORIGINAL)),'candidate_sha256':sha(pin_program(a.candidate)),'script_sha256':sha(__file__),'cases':rows}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in report.items() if k!='cases'}));raise SystemExit(bool(report['mismatches']))
if __name__=='__main__':main()
