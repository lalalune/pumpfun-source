# w17a18 stitch17 gene library on main bf01b5fd9 (programs/pump identical to bf01b5f). Experiment only.
G={}
LIB={}   # gene -> lib.rs edits
def apply(s,names,ls=None):
    for n in names:
        for e in G[n]:
            if callable(e): s=e(s); continue
            if len(e)==3: a,b,k=e
            else: (a,b),k=e,1
            c=s.count(a)
            if c!=k: raise Exception(f'gene {n}: {c} occurrences (want {k}) of {a[:120]!r}')
            s=s.replace(a,b)
        for a,b in LIB.get(n,[]):
            c=ls.count(a)
            if c!=1: raise Exception(f'lib gene {n}: {c} occurrences of {a[:80]!r}')
            ls=ls.replace(a,b)
    return s,ls
G['m0']=[]
_SH0='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
G['crl3']=[(_SH0,'let shared={let cr=a.bonding_curve.creator;cr==a.sharing_config.key()}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
G['crl2']=[(_SH0,'let shared={let cr=a.bonding_curve.creator;let sk=a.sharing_config.key();cr==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
G['t1n']=[('if shared{if holder{sharing_update=Some(None);(false,false)}else{','if shared{if new.is_none(){sharing_update=Some(None);(false,false)}else{')]
_SHIMT='target=unsafe{core::ptr::read_volatile(&a.bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the curve box pointer*/.creator;'
_VAL='let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;'
# g1: creator copied from st before validate, shared-arm target from that copy (replaces the curve-box reload shim)
G['g1']=[(_VAL,'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;'),('sharing_update=Some(args.0);'+_SHIMT,'sharing_update=Some(args.0);target=creator;')]
# g1 keeping a volatile read for the creator copy (shim-era g1)
G['g1v']=[(_VAL,'let sk=a.sharing_config.key();let creator=st.creator;let mut target=validate(&st,hopt,fee,new,holder_key,&sk)?;'),('sharing_update=Some(args.0);'+_SHIMT,'sharing_update=Some(args.0);target=unsafe{core::ptr::read_volatile(&creator)}/*shim: creator copy kept*/;')]
# un-shim the shared-arm target (plain a.bonding_curve.creator)
G['nobox']=[('sharing_update=Some(args.0);'+_SHIMT,'sharing_update=Some(args.0);target=a.bonding_curve.creator;')]
G['I6n']=[('sharing_update=Some(args.0);'+_SHIMT+'(false,true)',_SHIMT+'sharing_update=Some(args.0);(false,true)')]
G['vol334b']=[('unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{','if !st.fee_configurable{')]
G['vol338b']=[('return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}','return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}')]
# shim knobs: volatile CtoState flag loads (w17a03 L2735/L2737, w17a06 vl cells, w17a12 pins)
G['kcb']=[('cashback:a.bonding_curve.is_cashback_coin,quote_locked','cashback:unsafe{core::ptr::read_volatile(&a.bonding_curve.is_cashback_coin)}/*shim: pins the CtoState cashback load*/,quote_locked')]
G['khe']=[('holder_enabled:a.global.is_holder_reward_enabled};','holder_enabled:unsafe{core::ptr::read_volatile(&a.global.is_holder_reward_enabled)}/*shim: pins the CtoState holder_enabled load*/};')]
G['khr']=[('holder_reward:a.bonding_curve.is_holder_reward,cashback','holder_reward:unsafe{core::ptr::read_volatile(&a.bonding_curve.is_holder_reward)}/*shim: pins the CtoState holder_reward load*/,cashback')]
G['kmy']=[('mayhem:a.bonding_curve.is_mayhem_mode,','mayhem:unsafe{core::ptr::read_volatile(&a.bonding_curve.is_mayhem_mode)}/*shim: pins the CtoState mayhem load*/,')]
G['kfc']=[('let st=CtoState{fee_configurable:a.global.creator_fee_configurable,','let st=CtoState{fee_configurable:unsafe{core::ptr::read_volatile(&a.global.creator_fee_configurable)}/*shim: pins the CtoState fee_configurable load*/,')]
G['kmf']=[('max_fee:a.global.max_configurable_creator_fee_bps,','max_fee:unsafe{core::ptr::read_volatile(&a.global.max_configurable_creator_fee_bps)}/*shim: pins the CtoState max_fee load*/,')]
# shared-arm accounts pointer reload (w17a06 vl:execute:28871 form) on top of the landed curve-box reload
G['kacc']=[(_SHIMT,'target=unsafe{core::ptr::read_volatile(&(*core::ptr::read_volatile(core::mem::transmute::<&&mut AdminCto,*const &AdminCto>(a))).bonding_curve as *const Box<Account<BondingCurve>> as *const &Account<BondingCurve>)}/*shim: reload the accounts and curve box pointers*/.creator;')]
G['pcol']=[('if !collection_native||coin_present{','if collection_native==false||coin_present{')]
G['a1']=[('let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;','let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;')]
G['cumatch']=[('if let Some(f)=fee{curve.creator_fee_bps=f;}','match fee{Some(f)=>curve.creator_fee_bps=f,None=>{}}')]
G['shfk']=[('a.sharing_config.owner==&FEES','a.sharing_config.owner==a.pump_fees.key')]
G['cb5']=[('let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}','let shared={let sk=a.sharing_config.key();sk==a.bonding_curve.creator}')]
G['wlwe']=[('if !a.current_creator.is_writable{return','if a.current_creator.is_writable==false{return')]
G['c2']=[('if collect_old{wallet(&ctx)?;}','collect_old.then(||wallet(&ctx)).transpose()?;')]
G['gwclk']=[('     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,','     let ts=Clock::get()?.unix_timestamp;let e=CollectCreatorFeeEvent{timestamp:ts,')]
G['mapamt']=[('(if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)','if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner).map(|()|amount)}else{Ok(amount)}')]
G['mkql']=[('let q=a.bonding_curve.quote_mint;(unsafe{expect(q==Pubkey::default(),false)})','let q=a.bonding_curve.quote_mint;(unsafe{expect(Pubkey::default()==q,false)})')]
# fallback: the w16a17 union library (g16) for genes not re-spelled here (most apply verbatim to the shim-era source)
def _g16():
    import sys,os
    p=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a17-cto-stitch16/tools')
    if p not in sys.path: sys.path.insert(0,p)
    import g16; return g16
class _GD(dict):
    def __missing__(self,k):
        g=_g16()
        if k.startswith('lit:') and k not in g.G: g.G[k]=g._litgene(k)
        if k in g.G: return g.G[k]
        raise KeyError(k)
G=_GD(G)
G['unpcol']=[('if collection_native==false||coin_present{','if !collection_native||coin_present{')]
G['re334']=[('   if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','   unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
G['re334u']=[('   if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','   unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
G['re334']=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder before the fee_configurable test*/;if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
G['re334u']=[('  if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}','  unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};if !st.fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}')]
_PH='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;'
G['ph326']=[('  match fee{Some(f)=>{if st.quote_locked{','  match fee{Some(f)=>{'+_PH+'if st.quote_locked{')]
G['ph330']=[('   if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}','   '+_PH+'if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['ph314']=[('  let cashback=if holder{false}else{st.cashback};','  '+_PH+'let cashback=if holder{false}else{st.cashback};')]
G['ph338a']=[('   if f==0||f>st.max_fee{','   '+_PH+'if f==0||f>st.max_fee{')]
G['ph296']=[('  if holder&&!st.holder_reward&&!st.holder_enabled{','  '+_PH+'if holder&&!st.holder_reward&&!st.holder_enabled{')]
G['ph289']=[('  if st.holder_reward&&!(hopt==Some(true)){','  '+_PH+'if st.holder_reward&&!(hopt==Some(true)){')]
G['ph326']=[('match fee{Some(f)=>{if st.quote_locked{','match fee{Some(f)=>{'+_PH+'if st.quote_locked{')]
G['ph330']=[('if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}',_PH+'if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['ph314']=[('let cashback=if holder{false}else{st.cashback};',_PH+'let cashback=if holder{false}else{st.cashback};')]
G['ph338a']=[('if f==0||f>st.max_fee{',_PH+'if f==0||f>st.max_fee{')]
G['ph296']=[('if holder&&!st.holder_reward&&!st.holder_enabled{',_PH+'if holder&&!st.holder_reward&&!st.holder_enabled{')]
G['ph289']=[('if st.holder_reward&&!(hopt==Some(true)){',_PH+'if st.holder_reward&&!(hopt==Some(true)){')]
# leave-one-out revert genes (data/loo.json from tools/loo.py): looNNNN = whole landing; looNNNN_k = its k-th changed line only
def _loo():
    import json,os
    p=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'data','loo.json')
    if not os.path.exists(p): return
    for k,v in json.load(open(p)).items():
        G[k]=[tuple(e) for e in v['eds']]
        if len(v['eds'])>1:
            for i,e in enumerate(v['eds']): G[f'{k}_{i}']=[tuple(e)]
_loo()
# second placeholder copies (+8 B) at other validate sites (same marked construct as the 334/338 placeholders)
_PH2='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)}/*shim: holder_key byte read placeholder*/;'
G['p2_289']=[('if st.holder_reward&&!(hopt==Some(true)){',_PH2+'if st.holder_reward&&!(hopt==Some(true)){')]
G['p2_296']=[('if holder&&!st.holder_reward&&!st.holder_enabled{',_PH2+'if holder&&!st.holder_reward&&!st.holder_enabled{')]
G['p2_314']=[('let cashback=if holder{false}else{st.cashback};',_PH2+'let cashback=if holder{false}else{st.cashback};')]
G['p2_326']=[('match fee{Some(f)=>{if st.quote_locked{','match fee{Some(f)=>{'+_PH2+'if st.quote_locked{')]
G['p2_330']=[('if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}',_PH2+'if cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}')]
G['p2_338']=[('if f==0||f>st.max_fee{',_PH2+'if f==0||f>st.max_fee{')]
G['p2_306']=[('let t=if let Some(t)=new{t}else{',_PH2+'let t=if let Some(t)=new{t}else{')]
G['p2_307']=[('if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)',_PH2+'if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero)')]
G['p2_284']=[('if st.mayhem{return Err(',_PH2+'if st.mayhem{return Err(')]
def _pa(n,what): return f'unsafe{{&*(ptp({n},&**a as *const AdminCto as *const u8) as *const AdminCto)}}/*shim: passthrough on the accounts pointer of {what}*/'
G['ptsh']=[('a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&','a.bonding_curve.creator==sk}&&'+_pa(11,'the shared owner test')+'.sharing_config.owner==&FEES&&')]
G['ptmf']=[('max_fee:a.global.max_configurable_creator_fee_bps,','max_fee:'+_pa(12,'the max_fee load')+'.global.max_configurable_creator_fee_bps,')]
G['ptmy']=[('mayhem:a.bonding_curve.is_mayhem_mode,','mayhem:'+_pa(13,'the mayhem load')+'.bonding_curve.is_mayhem_mode,')]
G['pthr']=[('holder_reward:a.bonding_curve.is_holder_reward,','holder_reward:'+_pa(14,'the holder_reward load')+'.bonding_curve.is_holder_reward,')]
G['ptcb']=[('cashback:a.bonding_curve.is_cashback_coin,','cashback:'+_pa(15,'the cashback load')+'.bonding_curve.is_cashback_coin,')]
G['pthe']=[('holder_enabled:a.global.is_holder_reward_enabled}','holder_enabled:'+_pa(16,'the holder_enabled load')+'.global.is_holder_reward_enabled}')]
G['ptfc']=[('let st=CtoState{fee_configurable:a.global.creator_fee_configurable,','let st=CtoState{fee_configurable:'+_pa(17,'the fee_configurable load')+'.global.creator_fee_configurable,')]
G['ptcr']=[('creator:a.bonding_curve.creator,max_fee','creator:'+_pa(18,'the CtoState creator copy')+'.bonding_curve.creator,max_fee')]
G['pthr']=[('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,','mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:'+_pa(14,'the holder_reward load')+'.bonding_curve.is_holder_reward,')]
# w17a08 fences (ecedd17ac): AMM collect Ok continuation, native sweep result merge
G['fA']=[('_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;}','_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()}))?;core::hint::black_box(())/*shim: compiler memory fence on the AMM collect Ok continuation*/;}')]
G['fN']=[('   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{','   {let r=(if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount);core::hint::black_box(())/*shim: compiler memory fence at the native sweep result merge*/;r}}else{')]
G['ptfc2']=[('let st=CtoState{fee_configurable:a.global.creator_fee_configurable,','let st=CtoState{fee_configurable:'+_pa(31,'the fee_configurable load')+'.global.creator_fee_configurable,')]
G['pthe2']=[('holder_enabled:a.global.is_holder_reward_enabled}','holder_enabled:'+_pa(32,'the holder_enabled load')+'.global.is_holder_reward_enabled}')]
G['ptmy2']=[('mayhem:a.bonding_curve.is_mayhem_mode,','mayhem:'+_pa(33,'the mayhem load')+'.bonding_curve.is_mayhem_mode,')]
G['pthr2']=[('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,','mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:'+_pa(34,'the holder_reward load')+'.bonding_curve.is_holder_reward,')]
