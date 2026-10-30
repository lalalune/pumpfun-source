EDITS=[
("fn validate(st:&CtoState,holder:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{",
 "fn validate(st:&CtoState,holder:bool,shared:bool,fee:Option<u64>,new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey,su:&mut Option<Option<Pubkey>>,co:&mut bool)->Result<Pubkey>{"),
("{return Err(error!(PumpError::InvalidCreator));}t};","{return Err(error!(PumpError::InvalidCreator));}if shared{st.creator}else{t}};"),
(" Ok(target)}pub fn execute("," (*su,*co)=if shared{if holder{(Some(None),false)}else{(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())}; Ok(target)}pub fn execute("),
("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;let (sharing_update,collect_old)=if shared{if holder{(Some(None),false)}else{target=st.creator;(Some(new),false)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default())};",
 "let mut sharing_update=None;let mut collect_old=false;let target=validate(&st,holder,shared,fee,new,&holder_key,&a.sharing_config.key(),&mut sharing_update,&mut collect_old)?;"),
]
