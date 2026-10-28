use anchor_lang::prelude::*;

#[inline(never)]
pub fn ensure_rent_exempt<'info>(
    _size: usize,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
) -> Result<()> {
    let minimum = Rent::get()?.minimum_balance(0);
    if destination.lamports() < minimum {
        crate::legacy_buy::native_payments::transfer(system_program.as_ref(), payer, destination, minimum)
    } else {
        Ok(())
    }
}
