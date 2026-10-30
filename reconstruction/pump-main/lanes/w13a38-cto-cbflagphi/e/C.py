SIG_OLD="holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"
A298=" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"
A312="  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"
CB314=" let cashback=if holder{false}else{st.cashback};"
RET=" Ok(target)}pub fn execute("
EX="let hopt=holder;let holder=hopt==Some(true);let cashback=st.cashback&&!holder;let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;"
EDITS=[(SIG_OLD,"holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,bool)>{let holder=hopt==Some(true);"),
(A298," let (target,cashback)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,false)}else{"),
(A312,"  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}(t,st.cashback)};"),
(CB314," "),
(RET," Ok((target,cashback))}pub fn execute("),
(EX,"let hopt=holder;let holder=hopt==Some(true);let sk=a.sharing_config.key();let (mut target,cashback)=validate(&st,hopt,fee,new,&holder_key,&sk)?;")]
