EDITS=[("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let r=validate(&st,hopt,fee,new,&holder_key,&sk);let mut target=match r{Ok(t)=>t,Err(e)=>return Err(e)};")]
