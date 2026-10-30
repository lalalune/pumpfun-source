EDITS=[("fn validate(st:&CtoState,holder:bool,fee:","fn validate(st:&CtoState,holder:bool,shared:bool,fee:"),
("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","holder_key:&Pubkey,sharing:&Pubkey)->Result<(u64,Pubkey)>{"),
("{return Err(error!(PumpError::InvalidCreator));}t};","{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
(" Ok(target)}pub fn execute("," Ok((0,target))}pub fn execute("),
("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;","let (_,mut target)=validate(&st,holder,shared,fee,new,&holder_key,&a.sharing_config.key())?;"),
("else{target=st.creator;(Some(args.0),false,true)}","else{(Some(args.0),false,true)}")]
