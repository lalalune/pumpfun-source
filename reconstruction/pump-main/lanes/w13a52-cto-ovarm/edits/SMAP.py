EDITS=[
("if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{","if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{"),
("amount,&vsigner)?;}\n   Ok(amount)}","amount,&vsigner).map(|()|amount)}else{Ok(amount)}\n   }"),
]
