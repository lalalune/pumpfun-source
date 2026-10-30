L298=' let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{'
L312='  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};'
L312_OK='  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}Ok(t)}'
HOLD='fn hold(new:Option<Pubkey>,holder_key:&Pubkey)->Result<Pubkey>{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}Ok(*holder_key)}'
OTHER='fn other(new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{'
L314=' let cashback=if holder{false}else{st.cashback};'
SIG=('holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);', 'holder_key:&Pubkey,sharing:&Pubkey,ho:&mut bool)->Result<Pubkey>{let holder=hopt==Some(true);')
EXH2=('let hopt=holder;let holder=hopt==Some(true);let cashback=st.cashback&&!holder;let args=&(new,);let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;', 'let hopt=holder;let holder0=hopt==Some(true);let cashback=st.cashback&&!holder0;let args=&(new,);let mut holder=false;let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut holder)?;')
STORES=('  curve.is_cashback_coin=cashback;\n  curve.is_holder_reward=holder;\n', '  curve.is_holder_reward=holder;\n  curve.is_cashback_coin=cashback;\n')
POOL=('},signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;', '},signer_seeds),target,holder,fee)?;')
H2=[SIG,(L298,L298.replace('}*holder_key}else{','}*ho=true;*holder_key}else{')),EXH2,STORES,POOL]
POOL2=('let pargs=(target,a.bonding_curve.is_holder_reward,fee);','let pargs=(target,holder,fee);')
H2b=[SIG,(L298,L298.replace('}*holder_key}else{','}*ho=true;*holder_key}else{')),EXH2,STORES,POOL2]
ERR298='return Err(error!(PumpError::CtoNewCreatorNotAllowed));}'
END=('}None=>{}}\n Ok(target)}pub fn execute','}None=>{}}\n Ok(())} Ok(target)}pub fn execute')
FEEFN=' fn fee_ok(st:&CtoState,fee:Option<u64>,cashback:bool)->Result<()>{'
F1=[(L298,L298.replace(ERR298+'*holder_key',ERR298+'fee_ok(st,fee,false)?;*holder_key')),(L312,L312.replace('}t};','}fee_ok(st,fee,st.cashback)?;t};')),(L314,FEEFN),END]
L289='if st.holder_reward&&!(hopt==Some(true)){return Err(error!(PumpError::HolderRewardCreatorImmutable));}'
V2=(L289,'if st.holder_reward{if !holder{return Err(error!(PumpError::HolderRewardCreatorImmutable));}}')
P1E=[(L298,' let target=if holder{hold(new,holder_key)?}else{other(new,holder_key,sharing)?};'+HOLD+OTHER),(L312,L312_OK)]
