use anchor_lang::prelude::*;
use crate::Initialize;
pub fn execute(ctx:Context<Initialize>)->Result<()>{
 ctx.accounts.global.authority=ctx.accounts.user.key();
 ctx.accounts.global.initialized=true;
 Ok(())
}
#[event_cpi]
#[derive(Accounts)]
pub struct UpdateGlobalAuthority<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ crate::PumpError::NotAuthorized)]
 pub global:Account<'info,crate::Global>,
 pub authority:Signer<'info>,
 /// CHECK: new authority is assigned by the current signer; zero/self are accepted by the original.
 pub new_authority:AccountInfo<'info>,
}
