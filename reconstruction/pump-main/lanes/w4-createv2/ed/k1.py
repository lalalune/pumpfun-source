EDITS=[("else {reserves.unwrap_or(initial_virtual_quote_reserves)};","else {match reserves {Some(r)=>r,None=>initial_virtual_quote_reserves}};")]
