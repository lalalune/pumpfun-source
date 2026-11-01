#!/usr/bin/env python3
"""Signed Surfpool probes for assigned AMM findings; synthetic local state only."""
from __future__ import annotations
import base64, hashlib, json, struct, sys
from pathlib import Path
from types import SimpleNamespace
from solders.account import Account
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.keypair import Keypair
from solders.transaction import Transaction

HERE=Path(__file__).resolve().parent; ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/'scripts')]
from surfpool_rpc import Surfpool,RecordingVM,original,dependency,install_fixture,resign,sha256
import pump_amm_admin_differential as admin
import pump_amm_incentives_differential as inc
import pump_amm_accumulator_differential as accum
import pump_amm_cashback_differential as cashback
import pump_amm_trade_v2_differential as trade
import pump_amm_multi_hop_differential as multi
import pump_amm_creator_reassignment_differential as creators
import pump_amm_migration_create_differential as migration
import pump_amm_create_differential as create
import pump_migrate_v2_probe as migrate_probe

PROGRAM=admin.PROGRAM; PAYER=admin.PAYER; OUTSIDER=admin.OUTSIDER
DEPS=[(inc.TOKEN,'spl_token'),(inc.TOKEN22,'spl_token_2022'),(inc.ATA,'associated_token'),
      (trade.FEES,None),(multi.PUMP,None)]
OUT=HERE/'results/amm-evidence'; OUT.mkdir(parents=True,exist_ok=True)

class Recorder:
    def __init__(self): self.vms=[]
    def vm(self): v=RecordingVM();self.vms.append(v);return v
    def harness(self,_):
        v=self.vm()
        for kp in [PAYER,OUTSIDER]:v.airdrop(kp.pubkey(),10**12)
        v.set_account(admin.EVENT,Account(10**9,b'',Pubkey.default()))
        return SimpleNamespace(vm=v)
    def run_lite(self,module,fn,*args,**kwargs):
        old=module.LiteSVM;module.LiteSVM=lambda *a,**k:self.vm()
        try: fn(*args,**kwargs)
        finally: module.LiteSVM=old
        return self.vms[-1]
    def run_acq(self,module,fn,*args,**kwargs):
        old=module.acquire_harness;module.acquire_harness=self.harness
        try: fn(*args,**kwargs)
        finally: module.acquire_harness=old
        return self.vms[-1]

def state(pool,keys):
    ans={}
    for key in sorted(set(map(str,keys))):
        a=pool.get_account(key)
        if a is None: ans[key]=None;continue
        raw=bytes.fromhex(a['data'])
        ans[key]={'lamports':a['lamports'],'owner':a['owner'],'data_sha256':a['data_sha256'],
                  'data_len':len(raw),'token_amount':int.from_bytes(raw[64:72],'little') if len(raw)>=165 else None}
        if a['owner']==str(PROGRAM) and len(raw)<=1000:ans[key]['data_hex']=a['data']
    return ans

def replay(pool,vm,signers=(PAYER,),extra_keys=(),payer=None):
    install_fixture(pool,vm)
    # RecordingVM intentionally omits executable captures only when the local VM loaded them.
    # Custom recorders do not execute locally, so restore every pinned executable after fixture installation.
    for address,meta in list(pool.loaded_programs.items()):pool.load_program(address,Path(meta['path']))
    tx=vm.transaction if not signers else resign(vm.transaction,(payer or PAYER).pubkey(),list(signers),pool.latest_blockhash())
    keys=list(vm.accounts)+list(extra_keys)+list(tx.message.account_keys)
    before=state(pool,keys)
    try: r=pool.send(tx)
    except TimeoutError:
        sim=pool.simulate(tx,sig_verify=True)
        sig=pool.rpc('sendTransaction',[base64.b64encode(bytes(tx)).decode(),{'encoding':'base64','skipPreflight':True}])
        r={'signature':sig,'error':sim.get('err') or 'TransactionNotConfirmed','logs':sim.get('logs',[]),'return_data':sim.get('returnData'),'simulation':sim,'signature_verification':True,'confirmation':'not_observed'}
    after=state(pool,keys)
    r['before']=before;r['after']=after
    r['state_deltas']={k:{'before':before.get(k),'after':after.get(k)} for k in after if before.get(k)!=after.get(k)}
    return r

