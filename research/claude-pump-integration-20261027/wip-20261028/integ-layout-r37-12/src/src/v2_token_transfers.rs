use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, TokenAccount, TokenInterface, TransferChecked};
use crate::trade_types::BondingCurve;

/// Transfer curve tokens through the selected token program and signer seeds.
#[inline(never)]
pub fn transfer_curve_tokens<'info>(
    token_program: &Interface<'info, TokenInterface>,
    source: &InterfaceAccount<'info, TokenAccount>,
    destination: &InterfaceAccount<'info, TokenAccount>,
    authority: &Account<'info, BondingCurve>,
    decimals: u8,
    mint: &AccountInfo<'info>,
    amount: u64,
    signer_seeds: &[&[&[u8]]; 1],
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            token_program.to_account_info(),
            TransferChecked {
                from: source.to_account_info(),
                to: destination.to_account_info(),
                authority: authority.to_account_info(),
                mint: mint.clone(),
            },
            signer_seeds,
        ),
        amount,
        decimals,
    )
}

/// Transfer curve tokens with the curve authority passed by double reference.
#[inline(never)]
pub fn transfer_curve_tokens_ref<'info>(
    token_program: &Interface<'info, TokenInterface>,
    source: &InterfaceAccount<'info, TokenAccount>,
    destination: &InterfaceAccount<'info, TokenAccount>,
    authority: &&Account<'info, BondingCurve>,
    decimals: u8,
    mint: &AccountInfo<'info>,
    amount: u64,
    signer_seeds: &[&[&[u8]]; 1],
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            token_program.to_account_info(),
            TransferChecked {
                from: source.to_account_info(),
                to: destination.to_account_info(),
                authority: authority.to_account_info(),
                mint: mint.clone(),
            },
            signer_seeds,
        ),
        amount,
        decimals,
    )
}
