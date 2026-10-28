use anchor_lang::prelude::*;
use crate::Global;
#[derive(Accounts)]
pub struct Initialize<'info>{
 #[account(init,payer=user,space=1088,seeds=[b"global"],bump)]
 pub global:Account<'info,Global>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
}
pub fn execute(ctx:Context<Initialize>)->Result<()>{
 ctx.accounts.global.authority=ctx.accounts.user.key();
 ctx.accounts.global.initialized=true;
 Ok(())
}
