EDITS=[('if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{','if frozen{if amount!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}else if amount>0{')]
