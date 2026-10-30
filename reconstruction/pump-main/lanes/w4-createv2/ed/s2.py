EDITS=[(" let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n"," let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n let bonding_curve:&mut trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;\n"),
(" let bonding_curve:&mut trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;\n bonding_curve.creator=creator;\n",""),
(" bonding_curve.token_total_supply=global.token_total_supply;\n"," bonding_curve.token_total_supply=global.token_total_supply;\n bonding_curve.creator=creator;\n")]
