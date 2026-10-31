//! Pool records in a `create_v2` quote chain: a quote curve that is itself
//! quoted by another curve, and the records that price the empty ones.
//!
//! `create_v2.rs` walks one quote curve and stops there: a curve stored with
//! depth other than zero answers `QuoteChainAccountsRequired` (6109), and an
//! empty curve answers `QuotePoolAccountsRequired` (6101). `create_v2_quote_pool.rs`
//! prices one empty curve from its pool record, at the root of a one-curve
//! chain. This model walks the whole chain. The passed curve's stored depth
//! says how many curves stand under it: the walk consumes exactly that many
//! more curves, each the bonding curve of the previous curve's root mint, in
//! the order `[curve, record, curve, record, ...]` in the remaining accounts,
//! and the last curve is the root whatever its stored depth byte says.
//!
//! At each curve, in this order: the outermost curve's depth gate (6105) and
//! mayhem byte (6100) are read first — the inner curves' mayhem and depth
//! bytes are not read at all. An empty curve's record is required (6101 when
//! fewer than four accounts remain from the curve) and validated (6102/6103,
//! as in `create_v2_quote_pool.rs`) before the walk goes deeper; a non-empty
//! curve that is complete answers 6107; a missing next curve is 6109 and a
//! next curve that is not the canonical bonding curve of the root mint, or
//! does not decode, is 6099. The root curve's own root is resolved when the
//! walk reaches it, ahead of its record check: it seeds the price from SOL,
//! the whitelisted mint, or a `QuoteControl` listing, and an unlisted root
//! is 6100.
//!
//! The record accounts are read positionally from the one stream of
//! remaining accounts: when the stream runs on past a short record, the
//! following accounts fill the pool and vault slots and fail their checks
//! there (a curve read as a vault answers 6103, for one).
//!
//! Pricing runs in token amounts, not in seeds: the root seed is converted
//! once, at the root, by `real * seed / (virtual - real)`; each curve
//! outward is priced by the record formula if it is empty or by the
//! nested-curve formula of `create_v2.rs` if it is not, taking the previous
//! curve's token output as its amount with no further conversion; and the
//! outermost output is scaled back by `(virtual - real) / real` into the
//! new curve's virtual quote reserves.
//!
//! Vaults holding Token-2022 extensions change none of this: past the
//! account-type byte at 165 the extension bytes are not read, well-formed or
//! not, and 355 bytes is still refused outright.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_create_v2_pool_chain_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

pub const OVERFLOW: u32 = 6024;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const INVALID_QUOTE_BONDING_CURVE: u32 = 6099;
pub const QUOTE_BONDING_CURVE_NOT_ELIGIBLE: u32 = 6100;
pub const QUOTE_POOL_ACCOUNTS_REQUIRED: u32 = 6101;
pub const QUOTE_POOL_NOT_FOUND: u32 = 6102;
pub const INVALID_QUOTE_POOL: u32 = 6103;
pub const QUOTE_RESERVES_OUT_OF_RANGE: u32 = 6104;
pub const CURVE_DEPTH_EXCEEDED: u32 = 6105;
pub const QUOTE_CURVE_AWAITING_MIGRATION: u32 = 6107;
pub const QUOTE_CHAIN_ACCOUNTS_REQUIRED: u32 = 6109;

/// The `Global` fields the walk reads.
pub struct Global {
    pub initial_virtual_token_reserves: u64,
    pub initial_virtual_sol_reserves: u64,
    pub initial_real_token_reserves: u64,
    pub initial_virtual_quote_reserves: u64,
    pub pool_migration_fee: u64,
    pub max_curve_depth: u8,
}

/// What seeds the price at the root curve.
#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Root {
    Sol,
    Whitelisted,
    Listed(u64),
    Unlisted,
}

/// One curve of the chain, as stored.
#[derive(Clone, Copy, Debug)]
pub struct Curve {
    pub depth: u8,
    pub mayhem: bool,
    pub complete: bool,
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub token_total_supply: u64,
    pub root: Root,
    /// Accounts past the first are the canonical curve of the previous
    /// curve's root mint and decode as a bonding curve.
    pub valid: bool,
}

