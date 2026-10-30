EDITS=[
("fn validate(st:&CtoState,hopt:Option<bool>,fee:","fn validate(st:&CtoState,hopt:Option<bool>,hb:bool,shared:bool,fee:"),
("sharing:&Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);","sharing:&Pubkey,out:&mut Pubkey)->Result<Pubkey>{let holder=hopt==Some(true);"),
(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," *out=if hb{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"),
("{return Err(error!(PumpError::InvalidCreator));}t};","{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
(" Ok(target)}pub fn execute("," Ok(*holder_key)}pub fn execute("),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk.0)?;","let mut target=holder_key;validate(&st,hopt,holder,shared,fee,new,&holder_key,&sk.0,&mut target)?;"),
("else{target=st.creator;(Some(args.0),false,true)}","else{(Some(args.0),false,true)}"),
]
