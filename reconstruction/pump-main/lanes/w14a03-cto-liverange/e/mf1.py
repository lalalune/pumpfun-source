EDITS=[("struct CtoState{creator:Pubkey,max_fee:u64,","struct CtoState<'g>{creator:Pubkey,max_fee:&'g u64,"),
("fn validate(st:&CtoState,","fn validate(st:&CtoState<'_>,"),
("f>st.max_fee","f>*st.max_fee"),
("max_fee:a.global.max_configurable_creator_fee_bps","max_fee:&a.global.max_configurable_creator_fee_bps")]
