use anchor_lang::prelude::*;
use crate::{CloseUserVolume,CloseUserVolumeAccumulatorEvent};
pub fn execute(ctx:Context<CloseUserVolume>)->Result<()>{
      let a=&ctx.accounts.user_volume_accumulator;let event=CloseUserVolumeAccumulatorEvent{total_unclaimed_tokens:a.total_unclaimed_tokens,total_claimed_tokens:a.total_claimed_tokens,current_sol_volume:a.current_sol_volume,last_update_timestamp:a.last_update_timestamp,user:ctx.accounts.user.key(),timestamp:Clock::get()?.unix_timestamp};emit!(event.clone());emit_cpi!(event);Ok(())
}
