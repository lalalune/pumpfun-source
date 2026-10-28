use anchor_lang::prelude::*;

use super::state::{QuoteControl, QUOTE_CONTROL_SEED};

// layout-pad(2): aligns the next Source site with the original line

#[derive(Accounts)]
pub struct InitializeQuoteControl<'info> {
    #[account(
        init,
        payer = user,
        space = 8 + QuoteControl::INIT_SPACE,
        seeds = [QUOTE_CONTROL_SEED],
        bump,
    )]
    pub quote_control: Account<'info, QuoteControl>,

    #[account(mut)]
    pub user: Signer<'info>,

    pub system_program: Program<'info, System>,
}

/// Creates the empty quote-control account. The admin and reserves admin start as the
/// default key; the global authority assigns them afterwards.
pub fn initialize_quote_control(ctx: Context<InitializeQuoteControl>) -> Result<()> {
    let quote_control = &mut ctx.accounts.quote_control;
    quote_control.admin = Pubkey::default();
    quote_control.reserves_admin = Pubkey::default();
    quote_control._reserved = [0; 32];
    quote_control.mints = Vec::new();
    Ok(())
}
