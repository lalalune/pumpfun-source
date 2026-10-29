use anchor_lang::prelude::*;

use super::volume_accumulator::UserVolumeAccumulator;

// layout-pad(2): aligns the next Source site with the original line

#[event_cpi]
#[derive(Accounts)]
pub struct InitUserVolume<'info>{
 #[account(mut)] pub payer:Signer<'info>,
 /// CHECK: any user may be funded by the payer.
 pub user:AccountInfo<'info>,
 #[account(init_if_needed,payer=payer,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
 pub user_volume_accumulator:Account<'info,UserVolumeAccumulator>,
 pub system_program:Program<'info,System>,
}
use crate::InitUserVolumeAccumulatorEvent;
pub fn execute(ctx:Context<InitUserVolume>)->Result<()>{
      let event=InitUserVolumeAccumulatorEvent{payer:ctx.accounts.payer.key(),user:ctx.accounts.user.key(),timestamp:Clock::get()?.unix_timestamp};ctx.accounts.user_volume_accumulator.user=ctx.accounts.user.key();emit!(event.clone());emit_cpi!(event);Ok(())
}
