OLD="pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),"
NEW="pump_creator_vault_ata:{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,lamports:x.lamports.clone(),data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,"
EDITS=[(OLD,NEW)]
