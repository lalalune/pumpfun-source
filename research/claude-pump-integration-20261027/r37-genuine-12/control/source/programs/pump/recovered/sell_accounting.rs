//! Partial SOL sell-v3 accounting model; excludes quote-token extensions/rewards.
#![no_std]
#[derive(Debug, Clone, Copy)]
#[repr(u32)]
pub enum AccountingError { Overflow = 6024, Truncation = 6025 }
#[derive(Debug, Clone, Copy)]
pub struct SellAmounts {
    pub protocol_fee: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
    pub user_output: u64,
    pub retained_protocol_fee: u64,
}
fn ceil_fee(amount: u64, bps: u64) -> Result<u64, AccountingError> {
    let result = (amount as u128 * bps as u128 + 9999) / 10000;
    u64::try_from(result).map_err(|_| AccountingError::Truncation)
}
pub fn sell_accounting(quote_out: u64, protocol_bps: u64, creator_bps: u64,
                       buyback_share_bps: u64) -> Result<SellAmounts, AccountingError> {
    let protocol_fee = ceil_fee(quote_out, protocol_bps)?;
    let creator_fee = ceil_fee(quote_out, creator_bps)?;
    let buyback_fee = u64::try_from(protocol_fee as u128 * buyback_share_bps as u128 / 10000)
        .map_err(|_| AccountingError::Truncation)?;
    let user_output = quote_out.checked_sub(protocol_fee)
        .and_then(|x| x.checked_sub(creator_fee)).ok_or(AccountingError::Overflow)?;
    let retained_protocol_fee = protocol_fee.checked_sub(buyback_fee).ok_or(AccountingError::Overflow)?;
    Ok(SellAmounts { protocol_fee, creator_fee, buyback_fee, user_output, retained_protocol_fee })
}
