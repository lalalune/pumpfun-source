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

#[inline(never)]
pub fn tokens_for_quote(curve:&crate::trade_types::BondingCurve,quote:u64)->Result<u128>{
    let effective=quote.checked_sub(1).ok_or(PumpError::Overflow)?;
    output(effective as u128,curve.virtual_quote_reserves as u128,curve.virtual_token_reserves as u128)
}
