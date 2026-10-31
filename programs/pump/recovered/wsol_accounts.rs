//! Lamports of a wrapped-SOL token account across Pump calls on a curve whose
//! stored `quote_mint` is the wrapped-SOL mint.
//!
//! Such a curve takes the token routes, so `v2_token_quote.rs`, `sweep_fees.rs`
//! and `creator_fee_distribution_quote.rs` give its amounts. Their fixtures
//! hold plain token accounts with a fixed balance. A real wrapped-SOL account
//! carries `is_native` with its rent reserve, and SPL Token moves lamports with
//! every token move. Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_wsol_accounts_captured.py`. Not linked into the SBF crate. This
//! is not a byte-identity claim.
//!
//! Observed rules:
//! - The amounts, stops, events and stored state are those of the plain
//!   fixtures: Pump reads the token amount and never the lamports.
//! - After a call, every wrapped-SOL account of the call holds its reserve
//!   plus its token amount, plus any lamports it held beyond those before.
//! - Lamports sent to the account without a sync stay out of the amount, so
//!   they do not price a trade, count as reserves or leave with a sweep.
//! - A token account created by a call carries the reserve of 2,039,280 and
//!   nothing else.

pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;

/// `(lamports, reserve)` of the account after a call.
pub fn settled(reserve: Option<u64>, amount: u64, unsynced: u64) -> Option<(u64, u64)> {
    let reserve = reserve.unwrap_or(TOKEN_ACCOUNT_RENT);
    Some((reserve.checked_add(amount)?.checked_add(unsynced)?, reserve))
}
