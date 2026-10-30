EDITS=[
("new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","new:Option<Pubkey>,holder_key:&Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
("if t==*holder_key||t==*sharing{","if t==*holder_key||t==sharing{"),
("validate(&st,hopt,fee,new,&holder_key,&sk)?","validate(&st,hopt,fee,new,&holder_key,sk)?"),
]
