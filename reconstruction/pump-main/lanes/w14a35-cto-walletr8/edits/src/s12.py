EDITS=[("  if coin_present&do_coin{\n","  if do_coin{\n"),(" if collect_old{wallet(&ctx)?;}fn wallet"," if collect_old{if let Err(e)=wallet(&ctx){return Err(e);}}fn wallet")]
