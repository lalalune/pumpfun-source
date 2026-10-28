//! Source hypothesis for the create-linked ancestor walk; see the publication ledger.
//! Numeric/local contracts are recovered. Framework error payloads and runtime ABI
//! remain conditional; these are natural Rust types, not an original memory layout.
use crate::{Global, PumpError};
use crate::trade_types::BondingCurve;
use anchor_lang::prelude::*;

const CURVE_DISC: [u8; 8] = [23, 183, 248, 55, 96, 216, 172, 96];
const POOL_DISC: [u8; 8] = [241, 154, 109, 4, 17, 177, 109, 188];
use crate::quote_control::state::control_entry;
const AMM: Pubkey = anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");

#[derive(Clone, Copy)]
enum Record {
    Curve { vt: u64, vq: u64, rt: u64, rq: u64, pool_base: u64, migration_fee: u64 },
    Pool { base: u64, quote: u128 },
}

fn overflow() -> anchor_lang::error::Error { error!(PumpError::Overflow) }
fn u64_at(data: &[u8], at: usize) -> u64 {
    u64::from_le_bytes(data[at..at + 8].try_into().unwrap())
}
fn key_at(data: &[u8], at: usize) -> Pubkey {
    Pubkey::new_from_array(data[at..at + 32].try_into().unwrap())
}

// The captured ancestor reader calls the shared checked historical decoder.
fn decode_curve(data: &[u8]) -> Result<BondingCurve> {
    BondingCurve::try_deserialize(&mut &data[..])
        .map_err(|_| error!(PumpError::InvalidQuoteBondingCurve))
}

fn ancestor(account: &AccountInfo<'_>, mint: &Pubkey) -> Result<BondingCurve> {
    let expected = Pubkey::find_program_address(&[b"bonding-curve", mint.as_ref()], &crate::ID).0;
    require_keys_eq!(account.key(), expected, PumpError::InvalidQuoteBondingCurve);
    require_keys_eq!(*account.owner, crate::ID, PumpError::InvalidQuoteBondingCurve);
    let data = account.try_borrow_data()?;
    decode_curve(&data)
}

#[inline(never)]
pub(super) fn control_account(account: &AccountInfo<'_>, mint: &Pubkey) -> Result<Option<u64>> {
    let data = account.try_borrow_data()?;
    control_entry(&data, mint)
}

fn root_seed(g: &Global, quote: &Pubkey, control: &[u8]) -> Result<u64> {
    if quote == &Pubkey::default() { return Ok(g.initial_virtual_sol_reserves); }
    if quote == &anchor_spl::token::spl_token::native_mint::id()
        || g.whitelisted_quote_mints.contains(quote) {
        return Ok(g.initial_virtual_quote_reserves);
    }
    control_entry(control, quote)?.ok_or_else(|| error!(PumpError::QuoteBondingCurveNotEligible))
}

fn vault_amount(account: &AccountInfo<'_>, data: &[u8]) -> Result<u64> {
    require!(account.owner == &anchor_spl::token::ID || account.owner == &anchor_spl::token_2022::ID,
        PumpError::InvalidQuotePool);
    require_gte!(data.len(), 165usize, PumpError::InvalidQuotePool);
    require_neq!(data.len(), 355usize, PumpError::InvalidQuotePool);
    require_eq!(data[108], 1u8, PumpError::InvalidQuotePool);
    if data.len() != 165 { require_eq!(data[165], 2u8, PumpError::InvalidQuotePool); }
    Ok(u64_at(data, 64))
}

