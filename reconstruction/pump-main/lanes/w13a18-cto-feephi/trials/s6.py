EDITS=[("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;","let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key()).map_err(|e|e)?;")]
