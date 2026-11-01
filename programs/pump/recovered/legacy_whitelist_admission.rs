//! Captured account admission of Pump `buy`, `buy_exact_sol_in` and `sell` for the
//! whitelisted user: which accounts each handler refuses, with which code, and
//! which one wins when several are wrong. It includes the two trailing accounts
//! the IDL does not list, the `bonding-curve-v2` PDA and a buyback recipient.
//!
//! No recovered legacy model takes a whitelisted user. This model stops at the
//! end of admission: it answers `Pass` when the trade goes on to price. Recovered
//! from `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_legacy_whitelist_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Admission runs in four stages:
//!
//! 1. Accounts load in field order. `user_volume_accumulator` is skipped.
//! 2. On buys, `user_volume_accumulator` is created or loaded.
//! 3. Field constraints run in field order.
//! 4. The handler runs its gates. The buys read the recipients before anything
//!    else; `sell` reads the fee recipient first and the trailing accounts only
//!    after pricing and the token transfer.
//!
//! The whitelisted user pays no fee, so all of that stays and three checks go:
//! the wrong `bonding-curve-v2` key passes (6074 is never raised), and nothing is
//! paid to the fee recipient or the buyback slot, so the default key and a
//! read-only buyback slot pass too. The recipients are still compared.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 mints, Mayhem and
//! cashback coins, frozen accounts, and order inside a slot beyond the pairs the
//! test runs.

pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const NOT_ASSOCIATED: u32 = 2009;
pub const CONSTRAINT_TOKEN_MINT: u32 = 2014;
pub const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
pub const CONSTRAINT_SPACE: u32 = 2019;
pub const CONSTRAINT_TOKEN_PROGRAM: u32 = 2023;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const INVALID_PROGRAM_ID: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = 6023;
pub const BUY_NOT_ENOUGH_QUOTE: u32 = 6041;
pub const NOT_AUTHORIZED_BUYBACK: u32 = 6057;
pub const BUYBACK_RECIPIENT_MISSING: u32 = 6062;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// System program `AccountAlreadyInUse`, from the `init_if_needed` create.
pub const ALREADY_IN_USE: u32 = 0;
/// SPL Token `MintMismatch` and `OwnerMismatch`, at the transfer.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Handler {
    Sell,
    Buy,
    BuyExactSol,
}

