use anchor_lang::prelude::*;

/// Shared checked ceiling division, preserving addition/subtraction/division order.
#[inline(never)]
pub fn checked_ceil_div(numerator: u128, denominator: u128) -> Result<u128> {
    let sum = numerator.checked_add(denominator)
        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
    let adjusted = sum.checked_sub(1)
        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
    adjusted.checked_div(denominator)
        .ok_or_else(|| error!(crate::PumpError::DivisionByZero))
}

pub fn fee(quote_amount: u64, basis_points: u64) -> Result<u64> {
    let value = checked_ceil_div(u128::from(quote_amount) * u128::from(basis_points), 10000)?;
    u64::try_from(value).map_err(|_| error!(crate::PumpError::Truncation))
}
