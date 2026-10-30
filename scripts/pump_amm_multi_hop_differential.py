"""Original AMM multi-hop observations with normally signed synthetic local state."""

if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
import sys,pathlib,os

_CALLER_CWD=pathlib.Path.cwd()
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));os.chdir(ROOT)

_CALLER_CWD=pathlib.Path.cwd()
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));os.chdir(ROOT)

_CALLER_CWD=pathlib.Path.cwd()
ROOT=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));os.chdir(ROOT)

from pump_amm_legacy_sell_differential import *

PUMP_GLOBAL=Pubkey.find_program_address([b'global'],PUMP)[0];PUMP_FEES=Pubkey.find_program_address([b'fee_config',bytes(PUMP)],FEES)[0];PUMP_EVENT=Pubkey.find_program_address([b'__event_authority'],PUMP)[0]

PUMP_GLOBAL=Pubkey.find_program_address([b'global'],PUMP)[0];PUMP_FEES=Pubkey.find_program_address([b'fee_config',bytes(PUMP)],FEES)[0];PUMP_EVENT=Pubkey.find_program_address([b'__event_authority'],PUMP)[0]

PUMP_GLOBAL=Pubkey.find_program_address([b'global'],PUMP)[0];PUMP_FEES=Pubkey.find_program_address([b'fee_config',bytes(PUMP)],FEES)[0];PUMP_EVENT=Pubkey.find_program_address([b'__event_authority'],PUMP)[0]

def run(amount=10**9,limit=1,sell=False,tail=True,overrides=None,candidate=None,unsigned=False,separate_payer=False,payload_length=None,extra_data=b''):
 h=acquire_harness(pin_program(candidate or ROOT/'evidence/original/pump_amm/deployed.so'));h.vm.set_clock(Clock(100,1234567890,0,0,1234567890))
 for pid,p in [(TOKEN,'evidence/dependencies/spl_token/deployed.so'),(TOKEN22,'evidence/dependencies/spl_token_2022/deployed.so'),(FEES,'evidence/original/pump_fees/deployed.so'),(ATA,'evidence/dependencies/associated_token/deployed.so'),(PUMP,'evidence/original/pump/deployed.so')]:h.vm.add_program_from_file(pid,ROOT/p)
 for row in f['accounts'].values():h.vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 raw=bytearray(RAW);raw[56]=0;h.vm.set_account(CONFIG_KEY,Account(CONFIG['lamports'],bytes(raw),PROGRAM))
 for k,m,native in [(userbase,base,False),(userquote,quote,True)]:h.vm.set_account(k,Account(10**15+2039280 if native else 10**9,token(m,PAYER.pubkey(),10**15,native),TOKEN))
 h.vm.set_account(volume,Account(0,b'',Pubkey.default()))
 for k in [PUMP_GLOBAL,PUMP_FEES,PUMP_EVENT]:h.vm.set_account(k,Account(10**9,b'',Pubkey.default()))
 ix=next(x for x in IDL['instructions']if x['name']=='multi_hop_swap');keys=[PAYER.pubkey(),userbase if sell else userquote,userquote if sell else userbase,CONFIG_KEY,feeconfig,volume,buyback,TOKEN,TOKEN22,Pubkey.default(),EVENT,PROGRAM,PUMP,PUMP_GLOBAL,PUMP_FEES,PUMP_EVENT];m=[AccountMeta(k,bool(a.get('signer')),bool(a.get('writable')))for k,a in zip(keys,ix['accounts'])]
 if tail:m += [AccountMeta(base,False,False),AccountMeta(quote,False,False),AccountMeta(pool,False,True),AccountMeta(vaultbase,False,True),AccountMeta(vaultquote,False,True)]
 if overrides:overrides(h,m)
 payer=OUTSIDER if unsigned or separate_payer else PAYER
 if unsigned:m[0]=AccountMeta(PAYER.pubkey(),False,True)
 data=bytes(ix['discriminator'])+struct.pack('<QQ',amount,limit)+extra_data
 if payload_length is not None:data=data[:payload_length]
 def snap():
  out={}
  for k in sorted(set([x.pubkey for x in m]+[payer.pubkey()]),key=str):
   a=h.vm.get_account(k)
   if not a or not a.executable:out[str(k)]=None if not a else{'lamports':a.lamports,'owner':str(a.owner),'data_hex':bytes(a.data).hex()}
  return out
 before=snap();tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,data,m)],payer.pubkey(),[payer,PAYER]if separate_payer and not unsigned else[payer],h.vm.latest_blockhash());assert all(tx.verify_with_results());r=h.vm.send_transaction(tx);failed=isinstance(r,FailedTransactionMetadata);meta=r.meta()if failed else r
 return {'error':str(r.err())if failed else None,'logs':meta.logs(),'events':[x for x in meta.logs()if x.startswith('Program data: ')],'inner':json.loads(meta.to_json())['inner_instructions'],'return_data':json.loads(meta.to_json()).get('return_data'),'before':before,'after':snap(),'transaction_base64':base64.b64encode(bytes(tx)).decode()}

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