def custom_admin(vm,instruction,args):
    vm.set_clock(admin.Clock(100,1234567890,0,0,1234567890)) if hasattr(admin,'Clock') else None
    for kp in [PAYER,OUTSIDER]:vm.airdrop(kp.pubkey(),10**12)
    vm.set_account(admin.EVENT,Account(10**9,b'',Pubkey.default()))
    raw=bytearray(admin.RAW);raw[8:40]=bytes(PAYER.pubkey())
    vm.set_account(admin.CONFIG_KEY,Account(admin.CONFIG['lamports'],bytes(raw),PROGRAM))
    if instruction=='update_admin':
        metas=[AccountMeta(PAYER.pubkey(),True,True),AccountMeta(admin.CONFIG_KEY,False,True),AccountMeta(OUTSIDER.pubkey(),False,False),AccountMeta(admin.EVENT,False,False),AccountMeta(PROGRAM,False,False)]
    elif instruction=='update_creator_fee_config':
        metas=[AccountMeta(PAYER.pubkey(),True,True),AccountMeta(admin.CONFIG_KEY,False,True),AccountMeta(Pubkey.default(),False,False),AccountMeta(admin.EVENT,False,False),AccountMeta(PROGRAM,False,False)]
    disc=bytes(next(x for x in admin.IDL['instructions'] if x['name']==instruction)['discriminator'])
    tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,disc+args,metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash())
    vm.send_transaction(tx)

def create_config(vm):
    for kp in [PAYER]:vm.airdrop(kp.pubkey(),10**12)
    vm.set_account(admin.EVENT,Account(10**9,b'',Pubkey.default()))
    key=Pubkey.find_program_address([b'global_config'],PROGRAM)[0]
    vm.set_account(key,Account(0,b'',Pubkey.default()))
    ix=next(x for x in admin.IDL['instructions'] if x['name']=='create_config')
    metas=[AccountMeta(PAYER.pubkey(),True,True),AccountMeta(key,False,True),AccountMeta(Pubkey.default(),False,False),AccountMeta(admin.EVENT,False,False),AccountMeta(PROGRAM,False,False)]
    args=struct.pack('<QQ',25,5)+bytes(256)+struct.pack('<Q',0)+bytes(PAYER.pubkey())
    tx=Transaction.new_signed_with_payer([Instruction(PROGRAM,bytes(ix['discriminator'])+args,metas)],PAYER.pubkey(),[PAYER],vm.latest_blockhash());vm.send_transaction(tx)

def special_mint_override(special,extension_type=12):
    def ov(h,m):
        old=h.vm.get_account(create.base);raw=bytearray(old.data[:82])+bytes(83)+b'\1'+struct.pack('<HH',extension_type,32)+bytes(32)
        h.vm.set_account(special,Account(old.lamports,bytes(raw),inc.TOKEN22))
        pool=Pubkey.find_program_address([b'pool',struct.pack('<H',0),bytes(PAYER.pubkey()),bytes(special),bytes(create.quote)],PROGRAM)[0]
        lp=Pubkey.find_program_address([b'pool_lp_mint',bytes(pool)],PROGRAM)[0]
        ata=lambda owner,mint,tp:Pubkey.find_program_address([bytes(owner),bytes(tp),bytes(mint)],inc.ATA)[0]
        vb=ata(pool,special,inc.TOKEN22);vq=ata(pool,create.quote,inc.TOKEN);userlp=ata(PAYER.pubkey(),lp,inc.TOKEN22)
        ub=bytearray(h.vm.get_account(create.userbase).data[:165]);ub[:32]=bytes(special)
        h.vm.set_account(create.userbase,Account(10**9,bytes(ub),inc.TOKEN22))
        for key in [pool,lp,vb,vq,userlp]:h.vm.set_account(key,Account(0,b'',Pubkey.default()))
        for i,key in [(0,pool),(3,special),(5,lp),(8,userlp),(9,vb),(10,vq),(13,inc.TOKEN22)]:m[i]=AccountMeta(key,m[i].is_signer,m[i].is_writable)
    return ov

