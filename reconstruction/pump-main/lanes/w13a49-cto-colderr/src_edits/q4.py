EDITS=[("let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;","let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref()).map_err(#[cold]|e|e)?;")]
