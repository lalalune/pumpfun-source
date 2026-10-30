EDITS=[("  if !collection_native||coin_present{anchor_spl::associated_token::create_idempotent(","  if !collection_native||coin_present{if let Err(e)=anchor_spl::associated_token::create_idempotent("),
("token_program:a.quote_token_program.to_account_info()}))?;}\n  if do_collect{","token_program:a.quote_token_program.to_account_info()})){return Err(e);}}\n  if do_collect{")]
