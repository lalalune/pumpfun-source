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
_S='let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
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
