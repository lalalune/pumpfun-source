#!/usr/bin/env python3
"""Normal-signature local PumpSwap creator reassignment differential; no RPC."""
import sys
sys.path.insert(0,'scripts')
from pump_amm_liquidity_differential import *
from pump_amm_reusable_harness import pin_program
FEES=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ');PUMP=Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P');METAPLEX=Pubkey.from_string('metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s')
SHARING,SB=Pubkey.find_program_address([b'sharing-config',bytes(base)],FEES);CURVE=Pubkey.find_program_address([b'bonding-curve',bytes(base)],PUMP)[0];META=Pubkey.find_program_address([b'metadata',bytes(METAPLEX),bytes(base)],METAPLEX)[0]
def run_creator(c,binary=None):
 h=acquire_harness(pin_program(binary or ROOT/'evidence/original/pump_amm/deployed.so'));vm=h.vm;vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for kp in [PAYER,OUTSIDER]:vm.set_account(kp.pubkey(),Account(10**12,b'',Pubkey.default()))
 pd=bytearray(poolraw);pd[211:243]=bytes(Pubkey.from_string(c.get('coin_creator',str(PAYER.pubkey()) if c.get('op','migrate_pool_coin_creator').startswith('migrate') else str(Pubkey.default()))));pd[271:287]=bytes(16)
 sd=hashlib.sha256(b'account:SharingConfig').digest()[:8]+bytes([SB,c.get('version',2),c.get('status',1)])+bytes(Pubkey.from_string(c.get('sharing_mint',str(base))))+bytes(Pubkey.from_string(c.get('sharing_admin',str(PAYER.pubkey()))))+bytes([c.get('revoked',False)])+struct.pack('<I',1)+bytes(PAYER.pubkey())+struct.pack('<H',10000)
 cd=hashlib.sha256(b'account:BondingCurve').digest()[:8]+struct.pack('<QQQQQ',100,200,300,400,500)+bytes([c.get('complete',False)])+bytes(Pubkey.from_string(c.get('curve_creator',str(OUTSIDER.pubkey()))))+b'\0\0'
 creators=c.get('metadata_creators',[(str(OUTSIDER.pubkey()),c.get('verified',1),100)])
 creator_bytes=b'\0' if creators is None else bytes([1])+struct.pack('<I',len(creators))+b''.join(bytes(Pubkey.from_string(k))+bytes([v,share]) for k,v,share in creators)
 md=bytes([4])+bytes(PAYER.pubkey())+bytes(base)+struct.pack('<I',1)+b'x'+struct.pack('<I',1)+b'Y'+struct.pack('<I',1)+b'z'+struct.pack('<H',0)+creator_bytes+bytes([0,1,0,0,0,0,0])
 initial={'pool':(pool,pd,PROGRAM),'sharing':(SHARING,sd.ljust(1024,b'\0'),FEES),'curve':(CURVE,cd,PUMP),'metadata':(META,md,METAPLEX)}
 for name,(k,d,own) in initial.items():
  if name in c.get('missing',[]):d=b'';own=Pubkey.default()
  d=bytearray(d)
  for off,val in c.get('patches',{}).get(name,[]):d[off:off+len(bytes.fromhex(val))]=bytes.fromhex(val)
  if name in c.get('lengths',{}):n=c['lengths'][name];d=d[:n]+bytes(max(0,n-len(d)))
  vm.set_account(k,Account(c.get('lamports',{}).get(name,10**9),bytes(d),Pubkey.from_string(c.get('owners',{}).get(name,str(own)))))
 names={'pool':pool,'sharing_config':SHARING,'metadata':META,'bonding_curve':CURVE,'event_authority':EVENT,'program':PROGRAM}
 ix=next(x for x in IDL['instructions'] if x['name']==c.get('op','migrate_pool_coin_creator'));metas=[]
 for item in ix['accounts']:
  name=item['name'];key=PROGRAM if name in c.get('absent',[]) else names[name]
  if c.get('substitute')==name:
   replacement=Pubkey.from_bytes(bytes([88])*32);a=vm.get_account(key)
   if a and not a.executable:vm.set_account(replacement,a)
   key=replacement
  metas.append(AccountMeta(key,False,item.get('writable',False) and c.get('readonly')!=name))
 metas=metas[:c.get('account_count',len(metas))]
 data=bytes(ix['discriminator'])+bytes.fromhex(c.get('trailing',''))
 if 'payload_length' in c:data=data[:c['payload_length']]
 tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());assert all(tx.verify_with_results())
 def snap():
  out={}
  for k in set([x[0] for x in initial.values()]+[m.pubkey for m in metas]+[PAYER.pubkey()]):
   a=vm.get_account(k)
   if a and a.executable:continue
   out[str(k)]=None if a is None else {'data':a.data.hex(),'owner':str(a.owner),'lamports':a.lamports}
  return out
 before=snap();r=vm.send_transaction(tx);fail=isinstance(r,FailedTransactionMetadata);m=r.meta() if fail else r;raw=json.loads(m.to_json())
 return {'error':str(r.err()) if fail else None,'before':before,'after':snap(),'events':[l for l in m.logs() if l.startswith('Program data:')],'logs':m.logs(),'inner':raw['inner_instructions'],'return':raw['return_data'],'transaction_base64':base64.b64encode(bytes(tx)).decode()}

