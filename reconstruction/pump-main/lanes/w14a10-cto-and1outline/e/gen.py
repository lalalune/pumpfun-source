# gene library: each gene is a list of (old,new) applied in sequence on admin_cto.rs (composable in listed order)
G={}
G['v2']=[(' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}',
          ' if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}')]
G['ov']=[('holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{','holder_key:&Pubkey,sharing:&Pubkey,shared:bool)->Result<Pubkey>{'),
         ('{return Err(error!(PumpError::InvalidCreator));}t};','{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};'),
         ('validate(&st,hopt,fee,new,&holder_key,&sk)?;','validate(&st,hopt,fee,new,&holder_key,&sk,shared)?;'),
         ('else{target=st.creator;(false,Some(args.0),true)}','else{(false,Some(args.0),true)}')]
G['h2']=[('sharing:&Pubkey','sharing:&Pubkey,ho:&mut bool'),
         ('{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{','{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*ho=true;*holder_key}else{'),
         ('let holder=hopt==Some(true);let cashback=!holder&&st.cashback;','let holder0=hopt==Some(true);let cashback=!holder0&&st.cashback;let mut holder=false;'),
         ('&holder_key,&sk','&holder_key,&sk,&mut holder'),
         ('  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n','  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n'),
         ('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,holder,fee);')]
def mk(*names):
    E=[]
    for n in names: E+=G[n]
    return E
G['anew']=[('Some(args.0)','Some(new)'),('let args=&(new,);','')]
G['t296']=[('if holder&&!st.holder_reward&&!st.holder_enabled{','if holder&&!(st.holder_reward||st.holder_enabled){')]
G['hm']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=matches!(hopt,Some(true));')]
G['smap']=[('if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{', 'if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{'), ('crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner)?;}\n   Ok(amount)}', 'crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner).map(|()|amount)}else{Ok(amount)}\n   }')]
_l=[]
exec(open(__file__.replace('gen.py','lv3n.py')).read(),{'__builtins__':__builtins__},_d:={})
G['lv3n']=_d['EDITS']
def mkf(name):
    return mk(*name.split('_'))
_S='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
_H='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
G['pda']=[(_S+_H,_H+_S)]
_L289=' if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
G['d289']=[(_L289,' if st.holder_reward{if holder{}else{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}')]
G['g289']=[(_L289,' if st.holder_reward{if !(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}}')]
G['hu']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let holder=hopt.unwrap_or(false);')]
G['kv']=[('holder_key:&Pubkey,sharing:&Pubkey','holder_key:Pubkey,sharing:Pubkey'),('*holder_key}else{','holder_key}else{'),('t==*sharing||t==*holder_key','t==sharing||t==holder_key'),('&holder_key,&sk','holder_key,sk')]
ORDER=['main0','v2','d289','g289','hm','hu','t296','ov','lv3n','h2','kv','anew','smap','pda']
def mkf(name):
    gs=sorted(name.split('_'),key=ORDER.index)
    return mk(*gs)
G['main0']=[]
G['take']=[('fee:Option<u64>,new:Option<Pubkey>,holder_key','fee:Option<u64>,mut new:Option<Pubkey>,holder_key'),('let t=if let Some(t)=new{t}else{','let t=if let Some(t)=new.take(){t}else{')]
ORDER=['main0','v2','d289','g289','hm','hu','t296','take','ov','lv3n','h2','kv','anew','smap','pda']
_VH='->Result<Pubkey>{let holder=hopt==Some(true);'
_EH='let hopt=holder;let holder=hopt==Some(true);'
_289='&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
# all holder tests in matches! form (and-1 candidates)
G['hx']=[(_VH,'->Result<Pubkey>{let holder=matches!(hopt,Some(true));'),(_EH,'let hopt=holder;let holder=matches!(hopt,Some(true));'),(_289,'&&!matches!(hopt,Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
G['ux']=[(_VH,'->Result<Pubkey>{let holder=hopt.unwrap_or(false);'),(_EH,'let hopt=holder;let holder=hopt.unwrap_or(false);'),(_289,'&&!hopt.unwrap_or(false){return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
# execute-only
G['hxe']=[(_EH,'let hopt=holder;let holder=matches!(hopt,Some(true));')]
G['uxe']=[(_EH,'let hopt=holder;let holder=hopt.unwrap_or(false);')]
# 289 uses the shared bool
G['h289']=[(_289,'&&!holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
ORDER=['main0','v2','d289','g289','hm','hu','hx','ux','hxe','uxe','h289','t296','take','ov','lv3n','h2','kv','anew','smap','pda']
_EX='->Result<()>{ let a=&ctx.accounts;'
G['e1']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=holder;let holder=hb;'),(_VH,'->Result<Pubkey>{let holder=hopt.unwrap_or(false);'),(_289,'&&!hopt.unwrap_or(false){return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
G['e2']=[(_EX,'->Result<()>{ let hb=matches!(holder,Some(true));let a=&ctx.accounts;'),(_EH,'let hopt=holder;let holder=hb;'),(_VH,'->Result<Pubkey>{let holder=matches!(hopt,Some(true));'),(_289,'&&!matches!(hopt,Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
# validate takes the bool
G['e3']=[(_EX,'->Result<()>{ let hb=holder.unwrap_or(false);let a=&ctx.accounts;'),(_EH,'let hopt=hb;let holder=hb;'),('fn validate(st:&CtoState,hopt:Option<bool>,','fn validate(st:&CtoState,hopt:bool,'),(_VH,'->Result<Pubkey>{let holder=hopt;'),(_289,'&&!hopt{return Err(error!(PumpError::HolderRewardCreatorImmutable));}')]
# u8 view of the Option<bool> (bit 0 = Some(true))
G['e4']=[(_EX,'->Result<()>{ let hb=(holder==Some(true)) as u8&1!=0;let a=&ctx.accounts;'),(_EH,'let hopt=holder;let holder=hb;')]
G['e5']=[(_EH,'let hopt=holder;let holder=hopt.unwrap_or(false);let holder=std::hint::black_box(holder);')]
ORDER=['main0','v2','d289','g289','hm','hu','hx','ux','hxe','uxe','h289','e1','e2','e3','e4','t296','take','ov','lv3n','h2','kv','anew','smap','pda']
_T306='let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
_VS='new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
_VC='validate(&st,hopt,fee,new,'
G['thb']=[(_VS,'new:Option<Pubkey>,has:bool,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'),(_T306,'let t=if has{new.unwrap_or_default()}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'),(_VC,'validate(&st,hopt,fee,new,args.0.is_some(),')]
G['tu8']=[(_T306,'let t=if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
G['tu8d']=[(_T306,'let t=if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{new.unwrap_or_default()}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
G['tun']=[(_T306,'let t=if new.is_some(){unsafe{new.unwrap_unchecked()}}else{return Err(error!(PumpError::CtoNewCreatorRequired));};')]
ORDER=['main0','v2','d289','g289','hm','hu','hx','ux','hxe','uxe','h289','e1','e2','e3','e4','t296','take','thb','tu8','tu8d','tun','ov','lv3n','h2','kv','anew','smap','pda']
import json as _j
_K=_j.load(open('/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/w11/sizeknobs-cto.json'))['knobs']
for _k in _K:
    if _k.get('edit'): G['K'+_k['name'].replace('_','')]=[(e['old'],e['new']) for e in _k['edit']]
ORDER=ORDER+[k for k in G if k.startswith('K')]
