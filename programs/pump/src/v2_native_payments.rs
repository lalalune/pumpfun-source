use anchor_lang::prelude::*;

#[inline(never)]
pub fn ensure_rent_exempt<'info>(
    size: ZeroRentSize,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    destination: &AccountInfo<'info>,
) -> Result<()> {
    let minimum = Rent::get()?.minimum_balance(size as usize);
    if destination.lamports() < minimum {
        crate::legacy_buy::native_payments::transfer(system_program.as_ref(), payer, destination, minimum)
    } else {
        Ok(())
    }
}

/// Native vaults require rent for zero data bytes. This type makes other sizes
/// unrepresentable while retaining the original usize argument representation.
#[repr(usize)]
pub enum ZeroRentSize { Zero = 0 }
