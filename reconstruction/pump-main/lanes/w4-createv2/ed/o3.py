EDITS=[("->Result<(Pubkey,Option<u64>,QuoteSource)>{","->Result<(QuoteSource,Option<u64>,Pubkey)>{"),
(" if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}"," if remaining_accounts.is_empty() {return Ok((QuoteSource::Sol,None,Pubkey::default()));}"),
("  return Ok((Pubkey::default(),None,QuoteSource::Sol));","  return Ok((QuoteSource::Sol,None,Pubkey::default()));"),
(" Ok((mint_key,reserves,source))"," Ok((source,reserves,mint_key))"),
(" let (quote_mint,reserves,source)=validate_quote_mint("," let (source,reserves,quote_mint)=validate_quote_mint(")]
