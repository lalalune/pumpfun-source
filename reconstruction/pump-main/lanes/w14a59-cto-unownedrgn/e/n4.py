EDITS=[('let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;', 'let native=*a.quote_mint.to_account_info().key==anchor_spl::token::spl_token::native_mint::ID;')]
