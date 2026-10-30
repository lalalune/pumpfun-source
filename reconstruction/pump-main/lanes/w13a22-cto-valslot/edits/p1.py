EDITS=[("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,tb:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);",
"fn precheck(st:&CtoState,hopt:Option<bool>)->Result<()>{let holder=hopt==Some(true);"),
(" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n",
" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}Ok(())}fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,tb:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);\n"),
("let cashback=st.cashback&&!holder;let mut tb=Pubkey::default();let sk","let cashback=st.cashback&&!holder;precheck(&st,hopt)?;let mut tb=Pubkey::default();let sk")]
