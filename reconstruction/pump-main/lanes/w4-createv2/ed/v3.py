EDITS=[(" let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n init_curve(&mut ctx.accounts.bonding_curve,global,creator,quote_mint,reserves,depth,fee,",
"\n init_curve(&mut ctx.accounts.bonding_curve,global,creator,quote_mint,reserves,source,fee,"),
("reserves:Option<u64>,depth:u8,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){\n","reserves:Option<u64>,source:QuoteSource,fee:u64,is_mayhem_mode:bool,is_holder_reward:bool){\n let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n")]
