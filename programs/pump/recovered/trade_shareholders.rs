//! Captured read of the optional `sharing_config` account by Pump `sell_v2`,
//! `buy_v2` and `buy_exact_quote_in_v2`: what ends up in `TradeEvent.shareholders`.
//!
//! The account has its address checked and nothing else. The trade prices,
//! pays and stores the same whatever it holds; only the event list and, for a
//! long list, the heap limit depend on the bytes.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_trade_shareholders_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): `largest_list` on any other
//! fixture. The limit is the bump heap left at the event, so it moves with the
//! fee tiers stored in FeeConfig and with cashback curves. Lists at the limit
//! of a completing buy were only run on a token quote `buy_v2`.

/// Anchor `ConstraintSeeds`, for a `sharing_config` at any other address.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// First 8 bytes of sha256(`account:SharingConfig`).
pub const DISCRIMINATOR: [u8; 8] = [216, 74, 9, 0, 56, 140, 93, 75];
/// `discriminator`, `bump`, `version`.
const STATUS_AT: usize = 10;
/// `status`, `mint`, `admin` follow.
const ADMIN_REVOKED_AT: usize = 75;
const COUNT_AT: usize = 76;
const LIST_AT: usize = 80;
/// `address`, `share_bps`.
const ROW: usize = 34;
/// The decoded list starts at 120 rows and doubles once. The 241st row asks for
/// more than the heap has left, on every route, whether or not the list ends
/// up decoding.
pub const DECODE_ROWS: usize = 240;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Op {
    Sell,
    Buy,
    ExactQuote,
}

/// Which route the trade takes.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Family {
    /// A quote on SPL Token, wSOL included.
    Token,
    Token2022,
    Native,
    /// The whitelisted user on a Mayhem SPL token quote curve.
    Whitelisted,
    /// The whitelisted user on a native Mayhem curve.
    WhitelistedNative,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Shareholder {
    pub address: [u8; 32],
    pub share_bps: u16,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum Outcome {
    /// The trade succeeds and the event carries this list.
    Listed(Vec<Shareholder>),
    /// The event does not fit in the heap: a panic that undoes the trade.
    OutOfMemory,
    Refused(u32),
    /// The trade fails on its own, with the same code as without a config.
    TradeFailed,
}

/// The list the program reads, or `None` when the read itself runs out of
/// heap. Any data that does not decode reads as empty:
/// a short account, another discriminator, a status past `Active`, an
/// `admin_revoked` byte past 1, or a count past the rows present. The bump,
/// version, mint, admin and share values are not checked, nor is the owner,
/// and bytes after the last row are ignored.
pub fn read_shareholders(data: &[u8]) -> Option<Vec<Shareholder>> {
    if data.len() < LIST_AT || data[..8] != DISCRIMINATOR {
        return Some(Vec::new());
    }
    if data[STATUS_AT] > 1 || data[ADMIN_REVOKED_AT] > 1 {
        return Some(Vec::new());
    }
    let count = u32::from_le_bytes(data[COUNT_AT..LIST_AT].try_into().unwrap()) as usize;
    let rows = &data[LIST_AT..];
    let present = rows.len() / ROW;
    if count > DECODE_ROWS && present > DECODE_ROWS {
        return None;
    }
    if count > present {
        return Some(Vec::new());
    }
    let list = rows
        .chunks_exact(ROW)
        .take(count)
        .map(|row| Shareholder {
            address: row[..32].try_into().unwrap(),
            share_bps: u16::from_le_bytes([row[32], row[33]]),
        })
        .collect();
    Some(list)
}

/// The longest list whose event still fits, on the fixture of the test.
pub fn largest_list(op: Op, family: Family, complete: bool) -> usize {
    if complete {
        return 48;
    }
    match (family, op) {
        (Family::Token, Op::Sell) => 56,
        (Family::Token, Op::Buy) => 51,
        (Family::Token, Op::ExactQuote) => 50,
        (Family::Token2022, Op::Sell) => 55,
        (Family::Token2022, _) => 50,
        (Family::Native, Op::Sell) => 66,
        (Family::Native, Op::Buy) => 56,
        (Family::Native, Op::ExactQuote) => 55,
        (Family::Whitelisted, Op::Sell) => 71,
        (Family::WhitelistedNative, Op::Sell) => 74,
        (Family::Whitelisted | Family::WhitelistedNative, _) => 66,
    }
}

/// `trade_fails`: the same trade fails with no config present. A long list
/// costs nothing then, because the list is only read for the event.
pub fn trade(op: Op, family: Family, complete: bool, key_ok: bool, trade_fails: bool, data: &[u8]) -> Outcome {
    if !key_ok {
        return Outcome::Refused(CONSTRAINT_SEEDS);
    }
    if trade_fails {
        return Outcome::TradeFailed;
    }
    match read_shareholders(data) {
        Some(rows) if rows.len() <= largest_list(op, family, complete) => Outcome::Listed(rows),
        _ => Outcome::OutOfMemory,
    }
}

/// `TradeEvent.shareholders` as Borsh writes it.
pub fn encode(rows: &[Shareholder]) -> Vec<u8> {
    let mut out = (rows.len() as u32).to_le_bytes().to_vec();
    for row in rows {
        out.extend_from_slice(&row.address);
        out.extend_from_slice(&row.share_bps.to_le_bytes());
    }
    out
}
