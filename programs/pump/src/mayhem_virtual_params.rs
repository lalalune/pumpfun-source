use crate::create_v2::MAYHEM_ID;
use crate::trade_types::BondingCurve;
use crate::{Global, PumpError};
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{Mint, TokenAccount, TokenInterface};

// Mayhem resyncs a bonding curve's virtual quote (SOL-side) reserve against the mayhem
// sol-vault token balance. Account #0 (`sol_vault_authority`) is mayhem's ["sol-vault"] PDA
// and must sign, so this instruction is reachable only through a mayhem `invoke_signed` CPI.
#[event_cpi]
#[derive(Accounts)]
pub struct SetMayhemVirtualParams<'info> {
    /// CHECK: The signer constraint and foreign-program PDA seeds authenticate this account.
    #[account(mut, signer, seeds = [b"sol-vault"], bump, seeds::program = MAYHEM_ID)]
    pub sol_vault_authority: AccountInfo<'info>,
    #[account(mut, associated_token::mint = mint, associated_token::authority = sol_vault_authority, associated_token::token_program = token_program.key())]
    pub mayhem_token_vault: InterfaceAccount<'info, TokenAccount>,
    pub mint: InterfaceAccount<'info, Mint>,
    #[account(seeds = [b"global"], bump)]
    pub global: Account<'info, Global>,
    #[account(mut, seeds = [b"bonding-curve", mint.key().as_ref()], bump)]
    pub bonding_curve: Account<'info, BondingCurve>,
    
    pub token_program: Program<'info, anchor_spl::token_2022::Token2022>,
}

pub(crate) fn execute(ctx: Context<SetMayhemVirtualParams>) -> Result<()> {
    let bc = &mut ctx.accounts.bonding_curve;
    let virtual_token_reserves = bc.virtual_token_reserves;
    let virtual_sol_reserves = bc.virtual_quote_reserves;
    let quote_mint = bc.quote_mint;
    bc.sync_virtual_quote_reserves(
        ctx.accounts.global.initial_real_token_reserves,
        ctx.accounts.mayhem_token_vault.amount,
        &quote_mint,
    )?;

    let event = UpdateMayhemVirtualParamsEvent {
        timestamp: Clock::get()?.unix_timestamp,
        mint: ctx.accounts.mint.key(),
        virtual_token_reserves,
        virtual_sol_reserves,
        new_virtual_token_reserves: bc.virtual_token_reserves,
        new_virtual_sol_reserves: bc.virtual_quote_reserves,
        real_token_reserves: bc.real_token_reserves,
        real_sol_reserves: bc.real_quote_reserves,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}





















































#[event]
#[derive(Clone, Copy)]
pub struct UpdateMayhemVirtualParamsEvent {
    pub timestamp: i64,
    pub mint: Pubkey,
    pub virtual_token_reserves: u64,
    pub virtual_sol_reserves: u64,
    pub new_virtual_token_reserves: u64,
    pub new_virtual_sol_reserves: u64,
    pub real_token_reserves: u64,
    pub real_sol_reserves: u64,
}
