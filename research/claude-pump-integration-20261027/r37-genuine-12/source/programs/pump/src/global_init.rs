use anchor_lang::prelude::*;
use crate::Initialize;
pub fn execute(ctx:Context<Initialize>)->Result<()>{
 ctx.accounts.global.authority=ctx.accounts.user.key();
 ctx.accounts.global.initialized=true;
 Ok(())
}
