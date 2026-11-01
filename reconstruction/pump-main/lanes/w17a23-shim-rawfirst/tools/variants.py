FF='let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;'
RF='let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'
VARIANTS={
 'R':[(664,FF,RF)],
}
TV_OK='&vsigner))?;return Ok(amount);}'
VARIANTS['RF1']=[(664,FF,RF),(719,TV_OK,'&vsigner))?;core::hint::black_box(());/*shim: fence on the token-arm transfer Ok continuation*/return Ok(amount);}')]
TVA='transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,'
TVB='transfer_vault_tokens(&a.quote_token_program,unsafe{&(*(ptp(31,&**a as *const AdminCto as *const u8) as *const AdminCto)).creator_vault_quote_token_account}/*shim: passthrough on the accounts pointer of the transfer source arg (no long-lived field address)*/,'
FENCE=(719,TV_OK,'&vsigner))?;core::hint::black_box(());/*shim: fence on the token-arm transfer Ok continuation*/return Ok(amount);}')
VARIANTS['RX1']=[(664,FF,RF),(719,TVA,TVB)]
VARIANTS['RX1F']=[(664,FF,RF),(719,TVA,TVB),FENCE]
