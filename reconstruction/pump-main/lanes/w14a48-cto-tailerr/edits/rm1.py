EDITS=[('let min={let rent=Rent::get()?;rent.minimum_balance(0)};','let min={let rent=match Rent::get(){Ok(r)=>r,Err(e)=>return Err(e.into())};rent.minimum_balance(0)};')]
