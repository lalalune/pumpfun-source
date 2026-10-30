EDITS=[(" init_curve(ctx.accounts,creator,"," ctx.accounts.init_curve(creator,"),
("fn init_curve(accounts:&mut CreateV2,creator:Pubkey,","impl<'info> CreateV2<'info> {\nfn init_curve(&mut self,creator:Pubkey,"),
(" let global:&Global=&accounts.global;\n let bonding_curve:&mut trade_types::BondingCurve=&mut accounts.bonding_curve;\n"," let global:&Global=&self.global;\n let bonding_curve:&mut trade_types::BondingCurve=&mut self.bonding_curve;\n")]
APPEND='}\n'
