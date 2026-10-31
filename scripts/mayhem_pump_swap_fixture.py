"""Ordinary signed synthetic Mayhem trade state with captured AMM/dependency ELFs; no RPC."""
if not __debug__:
    raise SystemExit('Normal Python is required; do not use -O or PYTHONOPTIMIZE.')
from pathlib import Path
import json,base64,hashlib,struct
from solders.pubkey import Pubkey
from solders.account import Account
from solders.instruction import Instruction,AccountMeta
from solders.keypair import Keypair
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata
from solders.litesvm import LiteSVM
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
R=next(p for p in Path(__file__).resolve().parents if (p/'evidence/original/mayhem/deployed.so').is_file())
MAY=Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e');AMM=Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA');FEES=Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ');TOKEN=Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA');TOKEN22=Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb');ATA=Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
F=json.loads((R/'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json').read_text());CONFIG=next(x for x in json.loads((R/'research/imported-lab/analysis/pump_fun/config-snapshot.json').read_text())['accounts'] if x['program_name']=='pump_amm')
TRADER=Keypair.from_seed(hashlib.sha256(b'mayhem-pump-swap-ordinary-owned-trader-v1').digest());PAYER=Keypair.from_seed(hashlib.sha256(b'mayhem-pump-swap-ordinary-owned-payer-v1').digest());GLOBAL=Pubkey.find_program_address([b'global-params'],MAY)[0];SOL=Pubkey.find_program_address([b'sol-vault'],MAY)[0];EVENT=Pubkey.find_program_address([b'__event_authority'],MAY)[0];AEVENT=Pubkey.find_program_address([b'__event_authority'],AMM)[0]
ALT_TRADER=Keypair.from_seed(hashlib.sha256(b'mayhem-pump-swap-ordinary-owned-alternate-trader-v1').digest())
if not all(k.pubkey().is_on_curve() for k in (TRADER, PAYER, ALT_TRADER)):
    raise RuntimeError('synthetic swap keypairs must be on curve')
sha=lambda b:hashlib.sha256(b).hexdigest()
def token(mint,owner,amount,native=False):
 d=bytearray(165);d[:32]=bytes(mint);d[32:64]=bytes(owner);struct.pack_into('<Q',d,64,amount);d[108]=1
 if native:struct.pack_into('<IQ',d,109,1,2039280)
 return bytes(d)
