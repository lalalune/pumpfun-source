EDITS=[('let min={let rent=Rent::get()?;rent.minimum_balance(0)};','let min=match Rent::get(){Ok(rent)=>rent.minimum_balance(0),Err(e)=>return Err(e.into())};')]
