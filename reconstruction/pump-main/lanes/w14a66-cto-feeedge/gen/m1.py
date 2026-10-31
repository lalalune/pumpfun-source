EDITS=[["let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;", "let mut target=match validate(&st,hopt,fee,new,&holder_key,&sk){Ok(t)=>t,Err(e)=>return Err(e)};"]]
