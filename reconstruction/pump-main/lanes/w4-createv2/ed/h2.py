EDITS=[(" let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n ctx.accounts.init_curve(creator,quote_mint,reserves,depth,","\n ctx.accounts.init_curve(creator,quote_mint,reserves,if let QuoteSource::Nested(depth)=source {depth} else {0},")]
APPEND=''
