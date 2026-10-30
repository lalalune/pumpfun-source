SH='let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
HK1=[(SH+HK, HK+SH)]
BA=[('let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;','let a=&ctx.accounts;let bumpa=[ctx.bumps.creator_vault];let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'),
 ('let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&[bump]];','let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bumpa];')]
QL='let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);'
STF='mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin,'
STF2='mayhem:bc_m,holder_reward:bc_h,cashback:bc_c,'
def FL(order):
    names={'m':'bc_m','h':'bc_h','c':'bc_c'}; src={'m':'a.bonding_curve.is_mayhem_mode','h':'a.bonding_curve.is_holder_reward','c':'a.bonding_curve.is_cashback_coin'}
    lhs='('+','.join(names[x] for x in order)+')'; rhs='('+','.join(src[x] for x in order)+')'
    return [(QL,'let '+lhs+'='+rhs+';'+QL),(STF,STF2)]
def FLsep(order):
    names={'m':'bc_m','h':'bc_h','c':'bc_c'}; src={'m':'a.bonding_curve.is_mayhem_mode','h':'a.bonding_curve.is_holder_reward','c':'a.bonding_curve.is_cashback_coin'}
    return [(QL,''.join('let %s=%s;'%(names[x],src[x]) for x in order)+QL),(STF,STF2)]
FPA='let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);'
HK6=[(SH+HK, FPA+SH+'let holder_key;holder_key=hk.0;')]
HK7=[(SH+HK, 'let holder_key;'+FPA+SH+'holder_key=hk.0;')]
SK='let sk=a.sharing_config.key();'
SH9='let sk=a.sharing_config.key();let shared=a.bonding_curve.creator==sk&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
HK9=[(SH+HK, HK+SH9),('let args=&(new,);let sk=a.sharing_config.key();','let args=&(new,);')]
HK10=[(SH+HK, HK+SH9.replace('==sk&&','==sk.clone()&&')),('let args=&(new,);let sk=a.sharing_config.key();','let args=&(new,);')]
L298=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
SIG=('holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);', 'holder_key:&Pubkey,sharing:&Pubkey,ho:&mut bool)->Result<Pubkey>{let holder=hopt==Some(true);')
EXH2=('let hopt=holder;let holder=hopt==Some(true);let cashback=!holder&&st.cashback;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;', 'let hopt=holder;let holder0=hopt==Some(true);let cashback=!holder0&&st.cashback;let args=&(new,);let mut holder=false;let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut holder)?;')
STORES=('  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n', '  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n')
POOL2=('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,holder,fee);')
H2b=[SIG,(L298,L298.replace('}*holder_key}else{','}*ho=true;*holder_key}else{')),EXH2,STORES,POOL2]
H2n=[SIG,(L298,L298.replace('}*holder_key}else{','}*ho=true;*holder_key}else{')),EXH2]
