EDITS=[
 ("a.quote_mint.as_ref().as_ref(),amount,&vsigner)?;","a.quote_mint.as_ref().as_ref(),amount,&vsigner).map_err(cold_e)?;"),
 ("fn token_raw_amount(a:&AccountInfo)->Result<u64>{","#[cold]#[inline(never)]fn cold_e(e:anchor_lang::error::Error)->anchor_lang::error::Error{e} fn token_raw_amount(a:&AccountInfo)->Result<u64>{"),
]
