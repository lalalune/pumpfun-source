EDITS=[("let sk=a.sharing_config.key();",""),("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,a.sharing_config.key)?;"),
("  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};","  let sk=*sharing;if t==*holder_key||t==sk{return Err(error!(PumpError::InvalidCreator));}t};")]
