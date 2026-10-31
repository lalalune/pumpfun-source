EDITS=[('if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}', 'if frozen{if amount!=0{return err!(PumpError::CtoSharedVaultFrozen);}}')]
