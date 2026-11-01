import runpy,os
E=runpy.run_path(os.path.join(os.path.dirname(os.path.abspath(__file__)),'vb01v.py'))['EDITS']
EDITS=E+[("let quote_locked={let q=a.bonding_curve.quote_mint;q==Pubkey::default()||q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&q)};","let quote_locked={let q=&a.bonding_curve.quote_mint;*q==Pubkey::default()||*q==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(q)};")]
