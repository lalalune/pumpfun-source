EDITS=[
("new:Option<Pubkey>,holder_key:&Pubkey,sharing:&Pubkey)->Result<Pubkey>{","new:Option<Pubkey>,holder_key:Pubkey,sharing:Pubkey)->Result<Pubkey>{"),
("CtoNewCreatorNotAllowed));}*holder_key}else{","CtoNewCreatorNotAllowed));}holder_key}else{"),
("if t==*holder_key||t==*sharing{","if t==holder_key||t==sharing{"),
("validate(&st,hopt,fee,new,&holder_key,&sk)?","validate(&st,hopt,fee,new,holder_key,sk)?"),
]
