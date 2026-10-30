# w13a42 regrouping / boolean-spelling knobs on main 769f331 (semantics-preserving, newline count kept)
R={}
H='if holder&&!st.holder_reward&&!st.holder_enabled{'
R['r_he_par']=[(H,'if holder&&(!st.holder_reward&&!st.holder_enabled){')]
R['r_he_dm']=[(H,'if holder&&!(st.holder_reward||st.holder_enabled){')]
R['r_he_lpar']=[(H,'if (holder&&!st.holder_reward)&&!st.holder_enabled{')]
R['r_he_band']=[(H,'if holder&!st.holder_reward&!st.holder_enabled{')]
I='if t==*sharing||t==*holder_key{'
R['r_ik_bor']=[(I,'if (t==*sharing)|(t==*holder_key){')]
F='if f==0||f>st.max_fee{'
R['r_f_bor']=[(F,'if (f==0)|(f>st.max_fee){')]
R['r_f_not']=[(F,'if !(f>0&&f<=st.max_fee){')]
R['r_f_wrap']=[(F,'if f.wrapping_sub(1)>=st.max_fee{')]
R['r_f_rev']=[(F,'if f>st.max_fee||f==0{')]
S='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
R['r_sh_lpar']=[(S,'let shared=(a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES)&&!a.sharing_config.data_is_empty();')]
R['r_sh_dm']=[(S,'let shared=a.sharing_config.key()==a.bonding_curve.creator&&!(a.sharing_config.owner!=&FEES||a.sharing_config.data_is_empty());')]
R['r_sh_band3']=[(S,'let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&!a.sharing_config.data_is_empty();')]
C='(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)'
R['r_co_dm']=[(C,'(!(st.holder_reward||st.creator==Pubkey::default()),None,true)')]
R['r_co_band']=[(C,'(!st.holder_reward&(st.creator!=Pubkey::default()),None,true)')]
N='if !collection_native||coin_present{'
R['r_cn_dm']=[(N,'if !(collection_native&&!coin_present){')]
R['r_cn_rev']=[(N,'if coin_present||!collection_native{')]
P='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
R['r_pu_dm']=[(P,'let pool_updated=!(a.pool.data_is_empty() || a.pool.owner!=&AMM);')]
R['r_pu_band']=[(P,'let pool_updated=!a.pool.data_is_empty() & (a.pool.owner==&AMM);')]
R['r_pu_par']=[(P,'let pool_updated=(!a.pool.data_is_empty()) && (a.pool.owner==&AMM);')]
V='if st.holder_reward&&!(hopt==Some(true)){'
R['r_hr_dm']=[(V,'if !(!st.holder_reward||hopt==Some(true)){')]
R['r_hr_band']=[(V,'if st.holder_reward&!(hopt==Some(true)){')]
S0='let shared=a.sharing_config.key()==a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
R['ch_shpar']=[(S0,'let shared=a.sharing_config.key()==a.bonding_curve.creator&&(a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty());')]
R['ch_shkref']=[(S0,'let shared=a.sharing_config.key==&a.bonding_curve.creator&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();')]
C0='(!st.holder_reward&&st.creator!=Pubkey::default(),None,true)'
R['co_if']=[(C0,'(if st.holder_reward{false}else{st.creator!=Pubkey::default()},None,true)')]
R['co_then']=[(C0,'((!st.holder_reward).then(||st.creator!=Pubkey::default()).unwrap_or(false),None,true)')]
R['co_match']=[(C0,'(match st.holder_reward{true=>false,false=>st.creator!=Pubkey::default()},None,true)')]
R['co_ifn']=[(C0,'(if !st.holder_reward{st.creator!=Pubkey::default()}else{false},None,true)')]
R['co_dm2']=[(C0,'(!(st.creator==Pubkey::default()||st.holder_reward),None,true)')]
R['co_ne']=[(C0,'(!st.holder_reward&&st.creator.ne(&Pubkey::default()),None,true)')]
R['co_arr']=[(C0,'(!st.holder_reward&&st.creator.to_bytes()!=[0u8;32],None,true)')]
R['co_dm_par']=[(C0,'(!(st.holder_reward||(st.creator==Pubkey::default())),None,true)')]
Q0='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
NM='anchor_spl::token::spl_token::native_mint::ID'
R['q_nat1']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;q=='+NM+'||q==Pubkey::default()||a.global.whitelisted_quote_mints.contains(&q)};')]
R['q_wl1']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;a.global.whitelisted_quote_mints.contains(&q)||q==Pubkey::default()||q=='+NM+'};')]
R['q_any']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q=='+NM+'||a.global.whitelisted_quote_mints.iter().any(|m|*m==q)};')]
R['q_ref']=[(Q0,'let quote_locked={let q=&a.bonding_curve.quote_mint;*q==Pubkey::default()||*q=='+NM+'||a.global.whitelisted_quote_mints.contains(q)};')]
R['q_inl']=[(Q0,'let quote_locked={a.bonding_curve.quote_mint==Pubkey::default()||a.bonding_curve.quote_mint=='+NM+'||a.global.whitelisted_quote_mints.contains(&a.bonding_curve.quote_mint)};')]
R['q_rpar']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||(q=='+NM+'||a.global.whitelisted_quote_mints.contains(&q))};')]
R['q_g']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;let g=&a.global;q==Pubkey::default()||q=='+NM+'||g.whitelisted_quote_mints.contains(&q)};')]
R['q_ifs']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;if q==Pubkey::default()||q=='+NM+'{true}else{a.global.whitelisted_quote_mints.contains(&q)}};')]
R['q_bor']=[(Q0,'let quote_locked={let q=a.bonding_curve.quote_mint;(q==Pubkey::default())|(q=='+NM+')||a.global.whitelisted_quote_mints.contains(&q)};')]
PU1='let pool_updated=!a.pool.data_is_empty() && a.pool.owner==&AMM;'
R['f_hr']=[('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,holder,fee);')]
R['f_keyfn']=[(PU1,'let pool_updated=!a.pool.data_is_empty() && *a.pool.owner==a.pump_amm.key();')]
R['f_keyref']=[(PU1,'let pool_updated=!a.pool.data_is_empty() && a.pool.owner==a.pump_amm.key;')]
R['f_cbc']=[(PU1,'let cbc=a.bonding_curve.is_cashback_coin;'+PU1),('is_cashback_coin:a.bonding_curve.is_cashback_coin,','is_cashback_coin:cbc,')]
