# w16a14 vcretune genes: w16a05 genes_w16 (w15a16 genes_mp + stitch libraries) + VC base aliases + back-half compensator reverts
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import genes_w16 as _S
G=_S.G
def apply(s,names):
    out=[]
    for n in names:
        if n in ALIAS: out+=ALIAS[n]
        else: out.append(n)
    return _S.apply(s,out)
ALIAS={'VC':['v7c','lv_ny','lv_le','lv_cf_skc','lv_h289'],
       'VCsh':['v7c','lv_ny','lv_le','lv_cf_skc','lv_h289','lv_sh_ifelse']}
# ---- reverts of the back-half compensators landed since #3409 (pre-PR spellings, on the current source) ----
# #3430: wallet `!is_writable` -> `is_writable==false`; validate 334 read_volatile placeholder dropped (the 338 one stays)
G['r30w']=[('if !a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}','if a.current_creator.is_writable==false{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}')]
_V='unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};'
G['r30v']=[(_V+'if !st.fee_configurable{','if !st.fee_configurable{')]
# #3437: pool_authority rent_epoch via x -> a.pool_authority.rent_epoch; event new fee via nf local -> curve re-read
G['r37p']=[('AccountInfo{owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:x.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}},authority:','AccountInfo{owner:x.owner,lamports:x.lamports.clone(),data:x.data.clone(),rent_epoch:a.pool_authority.rent_epoch,is_signer:x.is_signer,is_writable:x.is_writable,key:x.key,executable:x.executable}},authority:')]
G['r37n']=[('let nf=a.bonding_curve.creator_fee_bps;let pool_updated','let pool_updated'),('new_creator_fee_bps:nf,','new_creator_fee_bps:a.bonding_curve.creator_fee_bps,')]
# #3480: event holder from the arg (pre-PR), curve store cashback first (pre-PR order)
G['r80e']=[('let e=AdminCtoEvent{is_holder_reward:a.bonding_curve.is_holder_reward,','let e=AdminCtoEvent{is_holder_reward:holder.unwrap_or(false),')]
G['r80o']=[('  curve.is_holder_reward=holder.unwrap_or(false);\n  curve.is_cashback_coin=cashback;\n','  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder.unwrap_or(false);\n')]
# #3495: shared test as key()==creator (pre-PR)
G['r95']=[('let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&','let shared=a.sharing_config.key()==a.bonding_curve.creator&&')]
# #3621: tuple-form sharing_update (pre-PR)
G['r21']=[('let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if holder{sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};',
           'let (collect_old,sharing_update,skip)=if shared{if holder{(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};')]
# #3666: CtoState fee_configurable last (pre-PR)
G['r66']=[('CtoState{fee_configurable:a.global.creator_fee_configurable,creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled}',
           'CtoState{creator:a.bonding_curve.creator,max_fee:a.global.max_configurable_creator_fee_bps,mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,quote_locked,holder_enabled:a.global.is_holder_reward_enabled,fee_configurable:a.global.creator_fee_configurable}')]
# #3859: (a) sweep guard if/else-if (pre-PR), (b) event is_holder_reward after new_creator (pre-PR)
def _r59s(s):
    a='  match (amm_present,amm_frozen){(_,false)=>if !a.coin_creator_vault_ata.data_is_empty(){'
    i=s.index(a); j=s.index('\n',i); tcf=s[i+len(a):j]
    k=s.index('\n',j+1); l2=s[j+1:k]
    assert l2=='  (true,true)=>{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}(false,true)=>{}}',l2
    m=s.index('\n',k+1); l3=s[k+1:m]
    assert l3.strip()=='',l3
    return s[:i]+'\n'+'  if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}'+'\n'+'  else if !a.coin_creator_vault_ata.data_is_empty(){'+tcf+s[m:]
G['r59s']=[_r59s]
G['r59e']=[('let e=AdminCtoEvent{is_holder_reward:a.bonding_curve.is_holder_reward,timestamp:','let e=AdminCtoEvent{timestamp:'),
           ('new_creator:a.bonding_curve.creator,is_cashback_coin:','new_creator:a.bonding_curve.creator,is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:')]
# ---- w16a04 genes_lac additions (c2, s1, tf_g1a, g0, po) ----
import runpy as _rp
G['c2']=[("pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),",
          "pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:x.data.clone(),owner:x.owner,")]
G['s1']=list(_rp.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'e_s1.py'))['EDITS'])
_NA="else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}"
G['tf_g1a']=[("let args=&(new,);","let creator=st.creator;let args=&(new,);"),(_NA,"else{target=creator;sharing_update=Some(args.0);(false,true)}}")]
G['g0']=[(_NA,"else{sharing_update=Some(args.0);target=st.creator;(false,true)}}")]
G['po']=[("let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;","let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();")]
# r21 on the t1n base (shared-arm test `new.is_none()`)
G['r21n']=[('let mut sharing_update:Option<Option<Pubkey>>=None;let (collect_old,skip)=if shared{if new.is_none(){sharing_update=Some(None);(false,false)}else{sharing_update=Some(args.0);target=a.bonding_curve.creator;(false,true)}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),true)};',
           'let (collect_old,sharing_update,skip)=if shared{if new.is_none(){(false,Some(None),false)}else{let r=(false,Some(args.0),true);target=a.bonding_curve.creator;r}}else{(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)};')]
