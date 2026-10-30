//! Quote reserve math recovered as its own module (programs/pump/src/pump_quote.rs).
use crate::trade_types::BondingCurve;
use crate::{Global, PumpError};
use anchor_lang::prelude::*;
pub const AMM: Pubkey = anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const POOL_DISC: [u8; 8] = [241, 154, 109, 4, 17, 177, 109, 188];
#[derive(Clone, Copy)]
pub enum Record {
    Pool { base: u64, quote: u128 },
    Curve { vt: u64, vq: u64, rt: u64, rq: u64, pool_base: u64, migration_fee: u64 },
}
















































pub fn depth(curve: &BondingCurve, g: &Global) -> Result<u8> {
    let depth = curve.depth.checked_add(1).ok_or_else(|| error!(PumpError::Overflow))?;
    require_gte!(g.max_curve_depth.min(5), depth, PumpError::CurveDepthExceeded);
    Ok(depth)
}













pub(crate) fn global_quote(quote: Pubkey, g: &Global) -> bool {
    quote == Pubkey::default() || quote == anchor_spl::token::spl_token::native_mint::ID || g.whitelisted_quote_mints.contains(&quote)
}

pub fn root_seed(curve: &BondingCurve, g: &Global, control: &[u8]) -> Result<u64> {
    if curve.quote_mint == Pubkey::default() {
        return Ok(g.initial_virtual_sol_reserves);
    }
    if global_quote(curve.quote_mint, g) {
        return Ok(g.initial_virtual_quote_reserves);
    }
    crate::quote_control::state::control_entry(control, &curve.quote_mint)?
        .ok_or_else(|| error!(PumpError::QuoteBondingCurveNotEligible))
}









pub fn initial_amount(seed: u64, g: &Global) -> Result<u128> {
    let real = g.initial_real_token_reserves as u128;
    let numerator = real * seed as u128;
    let difference = (g.initial_virtual_token_reserves as u128).checked_sub(real).ok_or_else(|| error!(PumpError::Overflow))?;

    let amount = numerator.checked_div(difference).ok_or_else(|| error!(PumpError::DivisionByZero))?;
    Ok(amount)
}





pub fn final_reserves(amount: u128, g: &Global) -> Result<u64> {
    let real = g.initial_real_token_reserves as u128;
    let virt = g.initial_virtual_token_reserves as u128;
    let difference = virt.checked_sub(real).ok_or_else(|| error!(PumpError::Overflow))?;

    let numerator = amount.checked_mul(difference).ok_or_else(|| error!(PumpError::Overflow))?;

    let quotient = numerator.checked_div(real).ok_or_else(|| error!(PumpError::DivisionByZero))?;
    u64::try_from(quotient).map_err(|_| error!(PumpError::Overflow))
}






pub fn constant_product(base: u64, quote: u128, amount: u128) -> Result<u128> {
    require!(quote != 0, PumpError::DivisionByZero);


    let denominator = quote.checked_add(amount).ok_or_else(|| error!(PumpError::Overflow))?;


    let numerator = (base as u128).checked_mul(amount).ok_or_else(|| error!(PumpError::Overflow))?;

    require!(denominator != 0, PumpError::DivisionByZero);
    Ok(numerator / denominator)
}
pub fn convert(record: &Record, amount: u128) -> Result<u128> {
    match *record {
        Record::Pool { base, quote } => constant_product(base, quote, amount),
        Record::Curve { vt, vq, rt, rq, pool_base, migration_fee } => {
            let output = constant_product(vt, vq as u128, amount)?;
            if output > rt as u128 {
            let numerator = rt as u128 * vq as u128;
            let denominator = (vt as u128).checked_sub(rt as u128);

















































            let denominator = denominator.ok_or_else(|| error!(PumpError::Overflow))?;

            require!(denominator != 0, PumpError::DivisionByZero);
            let completion = numerator / denominator + 1;
            let remainder = amount.saturating_sub(completion);
            if remainder > 1 {







                let pool_quote = (completion + rq as u128).checked_sub(migration_fee as u128).ok_or_else(|| error!(PumpError::Overflow))?;
                let extra = constant_product(pool_base, pool_quote, remainder - 1)?;








                return (rt as u128).checked_add(extra).ok_or_else(|| error!(PumpError::Overflow));
            }
            Ok(rt as u128) } else { Ok(output) }
        }
    }
}









