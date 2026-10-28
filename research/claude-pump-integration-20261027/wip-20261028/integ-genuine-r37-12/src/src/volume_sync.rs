use crate::*;
pub use crate::token_incentives::volume_accumulator::GlobalVolumeAccumulator;
#[event_cpi]
#[derive(Accounts)]
pub struct SyncUserVolumeAccumulator<'info> {
    /// CHECK: used to derive the user accumulator and name the event.
    pub user: AccountInfo<'info>,
    #[account(seeds=[b"global_volume_accumulator"],bump)]
    pub global_volume_accumulator: Account<'info,GlobalVolumeAccumulator>,
    #[account(mut,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
    pub user_volume_accumulator: Account<'info,UserVolumeAccumulator>,
}
pub fn execute(ctx:Context<SyncUserVolumeAccumulator>)->Result<()> {
    let timestamp=Clock::get()?.unix_timestamp;
    let start=ctx.accounts.global_volume_accumulator.start_time;
    let user=&mut ctx.accounts.user_volume_accumulator;
    if user.last_update_timestamp<start && timestamp<start {
        let before=user.total_claimed_tokens;
        user.total_claimed_tokens=0;
        user.has_total_claimed_tokens=false;
        if before>0 {
            let event=SyncUserVolumeAccumulatorEvent{user:ctx.accounts.user.key(),total_claimed_tokens_before:before,total_claimed_tokens_after:0,timestamp};
            emit!(event.clone());emit_cpi!(event);
        }
    }
    Ok(())
}
#[event]
#[derive(Clone)]
pub struct SyncUserVolumeAccumulatorEvent {
    pub user: Pubkey,
    pub total_claimed_tokens_before: u64,
    pub total_claimed_tokens_after: u64,
    pub timestamp: i64,
}
