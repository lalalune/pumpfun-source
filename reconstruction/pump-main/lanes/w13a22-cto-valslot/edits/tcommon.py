V=[("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);","holder_key:&Pubkey,sharing:&Pubkey,tb:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"),
("  let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","  *tb=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};let t=&*tb;"),
("  if t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((t,Pubkey::default())));}","  if *t==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((*t,Pubkey::default())));}"),
("  if t==*holder_key||t==*sharing{return Err(error!(PumpError::InvalidCreator));}t};","  if *t==*holder_key||*t==*sharing{return Err(error!(PumpError::InvalidCreator));}*t};"),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut tb)?;")]