def cases():
 rows=[]
 for op in ['migrate_pool_coin_creator','set_coin_creator']:
  def add(name,**kwargs): rows.append({'name':op+'-'+name,'op':op,**kwargs})
  add('base');add('trailing',trailing='112233445566778899');add('readonly-pool',readonly='pool')
  for n in range(8):add('payload-'+str(n),payload_length=n)
  for n in range(6):add('accounts-'+str(n),account_count=n)
  for name in ['pool','event_authority','program']+(['sharing_config'] if op.startswith('migrate') else ['metadata','bonding_curve']):add('substitute-'+name,substitute=name)
  for n in [0,7,8,210,211,242,243,244,245,260,261,268,269,270,271,278,279,286,287,300,301,302]:add('pool-size-'+str(n),lengths={'pool':n})
  for key in ['pool']+(['sharing'] if op.startswith('migrate') else ['metadata','curve']):
   for owner in [Pubkey.default(),FEES,PROGRAM,PUMP]: add('owner-'+key+'-'+str(owner),owners={key:str(owner)})
   add('discriminator-'+key,patches={key:[(0,'00')]})
  for off in [8,9,11,43,75,107,139,171,203,211,243,244,245,261,269,270,271,279]:
   width=32 if off in [11,43,75,107,139,171,211] else 16 if off==245 else 8 if off in [203,261,271,279] else 2 if off==9 else 1
   for value in [0,1,2]:add('pool-field-'+str((off,value)),patches={'pool':[(off,(value).to_bytes(width,'little').hex())]})
  for creator in [Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey(),SHARING]:add('coin-creator-'+str(creator),coin_creator=str(creator))
  if op.startswith('migrate'):
   for n in [0,1,2,3,255]:add('version-'+str(n),version=n)
   for n in [0,1,2,255]:add('status-'+str(n),status=n)
   for n in [0,1,2]:add('revoked-'+str(n),revoked=n)
   for name in ['sharing_admin','sharing_mint']:
    for k in [Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey(),SHARING,base]:add(name+'-'+str(k),**{name:str(k)})
   for n in [0,7,8,10,11,42,43,74,75,76,79,80,113,114,1023,1024]:add('sharing-size-'+str(n),lengths={'sharing':n})
   for off,val in [(8,'00'),(76,'00000000'),(76,'ffffffff'),(112,'0000'),(112,'ffff')]:add('sharing-field-'+str((off,val)),patches={'sharing':[(off,val)]})
   add('holder-unswept',patches={'pool':[(270,'01'),(279,'0100000000000000')]})
   add('holder-wrong-admin',sharing_admin=str(OUTSIDER.pubkey()),patches={'pool':[(270,'01')]})
  else:
   for cs in [None,[],[(str(Pubkey.default()),0,100)],[(str(PAYER.pubkey()),0,0),(str(OUTSIDER.pubkey()),1,100)],[(str(PAYER.pubkey()),1,100)]]:add('metadata-creators-'+str(cs),metadata_creators=cs)
   for v in [0,1,2,255]:add('creator-verified-'+str(v),verified=v)
   for k in [Pubkey.default(),PAYER.pubkey(),OUTSIDER.pubkey(),SHARING]:add('curve-creator-'+str(k),metadata_creators=None,curve_creator=str(k))
   for n in [0,7,8,48,49,80,81,82,83,84,166]:add('curve-size-'+str(n),lengths={'curve':n})
   for n in [0,1,32,65,70,75,80,82,83,84,85,86,87,118,119,120,126,127,128,200,679]:add('metadata-size-'+str(n),lengths={'metadata':n})
   for off in [48,81,82]:add('curve-bool-'+str(off),patches={'curve':[(off,'02')]})
   for off,val in [(0,'00'),(0,'ff'),(33,bytes(32).hex()),(65,'ffffffff'),(82,'0000')]:add('metadata-field-'+str((off,val)),patches={'metadata':[(off,val)]})
   add('existing-noncanonical-creator',coin_creator=str(PAYER.pubkey()),patches={'pool':[(11,bytes(OUTSIDER.pubkey()).hex())]})
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args();rows=[];bad=[]
 for c in cases():
  x=run_creator(c);y=run_creator(c,a.candidate) if a.candidate else None
  diffs=[k for k in ['error','before','after','events','inner','return'] if x[k]!=y[k]] if y else []
  rows.append({'case':c,'original':x,'candidate':y,'mismatched_fields':diffs,'match':not diffs if y else None})
  if diffs:bad.append(c['name'])
 sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();report={'scope':'Two creator reassignment paths with synthetic local state and normally verified signatures. Invalid injected states do not establish reachability. No binary identity or whole-program parity claimed.','original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'candidate_sha256':sha(pin_program(a.candidate)) if a.candidate else None,'script_sha256':sha(pathlib.Path(__file__)),'case_count':len(rows),'cases':rows,'mismatches':bad}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(json.dumps({'cases':len(rows),'mismatch_count':len(bad),'mismatches':bad[:40]}))
 if bad:raise SystemExit(1)
if __name__=='__main__':main()
