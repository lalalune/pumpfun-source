use anchor_lang::prelude::*;
use anchor_lang::system_program::{transfer, Transfer};

use super::state::{QuoteControl, QuoteControlMint, QUOTE_CONTROL_SEED};
use crate::{Global, PumpError};

#[event_cpi]
#[derive(Accounts)]
pub struct UpdateQuoteControlMints<'info> {
    #[account(
        mut,
        constraint = quote_control.is_admin(&authority.key())
            || global.authority == authority.key() @ PumpError::NotAuthorized
    )]
    pub authority: Signer<'info>,

    #[account(seeds = [b"global"], bump)]
    pub global: Account<'info, Global>,

    #[account(mut, seeds = [QUOTE_CONTROL_SEED], bump)]
    pub quote_control: Account<'info, QuoteControl>,

    pub system_program: Program<'info, System>,
}

#[event]
#[derive(Clone, Copy)]
pub struct AddQuoteControlMintEvent {
    pub quote_control: Pubkey,
    pub authority: Pubkey,
    pub quote_mint: Pubkey,
    pub initial_virtual_quote_reserves: u64,
    pub timestamp: i64,
}

#[event]
#[derive(Clone, Copy)]
pub struct RemoveQuoteControlMintEvent {
    pub quote_control: Pubkey,
    pub authority: Pubkey,
    pub quote_mint: Pubkey,
    pub timestamp: i64,
}

// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

/// Lists a new quote mint.
/// The account grows by one entry when it is full; the authority pays any
/// additional rent.
pub fn add_quote_control_mint(
    ctx: Context<UpdateQuoteControlMints>,
    quote_mint: Pubkey,
    initial_virtual_quote_reserves: u64,
) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    quote_control.validate_new_mint(&quote_mint)?;

    let new_space = QuoteControl::space(quote_control
        .mints
        .len()
        .checked_add(1)
        .ok_or_else(|| error!(PumpError::Overflow))?)?;

    let info = quote_control.to_account_info();
    if new_space > info.data_len() {
        let lamports_diff = Rent::get()?.minimum_balance(new_space).saturating_sub(info.lamports());
        pay_rent(&ctx, &info, lamports_diff)?;
        info.realloc(new_space, false)?;












    }
    let quote_control = &mut ctx.accounts.quote_control;
    quote_control.mints.push(QuoteControlMint {
        mint: quote_mint,
        initial_virtual_quote_reserves,
    });

    let event = AddQuoteControlMintEvent {
        quote_control: quote_control.key(),
        authority: ctx.accounts.authority.key(),
        quote_mint,
        initial_virtual_quote_reserves,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}

pub fn remove_quote_control_mint(ctx: Context<UpdateQuoteControlMints>, quote_mint: Pubkey) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    quote_control.remove_mint(quote_mint)?;
    let event = RemoveQuoteControlMintEvent {
        quote_control: quote_control.key(),
        authority: ctx.accounts.authority.key(),
        quote_mint,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}

// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
fn pay_rent<'info>(
    ctx: &Context<'_, '_, '_, '_, UpdateQuoteControlMints<'info>>,
    to: &AccountInfo<'info>,
    lamports: u64,
) -> Result<()> {
    if lamports > 0 {
        transfer(
            CpiContext::new(
                ctx.accounts.system_program.to_account_info(),
                Transfer {
                    from: ctx.accounts.authority.to_account_info(),
                    to: to.clone(),
                },
            ),
            lamports,
        )?;
    }
    Ok(())
}