/// One account slot as passed. Every field is a fault; the default is the
/// account the handler expects.
#[derive(Clone, Copy, Default, Debug)]
pub struct Slot {
    /// A valid copy of the account, at another address.
    pub wrong_address: bool,
    /// Owned by a program that cannot own it.
    pub wrong_owner: bool,
    /// No account: zero lamports, system owned.
    pub missing: bool,
    pub bad_discriminator: bool,
    /// Four bytes of data.
    pub short: bool,
    pub read_only: bool,
    /// A token account of another mint.
    pub wrong_mint: bool,
    /// A token account of another owner.
    pub wrong_authority: bool,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum ProgramSlot {
    #[default]
    Expected,
    /// Token-2022 in place of SPL Token, the accounts left as they were.
    OtherInterface,
    /// A program that is not the expected one, or a plain account.
    Invalid,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Accumulator {
    #[default]
    Stored,
    /// System owned with no data, whatever its lamports: created.
    Absent,
    /// System owned, holding data: the create fails.
    AbsentWithData,
    /// Eight bytes: the discriminator and nothing else.
    Truncated,
    /// 136 bytes: deserializes, but is not the declared 137.
    WrongSize,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Payee {
    /// Listed in `Global`.
    #[default]
    Listed,
    Unlisted,
    /// The default key.
    Zero,
}

/// The accounts past the IDL's list, in order. A third is ignored.
#[derive(Clone, Copy, PartialEq, Eq, Debug, Default)]
pub enum Trailing {
    #[default]
    CurveV2ThenBuyback,
    /// Only the curve-v2 PDA.
    CurveV2Only,
    None,
    /// The buyback recipient first.
    Swapped,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Gates {
    pub complete: bool,
    /// `amount` or `min_tokens_out` is zero.
    pub zero_amount: bool,
    /// `spendable_sol_in` is zero.
    pub zero_quote: bool,
    /// More than the user's balance (sell) or the curve's tokens (buy).
    pub over_amount: bool,
}

#[derive(Clone, Copy, Debug)]
pub struct Request {
    pub handler: Handler,
    pub global: Slot,
    pub fee_recipient: Slot,
    pub fee_payee: Payee,
    pub mint: Slot,
    pub bonding_curve: Slot,
    /// `bonding_curve.quote_mint` is not the default key.
    pub curve_has_quote_mint: bool,
    pub curve_token: Slot,
    pub user_token: Slot,
    pub user_unsigned: bool,
    pub system_program_ok: bool,
    pub token_program: ProgramSlot,
    pub creator_vault: Slot,
    pub event_authority_ok: bool,
    pub program_ok: bool,
    pub global_volume: Slot,
    pub accumulator: Slot,
    pub accumulator_shape: Accumulator,
    pub fee_config: Slot,
    pub fee_config_wrong_bump: bool,
    pub fee_config_truncated: bool,
    pub fee_program_ok: bool,
    pub trailing: Trailing,
    pub buyback_payee: Payee,
    pub gates: Gates,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Stop {
    Code(u32),
    /// `InvalidAccountData` from a custom account decoder.
    InvalidAccountData,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Outcome {
    /// Admitted; pricing and the transfers go on as on the expected accounts.
    Pass,
    /// Admitted and priced like the expected accounts; this code stops the
    /// trade, unless pricing stops first.
    AfterPricing(u32),
    Stop(Stop),
}

fn code(c: u32) -> Stop {
    Stop::Code(c)
}

/// `Account<T>`: the Anchor loader.
fn load_typed(s: &Slot) -> Result<(), Stop> {
    if s.missing {
        return Err(code(NOT_INITIALIZED));
    }
    if s.wrong_owner {
        return Err(code(OWNED_BY_WRONG_PROGRAM));
    }
    if s.short {
        return Err(code(DISCRIMINATOR_NOT_FOUND));
    }
    if s.bad_discriminator {
        return Err(code(DISCRIMINATOR_MISMATCH));
    }
    Ok(())
}

/// `InterfaceAccount<T>`, and the bonding curve's length-keyed decoder.
fn load_decoded(s: &Slot) -> Result<(), Stop> {
    if s.missing {
        return Err(code(NOT_INITIALIZED));
    }
    if s.wrong_owner {
        return Err(code(OWNED_BY_WRONG_PROGRAM));
    }
    if s.short || s.bad_discriminator {
        return Err(Stop::InvalidAccountData);
    }
    Ok(())
}

fn buys(r: &Request) -> bool {
    r.handler != Handler::Sell
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    load_typed(&r.global)?;
    load_decoded(&r.mint)?;
    load_decoded(&r.bonding_curve)?;
    load_decoded(&r.curve_token)?;
    load_decoded(&r.user_token)?;
    if r.user_unsigned {
        return Err(code(NOT_SIGNER));
    }
    if !r.system_program_ok || r.token_program == ProgramSlot::Invalid || !r.program_ok {
        return Err(code(INVALID_PROGRAM_ID));
    }
    if buys(r) {
        load_typed(&r.global_volume)?;
    }
    load_typed(&r.fee_config)?;
    if r.fee_config_truncated {
        return Err(code(DID_NOT_DESERIALIZE));
    }
    if !r.fee_program_ok {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
}

/// `init_if_needed`, ahead of every other constraint. `sell` has no such slot.
fn accumulator_stage(r: &Request) -> Result<(), Stop> {
    if !buys(r) {
        return Ok(());
    }
    let s = &r.accumulator;
    // The PDA is checked before the account is looked at.
    if s.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    match r.accumulator_shape {
        Accumulator::Absent => {}
        Accumulator::AbsentWithData => return Err(code(ALREADY_IN_USE)),
        Accumulator::Truncated => return Err(code(DID_NOT_DESERIALIZE)),
        Accumulator::WrongSize | Accumulator::Stored => {
            load_typed(s)?;
            if r.accumulator_shape == Accumulator::WrongSize {
                return Err(code(CONSTRAINT_SPACE));
            }
        }
    }
    if s.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    Ok(())
}

fn constraint_stage(r: &Request) -> Result<(), Stop> {
    if r.global.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.fee_recipient.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    // The curve PDA is derived from the mint passed.
    if r.bonding_curve.wrong_address || r.mint.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.bonding_curve.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.curve_has_quote_mint {
        return Err(code(UNSUPPORTED_QUOTE_MINT));
    }
    if r.token_program == ProgramSlot::OtherInterface {
        return Err(code(CONSTRAINT_TOKEN_PROGRAM));
    }
    // `associated_token::*` with no mint check: a right address of the wrong
    // mint goes on to the transfer.
    if r.curve_token.wrong_authority {
        return Err(code(CONSTRAINT_TOKEN_OWNER));
    }
    if r.curve_token.wrong_address {
        return Err(code(NOT_ASSOCIATED));
    }
    if r.curve_token.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.user_token.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.user_token.wrong_mint {
        return Err(code(CONSTRAINT_TOKEN_MINT));
    }
    if r.creator_vault.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.creator_vault.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if !r.event_authority_ok {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if buys(r) && r.global_volume.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.fee_config.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// The buyback reads, on any trailing shape.
fn buyback_stop(r: &Request) -> Option<u32> {
    match r.trailing {
        Trailing::None | Trailing::CurveV2Only => return Some(BUYBACK_RECIPIENT_MISSING),
        Trailing::Swapped => return Some(NOT_AUTHORIZED_BUYBACK),
        Trailing::CurveV2ThenBuyback => {}
    }
    match r.buyback_payee {
        Payee::Listed => None,
        Payee::Unlisted => Some(NOT_AUTHORIZED_BUYBACK),
        Payee::Zero => Some(BUYBACK_RECIPIENT_MISSING),
    }
}

fn gate_stage(r: &Request) -> Result<(), Stop> {
    let g = &r.gates;
    if r.fee_payee == Payee::Unlisted {
        return Err(code(NOT_AUTHORIZED));
    }
    if buys(r) {
        if let Some(c) = buyback_stop(r) {
            return Err(code(c));
        }
    }
    if g.complete {
        return Err(code(COMPLETE));
    }
    match r.handler {
        Handler::Sell => {
            if g.zero_amount {
                return Err(code(SELL_ZERO_AMOUNT));
            }
            if g.over_amount {
                return Err(code(NOT_ENOUGH_TOKENS_TO_SELL));
            }
        }
        Handler::Buy => {
            if g.zero_amount {
                return Err(code(BUY_ZERO_AMOUNT));
            }
            if g.over_amount {
                return Err(code(NOT_ENOUGH_TOKENS_TO_BUY));
            }
        }
        Handler::BuyExactSol => {
            if g.zero_amount {
                return Err(code(BUY_ZERO_AMOUNT));
            }
            if g.zero_quote {
                return Err(code(BUY_NOT_ENOUGH_QUOTE));
            }
        }
    }
    // The stored bump is not part of this program's check: the Pump Fees CPI
    // that prices the trade refuses it.
    if r.fee_config_wrong_bump {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// What is left once pricing has passed, in execution order.
fn after_pricing(r: &Request) -> Outcome {
    let selling = r.handler == Handler::Sell;
    if r.curve_token.wrong_mint {
        return Outcome::AfterPricing(TOKEN_MINT_MISMATCH);
    }
    if selling && r.user_token.wrong_authority {
        return Outcome::AfterPricing(TOKEN_OWNER_MISMATCH);
    }
    if selling {
        if let Some(c) = buyback_stop(r) {
            return Outcome::AfterPricing(c);
        }
    }
    Outcome::Pass
}

pub fn admit(r: &Request) -> Outcome {
    let stages = load_stage(r)
        .and_then(|()| accumulator_stage(r))
        .and_then(|()| constraint_stage(r))
        .and_then(|()| gate_stage(r));
    match stages {
        Ok(()) => after_pricing(r),
        Err(stop) => Outcome::Stop(stop),
    }
}
