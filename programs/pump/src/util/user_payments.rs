use anchor_lang::prelude::*;use anchor_spl::token_interface::TokenInterface;use crate::trade_types::BondingCurve;use crate::user_quote_payments::*;
    #[inline(never)]
    pub fn transfer_from_user<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &Account<'info, BondingCurve>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native(system_program, payer, destination, amount); }
        let (from, to) = crate::user_quote_accounts(quote_source, quote_destination);

        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }
    #[inline(never)]
    pub fn transfer_from_user_recipient<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: &&UncheckedAccount<'info>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native_recipient(system_program, payer, destination, amount); }
        let (from, to) = crate::user_quote_accounts(quote_source, quote_destination);

        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }
    #[inline(never)]
    pub fn transfer_from_user_owned<'info>(
        native: bool,
        system_program: &AccountInfo<'info>,
        payer: &Signer<'info>,
        destination: AccountInfo<'info>,
        amount: u64,
        token_program: &Interface<'info, TokenInterface>,
        quote_decimals: u8,
        quote_mint: &AccountInfo<'info>,
        quote_source: Option<&AccountInfo<'info>>,
        quote_destination: Option<&AccountInfo<'info>>,
    ) -> Result<()> {
        if native { return transfer_native_owned(system_program, payer, destination, amount); }
        let (from, to) = crate::user_quote_accounts(quote_source, quote_destination);

        let authority = payer.to_account_info();
        crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
            token_program, from, to, authority, quote_decimals, quote_mint, amount, &[],
        )
    }