BASE2=Pubkey.from_bytes(bytes([81])*32);CREATOR2=Pubkey.find_program_address([b'pool-authority',bytes(BASE2)],PUMP)[0];POOL2,BUMP2=Pubkey.find_program_address([b'pool',bytes(2),bytes(CREATOR2),bytes(BASE2),bytes(base)],PROGRAM);VB2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(BASE2)],ATA)[0];VQ2=Pubkey.find_program_address([bytes(POOL2),bytes(TOKEN),bytes(base)],ATA)[0];USER2=Pubkey.from_bytes(bytes([82])*32)

def route2(sell=False):
 def ov(h,m):
  h.vm.set_account(BASE2,h.vm.get_account(base));d=bytearray(poolraw);d[8]=BUMP2;d[9:11]=bytes(2);d[11:43]=bytes(CREATOR2);d[43:75]=bytes(BASE2);d[75:107]=bytes(base);d[139:171]=bytes(VB2);d[171:203]=bytes(VQ2);h.vm.set_account(POOL2,Account(10**9,bytes(d),PROGRAM))
  for k,mi,ow,amt in [(VB2,BASE2,POOL2,10**15),(VQ2,base,POOL2,10**15),(USER2,BASE2,PAYER.pubkey(),10**15)]:h.vm.set_account(k,Account(10**9,token(mi,ow,amt),TOKEN))
  second=[AccountMeta(BASE2,False,False),AccountMeta(base,False,False),AccountMeta(POOL2,False,True),AccountMeta(VB2,False,True),AccountMeta(VQ2,False,True)]
  if sell:m[1]=AccountMeta(USER2,False,True);m[16:16]=second
  else:m[2]=AccountMeta(USER2,False,True);m.extend(second)
 return ov

"""Synthetic local curve routes executed through the original AMM's actual CPI signer."""

x=json.load(open(ROOT/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'));s=x['steps'][4];keys={k:Pubkey.from_string(v)for k,v in x['accounts'].items()}

x=json.load(open(ROOT/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'));s=x['steps'][4];keys={k:Pubkey.from_string(v)for k,v in x['accounts'].items()}

x=json.load(open(ROOT/'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json'));s=x['steps'][4];keys={k:Pubkey.from_string(v)for k,v in x['accounts'].items()}

CURVE=keys['curve'];CB=keys['curve_base'];CM=keys['mint'];CQ=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(quote)],ATA)[0];CU=Pubkey.from_bytes(bytes([83])*32)

CURVE=keys['curve'];CB=keys['curve_base'];CM=keys['mint'];CQ=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(quote)],ATA)[0];CU=Pubkey.from_bytes(bytes([83])*32)

CURVE=keys['curve'];CB=keys['curve_base'];CM=keys['mint'];CQ=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(quote)],ATA)[0];CU=Pubkey.from_bytes(bytes([83])*32)

CURVE=keys['curve'];CB=keys['curve_base'];CM=keys['mint'];CQ=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(quote)],ATA)[0];CU=Pubkey.from_bytes(bytes([83])*32)

CURVE=keys['curve'];CB=keys['curve_base'];CM=keys['mint'];CQ=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(quote)],ATA)[0];CU=Pubkey.from_bytes(bytes([83])*32)

