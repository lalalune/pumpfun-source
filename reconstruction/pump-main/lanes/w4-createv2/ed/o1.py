EDITS=[("->Result<(Pubkey,Option<u64>,QuoteSource)>{","->Result<(Pubkey,QuoteSource,Option<u64>)>{"),
(" if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}"," if remaining_accounts.is_empty() {return Ok((Pubkey::default(),QuoteSource::Sol,None));}"),
("  return Ok((Pubkey::default(),None,QuoteSource::Sol));","  return Ok((Pubkey::default(),QuoteSource::Sol,None));"),
(" Ok((mint_key,reserves,source))"," Ok((mint_key,source,reserves))"),
(" let (quote_mint,reserves,source)=validate_quote_mint("," let (quote_mint,source,reserves)=validate_quote_mint(")]
