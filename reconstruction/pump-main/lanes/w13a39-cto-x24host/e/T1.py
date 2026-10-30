EDITS=[("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","holder_key:&Pubkey,sharing:&Pubkey)->Result<(Option<u64>,Pubkey)>{"),
("Ok(target)}pub fn execute","Ok((fee,target))}pub fn execute"),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?.1;")]
