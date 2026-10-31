# validate returns (target, holder flag) per arm; curve store from that flag (the #2766 tuple mechanism)
EDITS=[
("->Result<Pubkey>{let holder=hopt==Some(true);","->Result<(Pubkey,bool)>{let holder=hopt==Some(true);"),
(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," let (target,hf)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,true)}else{"),
("if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};","if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}(t,false)};"),
(" Ok(target)}pub fn execute"," Ok((target,hf))}pub fn execute"),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let (mut target,_hf)=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
]
