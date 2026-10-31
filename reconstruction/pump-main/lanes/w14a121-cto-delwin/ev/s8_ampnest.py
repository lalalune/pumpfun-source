EDITS=[("let amm_present=!a.coin_creator_vault_ata.data_is_empty();let amm_frozen=amm_present&&token_frozen(a.coin_creator_vault_ata.as_ref())?;","let amm_present=!a.coin_creator_vault_ata.data_is_empty();"),
("  if amm_frozen{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}","  if amm_present{if token_frozen(a.coin_creator_vault_ata.as_ref())?{require!(token_raw_amount(a.coin_creator_vault_ata.as_ref())?==0,PumpError::CtoSharedVaultFrozen);}"),
("  else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm","  else{crate::pump_amm"),
("is_writable:x.is_writable,executable:x.executable}}}))?;}","is_writable:x.is_writable,executable:x.executable}}}))?;}}")]