def quote_delegate_reject(h,m):
    # Noncanonical create_pool must reject PermanentDelegate; canonical CPI admission is separate.
    a=h.vm.get_account(create.quote);raw=a.data[:82]+bytes(83)+b'\1'+struct.pack('<HH',12,32)+bytes(32)
    h.vm.set_account(create.quote,Account(a.lamports,raw,inc.TOKEN22))
    uq=h.vm.get_account(create.userquote);h.vm.set_account(create.userquote,Account(uq.lamports,uq.data[:165],inc.TOKEN22))
    m[14]=AccountMeta(inc.TOKEN22,False,False)
    pool=m[0].pubkey;vq=Pubkey.find_program_address([bytes(pool),bytes(inc.TOKEN22),bytes(create.quote)],inc.ATA)[0]
    h.vm.set_account(vq,Account(0,b'',Pubkey.default()));m[10]=AccountMeta(vq,False,True)

def token_account(mint,owner,amount):
    raw=bytearray(165);raw[:32]=bytes(mint);raw[32:64]=bytes(owner);struct.pack_into('<Q',raw,64,amount);raw[108]=1
    return bytes(raw)

def independent_delegate_transfer(pool,quote,vault,delegate,amount=1):
    recipient=Pubkey.from_bytes(bytes([239])*32)
    pool.set_account(recipient,Account(2039280,token_account(quote,recipient,0),inc.TOKEN22))
    pool.set_account(delegate.pubkey(),Account(10**12,b'',Pubkey.default()))
    keys=[quote,vault,recipient,delegate.pubkey()];before=state(pool,keys)
    ix=Instruction(inc.TOKEN22,bytes([12])+struct.pack('<QB',amount,6),[
        AccountMeta(vault,False,True),AccountMeta(quote,False,False),
        AccountMeta(recipient,False,True),AccountMeta(delegate.pubkey(),True,False)])
    tx=Transaction.new_signed_with_payer([ix],delegate.pubkey(),[delegate],pool.latest_blockhash())
    r=pool.send(tx);after=state(pool,keys);r['before']=before;r['after']=after
    r['state_deltas']={k:{'before':before.get(k),'after':after.get(k)} for k in after if before.get(k)!=after.get(k)}
    r['recipient']=str(recipient)
    return r

