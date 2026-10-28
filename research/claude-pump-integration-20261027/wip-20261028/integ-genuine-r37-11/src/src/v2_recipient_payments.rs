use anchor_lang::prelude::*;

/// Transfer a native fee payment to a configured recipient.
#[inline(never)]
pub(super) fn transfer_native<'info>(
    system_program: &AccountInfo<'info>,
    recipient: &UncheckedAccount<'info>,
    payer: &AccountInfo<'info>,
    amount: u64,
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    anchor_lang::system_program::transfer(
        CpiContext::new(
            system_program.clone(),
            anchor_lang::system_program::Transfer {
                to: recipient.to_account_info(),
                from: payer.clone(),
            },
        ),
        amount,
    )
}

pub(crate) use crate::split_protocol_fee;
