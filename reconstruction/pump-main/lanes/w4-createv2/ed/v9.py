EDITS=[(" init_curve(&mut ctx.accounts.bonding_curve,global,creator,"," init_curve(ctx.accounts,creator,"),
("fn init_curve(bonding_curve:&mut trade_types::BondingCurve,global:&Global,creator:Pubkey,","fn init_curve(accounts:&mut CreateV2,creator:Pubkey,"),
(" let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n"," let global:&Global=&accounts.global;\n let bonding_curve:&mut trade_types::BondingCurve=&mut accounts.bonding_curve;\n let initial_virtual_quote_reserves=global.initial_virtual_quote_reserves;\n")]
