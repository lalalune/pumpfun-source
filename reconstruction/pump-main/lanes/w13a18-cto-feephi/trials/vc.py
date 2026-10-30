EDITS=[
("fn validate(st:&CtoState,holder:bool,fee:","fn validate(st:&CtoState,holder:bool,shared:bool,fee:"),
("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","holder_key:&Pubkey,sharing:&Pubkey)->Result<(Pubkey,u8)>{"),
(" let target=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}*holder_key}else{"," let (target,arm)=if holder{if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}(*holder_key,0u8)}else{"),
("{return Err(error!(PumpError::InvalidCreator));}t};","{return Err(error!(PumpError::InvalidCreator));}if shared{(st.creator,1)}else{(t,2)}};"),
(" Ok(target)}pub fn execute("," Ok((target,arm))}pub fn execute("),
("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};",
 "let (target,arm)=validate(&st,holder,shared,fee,new,&holder_key,&a.sharing_config.key())?;let (sharing_update,collect_old,skip)=match arm{0=>if shared{(Some(None),false,false)}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)},1=>(Some(args.0),false,true),_=>(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};"),
]