# ---- conditional-update idioms at the curve store (semantically equal: 289 forces is_holder_reward==false when holder!=Some(true);
#      cashback=!holder&&st.cashback equals the current flag unless holder) ----
_CS='curve.is_holder_reward=holder.unwrap_or(false);'
G['c0cs']=[(_CS,'if let Some(h)=holder{curve.is_holder_reward=h;}')]
G['c0cm']=[(_CS,'match holder{Some(h)=>curve.is_holder_reward=h,None=>{}}')]
G['c0uc']=[(_CS,'curve.is_holder_reward=holder.unwrap_or(curve.is_holder_reward);')]
_CB='curve.is_cashback_coin=cashback;'
G['cbcs']=[(_CB,'if _holder{curve.is_cashback_coin=false;}')]
G['cbcs2']=[(_CB,'if cashback!=curve.is_cashback_coin{curve.is_cashback_coin=cashback;}')]
# ---- outer cashback in the closure's and-1 form (so the outer `and -3` holder disappears on the t1n base) ----
_CBO='let cashback=!holder&&st.cashback;'
G['cbu']=[(_CBO,'let cashback=!hopt.unwrap_or(false)&&st.cashback;')]
G['cbi']=[(_CBO,'let cashback=if hopt.unwrap_or(false){false}else{st.cashback};')]
# ---- per-arm holder flag out of the VC closure (the original's 0x950 phi-of-constants at the curve store) ----
_VH='let mut target=(||->Result<Pubkey>{let st=&st;let holder_key=&holder_key;let sharing=&{sk};let holder=hopt==Some(true);'
_T298='let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{let new=new;'
_T312='if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
_TUP='(holder,cashback,target,sharing_update,collect_old,skip)'
_CSH='curve.is_holder_reward=holder.unwrap_or(false);'
G['vflag']=[(_VH,'let (mut target,hflag)=(||->Result<(Pubkey,bool)>{let st=&st;let holder_key=&holder_key;let sharing=&{sk};let holder=hopt==Some(true);'),
            (_T298,'let (target,hflag)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,true)}else{let new=new;'),
            (_T312,'if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}(t,false)};'),
            ('Ok(target)})()?;','Ok((target,hflag))})()?;'),(_TUP,'(hflag,cashback,target,sharing_update,collect_old,skip)'),(_CSH,'curve.is_holder_reward=_holder;')]
G['vflag2']=[(_VH,'let mut hflag=false;'+_VH.replace('let mut target=','let mut target=')),
            (_T298,'let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}hflag=true;*holder_key}else{let new=new;'),
            (_TUP,'(hflag,cashback,target,sharing_update,collect_old,skip)'),(_CSH,'curve.is_holder_reward=_holder;')]
# ---- per-arm cashback out of the VC closure (the original's 0x958 phi at the curve store); outer cashback removed ----
G['vcb2']=[('let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;','let hopt=holder;let holder=hopt==Some(true);let mut cbf=false;'),
           ('\n let cashback=if holder{false}else{st.cashback};\n','\n let cashback=if holder{false}else{st.cashback};cbf=cashback;\n'),
           (_TUP,'(holder,cbf,target,sharing_update,collect_old,skip)')]
_TUPF='(hflag,cashback,target,sharing_update,collect_old,skip)'
G['vboth']=G['vflag2'][:3]+[(_TUP,'(hflag,cbf,target,sharing_update,collect_old,skip)'),(_CSH,'curve.is_holder_reward=_holder;'),
           ('let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;','let hopt=holder;let holder=hopt==Some(true);let mut cbf=false;'),
           ('\n let cashback=if holder{false}else{st.cashback};\n','\n let cashback=if holder{false}else{st.cashback};cbf=cashback;\n')]
G['vboth']=[e for e in G['vboth'] if not (isinstance(e,tuple) and e[0]==_TUP and e[1]==_TUPF)]
# ---- sweep-head live ranges: native flag computed after the dest check, or inline at its use ----
_NAT='let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;\n'
_DST='return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}\n'
G['natl']=[(_NAT,'let a=&ctx.accounts;\n'),(_DST,_DST[:-1]+'let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;\n')]
G['nati']=[(_NAT,'let a=&ctx.accounts;\n'),('  if native{let min=','  if a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID{let min=')]
G['natf']=[(_NAT,'let native=ctx.accounts.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;let a=&ctx.accounts;\n')]
# ---- outer cashback from new's tag (after validate, holder <=> new.is_none()), so hopt is reloaded once (the closure's and-1) ----
G['cbn']=[(_CBO,'let cashback=new.is_some()&&st.cashback;')]
G['cbn2']=[(_CBO,'let cashback=st.cashback&&new.is_some();')]
G['cbn3']=[(_CBO,'let cashback=args.0.is_some()&&st.cashback;')]
# ---- TCF token_program / system_program as explicit AccountInfo clones (field orders), for B's TCF clone-temp rotation ----
_TPS='token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),coin_creator'
_FD={'k':'key:x.key','l':'lamports:x.lamports.clone()','d':'data:x.data.clone()','o':'owner:x.owner','r':'rent_epoch:x.rent_epoch','s':'is_signer:x.is_signer','w':'is_writable:x.is_writable','e':'executable:x.executable'}
def _lit(acc,order): return '{let x:&AccountInfo='+acc+'.as_ref();AccountInfo{'+','.join(_FD[c] for c in order)+'}}'
for _o in ['kldorswe','okldrswe','klodrewsx'[:8],'ldkorswe','kldoresw','kldorews','rkldoswe','ekldorsw']:
    if sorted(_o)!=sorted('kldorswe'): continue
    G['tp_'+_o]=[(_TPS,_TPS.replace('token_program:a.quote_token_program.to_account_info()','token_program:'+_lit('a.quote_token_program',_o)))]
    G['sp_'+_o]=[(_TPS,_TPS.replace('system_program:a.system_program.to_account_info()','system_program:'+_lit('a.system_program',_o)))]
