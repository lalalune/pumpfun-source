# validate returns (target, holder flag) per arm; curve store from that flag (the #2766 tuple mechanism)
EDITS=[
("->Result<Pubkey>{let holder=hopt==Some(true);","->Result<(Pubkey,u8)>{let holder=hopt==Some(true);"),
(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," let (target,hf)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,1)}else{"),
("if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};","if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}(t,0)};"),
(" Ok(target)}pub fn execute"," Ok((target,hf))}pub fn execute"),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let (mut target,hf)=validate(&st,hopt,fee,new,&holder_key,&sk)?;"),
("(holder,cashback,target,sharing_update,collect_old,skip)}","(hf!=0,cashback,target,sharing_update,collect_old,skip)}"),
("curve.is_holder_reward=holder.unwrap_or(false);","curve.is_holder_reward=_holder;"),
]
