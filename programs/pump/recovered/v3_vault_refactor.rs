//! Native model of the two code paths that PR #1554 restructures.
//!
//! * `buy_payment`: the user quote payment in `trade_v3::v3_execute_buy`.
//!   `pool_quote` is the quote, protocol fee and creator fee of the curve fill
//!   plus the same three amounts of an optional post-complete fill, minus the
//!   buyback share. The buyback share goes to the buyback fee recipient.
//!   On the SOL path the user pays `pool_quote + total_buyback` lamports to the
//!   curve and the curve pays `total_buyback` out. On the token path the user
//!   pays `pool_quote` tokens to the curve vault and `total_buyback` tokens to
//!   the recipient's token account. Both paths move the same amounts; only the
//!   accounts differ. Token-2022 transfer fees are not modelled.
//! * `admit_vaults`: curve-hop vault admission in
//!   `multi_hop_curve_swap::transfer_input`. The base vault address is checked
//!   first. A native quote vault is then checked by address only; a token
//!   quote vault goes through `buy_v2::admit_associated_token_account` with
//!   creation disabled. A wrong address is Anchor `ConstraintSeeds` (2006);
//!   a token quote vault at the right address that does not exist yet is
//!   `AccountNotInitialized` (3012). An absent native quote vault passes.
//!
//! The file is not linked into the SBF crate.

pub const OVERFLOW: u32 = 6024;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Fill {
    pub quote: u64,
    pub protocol_fee: u64,
    pub creator_fee: u64,
    pub buyback_fee: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Payment {
    /// Lamports (SOL path) or quote tokens (token path) leaving the user.
    pub user_out: u64,
    /// Net quote kept by the curve (lamports or vault tokens).
    pub curve_in: u64,
    /// Quote received by the buyback fee recipient.
    pub recipient_in: u64,
}

fn gross(fill: &Fill) -> Result<u64, u32> {
    fill.quote
        .checked_add(fill.protocol_fee)
        .and_then(|v| v.checked_add(fill.creator_fee))
        .ok_or(OVERFLOW)
}

pub fn buy_payment(curve: Fill, post: Option<Fill>) -> Result<Payment, u32> {
    let total_buyback = curve
        .buyback_fee
        .checked_add(post.map_or(0, |p| p.buyback_fee))
        .ok_or(OVERFLOW)?;
    let first = gross(&curve)?;
    let second = match post {
        Some(p) => gross(&p)?,
        None => 0,
    };
    let pool_quote = first
        .checked_add(second)
        .and_then(|v| v.checked_sub(total_buyback))
        .ok_or(OVERFLOW)?;
    let user_out = pool_quote.checked_add(total_buyback).ok_or(OVERFLOW)?;
    Ok(Payment { user_out, curve_in: pool_quote, recipient_in: total_buyback })
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rejection {
    BaseVault,
    NativeQuoteVault,
    TokenQuoteVault,
    TokenQuoteVaultMissing,
}

/// The curve quote vault passed to the hop.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum QuoteVault {
    /// Not the curve's associated token account address.
    WrongAddress,
    /// The right address, holding an account.
    Ready,
    /// The right address, but still a system account (never created).
    Absent,
}

pub fn admit_vaults(native: bool, base_ok: bool, quote: QuoteVault) -> Result<(), Rejection> {
    if !base_ok {
        return Err(Rejection::BaseVault);
    }
    match quote {
        QuoteVault::WrongAddress => {
            Err(if native { Rejection::NativeQuoteVault } else { Rejection::TokenQuoteVault })
        }
        QuoteVault::Absent if !native => Err(Rejection::TokenQuoteVaultMissing),
        _ => Ok(()),
    }
}

pub fn rejection_code(r: Rejection) -> u32 {
    match r {
        Rejection::TokenQuoteVaultMissing => ACCOUNT_NOT_INITIALIZED,
        _ => CONSTRAINT_SEEDS,
    }
}

/// Source line named by the AnchorError log of each rejection, in the
/// original's embedded paths. The base and native-quote checks share one
/// `require_ata` line, so their order is not visible from the log.
pub fn rejection_site(r: Rejection) -> &'static str {
    match r {
        Rejection::BaseVault | Rejection::NativeQuoteVault => "programs/pump/src/multi_hop_curve_swap.rs:369",
        Rejection::TokenQuoteVault => "programs/pump/src/buy_v2.rs:55",
        Rejection::TokenQuoteVaultMissing => "programs/pump/src/buy_v2.rs:60",
    }
}
