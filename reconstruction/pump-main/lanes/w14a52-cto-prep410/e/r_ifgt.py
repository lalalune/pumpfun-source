EDITS=[[" require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);", " if a.bonding_curve.creator_fee>0{return Err(error!(PumpError::CreatorFeesNotSwept));}"]]
