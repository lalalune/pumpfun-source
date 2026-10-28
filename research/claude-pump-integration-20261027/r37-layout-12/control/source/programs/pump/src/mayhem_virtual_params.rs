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
    pub sol_vault_authority: UncheckedAccount<'info>,
    #[account(mut, associated_token::mint = mint, associated_token::authority = sol_vault_authority, associated_token::token_program = token_program)]
    pub mayhem_token_vault: InterfaceAccount<'info, TokenAccount>,
    pub mint: InterfaceAccount<'info, Mint>,
    #[account(seeds = [b"global"], bump)]
    pub global: Box<Account<'info, Global>>,
    #[account(mut, seeds = [b"bonding-curve", mint.key().as_ref()], bump)]
    pub bonding_curve: Account<'info, BondingCurve>,
    #[account(address = anchor_spl::token_2022::ID)]
    pub token_program: Interface<'info, TokenInterface>,
}

pub fn execute(ctx: Context<SetMayhemVirtualParams>) -> Result<()> {
    let vault_amount = ctx.accounts.mayhem_token_vault.amount;
    let initial_real_token_reserves = ctx.accounts.global.initial_real_token_reserves;
    let mint = ctx.accounts.mint.key();
    let bc = &mut ctx.accounts.bonding_curve;
    let virtual_token_reserves = bc.virtual_token_reserves;
    let virtual_sol_reserves = bc.virtual_quote_reserves;

    let quote_mint = bc.quote_mint;
    bc.sync_virtual_quote_reserves(initial_real_token_reserves, vault_amount, &quote_mint)?;

    let event = UpdateMayhemVirtualParamsEvent {
        timestamp: Clock::get()?.unix_timestamp,
        mint,
        virtual_token_reserves,
        virtual_sol_reserves,
        new_virtual_token_reserves: bc.virtual_token_reserves,
        new_virtual_sol_reserves: bc.virtual_quote_reserves,
        real_token_reserves: bc.real_token_reserves,
        real_sol_reserves: bc.real_quote_reserves,
    };
    emit!(event.clone());
    emit_cpi!(event);
    Ok(())
}

impl BondingCurve {
    // The original handler calls a separate helper at 0xa23f0.
    #[inline(never)]
    fn sync_virtual_quote_reserves(
        &mut self,
        initial_real_token_reserves: u64,
        vault_amount: u64,
        quote_mint: &Pubkey,
    ) -> Result<()> {
        let bc = self;
        if bc.complete || !bc.is_mayhem_mode {
            return Ok(());
        }
        let real_quote_reserves = bc.real_quote_reserves;
        let virtual_token_reserves = bc.virtual_token_reserves;
        let denominator = bc
            .token_total_supply
            .checked_mul(2)
            .ok_or(PumpError::Overflow)?
            .checked_sub(initial_real_token_reserves)
            .ok_or(PumpError::Overflow)?
            .checked_sub(vault_amount)
            .ok_or(PumpError::Overflow)?;
        if *quote_mint == Pubkey::default() {
            if real_quote_reserves < 10_000_000 || denominator < 1_000_000_000_000 {
                return Ok(());
            }
        } else if real_quote_reserves < 1_000_000 || denominator < 1_000_000_000_000 {
            return Ok(());
        }
        // Keep these fallible operations separate: the captured helper has
        // distinct Overflow returns for multiplication and division.
        let numerator = (denominator as u128 + virtual_token_reserves as u128)
            .checked_mul(real_quote_reserves as u128)
            .ok_or(PumpError::Overflow)?;
        let computed = numerator
            .checked_div(denominator as u128)
            .ok_or(PumpError::Overflow)?;
        // Conversion precedes the cap in both captured branches.
        if *quote_mint == Pubkey::default() {
            let amount = u64::try_from(computed)?;
            bc.virtual_quote_reserves = amount.min(2_000_000_000_000);
        } else {
            let amount = u64::try_from(computed)?;
            bc.virtual_quote_reserves = amount.min(160_000_000_000);
        }
        Ok(())
    }
}

#[event]
#[derive(Clone)]
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
