//! How the Pump v2 and v3 trade routes (`buy_v2`, `buy_exact_quote_in_v2`,
//! `sell_v2`, `buy_v3`, `buy_exact_quote_in_v3`, `sell_v3`) read a
//! `BondingCurve` account shorter than the current 166 bytes when the pair's
//! quote mint is a token, not native SOL.
//!
//! The short-curve packets cover the trades on native pairs (#3410) and the
//! non-trade callers (#3545, #3776), and the model there leaves the non-zero
//! quote-mint path of the rent top-up unconfirmed: the routes it checked stop
//! those trades first. This file names the same historical shapes for the
//! token-quote routes. A shape reads a prefix of the fields and defaults the
//! rest, so bytes past that prefix are ignored even when the account holds
//! them.
//!
//! The quote mint sits at bytes 83..115, inside the prefix only from 115
//! bytes up. Below 115 the account reads as a native curve whatever quote
//! bytes it holds, and the token-quote routes refuse it with 6004
//! (`MintDoesNotMatchBondingCurve`), exactly as they refuse the full
//! native-reading account. From 115 the stored quote mint is read, the trade
//! proceeds, and the rent top-up holds nothing back: a token-quote curve's
//! reserves and accrued fees are quote tokens, not lamports, so the reserved
//! part of the top-up is zero.
//!
//! Recovered from `evidence/original/pump/deployed.so` and checked against it
//! on LiteSVM by `tests/test_short_curve_quote_captured.py`. The test runs
//! the short account and the full account this file predicts, and every
//! effect of the two runs must agree.
//!
//! Not linked into the SBF crate. This is not a byte-identity claim.

pub const OVERFLOW: u32 = 6024;

pub const CURRENT_LEN: usize = 166;
const COMPLETE: usize = 48;
const CREATOR_END: usize = 81;
const MAYHEM: usize = 81;
const CASHBACK: usize = 82;
const QUOTE_MINT: usize = 83;
const CAN_EDIT_CREATOR_FEE: usize = 123;
const IS_HOLDER_REWARD: usize = 124;
const CREATOR_FEE: usize = 125;
const PROTOCOL_FEES: usize = 133;
const DISCRIMINATOR: [u8; 8] = [23, 183, 248, 55, 96, 216, 172, 96];

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    /// `ProgramError::InvalidAccountData`: below 49 bytes, or the wrong discriminator.
    InvalidAccountData,
    /// A bool byte the shape reads is neither 0 nor 1.
    InvalidBool,
    Code(u32),
}

/// How many leading bytes a shape reads.
fn read_end(len: usize) -> usize {
    match len {
        0..=80 => COMPLETE + 1,
        81 => CREATOR_END,
        82 => MAYHEM + 1,
        83..=114 => CASHBACK + 1,
        115..=123 => QUOTE_MINT + 32,
        124 => CAN_EDIT_CREATOR_FEE + 1,
        125..=140 => IS_HOLDER_REWARD + 1,
        141..=165 => PROTOCOL_FEES + 8,
        _ => CURRENT_LEN,
    }
}

/// The account a short one is read as: the bytes its shape reads, then zeros.
/// An account of 166 bytes or more is itself.
pub fn effective(data: &[u8]) -> Result<Vec<u8>, Stop> {
    if data.len() < COMPLETE + 1 || data[..8] != DISCRIMINATOR {
        return Err(Stop::InvalidAccountData);
    }
    if data.len() >= CURRENT_LEN {
        return bools_ok(data, CURRENT_LEN).map(|_| data.to_vec());
    }
    let end = read_end(data.len());
    bools_ok(data, end)?;
    let mut out = data[..end].to_vec();
    out.resize(CURRENT_LEN, 0);
    Ok(out)
}

fn bools_ok(data: &[u8], end: usize) -> Result<(), Stop> {
    for offset in [COMPLETE, MAYHEM, CASHBACK, CAN_EDIT_CREATOR_FEE, IS_HOLDER_REWARD] {
        if offset < end && data[offset] > 1 {
            return Err(Stop::InvalidBool);
        }
    }
    Ok(())
}

fn rent(len: usize) -> u64 {
    (len as u64 + 128) * 6960
}

fn word(data: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(data[offset..offset + 8].try_into().unwrap())
}

/// Lamports the signer pays into the curve before the handler runs. `image`
/// is the result of `effective`. The reserved part — real reserves plus
/// accrued creator and protocol fees — is held back only when the read quote
/// mint is the all-zero key; a token-quote curve holds those amounts as
/// tokens, so nothing is held back.
pub fn top_up(image: &[u8], curve_lamports: u64) -> Result<u64, Stop> {
    let native = image[QUOTE_MINT..QUOTE_MINT + 32] == [0; 32];
    let reserved = if native {
        word(image, 32)
            .checked_add(word(image, CREATOR_FEE))
            .and_then(|sum| sum.checked_add(word(image, PROTOCOL_FEES)))
            .ok_or(Stop::Code(OVERFLOW))?
    } else {
        0
    };
    Ok(rent(image.len()).saturating_sub(curve_lamports.saturating_sub(reserved)))
}
