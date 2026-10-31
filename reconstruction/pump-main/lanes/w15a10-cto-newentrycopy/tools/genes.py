G={}
G['nop']=[]
SH='let shared={let sk=a.sharing_config.key();a.bonding_curve.creator==sk}&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();'
PDA='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
QL='let quote_locked={let q=a.bonding_curve.quote_mint;'
ST='let st=CtoState{'
ARGS='let args=&(new,);'
VC='validate(&st,hopt,fee,new,&holder_key,&sk)?'
SA='sharing_update=Some(args.0);'
VSIG='fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
VT='  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'
VH='if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}'
# --- joint dims (current-main spellings of the w14a93 genes)
G['pda']=[(SH+PDA, PDA+SH)]
G['fl']=[(QL,'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);'+QL),
      ('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0')]
G['hkc']=[('&holder_key,&sk)?','&{holder_key},&sk)?')]
# --- entry-copy forms of new
# Fa: validate reads the (new,) tuple copy
G['Fa']=[('fee,new,&holder_key','fee,args.0,&holder_key')]
# Fb: named by-value local bound before CtoState, used by validate and the sharing arm
G['Fb']=[(ST,'let nc=new;'+ST,),(ARGS,''),('fee,new,&holder_key','fee,nc,&holder_key'),(SA,'sharing_update=Some(nc);')]
# Fb0: named local before CtoState, validate reads new, sharing arm reads the local
G['Fb0']=[(ST,'let nc=new;'+ST,),(ARGS,''),(SA,'sharing_update=Some(nc);')]
# Fc: args by value
G['Fc']=[(ARGS,'let args=(new,);'),('fee,new,&holder_key','fee,args.0,&holder_key')]
G['Fc0']=[(ARGS,'let args=(new,);')]
# Ft: new bound at the very top of execute (before the shared chain / PDA)
G['Ft']=[('{ let a=&ctx.accounts;let mint=a.mint.key();','{ let new_c=new;let a=&ctx.accounts;let mint=a.mint.key();'),(ARGS,''),('fee,new,&holder_key','fee,new_c,&holder_key'),(SA,'sharing_update=Some(new_c);')]
# Fr: validate holds new by reference
G['Fr']=[(VSIG,VSIG.replace('new:Option<Pubkey>','new:&Option<Pubkey>')),(VT,'  let t=if let Some(t)=*new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'),('fee,new,&holder_key','fee,&args.0,&holder_key')]
G['Frn']=[(VSIG,VSIG.replace('new:Option<Pubkey>','new:&Option<Pubkey>')),(VT,'  let t=if let Some(t)=*new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};'),('fee,new,&holder_key','fee,&new,&holder_key')]
# Fs: struct of new before CtoState
G['Fs']=[(ST,'let na=NewArg{new};'+ST),(ARGS,''),('fee,new,&holder_key','fee,na.new,&holder_key'),(SA,'sharing_update=Some(na.new);'),
         ('struct CtoState{','struct NewArg{new:Option<Pubkey>}struct CtoState{')]
# Fv: entry copy inside validate (first statement)
G['Fv']=[('->Result<Pubkey>{let holder=hopt==Some(true);','->Result<Pubkey>{let new=new;let holder=hopt==Some(true);')]
# V1/V2 by-value keys (orig copy order new, sk, hk)
G['V1']=[('holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>','holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>'),(',&holder_key,&sk)?',',holder_key,&sk)?'),
         ('t==*sharing||t==*holder_key','t==*sharing||t==holder_key'),('}*holder_key}else{','}holder_key}else{'),
         ('read_volatile(holder_key as *const Pubkey as *const u8)};if','read_volatile(&holder_key as *const Pubkey as *const u8)};if'),
         ('read_volatile(holder_key as *const Pubkey as *const u8)};}None','read_volatile(&holder_key as *const Pubkey as *const u8)};}None')]
G['V2']=G['V1']+[('holder_key:Pubkey,sharing:&Pubkey)->Result<Pubkey>','holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>'),
   (',holder_key,&sk)?',',holder_key,sk)?'),('t==*sharing||','t==sharing||')]
G['sn']=[(SA,'sharing_update=Some(new);')]
G['rar']=[(ARGS,''),(ST,ARGS+ST)]
G['hkt']=[(PDA,'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')]
G['flb']=[('mayhem:a.bonding_curve.is_mayhem_mode,holder_reward:a.bonding_curve.is_holder_reward,cashback:a.bonding_curve.is_cashback_coin','mayhem:my0,holder_reward:hr0,cashback:cb0'),
      (SH,SH+'let (cb0,hr0,my0)=(a.bonding_curve.is_cashback_coin,a.bonding_curve.is_holder_reward,a.bonding_curve.is_mayhem_mode);')]
G['sut']=[(SA,'sharing_update=Some(Some(target));')]
QLF='let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};'
G['qli']=[(QLF,''),('cashback:a.bonding_curve.is_cashback_coin,quote_locked,','cashback:a.bonding_curve.is_cashback_coin,quote_locked:{let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)},')]
