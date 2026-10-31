EDITS=[('if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{', 'if frozen&&amount!=0{return err!(PumpError::CtoSharedVaultFrozen);}if !frozen&&amount>0{')]
