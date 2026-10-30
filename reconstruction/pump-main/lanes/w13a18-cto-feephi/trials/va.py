EDITS=[
("holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","holder_key:&Pubkey,sharing:&Pubkey,out:&mut Pubkey)->Result<()>{"),
(" let target=if holder{if new.is_some()"," *out=if holder{if new.is_some()"),
(" Ok(target)}pub fn execute("," Ok(())}pub fn execute("),
("let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;","let mut target=Pubkey::default();validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key(),&mut target)?;"),
]
