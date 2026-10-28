use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, TokenAccount, TokenInterface, TransferChecked};

/// Transfer user tokens through the selected token program.
#[inline(never)]
pub fn transfer_user_tokens<'info>(
    token_program: &Interface<'info, TokenInterface>,
    source: &InterfaceAccount<'info, TokenAccount>,
    destination: &InterfaceAccount<'info, TokenAccount>,
    authority: &AccountInfo<'info>,
    decimals: u8,
    mint: &AccountInfo<'info>,
    amount: u64,
) -> Result<()> {
    token_interface::transfer_checked(
        CpiContext::new(
            token_program.to_account_info(),
            TransferChecked {
                from: source.to_account_info(),
                to: destination.to_account_info(),
                authority: authority.clone(),
                mint: mint.clone(),
            },
        ),
        amount,
        decimals,
    )
}
