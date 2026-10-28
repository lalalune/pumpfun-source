//! Semantics recovered from Pump function 0x880b0..0x88908.
//! This arithmetic fragment does not implement its enclosing trade handler.
#![no_std]

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u32)]
pub enum ArithmeticError {
    Overflow = 6024,
    DivisionByZero = 6026,
}

#[no_mangle]
pub fn constant_product_output(amount_in: u128, reserve_in: u128, reserve_out: u128)
    -> Result<u128, ArithmeticError>
{
    let numerator = amount_in.checked_mul(reserve_out).ok_or(ArithmeticError::Overflow)?;
    let denominator = reserve_in.checked_add(amount_in).ok_or(ArithmeticError::Overflow)?;
    numerator.checked_div(denominator).ok_or(ArithmeticError::DivisionByZero)
}
