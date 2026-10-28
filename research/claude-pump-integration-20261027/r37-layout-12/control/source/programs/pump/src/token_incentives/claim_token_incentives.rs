//! Claim of Token-2022 incentives using the shared volume accumulator worker.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::{
    instruction::{AccountMeta, Instruction},
    program::invoke_signed,
};
use anchor_lang::Event;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked};

use crate::{GlobalVolumeAccumulator, UserVolumeAccumulator};

const EVENT_CPI_DISCRIMINATOR: [u8; 8] = [228, 69, 165, 46, 81, 203, 154, 29];

#[derive(Accounts)]
pub struct ClaimTokenIncentives<'info> {
    /// CHECK: The user key names its ATA and volume PDA; it is not a signer.
    pub user: AccountInfo<'info>,
    #[account(init_if_needed, payer = payer, associated_token::mint = mint,
        associated_token::authority = user,
        associated_token::token_program = token_program)]
    pub user_ata: InterfaceAccount<'info, TokenAccount>,
    #[account(seeds = [b"global_volume_accumulator"], bump,
        has_one = mint @ crate::PumpError::InvalidIncentiveMint)]
    pub global_volume_accumulator: Account<'info, GlobalVolumeAccumulator>,
    #[account(mut, associated_token::mint = mint,
        associated_token::authority = global_volume_accumulator,
        associated_token::token_program = token_program)]
    pub global_incentive_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(mut, seeds = [b"user_volume_accumulator", user.key().as_ref()], bump)]
    pub user_volume_accumulator: Account<'info, UserVolumeAccumulator>,
    pub mint: InterfaceAccount<'info, Mint>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    /// CHECK: This is the program's event CPI signer PDA.
    #[account(seeds = [b"__event_authority"], bump)]
    pub event_authority: AccountInfo<'info>,
    pub program: Program<'info, crate::program::PumpRecovered>,
    #[account(mut)]
    pub payer: Signer<'info>,
}

#[event]
#[derive(Clone)]
pub struct ClaimTokenIncentivesEvent {
    pub user: Pubkey,
    pub mint: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
}

pub fn claim(ctx: Context<ClaimTokenIncentives>) -> Result<()> {
    let now = Clock::get()?.unix_timestamp;
    let global = &mut ctx.accounts.global_volume_accumulator;
    let user = &mut ctx.accounts.user_volume_accumulator;
    super::volume_accumulator::update(global, user, now, 0, &ctx.accounts.user.key())?;
    let amount = user.total_unclaimed_tokens;
    if amount == 0 {
        msg!("No tokens to claim");
        return Ok(());
    }
    let bump = [ctx.bumps.global_volume_accumulator];
    let signer: &[&[u8]] = &[b"global_volume_accumulator", &bump];
    let transfer = TransferChecked {
        from: ctx
            .accounts
            .global_incentive_token_account
            .to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.user_ata.to_account_info(),
        authority: global.to_account_info(),
    };
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            transfer,
            &[signer],
        ),
        amount,
        ctx.accounts.mint.decimals,
    )?;
    super::volume_accumulator::record_claim(user, now);
    let event = ClaimTokenIncentivesEvent {
        user: ctx.accounts.user.key(),
        mint: ctx.accounts.mint.key(),
        amount,
        timestamp: now,
        total_claimed_tokens: user.total_claimed_tokens,
        current_sol_volume: user.current_sol_volume,
    };
    emit!(event.clone());
    let mut data = EVENT_CPI_DISCRIMINATOR.to_vec();
    data.extend_from_slice(&event.data());
    let ix = Instruction {
        program_id: crate::ID,
        accounts: vec![AccountMeta::new_readonly(
            ctx.accounts.event_authority.key(),
            true,
        )],
        data,
    };
    let event_bump = [ctx.bumps.event_authority];
    let event_signer: &[&[u8]] = &[b"__event_authority", &event_bump];
    invoke_signed(
        &ix,
        &[ctx.accounts.event_authority.to_account_info()],
        &[event_signer],
    )?;
    Ok(())
}
