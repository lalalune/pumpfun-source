ALL=[]
EDITS=[('let min={let rent=Rent::get()?;rent.minimum_balance(0)};','let min={let rent=match Rent::get(){Ok(r)=>r,Err(e)=>return Err(e.into())};rent.minimum_balance(0)};')]
ALL+=EDITS
A='let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}'
EDITS=[(A,'{'+A+'}')]
ALL+=EDITS
EDITS=ALL