impl Curve {
    fn empty(&self) -> bool {
        self.real_quote_reserves == 0
            && self.virtual_quote_reserves == 0
            && self.real_token_reserves == 0
            && self.virtual_token_reserves == 0
    }
}

/// A pool's vault, as in `create_v2_quote_pool.rs`. Extension bytes past the
/// account-type byte are not an input: the program does not read them.
#[derive(Clone, Copy, Debug)]
pub struct Vault {
    pub owner_ok: bool,
    pub len: usize,
    pub state: u8,
    pub account_type: u8,
    pub amount: u64,
}

/// One level's pool record. `tail` counts the accounts from this curve to
/// the end of the remaining accounts, the curve itself included: fewer than
/// four means the pool and its two vaults are not all there. The vault
/// fields describe the accounts the walk reads in the vault slots, which
/// are the record's own vaults unless the stream ran on past a short record.
#[derive(Clone, Copy, Debug)]
pub struct Record {
    pub tail: usize,
    pub key_ok: bool,
    pub owner_ok: bool,
    pub len: usize,
    pub discriminator_ok: bool,
    pub base_key_ok: bool,
    pub quote_key_ok: bool,
    pub base: Vault,
    pub quote: Vault,
    pub adjustment: i128,
}

fn vault_amount(v: &Vault) -> Result<u64, u32> {
    if !v.owner_ok || v.len < 165 || v.len == 355 || v.state != 1 {
        return Err(INVALID_QUOTE_POOL);
    }
    if v.len != 165 && v.account_type != 2 {
        return Err(INVALID_QUOTE_POOL);
    }
    Ok(v.amount)
}

/// The record's shape checks, in their order, without the pricing.
fn validate_record(r: &Record) -> Result<(u64, u128), u32> {
    if r.tail < 4 {
        return Err(QUOTE_POOL_ACCOUNTS_REQUIRED);
    }
    if !r.key_ok {
        return Err(INVALID_QUOTE_POOL);
    }
    if !r.owner_ok {
        return Err(QUOTE_POOL_NOT_FOUND);
    }
    if r.len < 211 || !r.discriminator_ok || !r.base_key_ok || !r.quote_key_ok {
        return Err(INVALID_QUOTE_POOL);
    }
    let base = vault_amount(&r.base)?;
    let quote = vault_amount(&r.quote)?;
    let adjustment = if r.len >= 261 { r.adjustment } else { 0 };
    let quote = (quote as i128).checked_add(adjustment).and_then(|v| u128::try_from(v).ok()).ok_or(OVERFLOW)?;
    Ok((base, quote))
}

/// `amount_in * base / (quote + amount_in)`.
fn constant_product(base: u64, quote: u128, amount: u128) -> Result<u128, u32> {
    if quote == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    let denominator = quote.checked_add(amount).ok_or(OVERFLOW)?;
    let numerator = (base as u128).checked_mul(amount).ok_or(OVERFLOW)?;
    Ok(numerator / denominator)
}

/// The record formula of `create_v2_quote_pool.rs`, in token amounts.
fn record_amount(base: u64, quote: u128, amount: u128) -> Result<u128, u32> {
    constant_product(base, quote, amount)
}

