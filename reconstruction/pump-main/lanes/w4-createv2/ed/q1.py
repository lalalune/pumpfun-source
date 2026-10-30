import runpy
EDITS=runpy.run_path('ed/r1nc.py')['EDITS']+[
(" let (quote_mint,reserves,source)=validate_quote_mint(&ctx,ctx.remaining_accounts)?;"," let quote=validate_quote_mint(&ctx,ctx.remaining_accounts)?;"),
("global_quote(quote_mint,&a.global),PumpError::MayhemModeQuoteMintNotAllowed","global_quote(quote.0,&a.global),PumpError::MayhemModeQuoteMintNotAllowed"),
("matches!(source,QuoteSource::Controlled|QuoteSource::Nested(_))","matches!(quote.2,QuoteSource::Controlled|QuoteSource::Nested(_))"),
("if let QuoteSource::Nested(depth)=source {depth}","if let QuoteSource::Nested(depth)=quote.2 {depth}"),
("if quote_mint==Pubkey::default() {global.initial_virtual_sol_reserves} else {reserves.unwrap_or(","if quote.0==Pubkey::default() {global.initial_virtual_sol_reserves} else {quote.1.unwrap_or("),
(" bonding_curve.quote_mint=quote_mint;"," bonding_curve.quote_mint=quote.0;")]