fn pool_record(mint: &Pubkey, quote: &Pubkey, pool: &AccountInfo<'_>,
    base: &AccountInfo<'_>, quote_vault: &AccountInfo<'_>) -> Result<Record> {
    let authority = Pubkey::find_program_address(&[b"pool-authority", mint.as_ref()], &crate::ID).0;
    let pool_quote = if quote == &Pubkey::default() {
        anchor_spl::token::spl_token::native_mint::id()
    } else { *quote };
    let expected = Pubkey::find_program_address(
        &[b"pool", &0u16.to_le_bytes(), authority.as_ref(), mint.as_ref(), pool_quote.as_ref()], &AMM).0;
    // All three borrows precede key/owner validation; retain their lifetimes.
    let pool_data = pool.try_borrow_data()?;
    let base_data = base.try_borrow_data()?;
    let quote_data = quote_vault.try_borrow_data()?;
    require_keys_eq!(pool.key(), expected, PumpError::InvalidQuotePool);
    require_keys_eq!(*pool.owner, AMM, PumpError::QuotePoolNotFound);
    require!(pool_data.len() >= 211, PumpError::InvalidQuotePool);
    require!(pool_data[..8] == POOL_DISC, PumpError::InvalidQuotePool);
    let base_key = key_at(&pool_data, 139);
    let quote_key = key_at(&pool_data, 171);
    let adjustment = if pool_data.len() >= 261 {
        i128::from_le_bytes(pool_data[245..261].try_into().unwrap())
    } else { 0 };
    require_keys_eq!(base.key(), base_key, PumpError::InvalidQuotePool);
    require_keys_eq!(quote_vault.key(), quote_key, PumpError::InvalidQuotePool);
    let base_amount = vault_amount(base, &base_data)?;
    let quote_amount = vault_amount(quote_vault, &quote_data)?;
    let adjusted = (quote_amount as i128).checked_add(adjustment).ok_or_else(overflow)?;
    require!(adjusted >= 0, PumpError::Overflow);
    Ok(Record::Pool { base: base_amount, quote: adjusted as u128 })
}

pub(super) fn walk(g: &Global, accounts: &[AccountInfo<'_>]) -> Result<(u64, u8)> {
    // Slicing preserves the original <4 bounds failure. The ordinary caller has
    // already admitted the prefix; exactly four is UnsupportedQuoteMint.
    let mut tail = &accounts[4..];
    let first = tail.first().ok_or_else(|| error!(PumpError::UnsupportedQuoteMint))?;
    let mut mint = *accounts[0].key;
    let mut curve = ancestor(first, &mint)?;
    let depth = curve.depth.checked_add(1).ok_or_else(overflow)?;
    require_gte!(g.max_curve_depth.min(5), depth, PumpError::CurveDepthExceeded);
    require!(!curve.is_mayhem_mode, PumpError::QuoteBondingCurveNotEligible);
    // Five logical slots; inactive storage has no Pool tail interpretation.
    let mut records = [Record::Pool { base: 0, quote: 0 }; 5];
    let mut seed = 0;
    for position in 0..usize::from(depth) {
        if position != 0 {
            mint = curve.quote_mint;
            let account = tail.first().ok_or_else(|| error!(PumpError::QuoteChainAccountsRequired))?;
            curve = ancestor(account, &mint)?;
        }
        if position + 1 == usize::from(depth) {
            let control = accounts[3].try_borrow_data()?;
            seed = root_seed(g, &curve.quote_mint, &control)?;
        }
        if curve.virtual_token_reserves == 0 && curve.virtual_quote_reserves == 0
            && curve.real_token_reserves == 0 && curve.real_quote_reserves == 0 {
            require!(tail.len() >= 4, PumpError::QuotePoolAccountsRequired);
            records[position] = pool_record(&mint, &curve.quote_mint, &tail[1], &tail[2], &tail[3])?;
            tail = &tail[4..];
        } else {
            require!(!curve.complete, PumpError::QuoteCurveAwaitingMigration);
            let pool_base = curve.token_total_supply.checked_sub(g.initial_real_token_reserves).ok_or_else(overflow)?;
            records[position] = Record::Curve {
                vt: curve.virtual_token_reserves, vq: curve.virtual_quote_reserves,
                rt: curve.real_token_reserves, rq: curve.real_quote_reserves, pool_base,
                migration_fee: if curve.quote_mint == Pubkey::default() { g.pool_migration_fee } else { 0 },
            };
            tail = &tail[1..];
        }
    }
    // No positional-depth equality, repeated eligibility, or tail-count guard.
    Ok((price(g, seed, &records[..usize::from(depth)])?, depth))
}

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
            let pool_quote = (completion + rq as u128)
                .checked_sub(migration_fee as u128).ok_or_else(overflow)?;
            let extra = constant_product(pool_base, pool_quote, remainder - 1)?;
            (rt as u128).checked_add(extra).ok_or_else(overflow)
        }
    }
}

fn price(g: &Global, seed: u64, records: &[Record]) -> Result<u64> {
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