def snap(a):return None if a is None else {'lamports':a.lamports,'owner':str(a.owner),'executable':a.executable,'rent_epoch':a.rent_epoch,'data_base64':None if a.executable else base64.b64encode(a.data).decode(),'data_sha256':sha(a.data)}
def run(c,binary=None):
 vm=LiteSVM().with_sigverify(True).with_blockhash_check(True).with_log_bytes_limit(None)
 for name,pid in [('mayhem',MAY),('pump_amm',AMM),('pump_fees',FEES)]:vm.add_program_from_file(pid,binary if name=='mayhem' and binary else R/f'evidence/original/{name}/deployed.so')
 for name,pid in [('spl_token',TOKEN),('spl_token_2022',TOKEN22),('associated_token',ATA)]:vm.add_program_from_file(pid,R/f'evidence/dependencies/{name}/deployed.so')
 for row in F['accounts'].values():vm.set_account(Pubkey.from_string(row['address']),Account(row['lamports'],base64.b64decode(row['data_base64']),Pubkey.from_string(row['owner'])))
 vm.set_clock(Clock(100,0,0,0,c.get('now',100)))
 for k in [TRADER.pubkey(),PAYER.pubkey(),SOL,EVENT,AEVENT]:vm.set_account(k,Account(10**10,b'',Pubkey.default()))
 base=Pubkey.from_string(F['keys']['base_mint']);quote=Pubkey.from_string(F['keys']['quote_mint']);pool=Pubkey.from_string(F['pool']);vb=Pubkey.from_string(F['keys']['pool_base_token_account']);vq=Pubkey.from_string(F['keys']['pool_quote_token_account']);feeconfig=Pubkey.from_string(F['keys']['fee_config']);config=Pubkey.from_string(CONFIG['address']);btoken=vm.get_account(base).owner;qtoken=vm.get_account(quote).owner
 oldvb=vm.get_account(vb);btoken=TOKEN22;vm.set_account(base,Account(vm.get_account(base).lamports,vm.get_account(base).data,btoken));vb=Pubkey.find_program_address([bytes(pool),bytes(btoken),bytes(base)],ATA)[0];vm.set_account(vb,Account(oldvb.lamports,oldvb.data,btoken))
 pd=bytearray(vm.get_account(pool).data);pd[139:171]=bytes(vb);pd[245:261]=c.get('virtual_quote',0).to_bytes(16,'little',signed=True);pd[271:287]=bytes(16)
 if c.get('token_quote'):
  quote=Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v');qtoken=TOKEN22 if c.get('quote_token22') else TOKEN
  qm=bytearray(82);struct.pack_into('<Q',qm,36,10**15);qm[44]=6;qm[45]=1;vm.set_account(quote,Account(10**9,bytes(qm),qtoken))
  oldpool=vm.get_account(pool);oldvb=vm.get_account(vb);oldvq=vm.get_account(vq)
  pool,bump=Pubkey.find_program_address([b'pool',bytes(pd[9:11]),bytes(pd[11:43]),bytes(base),bytes(quote)],AMM)
  vb=Pubkey.find_program_address([bytes(pool),bytes(btoken),bytes(base)],ATA)[0];vq=Pubkey.find_program_address([bytes(pool),bytes(qtoken),bytes(quote)],ATA)[0]
  pd[8]=bump;pd[75:107]=bytes(quote);pd[139:171]=bytes(vb);pd[171:203]=bytes(vq)
  vm.set_account(vb,Account(oldvb.lamports,token(base,pool,int.from_bytes(oldvb.data[64:72],'little')),btoken));vm.set_account(vq,Account(oldvq.lamports,token(quote,pool,int.from_bytes(oldvq.data[64:72],'little')),qtoken))
  vm.set_account(pool,Account(oldpool.lamports,bytes(pd),AMM))
 else:vm.set_account(pool,Account(vm.get_account(pool).lamports,bytes(pd),AMM))
 gd=bytearray(base64.b64decode(CONFIG['data_base64']));gd[56]=0;vm.set_account(config,Account(CONFIG['lamports'],bytes(gd),AMM))
 protocol=Pubkey(gd[57:89]);creator=Pubkey(pd[211:243]);creatorvault=Pubkey.find_program_address([b'creator_vault',bytes(creator)],AMM)[0]
 bb=Pubkey(base64.b64decode(F['accounts']['buyback_fee_recipient']['data_base64'])[32:64]);bba=Pubkey.find_program_address([bytes(bb),bytes(qtoken),bytes(quote)],ATA)[0]
 def ata(owner,mint,tok):return Pubkey.find_program_address([bytes(owner),bytes(tok),bytes(mint)],ATA)[0]
 basevault=ata(SOL,base,btoken);quotevault=ata(SOL,quote,qtoken);protocolata=ata(protocol,quote,qtoken);creatorata=ata(creatorvault,quote,qtoken)
 vm.set_account(basevault,Account(10**8,token(base,SOL,c.get('tokens',10**9)),btoken))
 for addr,owner,amount in [(quotevault,SOL,c.get('quote_tokens',10**12 if c.get('token_quote') else 0)),(protocolata,protocol,0),(creatorata,creatorvault,0),(bba,bb,0)]:vm.set_account(addr,Account(amount+2039280 if not c.get('token_quote') else 10**8,token(quote,owner,amount,not c.get('token_quote')),qtoken))
 for k in [protocol,creatorvault,bb]:vm.set_account(k,Account(10**8,b'',Pubkey.default()))
 state=Pubkey.find_program_address([b'mayhem-state',bytes(base)],MAY)[0]
 gd=bytearray(hashlib.sha256(b'account:GlobalParams').digest()[:8]+bytes(310));gd[49:81]=bytes(TRADER.pubkey());gd[81:113]=bytes(TRADER.pubkey());gd[48]=c.get('paused',0)
 for off,val in [(16,c.get('cap',0)),(129,c.get('threshold',0)),(146,c.get('interval',0)),(32,c.get('global_risk',(1<<64)-1)),(40,c.get('coin_risk',(1<<64)-1)),(182,c.get('stable_cap',0)),(190,c.get('stable_global_risk',(1<<64)-1)),(198,c.get('stable_coin_risk',(1<<64)-1)),(222,c.get('stable_threshold',0))]:struct.pack_into('<Q',gd,off,val%(1<<64))
 gd[113:129]=c.get('global_sol',0).to_bytes(16,'little',signed=True);gd[206:222]=c.get('global_stable',0).to_bytes(16,'little',signed=True);vm.set_account(GLOBAL,Account(10**8,bytes(gd),MAY))
 sd=bytearray(hashlib.sha256(b'account:MayhemState').digest()[:8]+bytes(162));sd[24:56]=bytes(base);struct.pack_into('<q',sd,16,c.get('deadline',10000));struct.pack_into('<Q',sd,89,c.get('last',0)%(1<<64));sd[97]=c.get('status',1);sd[56:72]=c.get('state_quote',0).to_bytes(16,'little',signed=True);sd[72:88]=c.get('state_tokens',0).to_bytes(16,'little',signed=True);vm.set_account(state,Account(10**8,bytes(sd),MAY))
 gv=Pubkey.find_program_address([b'global_volume_accumulator'],AMM)[0];uv=Pubkey.find_program_address([b'user_volume_accumulator',bytes(SOL)],AMM)[0]
 vol=hashlib.sha256(b'account:GlobalVolumeAccumulator').digest()[:8]+struct.pack('<qqq',1000,10000,86400)+bytes(base)+bytes(480);vm.set_account(gv,Account(10**8,vol,AMM));vm.set_account(uv,Account(10**8,hashlib.sha256(b'account:UserVolumeAccumulator').digest()[:8]+bytes(SOL)+bytes(97),AMM))
 p2=Pubkey.find_program_address([b'pool-v2',bytes(base)],MAY)[0];vm.set_account(p2,Account(10**8,b'',Pubkey.default()))
 keys=[TRADER.pubkey(),GLOBAL,state,base,basevault,quotevault,SOL,Pubkey.default(),qtoken,btoken,ATA,pool,config,quote,vb,vq,protocol,protocolata,AEVENT,AMM,creatorata,creatorvault,gv,uv,feeconfig,FEES,EVENT,MAY,p2,bb,bba]
 writable={0,1,2,4,5,6,11,14,15,16,17,20,22,23,30}
 name=c.get('instruction','buy_pump_swap')
 if name=='sell_pump_swap':keys=keys[:22]+keys[24:];writable={i for i in writable if i<22}|{i-2 for i in writable if i>=24}
 if c.get('missing_quote_vault'):vm.set_account(quotevault,Account(0,b'',Pubkey.default()))
 for i,j in c.get('swap_accounts',[]):keys[i],keys[j]=keys[j],keys[i]
 for idx,spec in c.get('mutations',{}).items():
  key=keys[int(idx)];ac=vm.get_account(key) or Account(10**7,b'',Pubkey.default());d=bytearray(ac.data)
  for off,val in spec.get('bytes',[]):
   if off>=len(d):d.extend(bytes(off+1-len(d)))
   d[off]=val
  for off,val in spec.get('u64',[]):struct.pack_into('<Q',d,off,val)
  for off,val in spec.get('pubkey',[]):d[off:off+32]=bytes(Pubkey.from_string(val))
  if 'length' in spec:d=d[:spec['length']]
  owner=Pubkey.default() if spec.get('system_owner') else Pubkey.from_string(spec['owner']) if 'owner' in spec else ac.owner
  vm.set_account(key,Account(spec.get('lamports',ac.lamports),bytes(d),owner,ac.executable,ac.rent_epoch))
 for idx in c.get('wrong_keys',[]):
  old=keys[idx];key=ALT_TRADER.pubkey() if idx==0 else Pubkey(bytes([60+idx])*32);ac=vm.get_account(old)
  vm.set_account(key,ac if ac and not ac.executable else Account(10**7,b'',Pubkey.default()));keys[idx]=key
 for idx,key in c.get('replace_keys',{}).items():keys[int(idx)]=Pubkey.from_string(key)
 metas=[AccountMeta(k,i==0 and not c.get('unsigned_trader'),i in writable and i not in c.get('readonly',[])) for i,k in enumerate(keys)]
 if 'account_count' in c:metas=metas[:c['account_count']]
 if c.get('extra_account'):metas.append(AccountMeta(TRADER.pubkey(),False,False))
 reserve_base=int.from_bytes(vm.get_account(vb).data[64:72],'little');reserve_quote=int.from_bytes(vm.get_account(vq).data[64:72],'little')+c.get('virtual_quote',0)
 ref=c.get('reference',max(0,min((1<<128)-1,reserve_quote*10**15//reserve_base)) if reserve_base else 0);data=hashlib.sha256(('global:'+name).encode()).digest()[:8]+ref.to_bytes(16,'little')+struct.pack('<HH',c.get('tolerance',2400),c.get('retained',9000))
 if 'payload_length' in c:data=data[:8+c['payload_length']]
 data+=bytes.fromhex(c.get('trailing',''))
 signers=[PAYER]+[keypair for keypair in [TRADER,ALT_TRADER] if any(m.pubkey==keypair.pubkey() and m.is_signer for m in metas)]
 tx=Transaction.new_signed_with_payer([set_compute_unit_limit(1400000),Instruction(MAY,data,metas)],PAYER.pubkey(),signers,vm.latest_blockhash())
 if not all(tx.verify_with_results()):
  raise RuntimeError('transaction signature verification failed')
 watched=list(dict.fromkeys(list(tx.message.account_keys)+keys));before={str(k):snap(vm.get_account(k)) for k in watched};res=vm.send_transaction(tx);failed=isinstance(res,FailedTransactionMetadata);meta=res.meta() if failed else res
 if not all(tx.verify_with_results()):
  raise RuntimeError('transaction signature verification failed')
 return {'case':c,'error':str(res.err()) if failed else None,'signature':str(tx.signatures[0]),'signature_verified':True,'synthetic_trader':str(TRADER.pubkey()),'transaction_base64':base64.b64encode(bytes(tx)).decode(),'before':before,'after':{str(k):snap(vm.get_account(k)) for k in watched},'metadata':json.loads(meta.to_json()),'inputs':{'pool_base':reserve_base,'pool_quote':reserve_quote,'reference':ref}}
