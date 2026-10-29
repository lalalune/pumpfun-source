use anchor_lang::prelude::*;
use super::state::{QuoteControl, QUOTE_CONTROL_SEED};
use crate::{Global, PumpError};

#[event_cpi]
#[derive(Accounts)]
pub struct SetQuoteControlAdmin<'info> {
    #[account(seeds = [b"global"], bump, has_one = authority @ PumpError::NotAuthorized)]
    pub global: Account<'info, Global>,

    pub authority: Signer<'info>,

    #[account(mut, seeds = [QUOTE_CONTROL_SEED], bump)]
    pub quote_control: Account<'info, QuoteControl>,
}

#[event]
#[derive(Clone, Copy)]
pub struct SetQuoteControlAdminEvent {
    pub quote_control: Pubkey,
    pub authority: Pubkey,
    pub old_admin: Pubkey,
    pub new_admin: Pubkey,
    pub timestamp: i64,
}

pub fn set_quote_control_admin(ctx: Context<SetQuoteControlAdmin>, new_admin: Pubkey) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    let old_admin = quote_control.admin;
    quote_control.admin = new_admin;
    let event = SetQuoteControlAdminEvent {
        quote_control: quote_control.key(),
        authority: ctx.accounts.authority.key(),
        old_admin,
        new_admin,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}

#[event]
#[derive(Clone, Copy)]
pub struct SetQuoteControlMintReservesEvent {
    pub quote_control: Pubkey,
    pub authority: Pubkey,
    pub quote_mint: Pubkey,
    pub old_initial_virtual_quote_reserves: u64,
    pub new_initial_virtual_quote_reserves: u64,
    pub timestamp: i64,
}

#[event_cpi]
#[derive(Accounts)]
pub struct SetQuoteControlMintReserves<'info> {
    #[account(
        constraint = quote_control.is_reserves_admin(&authority.key())
            || quote_control.is_admin(&authority.key())
            || global.authority == authority.key() @ PumpError::NotAuthorized
    )]
    pub authority: Signer<'info>,

    #[account(seeds = [b"global"], bump)]
    pub global: Account<'info, Global>,

    #[account(mut, seeds = [QUOTE_CONTROL_SEED], bump)]
    pub quote_control: Account<'info, QuoteControl>,
}

pub fn set_quote_control_mint_reserves(
    ctx: Context<SetQuoteControlMintReserves>,
    quote_mint: Pubkey,
    initial_virtual_quote_reserves: u64,
) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    let old = quote_control.set_mint_reserves(quote_mint, initial_virtual_quote_reserves)?;
    let event = SetQuoteControlMintReservesEvent {
        quote_control: quote_control.key(),
        authority: ctx.accounts.authority.key(),
        quote_mint,
        old_initial_virtual_quote_reserves: old,
        new_initial_virtual_quote_reserves: initial_virtual_quote_reserves,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}

#[event_cpi]
#[derive(Accounts)]
pub struct SetQuoteControlReservesAdmin<'info> {
    #[account(
        constraint = quote_control.is_admin(&authority.key())
            || global.authority == authority.key() @ PumpError::NotAuthorized
    )]
    pub authority: Signer<'info>,

    #[account(seeds = [b"global"], bump)]
    pub global: Account<'info, Global>,

    #[account(mut, seeds = [QUOTE_CONTROL_SEED], bump)]
    pub quote_control: Account<'info, QuoteControl>,
}

#[event]
#[derive(Clone, Copy)]
pub struct SetQuoteControlReservesAdminEvent {
    pub quote_control: Pubkey,
    pub authority: Pubkey,
    pub old_reserves_admin: Pubkey,
    pub new_reserves_admin: Pubkey,
    pub timestamp: i64,
}

pub fn set_quote_control_reserves_admin(
    ctx: Context<SetQuoteControlReservesAdmin>,
    new_reserves_admin: Pubkey,
) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    let old_reserves_admin = quote_control.reserves_admin;
    quote_control.reserves_admin = new_reserves_admin;
    let event = SetQuoteControlReservesAdminEvent {
        quote_control: quote_control.key(),
        authority: ctx.accounts.authority.key(),
        old_reserves_admin,
        new_reserves_admin,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}