def curve_route(sell=False):
 def ov(h,m):
  for name in ['global','fee_config','mint','curve','curve_base']:
   row=s['before'][name];h.vm.set_account(keys[name],Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
  ca=h.vm.get_account(CURVE)
  h.vm.set_account(CQ,Account(10**15+2039280,token(quote,CURVE,10**15,True),TOKEN))
  u=bytearray(base64.b64decode(s['before']['user_base']['data_base64']));u[32:64]=bytes(PAYER.pubkey());u[64:72]=struct.pack('<Q',10**15);h.vm.set_account(CU,Account(10**9,bytes(u),TOKEN22))
  m[1 if sell else 2]=AccountMeta(CU,False,True)
  m[16:]=[AccountMeta(CM,False,False),AccountMeta(quote,False,False),AccountMeta(CURVE,False,True),AccountMeta(CB,False,True),AccountMeta(CQ,False,True)]
 return ov

def curve_then_amm(sell=False):
 def ov(h,m):
  curve_route(sell)(h,m);saved=m[16:];route2(sell)(h,m)
  creator=CREATOR2;newpool,bump=Pubkey.find_program_address([b'pool',bytes(2),bytes(creator),bytes(BASE2),bytes(CM)],PROGRAM);vb=Pubkey.find_program_address([bytes(newpool),bytes(TOKEN),bytes(BASE2)],ATA)[0];vq=Pubkey.find_program_address([bytes(newpool),bytes(TOKEN22),bytes(CM)],ATA)[0]
  d=bytearray(h.vm.get_account(POOL2).data);d[8]=bump;d[75:107]=bytes(CM);d[139:171]=bytes(vb);d[171:203]=bytes(vq);h.vm.set_account(newpool,Account(10**9,bytes(d),PROGRAM))
  h.vm.set_account(vb,Account(10**9,token(BASE2,newpool,10**15),TOKEN));d=bytearray(h.vm.get_account(CB).data);d[32:64]=bytes(newpool);d[64:72]=struct.pack('<Q',10**15);h.vm.set_account(vq,Account(10**9,bytes(d),TOKEN22))
  second=[AccountMeta(BASE2,False,False),AccountMeta(CM,False,False),AccountMeta(newpool,False,True),AccountMeta(vb,False,True),AccountMeta(vq,False,True)]
  m[16:]=second+saved if sell else saved+second
  m[1 if sell else 2]=AccountMeta(USER2,False,True)
 return ov

def amm_then_curve(sell=False):
 def ov(h,m):
  saved=m[16:];curve_route(sell)(h,m);d=bytearray(h.vm.get_account(CURVE).data);d[83:115]=bytes(base);h.vm.set_account(CURVE,Account(10**12,bytes(d),PUMP));newq=Pubkey.find_program_address([bytes(CURVE),bytes(TOKEN),bytes(base)],ATA)[0];h.vm.set_account(newq,Account(10**9,token(base,CURVE,10**15),TOKEN));second=[AccountMeta(CM,False,False),AccountMeta(base,False,False),AccountMeta(CURVE,False,True),AccountMeta(CB,False,True),AccountMeta(newq,False,True)];m[16:]=second+saved if sell else saved+second
 return ov

CM2=Pubkey.from_bytes(bytes([84])*32);CV2=Pubkey.find_program_address([b'bonding-curve',bytes(CM2)],PUMP)[0];CB2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM2)],ATA)[0];CQ2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM)],ATA)[0];CU2=Pubkey.from_bytes(bytes([85])*32)

CM2=Pubkey.from_bytes(bytes([84])*32);CV2=Pubkey.find_program_address([b'bonding-curve',bytes(CM2)],PUMP)[0];CB2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM2)],ATA)[0];CQ2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM)],ATA)[0];CU2=Pubkey.from_bytes(bytes([85])*32)

CM2=Pubkey.from_bytes(bytes([84])*32);CV2=Pubkey.find_program_address([b'bonding-curve',bytes(CM2)],PUMP)[0];CB2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM2)],ATA)[0];CQ2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM)],ATA)[0];CU2=Pubkey.from_bytes(bytes([85])*32)

CM2=Pubkey.from_bytes(bytes([84])*32);CV2=Pubkey.find_program_address([b'bonding-curve',bytes(CM2)],PUMP)[0];CB2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM2)],ATA)[0];CQ2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM)],ATA)[0];CU2=Pubkey.from_bytes(bytes([85])*32)

CM2=Pubkey.from_bytes(bytes([84])*32);CV2=Pubkey.find_program_address([b'bonding-curve',bytes(CM2)],PUMP)[0];CB2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM2)],ATA)[0];CQ2=Pubkey.find_program_address([bytes(CV2),bytes(TOKEN22),bytes(CM)],ATA)[0];CU2=Pubkey.from_bytes(bytes([85])*32)

