EDITS=[('require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,','require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?.checked_sub(1).is_none(),')]
