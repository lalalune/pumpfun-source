EDITS=[('if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{', 'if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0&&!frozen{')]
