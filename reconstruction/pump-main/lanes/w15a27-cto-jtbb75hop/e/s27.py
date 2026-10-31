EDITS=[("fn validate(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{",
        "fn validate<'a>(st:&CtoState,hopt:Option<bool>,fee:Option<u64>,new:&'a Option<Pubkey>,holder_key:&'a Pubkey,sharing:&Pubkey)->Result<&'a Pubkey>{"),
 ("CtoNewCreatorNotAllowed));}*holder_key}else{","CtoNewCreatorNotAllowed));}holder_key}else{"),
 ("  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}",
  "  if *t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((*t,Pubkey::default())));}"),
 ("  if t==*sharing||t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};","  if *t==*sharing||*t==*holder_key{return Err(error!(PumpError::InvalidCreator));}t};"),
 ("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=*validate(&st,hopt,fee,&new,&holder_key,&sk)?;")]
