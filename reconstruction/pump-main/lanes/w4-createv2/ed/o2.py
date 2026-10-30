EDITS=[("->Result<(Pubkey,Option<u64>,QuoteSource)>{","->Result<(QuoteSource,Pubkey,Option<u64>)>{"),
(" if remaining_accounts.is_empty() {return Ok((Pubkey::default(),None,QuoteSource::Sol));}"," if remaining_accounts.is_empty() {return Ok((QuoteSource::Sol,Pubkey::default(),None));}"),
("  return Ok((Pubkey::default(),None,QuoteSource::Sol));","  return Ok((QuoteSource::Sol,Pubkey::default(),None));"),
(" Ok((mint_key,reserves,source))"," Ok((source,mint_key,reserves))"),
(" let (quote_mint,reserves,source)=validate_quote_mint("," let (source,quote_mint,reserves)=validate_quote_mint(")]