pub fn price(seed: u64, records: &[Record], g: &Global) -> Result<u64> {
    let mut amount = initial_amount(seed, g)?;
    for record in records.iter().rev() { amount = convert(record, amount)?; }
    let reserves = final_reserves(amount, g)?;
    require_gte!(reserves, 1, PumpError::QuoteReservesOutOfRange);
    Ok(reserves)
}
pub struct View<'a> {
    pub key: &'a Pubkey,
    pub owner: &'a Pubkey,
    pub data: &'a [u8],
}
pub struct PoolState {
    pub base_vault: Pubkey,
    pub quote_vault: Pubkey,
    pub adjustment: i128,
}
























pub fn parse_pool(data: &[u8]) -> Result<PoolState> {
    let header = data.get(..211).ok_or_else(|| error!(PumpError::InvalidQuotePool))?;
    require!(header.starts_with(&POOL_DISC), PumpError::InvalidQuotePool);
    let adjustment = if data.len() >= 261 {
        i128::from_le_bytes(data[245..261].try_into().map_err(|_| error!(PumpError::InvalidQuotePool))?)
    } else { 0 };
    Ok(PoolState { base_vault: read_pubkey(header, 139)?, quote_vault: read_pubkey(header, 171)?, adjustment })
}




















pub fn read_pubkey(data: &[u8], offset: usize) -> Result<Pubkey> {
    let bytes: [u8; 32] = data.get(offset..offset.wrapping_add(32)).and_then(|b| b.try_into().ok()).ok_or_else(|| error!(PumpError::InvalidQuotePool))?;
    Ok(Pubkey::new_from_array(bytes))
}























pub fn adjusted_quote(amount: u64, adjustment: i128) -> Result<u128> {
    (amount as i128).checked_add(adjustment).and_then(|v| u128::try_from(v).ok()).ok_or_else(|| error!(PumpError::Overflow))
}




























pub fn vault_amount(owner: &Pubkey, data: &[u8]) -> Result<u64> {
    require!([&anchor_spl::token::ID, &anchor_spl::token_2022::ID].iter().any(|id| owner == *id), PumpError::InvalidQuotePool);
    require_gte!(data.len(), 165usize, PumpError::InvalidQuotePool);




    require_neq!(data.len(), 355usize, PumpError::InvalidQuotePool);
    require_eq!(data[108], 1u8, PumpError::InvalidQuotePool);
    if data.len() == 165 { return Ok(u64::from_le_bytes(data[64..72].try_into().unwrap_or_default())); }




    require_eq!(data[165], 2u8, PumpError::InvalidQuotePool);
    Ok(u64::from_le_bytes(data[64..72].try_into().unwrap_or_default()))
}
























pub fn validate_pool(pool: &View<'_>, expected: &Pubkey, base: &View<'_>, quote: &View<'_>) -> Result<(u64, u128)> {
    require_keys_eq!(*pool.key, *expected, PumpError::InvalidQuotePool);
    require_keys_eq!(*pool.owner, AMM, PumpError::QuotePoolNotFound);
    let state = parse_pool(pool.data)?;

    require_keys_eq!(*base.key, state.base_vault, PumpError::InvalidQuotePool);




    require_keys_eq!(*quote.key, state.quote_vault, PumpError::InvalidQuotePool);
    let base_amount = vault_amount(base.owner, base.data)?;
    let quote_amount = vault_amount(quote.owner, quote.data)?;
    let quote_reserves = adjusted_quote(quote_amount, state.adjustment)?;
    Ok((base_amount, quote_reserves))
}
pub fn pool_record(pool: &AccountInfo<'_>, expected: &Pubkey, base: &AccountInfo<'_>,
    quote: &AccountInfo<'_>) -> Result<(u64, u128)> {
    let pool_data = pool.try_borrow_data()?;
    let base_data = base.try_borrow_data()?;
    let quote_data = quote.try_borrow_data()?;
    validate_pool(&View { key: pool.key, owner: pool.owner, data: &pool_data }, expected,
        &View { key: base.key, owner: base.owner, data: &base_data },
        &View { key: quote.key, owner: quote.owner, data: &quote_data })
}