def two_curves(sell=False):
 def ov(h,m):
  curve_route(sell)(h,m);first=m[16:]
  h.vm.set_account(CM2,h.vm.get_account(CM));d=bytearray(h.vm.get_account(CURVE).data);d[83:115]=bytes(CM);d[8:48]=struct.pack('<QQQQQ',10**15,10**15,10**15,10**15,10**15);h.vm.set_account(CV2,Account(10**12,bytes(d),PUMP))
  for key,mi,owner,amount in [(CB2,CM2,CV2,10**15),(CQ2,CM,CV2,10**15),(CU2,CM2,PAYER.pubkey(),10**15)]:
   d=bytearray(h.vm.get_account(CB).data);d[:32]=bytes(mi);d[32:64]=bytes(owner);d[64:72]=struct.pack('<Q',amount);h.vm.set_account(key,Account(10**9,bytes(d),TOKEN22))
  second=[AccountMeta(CM2,False,False),AccountMeta(CM,False,False),AccountMeta(CV2,False,True),AccountMeta(CB2,False,True),AccountMeta(CQ2,False,True)]
  m[1 if sell else 2]=AccountMeta(CU2,False,True);m[16:]=second+first if sell else first+second
 return ov

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

BASE3=Pubkey.from_bytes(bytes([86])*32);C3=Pubkey.find_program_address([b'pool-authority',bytes(BASE3)],PUMP)[0];P3,B3=Pubkey.find_program_address([b'pool',bytes(2),bytes(C3),bytes(BASE3),bytes(BASE2)],PROGRAM);VB3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE3)],ATA)[0];VQ3=Pubkey.find_program_address([bytes(P3),bytes(TOKEN),bytes(BASE2)],ATA)[0];U3=Pubkey.from_bytes(bytes([87])*32)

def three_amm(sell=False):
 def ov(h,m):
  route2(sell)(h,m);h.vm.set_account(BASE3,h.vm.get_account(base));d=bytearray(poolraw);d[8]=B3;d[9:11]=bytes(2);d[11:43]=bytes(C3);d[43:75]=bytes(BASE3);d[75:107]=bytes(BASE2);d[139:171]=bytes(VB3);d[171:203]=bytes(VQ3);h.vm.set_account(P3,Account(10**9,bytes(d),PROGRAM))
  for k,mi,owner in [(VB3,BASE3,P3),(VQ3,BASE2,P3),(U3,BASE3,PAYER.pubkey())]:h.vm.set_account(k,Account(10**9,token(mi,owner,10**15),TOKEN))
  group=[AccountMeta(BASE3,False,False),AccountMeta(BASE2,False,False),AccountMeta(P3,False,True),AccountMeta(VB3,False,True),AccountMeta(VQ3,False,True)];m[1 if sell else 2]=AccountMeta(U3,False,True)
  if sell:m[16:16]=group
  else:m.extend(group)
 return ov

def account_change(index,which,value):
 def ov(h,m):
  k=m[index].pubkey;a=h.vm.get_account(k)
  if which=='owner':a=Account(a.lamports,bytes(a.data),value)
  elif which=='data':a=Account(max(a.lamports,10**9),value,a.owner)
  elif which=='readonly':m[index]=AccountMeta(k,m[index].is_signer,False);return
  h.vm.set_account(k,a)
 return ov

def mutate_at(index,offset,data):
 def ov(h,m):
  k=m[index].pubkey;a=h.vm.get_account(k);d=bytearray(a.data);d[offset:offset+len(data)]=data;h.vm.set_account(k,Account(max(a.lamports,10**9),bytes(d),a.owner))
 return ov

"""Bounded original-vs-candidate multi-hop differential; all outer signatures verified."""

from pump_amm_trade_v2_differential import custom_fee_table

import hashlib

