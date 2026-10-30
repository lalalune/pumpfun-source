EDITS=[(" ctx.accounts.init_curve(creator,quote_mint,reserves,depth,fee,is_mayhem_mode,is_holder_reward.0);"," ctx.accounts.init_curve(quote_mint,reserves,creator,depth,fee,is_mayhem_mode,is_holder_reward.0);"),
("fn init_curve(&mut self,creator:Pubkey,quote_mint:Pubkey,reserves:Option<u64>,","fn init_curve(&mut self,quote_mint:Pubkey,reserves:Option<u64>,creator:Pubkey,")]
