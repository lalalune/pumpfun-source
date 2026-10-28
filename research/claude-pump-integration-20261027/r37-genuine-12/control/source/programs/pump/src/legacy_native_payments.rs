use anchor_lang::prelude::*;

#[inline(never)]
pub(crate) fn ensure_rent_exempt<'info>(
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
) -> Result<()> {
    let minimum = Rent::get()?.minimum_balance(0);
    if destination.lamports() < minimum {
        transfer(system_program.as_ref(), payer, destination, minimum)
    } else {
        Ok(())
    }
}

#[inline(never)]
pub(super) fn transfer<'info>(
    system_program: &AccountInfo<'info>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
    amount: u64,
) -> Result<()> {
    if amount == 0 {
        return Ok(());
    }
    anchor_lang::system_program::transfer(
            CpiContext::new(
                system_program.clone(),
                anchor_lang::system_program::Transfer {
                    from: payer.to_account_info(),
                    to: destination.clone(),
                },
            ),
            amount,
        )
}