def tf(key,bps,maximum):
 def ov(h,m):
  a=h.vm.get_account(key);d=bytearray(a.data[:82])+bytes(83)+bytes([1]);conf=bytes(72)+struct.pack('<QQH',0,maximum,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(key,Account(10**9,bytes(d),TOKEN22))
  for k in ([vaultbase,userbase]if key==base else[vaultquote,userquote]):
   a=h.vm.get_account(k);d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(k,Account(max(a.lamports,10**9),d,TOKEN22))
  if key==quote:
   a=h.vm.get_account(buyback);owner=Pubkey.from_bytes(a.data[32:64]);k=Pubkey.find_program_address([bytes(owner),bytes(TOKEN22),bytes(quote)],ATA)[0];d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(k,Account(10**9,d,TOKEN22));m[6]=AccountMeta(k,False,True)
 return ov

def two_amm_tf(sell,key,bps,maximum):
 def ov(h,m):
  route2(sell)(h,m)
  if key==base:
   tf(key,bps,maximum)(h,m)
   a=h.vm.get_account(VQ2);d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(VQ2,Account(10**9,d,TOKEN22))
  else:
   a=h.vm.get_account(key);d=bytearray(a.data[:82])+bytes(83)+bytes([1]);conf=bytes(72)+struct.pack('<QQH',0,maximum,bps)*2;d+=struct.pack('<HH',1,len(conf))+conf;h.vm.set_account(key,Account(10**9,bytes(d),TOKEN22))
   for k in [VB2,USER2]:
    a=h.vm.get_account(k);d=a.data[:165]+bytes([2])+struct.pack('<HHQ',2,8,0);h.vm.set_account(k,Account(10**9,d,TOKEN22))
 return ov

def volume_state(length=137,offset=None,value=b''):
 def ov(h,m):
  d=bytearray(bytes(next(x for x in IDL['accounts']if x['name']=='UserVolumeAccumulator')['discriminator'])+bytes(PAYER.pubkey())+bytes(97));d=d[:length].ljust(length,b'\0')
  if offset is not None:d[offset:offset+len(value)]=value
  h.vm.set_account(volume,Account(10**9,bytes(d),PROGRAM))
 return ov

def remaining_shape(n):
 def ov(h,m):
  if n<5:m[16:]=m[16:16+n]
  else:m.extend([m[16]]*(n-5))
 return ov

def mixed_direction(h,m):
 route2(False)(h,m);second=m[21:];m[21]=second[1];m[22]=second[0];d=bytearray(h.vm.get_account(USER2).data);d[:32]=bytes(BASE2);h.vm.set_account(USER2,Account(10**9,bytes(d),TOKEN))

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=pathlib.Path,required=True);parser.add_argument('--output',type=pathlib.Path,required=True);args=parser.parse_args();candidate=(_CALLER_CWD/args.candidate).resolve();output=(_CALLER_CWD/args.output).resolve();output.parent.mkdir(parents=True,exist_ok=True);rows=[]
 def test(label,**params):
  original=run(**params);recovered=run(candidate=candidate,**params);diff=[k for k in original if k!='logs'and original[k]!=recovered[k]];rows.append({'case':label,'mismatches':diff,'original':original,'candidate':recovered});None
 for sell in [False,True]:
  for amount in [0,1,2,3,4,5,10,100,1000,10**6,10**9,10**12,10**15,2**64-1]:
   for limit in [0,1,2**64-1]:test(f'amount-limit-{sell}-{amount}-{limit}',sell=sell,amount=amount,limit=limit)
  test(f'unsigned-{sell}',sell=sell,unsigned=True);test(f'separate-payer-{sell}',sell=sell,separate_payer=True);test(f'readonly-user-{sell}',sell=sell,separate_payer=True,overrides=meta_mutation(0,'readonly'))
  for n in range(24):test(f'payload-{sell}-{n}',sell=sell,payload_length=n)
  test(f'extra-data-{sell}',sell=sell,extra_data=b'abc')
  for idx in range(1,21):test(f'substitute-{sell}-{idx}',sell=sell,overrides=meta_mutation(idx,'substitute'))
  for idx in [1,2,3,4,5,6,18,19,20]:test(f'readonly-{sell}-{idx}',sell=sell,overrides=meta_mutation(idx,'readonly'))
  for key in [pool,CONFIG_KEY,base,quote,userbase,userquote,vaultbase,vaultquote,feeconfig,buyback]:test(f'owner-{sell}-{key}',sell=sell,overrides=mutate(key,0,b'',owner=Pubkey.default()))
  for key in [userbase,userquote,vaultbase,vaultquote,buyback]:
   for off,d in [(0,bytes(32)),(32,bytes(32)),(108,b'\0'),(108,b'\2')]:test(f'token-{sell}-{key}-{off}-{d.hex()}',sell=sell,overrides=mutate(key,off,d))
   for n in [0,1,2**64-1]:test(f'balance-{sell}-{key}-{n}',sell=sell,overrides=mutate(key,64,struct.pack('<Q',n)))
  for off,d in [(8,b'\0'),(11,bytes(32)),(43,bytes(32)),(75,bytes(32)),(139,bytes(32)),(171,bytes(32)),(211,bytes(32)),(243,b'\1'),(244,b'\1'),(270,b'\1')]:test(f'pool-field-{sell}-{off}',sell=sell,overrides=mutate(pool,off,d))
  for v in [-2**127,-10**13,-125882,-125881,0,1,10**9,2**64,2**127-1]:test(f'virtual-{sell}-{v}',sell=sell,overrides=mutate(pool,245,v.to_bytes(16,'little',signed=True)))
  for off in [261,271,279]:
   for v in [0,1,10**9,2**64-1]:test(f'pool-fees-{sell}-{off}-{v}',sell=sell,overrides=mutate(pool,off,struct.pack('<Q',v)))
  for v in [0,1,9999,10000,10001,2**64-1]:test(f'buyback-bps-{sell}-{v}',sell=sell,overrides=mutate(CONFIG_KEY,899,struct.pack('<Q',v)))
  for flags in [0,1,2,4,8,16,31,255]:test(f'disabled-{sell}-{flags}',sell=sell,overrides=mutate(CONFIG_KEY,56,bytes([flags])))
  for length in [0,7,8,210,211,243,244,245,261,270,271,286,287,300]:test(f'pool-length-{sell}-{length}',sell=sell,overrides=mutate(pool,0,b'',length))
  for length in [0,7,8,40,73,89,90,136,137,138]:test(f'volume-length-{sell}-{length}',sell=sell,overrides=volume_state(length))
  for off,d in [(8,bytes(32)),(8,bytes(OUTSIDER.pubkey())),(40,b'\1'),(41,struct.pack('<Q',123)),(49,struct.pack('<Q',456)),(57,struct.pack('<Q',789)),(65,struct.pack('<Q',1234))]:test(f'volume-field-{sell}-{off}-{d.hex()}',sell=sell,overrides=volume_state(offset=off,value=d))
  for length in [0,7,8,40,65,69,1068,1069,2511,2512,3000,4072,4073,4096,4097]:test(f'fee-length-{sell}-{length}',sell=sell,overrides=mutate(feeconfig,0,b'',length))
  for tiers in [[],[(0,(0,0,0))],[(0,(10,20,30))],[(2**120,(10,20,30)),(0,(40,50,60))],[(0,(10,20,30)),(0,(40,50,60))],[(0,(10000,10000,10000))],[(0,(2**64-1,0,0))]]:test(f'fee-table-{sell}-{tiers}',sell=sell,overrides=custom_fee_table(tiers))
  for key in [base,quote]:
   for bps in [0,1,100,9999,10000]:
    for maximum in [0,1,123,2**64-1]:test(f'transfer-fee-{sell}-{key}-{bps}-{maximum}',sell=sell,overrides=tf(key,bps,maximum))
  for count in [0,1,2,3,4,5,6,9,10,11]:test(f'remaining-{sell}-{count}',sell=sell,overrides=remaining_shape(count))
  for kind,setup in [('two-amm',route2),('three-amm',three_amm),('curve',curve_route),('curve-amm',curve_then_amm),('amm-curve',amm_then_curve),('two-curves',two_curves)]:
   for amount in [1,10**6,10**9,10**12]:
    for limit in [1,2**64-1]:test(f'route-{kind}-{sell}-{amount}-{limit}',sell=sell,amount=amount,limit=limit,overrides=setup(sell))
  for length in [0,7,8,56,642,907,939,940,948,949,1000]:test(f'global-length-{sell}-{length}',sell=sell,overrides=mutate(CONFIG_KEY,0,b'',length))
 for sell in [False,True]:
  for key in [base,BASE2]:
   for bps in [0,1,100,10000]:
    for maximum in [123,2**64-1]:test(f'two-amm-tf-{sell}-{key}-{bps}-{maximum}',sell=sell,overrides=two_amm_tf(sell,key,bps,maximum))
 test('mixed-direction',overrides=mixed_direction)
 failures=[i for i,r in enumerate(rows)if r['mismatches']];sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest();output.write_text(json.dumps({'scope':'Bounded original-vs-candidate offline MultiHopSwap with normal verified test-owned signatures and captured dependencies. Synthetic fixture mutations.','candidate':str(candidate),'candidate_sha256':sha(pin_program(candidate)),'original_sha256':sha(pin_program(ROOT/'evidence/original/pump_amm/deployed.so')),'case_count':len(rows),'passed':len(rows)-len(failures),'mismatches':failures,'cases':rows},separators=(',',':'))+'\n',encoding='utf-8',newline='\n');print(len(rows),len(failures));raise SystemExit(bool(failures))

