EDITS=[(" let (quote_mint,reserves,source)=validate_quote_mint(&ctx,ctx.remaining_accounts)?;\n\n"," let (quote_mint,reserves,source)=validate_quote_mint(&ctx,ctx.remaining_accounts)?;\n let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n"),
(" let depth=if let QuoteSource::Nested(depth)=source {depth} else {0};\n ctx.accounts.init_curve(","\n ctx.accounts.init_curve(")]
