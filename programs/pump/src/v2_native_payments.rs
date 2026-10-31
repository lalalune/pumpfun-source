use anchor_lang::prelude::*;

// Original window 0x3b598. Native vaults are topped up to the rent-exempt minimum for zero data bytes.
// The size argument keeps the original usize representation; its type admits only zero.
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

/// Data size of a native vault: always zero bytes.
#[repr(usize)]
pub enum ZeroRentSize { Zero = 0 }