def main():
    evidence={}
    with Surfpool(OUT,binary=HERE/'tools/surfpool') as pool:
        pool.load_program(PROGRAM,original('pump_amm'))
        for pid,name in DEPS:pool.load_program(pid,original('pump_fees') if name is None and pid==trade.FEES else original('pump') if name is None else dependency(name))
        loaded=pool.loaded_programs.copy()
        def save(name,vm,signers=(PAYER,),payer=None):
            evidence[name]=replay(pool,vm,signers,payer=payer)
            print(name,evidence[name]['error'],flush=True)
        # L-02 / L-10 / H-09
        r=Recorder();vm=r.vm();custom_admin(vm,'update_creator_fee_config',struct.pack('<BQ',1,10001));save('L-02_max_10001',vm)
        r=Recorder();vm=r.vm();custom_admin(vm,'update_creator_fee_config',struct.pack('<BQ',1,10000));save('L-02_max_10000_control',vm)
        r=Recorder();vm=r.vm();custom_admin(vm,'update_admin',b'');save('L-10_nonsigner_new_admin',vm)
        r=Recorder();vm=r.vm();create_config(vm);save('H-09_wrong_fixed_admin',vm)
        # Incentives and closure
        for label,period in [('L-03_zero_period',0),('L-03_negative_period',-1)]:
            r=Recorder();r.run_acq(inc,inc.run,{'instruction':'admin_update_token_incentives','new_start':0,'new_end':0,'new_period':period,'day':0,'supply':0});save(label,r.vms[-1])
        r=Recorder();r.run_acq(inc,inc.run,{'instruction':'admin_update_token_incentives','missing':['global_volume_accumulator']});save('M-06_missing_global',r.vms[-1])
        r=Recorder();r.run_acq(inc,inc.run,{'instruction':'admin_update_token_incentives','new_start':0,'new_end':0,'day':0,'supply':0,'mutate':'global_incentive_token_account','offset':72,'value':(b'\1\0\0\0'+bytes(32)).hex()});save('M-17_delegated_reward_vault',r.vms[-1])
        r=Recorder();vm=r.vm();ah=accum.AccumulatorHarness.__new__(accum.AccumulatorHarness);ah.vm=vm;ah.run('close_user_volume_accumulator',offset=41,value=struct.pack('<Q',5));save('L-06_close_pending',vm)
        # M-15 foreign-mint counter boundary
        r=Recorder();r.run_acq(cashback,cashback.run,{'non_native':True,'earned':42,'amount':2**64-14});save('M-15_saturate',r.vms[-1])
        r=Recorder();r.run_acq(cashback,cashback.run,{'non_native':True,'earned':2**64-1,'claimed':2**64-1,'amount':1});save('M-15_positive_after_saturation',r.vms[-1])
        # Trading, whitelist, route direction, and rounding boundary fixture
        r=Recorder();r.run_acq(trade,trade.trade,'buy_v2',10**7,2**64-1);save('M-03_buy_volume',r.vms[-1])
        r=Recorder();r.run_acq(trade,trade.trade,'buy_exact_quote_in_v2',337,1,trade.custom_fee_table([(0,(100,100,100))]));save('L-13_exact_337',r.vms[-1])
        def whitelist(h,m):
            a=h.vm.get_account(admin.CONFIG_KEY);d=bytearray(a.data);d[353:385]=bytes(PAYER.pubkey());h.vm.set_account(admin.CONFIG_KEY,Account(a.lamports,bytes(d),a.owner))
        r=Recorder();r.run_acq(trade,trade.trade,'buy_v2',10**7,2**64-1,whitelist);save('L-14_direct_whitelist',r.vms[-1])
        r=Recorder();r.run_acq(multi,multi.run,10**7,1,False,True,whitelist);save('L-14_routed_whitelist',r.vms[-1])
        r=Recorder();r.run_acq(multi,multi.run,10**7,1,False,True,multi.mixed_direction);save('M-04_mixed_direction',r.vms[-1])
        # Creator migration and metadata behavior
        r=Recorder();r.run_acq(creators,creators.run_creator,{'op':'migrate_pool_coin_creator','status':0});save('L-04_paused_migration',r.vms[-1])
        r=Recorder();r.run_acq(creators,creators.run_creator,{'op':'set_coin_creator','verified':0});save('L-05_unverified_metadata',r.vms[-1])
        r=Recorder();r.run_acq(creators,creators.run_creator,{'op':'set_coin_creator','metadata_creators':[]});save('L-05_empty_metadata',r.vms[-1])
        # Genuine saved Pump signature; no sigVerify bypass.
        r=Recorder();r.run_lite(migration,migration.run_migration,None,'missing_boost',lambda vm,k:[(lambda a,d:vm.set_account(k['bonding_curve'],Account(a.lamports,bytes(d),a.owner)))(vm.get_account(k['bonding_curve']),(lambda d:(d.__setitem__(slice(115,123),struct.pack('<Q',10001)),d)[1])(bytearray(vm.get_account(k['bonding_curve']).data)))]);save('M-05_canonical_curve_mutation',r.vms[-1],signers=())
        # Fixed PUMP mint bypass; ordinary quote delegate rejection.
        special=Pubkey.from_bytes(bytes([12,69,247,223,141,158,114,149,98,132,147,63,109,152,183,87,3,46,131,223,132,96,79,181,225,23,255,246,29,91,18,249]))
        r=Recorder();r.run_acq(create,create.create,10**9,10**9,0,None,False,b'',None,special_mint_override(special));save('M-19_fixed_mint_extension',r.vms[-1])
        r=Recorder();r.run_acq(create,create.create,10**9,10**9,0,None,False,b'',None,quote_delegate_reject);save('H-08_ordinary_delegate_rejected',r.vms[-1])
        # Second pass: fresh, genuinely signed original Pump migrate_v2 CPI routes.
        migration_signers=[migrate_probe.PAYER,migrate_probe.USER]
        r=Recorder();r.run_lite(migrate_probe,migrate_probe.run,{'boost':True});save('M-05_valid_canonical_control',r.vms[-1],migration_signers,migrate_probe.PAYER)
        invalid={'boost':True,'mutations':{'bonding_curve':{'patches':[(115,struct.pack('<Q',10001).hex())]}}}
        r=Recorder();r.run_lite(migrate_probe,migrate_probe.run,invalid);save('M-05_invalid_creator_fee_forwarded',r.vms[-1],migration_signers,migrate_probe.PAYER)
        canonical={'boost':True,'stable':True,'quote22':True}
        r=Recorder();r.run_lite(migrate_probe,migrate_probe.run,canonical);save('H-08_canonical_token22_control',r.vms[-1],migration_signers,migrate_probe.PAYER)
        delegate=Keypair.from_seed(bytes([240])*32)
        tlv=bytes(83)+b'\1'+struct.pack('<HH',12,32)+bytes(delegate.pubkey())
        delegated={'boost':True,'stable':True,'quote22':True,'mutations':{'quote_mint':{'patches':[(82,tlv.hex())]}}}
        r=Recorder();r.run_lite(migrate_probe,migrate_probe.run,delegated);save('H-08_canonical_delegate_migration',r.vms[-1],migration_signers,migrate_probe.PAYER)
        if evidence['H-08_canonical_delegate_migration']['error'] is None:
            stable_mint=Pubkey.from_bytes(bytes([217])*32)
            pa=Pubkey.find_program_address([b'pool-authority',bytes(migrate_probe.MINT)],multi.PUMP)[0]
            pool_key=Pubkey.find_program_address([b'pool',bytes(2),bytes(pa),bytes(migrate_probe.MINT),bytes(stable_mint)],PROGRAM)[0]
            vault=Pubkey.find_program_address([bytes(pool_key),bytes(inc.TOKEN22),bytes(stable_mint)],inc.ATA)[0]
            evidence['H-08_independent_delegate_transfer']=independent_delegate_transfer(pool,stable_mint,vault,delegate)
            print('H-08_independent_delegate_transfer',evidence['H-08_independent_delegate_transfer']['error'],flush=True)
    idl_path=ROOT/'evidence/upstream/pump_amm.json';idl=json.loads(idl_path.read_text())
    inventory={'idl_path':str(idl_path),'idl_sha256':sha256(idl_path),'global_volume_account':next(a for a in idl['accounts'] if a['name']=='GlobalVolumeAccumulator'),
               'initializer_like_instructions':[i['name'] for i in idl['instructions'] if any(s in i['name'] for s in ('init','create','admin_update_token_incentives'))],
               'global_volume_initializer_candidates':[i['name'] for i in idl['instructions'] if 'global' in i['name'] and ('init' in i['name'] or 'create' in i['name'])],
               'live_deployment_account_state':'not queried; offline Surfpool fixtures only'}
    (OUT/'initializer-inventory.json').write_text(json.dumps(inventory,indent=2)+'\n')
    blob={'target':'evidence/original/pump_amm/deployed.so','loaded_programs':loaded,'surfpool':'pinned tools/surfpool 1.6.1','signature_verification':True,'cases':evidence}
    (OUT/'transactions.json').write_text(json.dumps(blob,indent=2)+'\n')

if __name__=='__main__':main()
