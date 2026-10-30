use anchor_lang::prelude::*;

// Original window 0x3b598. The unreachable hint keeps `_size` live through DeadArgElim,
// so callers still pass the original's r2=0 while the body uses minimum_balance(0).
#[inline(never)]
pub fn ensure_rent_exempt<'info>(
    _size: usize,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
) -> Result<()> {
    if _size != 0 { unsafe { core::hint::unreachable_unchecked() } } let minimum = Rent::get()?.minimum_balance(0);
    if destination.lamports() < minimum {
        crate::legacy_buy::native_payments::transfer(system_program.as_ref(), payer, destination, minimum)
    } else {
        Ok(())
    }
}
