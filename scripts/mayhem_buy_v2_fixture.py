#!/usr/bin/env python3
"""Original or source-built candidate ELF, signed synthetic accounts, local LiteSVM; never RPC.
No authorization is weakened: the owned trader signs, GlobalParams.trader matches it,
and Mayhem itself signs for the real sol-vault PDA during its CPI.
"""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path
import sys,json,base64,hashlib,struct
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'evidence/original/mayhem/deployed.so').is_file())
sys.path.insert(0,str(ROOT/'scripts'))
import pump_trade_fixture as f
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
MAY=f.Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
TRADER=f.Keypair.from_seed(hashlib.sha256(b'mayhem-buy-v2-static-followup-owned-trader-v1').digest())
if not TRADER.pubkey().is_on_curve():
    raise RuntimeError('synthetic trader pubkey must be on curve')
GLOBAL=f.Pubkey.find_program_address([b'global-params'],MAY)[0]
SOL=f.Pubkey.find_program_address([b'sol-vault'],MAY)[0]
EVENT=f.Pubkey.find_program_address([b'__event_authority'],MAY)[0]
PUMP=f.Pubkey.from_string(f.x['program']);ATA=f.Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
CURVE=f.Pubkey.from_string(f.x['accounts']['curve']);PGLOBAL=f.Pubkey.from_string(f.x['accounts']['global'])
INITIAL={k:f.vm.get_account(k) for k in f.msg.account_keys}
sha=lambda b:hashlib.sha256(b).hexdigest()
def snap(a):
 return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'executable':a.executable,'rent_epoch':a.rent_epoch,'data_base64':base64.b64encode(a.data).decode() if not a.executable else None,'data_sha256':sha(a.data)}
