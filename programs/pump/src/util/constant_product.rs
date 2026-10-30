use anchor_lang::prelude::*;
use crate::PumpError;

// layout-pad(7): aligns the next Source site with the original line






#[inline(never)]
pub fn output(amount_in:u128,reserve_in:u128,reserve_out:u128)->Result<u128> {
    let numerator=amount_in.checked_mul(reserve_out).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad(3): aligns the next Source site with the original line


    let denominator=reserve_in.checked_add(amount_in).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad(1): aligns the next Source site with the original line
    numerator.checked_div(denominator).ok_or_else(||error!(PumpError::DivisionByZero))
}

pub use crate::tokens_for_quote;




