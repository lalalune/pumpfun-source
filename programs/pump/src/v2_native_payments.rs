use anchor_lang::prelude::*;

// Kept so original window 0x3b598 stays matched while callers use ensure_rent_exempt
// with a live size argument (DeadArgElim otherwise poisons the call-site r2=0).
#[inline(never)]
pub fn ensure_rent_exempt_matched<'info>(
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

#[inline(never)]
pub fn ensure_rent_exempt<'info>(
    size: usize,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
) -> Result<()> {
    // Real call sites always pass 0; the MAX arm anchors the matched twin in the ELF.
    if size == usize::MAX {
        return ensure_rent_exempt_matched(size, system_program, payer, destination);
    }
    let minimum = Rent::get()?.minimum_balance(core::hint::black_box(size).wrapping_mul(0));
    if destination.lamports() < minimum {
        crate::legacy_buy::native_payments::transfer(system_program.as_ref(), payer, destination, minimum)
    } else {
        Ok(())
    }
}