def run(c,binary=None):
 vm=f.LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
 for name,key in [('mayhem',MAY),('pump',PUMP),('pump_fees',f.Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ'))]:
  vm.add_program_from_file(key,binary if name=='mayhem' and binary else ROOT/f'evidence/original/{name}/deployed.so')
 for name in ['spl_token','spl_token_2022','associated_token']:
  capture=json.loads((ROOT/f'evidence/dependencies/{name}/capture.json').read_text());vm.add_program_from_file(f.Pubkey.from_string(capture['program']),ROOT/f'evidence/dependencies/{name}/deployed.so')
 for key,a in INITIAL.items():
  if a is not None and not a.executable:vm.set_account(key,a)
 vm.set_clock(Clock(100,0,0,0,c.get('now',100)))
 vm.set_account(TRADER.pubkey(),f.Account(10**10,b'',f.Pubkey.default()))
 vm.set_account(SOL,f.Account(10**10,b'',f.Pubkey.default()))
 v3=f.ixs[-1].accounts;mint=v3[1].pubkey;token=v3[3].pubkey
 statekey=f.Pubkey.find_program_address([b'mayhem-state',bytes(mint)],MAY)[0]
 vault=f.Pubkey.find_program_address([bytes(SOL),bytes(token),bytes(mint)],ATA)[0]
 td=bytearray(INITIAL[v3[9].pubkey].data);td[32:64]=bytes(SOL);struct.pack_into('<Q',td,64,c.get('tokens',10**9));vm.set_account(vault,f.Account(10**8,bytes(td),token))
 gd=bytearray(hashlib.sha256(b'account:GlobalParams').digest()[:8]+bytes(310));gd[49:81]=bytes(TRADER.pubkey());gd[81:113]=bytes(TRADER.pubkey());gd[48]=c.get('paused',0)
 for off,val in [(16,c.get('cap',0)),(129,c.get('threshold',0)),(146,c.get('interval',0)),(32,c.get('global_risk',(1<<64)-1)),(40,c.get('token_risk',(1<<64)-1)),(190,c.get('stable_global_risk',c.get('global_risk',(1<<64)-1))),(198,c.get('stable_token_risk',c.get('token_risk',(1<<64)-1)))]:struct.pack_into('<Q',gd,off,val%(1<<64))
 gd[113:129]=c.get('global_sol',0).to_bytes(16,'little',signed=True)
 gd[206:222]=c.get('global_stable',c.get('global_sol',0) if c.get('token_quote') else 0).to_bytes(16,'little',signed=True)
 struct.pack_into('<Q',gd,182,c.get('stable_cap',c.get('cap',0)));struct.pack_into('<Q',gd,222,c.get('stable_threshold',c.get('threshold',0)))
 vm.set_account(GLOBAL,f.Account(10**8,bytes(gd),MAY))
 sd=bytearray(hashlib.sha256(b'account:MayhemState').digest()[:8]+bytes(162));sd[24:56]=bytes(mint);struct.pack_into('<q',sd,16,c.get('deadline',10000));struct.pack_into('<Q',sd,89,c.get('last',0)%(1<<64));sd[97]=c.get('status',1)
 sd[56:72]=c.get('state_sol',0).to_bytes(16,'little',signed=True);sd[72:88]=c.get('state_tokens',0).to_bytes(16,'little',signed=True)
 vm.set_account(statekey,f.Account(10**8,bytes(sd),MAY))
 curve=bytearray(INITIAL[CURVE].data);curve[81]=1
 for off,val in c.get('curve_u64',[]):struct.pack_into('<Q',curve,off,val)
 for off,val in c.get('curve_bytes',[]):curve[off]=val
 vm.set_account(CURVE,f.Account(INITIAL[CURVE].lamports,bytes(curve),PUMP))
 creator=f.Pubkey(curve[49:81]);creatorvault=f.Pubkey.find_program_address([b'creator-vault',bytes(creator)],PUMP)[0]
 fee=f.Pubkey(INITIAL[PGLOBAL].data[483:515]);pump_event=f.Pubkey.find_program_address([b'__event_authority'],PUMP)[0]
 v2=f.Pubkey.find_program_address([b'bonding-curve-v2',bytes(mint)],PUMP if c.get('wrong_v2_program') else MAY)[0]
 vm.set_account(v2,f.Account(10**7,bytes(curve),PUMP))
 for key in [creatorvault,fee]:
  if vm.get_account(key) is None:vm.set_account(key,f.Account(10**7,b'',f.Pubkey.default()))
 quote=f.Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v' if c.get('token_quote') else 'So11111111111111111111111111111111111111112')
 qtoken=f.Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb' if c.get('quote_token22') else 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
 if c.get('token_quote'):
  curve[83:115]=bytes(quote);vm.set_account(CURVE,f.Account(INITIAL[CURVE].lamports,bytes(curve),PUMP))
 qm=bytearray(82);struct.pack_into('<Q',qm,36,10**15);qm[44]=6 if c.get('token_quote') else 9;qm[45]=1;vm.set_account(quote,f.Account(10**9,bytes(qm),qtoken))
 gv=f.Pubkey.find_program_address([b'global_volume_accumulator'],PUMP)[0]
 volume=bytearray(600);volume[:8]=hashlib.sha256(b'account:GlobalVolumeAccumulator').digest()[:8];struct.pack_into('<qqq',volume,8,1000,10000,86400);vm.set_account(gv,f.Account(10**8,bytes(volume),PUMP))
 uv=f.Pubkey.find_program_address([b'user_volume_accumulator',bytes(SOL)],PUMP)[0]
 ud=bytearray(137);ud[:8]=hashlib.sha256(b'account:UserVolumeAccumulator').digest()[:8];ud[8:40]=bytes(SOL);vm.set_account(uv,f.Account(10**8,bytes(ud),PUMP))
 sharing=f.Pubkey.find_program_address([b'sharing-config',bytes(mint)],f.Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ'))[0];vm.set_account(sharing,f.Account(10**7,b'',f.Pubkey.default()))
 qkeys={}
 for name,authority in [('vault',SOL),('curve',CURVE),('fee',fee),('creator',creatorvault),('volume',uv),('buyback',v3[13].pubkey)]:
  key=f.Pubkey.find_program_address([bytes(authority),bytes(qtoken),bytes(quote)],ATA)[0];qkeys[name]=key;d=bytearray(165);d[:32]=bytes(quote);d[32:64]=bytes(authority);struct.pack_into('<Q',d,64,10**12);d[108]=1;vm.set_account(key,f.Account(10**9,bytes(d),qtoken))
 keys=[TRADER.pubkey(),GLOBAL,statekey,mint,quote,ATA,vault,qkeys['vault'],SOL,f.Pubkey.default(),token,qtoken,PGLOBAL,CURVE,qkeys['curve'],fee,qkeys['fee'],v3[6].pubkey,creatorvault,qkeys['creator'],sharing,pump_event,PUMP,gv,uv,qkeys['volume'],f.Pubkey.from_string(f.x['accounts']['fee_config']),f.Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ'),EVENT,MAY,v3[13].pubkey,qkeys['buyback']]
 for i,j in c.get('swap_accounts',[]):keys[i],keys[j]=keys[j],keys[i]
 # All mutations below are explicit simulator starting-state fixtures.
 for idx,spec in c.get('mutations',{}).items():
  idx=int(idx);key=keys[idx];ac=vm.get_account(key)
  if ac is None:ac=f.Account(10**7,b'',f.Pubkey.default())
  data=bytearray(ac.data)
  for off,val in spec.get('bytes',[]):
   if off>=len(data):data.extend(bytes(off+1-len(data))) # Explicit synthetic malformed starting data.
   data[off]=val
  for off,val in spec.get('u64',[]):struct.pack_into('<Q',data,off,val)
  for off,val in spec.get('pubkey',[]):data[off:off+32]=bytes(f.Pubkey.from_string(val))
  if 'length' in spec:data=data[:spec['length']]
  owner=f.Pubkey.default() if spec.get('system_owner') else f.Pubkey.from_string(spec['owner']) if 'owner' in spec else ac.owner
  vm.set_account(key,f.Account(spec.get('lamports',ac.lamports),bytes(data),owner,ac.executable,ac.rent_epoch))
 for idx in c.get('wrong_keys',[]):
  old=keys[idx];key=f.Pubkey(bytes([60+idx])*32);ac=vm.get_account(old)
  if ac is not None and not ac.executable:vm.set_account(key,ac)
  else:vm.set_account(key,f.Account(10**7,b'',f.Pubkey.default()))
  keys[idx]=key
 for idx,key in c.get('replace_keys',{}).items():keys[int(idx)]=f.Pubkey.from_string(key)
 writable={0,1,2,6,7,8,13,14,15,16,17,18,19,23,24,25,30,31}
 metas=[f.AccountMeta(k,i==0 and not c.get('unsigned_trader'),i in writable and i not in c.get('readonly',[])) for i,k in enumerate(keys)]
 if 'account_count' in c:metas=metas[:c['account_count']]
 if c.get('extra_account'):metas.append(f.AccountMeta(TRADER.pubkey(),False,False))
 vt,vs,rt,rs=struct.unpack_from('<QQQQ',curve,8)
 reference=c.get('reference',vs*10**15//vt if vt else 0)
 payload=hashlib.sha256(b'global:buy_v2').digest()[:8]+reference.to_bytes(16,'little')+struct.pack('<HH',c.get('tolerance',2400),c.get('retained',9000))
 if 'payload_length' in c:payload=payload[:8+c['payload_length']]
 payload+=bytes.fromhex(c.get('trailing',''))
 # A separate test-owned payer permits a genuine negative unsigned-trader case.
 payer=f.Keypair.from_seed(hashlib.sha256(b'mayhem-buy-v2-sbf-owned-payer-v1').digest())
 vm.set_account(payer.pubkey(),f.Account(10**10,b'',f.Pubkey.default()))
 signers=[payer]+([TRADER] if any(m.pubkey==TRADER.pubkey() and m.is_signer for m in metas) else [])
 tx=f.Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),f.Instruction(MAY,payload,metas)],payer.pubkey(),signers,vm.latest_blockhash())
 if not all(tx.verify_with_results()):
  raise RuntimeError('transaction signature verification failed')
 watched=list(dict.fromkeys(list(tx.message.account_keys)+keys))
 before={str(k):snap(vm.get_account(k)) for k in watched}
 result=vm.send_transaction(tx);failed=isinstance(result,f.FailedTransactionMetadata);meta=result.meta() if failed else result
 if not all(tx.verify_with_results()):
  raise RuntimeError('transaction signature verification failed')
 after={str(k):snap(vm.get_account(k)) for k in watched}
 return {'case':c,'error':str(result.err()) if failed else None,'signature':str(tx.signatures[0]),'signature_verified':True,'transaction_base64':base64.b64encode(bytes(tx)).decode(),'synthetic_trader':str(TRADER.pubkey()),'inputs':{'curve':[vt,vs,rt,rs],'reference':reference},'before':before,'after':after,'metadata':json.loads(meta.to_json())}