/// The nested-curve formula of `create_v2.rs`, in token amounts: the
/// constant product against the curve's stored reserves, with the
/// completion branch when the output passes the real token reserves.
fn nested_amount(q: &Curve, amount: u128, g: &Global) -> Result<u128, u32> {
    let pool_base = q.token_total_supply.checked_sub(g.initial_real_token_reserves).ok_or(OVERFLOW)?;
    let (vt, vq, rt) = (q.virtual_token_reserves as u128, q.virtual_quote_reserves as u128, q.real_token_reserves as u128);
    let mut output = constant_product(q.virtual_token_reserves, vq, amount)?;
    if output > rt {
        let denominator = vt.checked_sub(rt).ok_or(OVERFLOW)?;
        if denominator == 0 {
            return Err(DIVISION_BY_ZERO);
        }
        let completion = rt * vq / denominator + 1;
        let remainder = amount.saturating_sub(completion);
        output = rt;
        if remainder > 1 {
            let migration_fee = if q.root == Root::Sol { g.pool_migration_fee as u128 } else { 0 };
            let pool_quote = (completion + q.real_quote_reserves as u128).checked_sub(migration_fee).ok_or(OVERFLOW)?;
            output = rt.checked_add(constant_product(pool_base, pool_quote, remainder - 1)?).ok_or(OVERFLOW)?;
        }
    }
    Ok(output)
}

/// Price a create whose quote mint's curve is `curves[0]`. `curves` and
/// `records` describe the accounts actually passed: `curves[i]` for `i > 0`
/// is the account passed as the next curve, `records[i]` the record accounts
/// passed after `curves[i]` (absent when none were). Returns the new curve's
/// virtual quote reserves and its depth.
pub fn price(g: &Global, curves: &[Curve], records: &[Option<Record>]) -> Result<(u64, u8), u32> {
    let head = curves[0];
    let depth = head.depth.checked_add(1).ok_or(OVERFLOW)?;
    if depth > g.max_curve_depth.min(5) {
        return Err(CURVE_DEPTH_EXCEEDED);
    }
    if head.mayhem {
        return Err(QUOTE_BONDING_CURVE_NOT_ELIGIBLE);
    }
    // Descend to the root curve, validating each level as it is read. The
    // root curve's own root is resolved when the walk reaches it, ahead of
    // its record or completion checks, as in `create_v2.rs`'s walk.
    let mut validated: Vec<Option<(u64, u128)>> = Vec::new();
    let mut seed = 0;
    for i in 0..=head.depth as usize {
        if i >= curves.len() {
            return Err(QUOTE_CHAIN_ACCOUNTS_REQUIRED);
        }
        let curve = &curves[i];
        if i > 0 && !curve.valid {
            return Err(INVALID_QUOTE_BONDING_CURVE);
        }
        if i == head.depth as usize {
            seed = match curve.root {
                Root::Sol => g.initial_virtual_sol_reserves,
                Root::Whitelisted => g.initial_virtual_quote_reserves,
                Root::Listed(reserves) => reserves,
                Root::Unlisted => return Err(QUOTE_BONDING_CURVE_NOT_ELIGIBLE),
            };
        }
        if curve.empty() {
            let record = records.get(i).copied().flatten().ok_or(QUOTE_POOL_ACCOUNTS_REQUIRED)?;
            validated.push(Some(validate_record(&record)?));
        } else {
            if curve.complete {
                return Err(QUOTE_CURVE_AWAITING_MIGRATION);
            }
            validated.push(None);
        }
    }
    // Price from the root curve outward, in token amounts: the seed is
    // converted once here, each level's output is the next level's amount,
    // and the outermost output is scaled back into quote reserves.
    let real = g.initial_real_token_reserves as u128;
    let difference = (g.initial_virtual_token_reserves as u128).checked_sub(real).ok_or(OVERFLOW)?;
    let mut amount = (real * seed as u128).checked_div(difference).ok_or(DIVISION_BY_ZERO)?;
    for i in (0..=head.depth as usize).rev() {
        amount = match validated[i] {
            Some((base, quote)) => record_amount(base, quote, amount)?,
            None => nested_amount(&curves[i], amount, g)?,
        };
    }
    let scaled = amount.checked_mul(difference).ok_or(OVERFLOW)?.checked_div(real).ok_or(DIVISION_BY_ZERO)?;
    let reserves = u64::try_from(scaled).map_err(|_| OVERFLOW)?;
    if reserves == 0 {
        return Err(QUOTE_RESERVES_OUT_OF_RANGE);
    }
    Ok((reserves, depth))
}
