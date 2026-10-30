EDITS=[("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,tb:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);",
"fn precheck(st:&CtoState,hopt:Option<bool>)->Result<()>{let holder=hopt==Some(true);"),
(" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}\n",
" if holder&&!st.holder_reward&&!st.holder_enabled{return Err(error!(PumpError::HolderRewardDisabled));}Ok(())}fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,tb:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);\n"),
("{ let hopt=holder;","{ let hopt=holder;precheck(&st,hopt)?;")]
