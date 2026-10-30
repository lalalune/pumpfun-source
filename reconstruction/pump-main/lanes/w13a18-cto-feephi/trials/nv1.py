EDITS=[
("fn validate(st:&CtoState,hopt:Option<bool>,fee:","fn validate(st:&CtoState,hopt:Option<bool>,shared:bool,fee:"),
(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*tb=*holder_key}else{"),
("if *t==*holder_key||*t==*sharing{return Err(error!(PumpError::InvalidCreator));}*t};","if *t==*holder_key||*t==*sharing{return Err(error!(PumpError::InvalidCreator));}if shared{*tb=st.creator}}"),
(" Ok(target)}pub fn execute("," Ok(*holder_key)}pub fn execute("),
("let mut target=validate(&st,hopt,fee,new,&holder_key,&sk,&mut tb)?;","validate(&st,hopt,shared,fee,new,&holder_key,&sk,&mut tb)?;let mut target=tb;"),
("else{target=st.creator;(Some(args.0),false,true)}","else{(Some(args.0),false,true)}"),
]
