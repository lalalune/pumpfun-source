ALL=[]
EDITS=[('swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);','let swr=(!skip).then(||sweep(&ctx,&holder_key)).transpose();let pab=ctx.bumps.pool_authority;swept=swr?.unwrap_or(0);'),('&[ctx.bumps.pool_authority]]];','&[pab]]];')]
ALL+=EDITS
A='let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}'
EDITS=[(A,'{'+A+'}')]
ALL+=EDITS
EDITS=ALL
