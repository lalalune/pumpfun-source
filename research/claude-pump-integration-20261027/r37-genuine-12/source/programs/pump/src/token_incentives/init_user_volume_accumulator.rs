use anchor_lang::prelude::*;

use super::volume_accumulator::UserVolumeAccumulator;

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
