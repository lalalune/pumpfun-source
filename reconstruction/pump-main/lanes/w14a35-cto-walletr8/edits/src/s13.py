# per-site Err on do_collect token_frozen too
EDITS=[("&&!token_frozen(a.creator_vault_quote_token_account.as_ref())?);","&&!match token_frozen(a.creator_vault_quote_token_account.as_ref()){Ok(v)=>v,Err(e)=>return Err(e)});")]
