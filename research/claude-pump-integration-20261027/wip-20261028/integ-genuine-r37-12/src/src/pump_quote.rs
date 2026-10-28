//! Quote reserve math recovered as its own module (programs/pump/src/pump_quote.rs).
use crate::{Global, PumpError};
use crate::create_v2::nested_create::{Record, overflow};
use anchor_lang::prelude::*;
fn constant_product(base: u64, quote: u128, amount: u128) -> Result<u128> {
    require!(quote != 0, PumpError::DivisionByZero);
    let denominator = quote.checked_add(amount).ok_or_else(overflow)?;
    let numerator = (base as u128).checked_mul(amount).ok_or_else(overflow)?;
    require!(denominator != 0, PumpError::DivisionByZero);
    Ok(numerator / denominator)
}
fn convert(record: Record, amount: u128) -> Result<u128> {
    match record {
        Record::Pool { base, quote } => constant_product(base, quote, amount),
        Record::Curve { vt, vq, rt, rq, pool_base, migration_fee } => {
            let output = constant_product(vt, vq as u128, amount)?;
            if output <= rt as u128 { return Ok(output); }
            let numerator = rt as u128 * vq as u128;
            let denominator = vt.checked_sub(rt).ok_or_else(overflow)?;
            require!(denominator != 0, PumpError::DivisionByZero);
            // Bounded u64 operands guarantee that this floor-plus-one fits u128.
            let completion = numerator / denominator as u128 + 1;
            let remainder = amount.saturating_sub(completion);
            if remainder <= 1 { return Ok(rt as u128); }
            let pool_quote = (completion + rq as u128).checked_sub(migration_fee as u128).ok_or_else(|| error!(PumpError::Overflow))?;
            let extra = constant_product(pool_base, pool_quote, remainder - 1)?;
            (rt as u128).checked_add(extra).ok_or_else(|| error!(PumpError::Overflow))
        }
    }
}
pub(crate) fn price(g: &Global, seed: u64, records: &[Record]) -> Result<u64> {
    let real = g.initial_real_token_reserves;
    let numerator = real as u128 * seed as u128;
    let difference = g.initial_virtual_token_reserves.checked_sub(real).ok_or_else(overflow)?;
    require!(difference != 0, PumpError::DivisionByZero);
    let mut amount = numerator / difference as u128;
    for record in records.iter().rev() { amount = convert(*record, amount)?; }
    let difference = g.initial_virtual_token_reserves.checked_sub(real).ok_or_else(overflow)?;
    let numerator = amount.checked_mul(difference as u128).ok_or_else(overflow)?;
    require!(real != 0, PumpError::DivisionByZero);
    let reserves = u64::try_from(numerator / real as u128).map_err(|_| overflow())?;
    require_gte!(reserves, 1, PumpError::QuoteReservesOutOfRange);
    Ok(reserves)
}
