EDITS=[
("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);","holder_key:&Pubkey,sharing:&Pubkey)->Result<()>{let holder=hopt==Some(true);"),
("let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{","if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}}else{"),
("if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};","if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}}"),
("return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}unsafe{core::ptr::read_volatile(holder_key as *const Pubkey as *const u8)};}None=>{}}\n Ok(target)}","return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}None=>{}}\n Ok(())}"),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","validate(&st,hopt,fee,new,&holder_key,&sk)?;let mut target=if holder{holder_key}else{match new{Some(t)=>t,None=>Pubkey::default()}};"),
]