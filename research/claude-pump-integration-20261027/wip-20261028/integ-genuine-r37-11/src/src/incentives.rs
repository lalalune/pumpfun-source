//! Bounded reconstruction of Pump admin token-incentive scheduling.
use anchor_lang::prelude::*;
use anchor_spl::{
    associated_token::AssociatedToken,
    token_interface::{Mint, TokenAccount, TokenInterface},
};

use crate::{Global, GlobalVolumeAccumulator, PumpError};

#[event_cpi]
#[derive(Accounts)]
pub struct AdminUpdateTokenIncentives<'info> {
    #[account(mut)]
    pub authority: Signer<'info>,
    #[account(seeds = [b"global"], bump, has_one = authority @ PumpError::NotAuthorized)]
    pub global: Box<Account<'info, Global>>,
    #[account(mut, seeds = [b"global_volume_accumulator"], bump)]
    pub global_volume_accumulator: Account<'info, GlobalVolumeAccumulator>,
    pub mint: InterfaceAccount<'info, Mint>,
    #[account(
        init_if_needed,
        payer = authority,
        associated_token::mint = mint,
        associated_token::authority = global_volume_accumulator,
        associated_token::token_program = token_program
    )]
    pub global_incentive_token_account: InterfaceAccount<'info, TokenAccount>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    pub system_program: Program<'info, System>,
    pub token_program: Interface<'info, TokenInterface>,
}

#[event]
#[derive(Clone)]
pub struct AdminUpdateTokenIncentivesEvent {
    pub start_time: i64,
    pub end_time: i64,
    pub day_number: u64,
    pub token_supply_per_day: u64,
    pub mint: Pubkey,
    pub seconds_in_a_day: i64,
    pub timestamp: i64,
}

pub fn execute(
    ctx: Context<AdminUpdateTokenIncentives>,
    start_time: i64,
    end_time: i64,
    seconds_in_a_day: i64,
    day_number: u64,
    token_supply_per_day: u64,
) -> Result<()> {
    let timestamp = Clock::get()?.unix_timestamp;
    crate::token_incentives::volume_accumulator::update_schedule(
        &mut ctx.accounts.global_volume_accumulator,
        start_time,
        end_time,
        seconds_in_a_day,
        &ctx.accounts.mint.key(),
        day_number,
        token_supply_per_day,
        timestamp,
    )?;
    let event = AdminUpdateTokenIncentivesEvent {
        start_time,
        end_time,
        day_number,
        token_supply_per_day,
        mint: ctx.accounts.mint.key(),
        seconds_in_a_day,
        timestamp,
    };
    emit!(event.clone());
    emit_cpi!(event);
    msg!(
        "GlobalVolumeAccumulator={:?}",
        ctx.accounts.global_volume_accumulator
    );
    Ok(())
}
