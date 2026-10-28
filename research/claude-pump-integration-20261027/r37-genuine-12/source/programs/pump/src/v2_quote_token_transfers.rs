use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, TokenInterface, TransferChecked};

/// Transfer quote tokens through the selected token program and signer seeds.
#[inline(never)]
pub fn transfer_quote_tokens<'info>(
    token_program: &Interface<'info, TokenInterface>,
    source: &AccountInfo<'info>,
    destination: &AccountInfo<'info>,
    authority: AccountInfo<'info>,
    decimals: u8,
    mint: &AccountInfo<'info>,
    amount: u64,
    signer_seeds: &[&[&[u8]]],
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            token_program.to_account_info(),
            TransferChecked {
                from: source.clone(),
                to: destination.clone(),
                authority: authority.clone(),
                mint: mint.clone(),
            },
            signer_seeds,
        ),
        amount,
        decimals,
    )
}
