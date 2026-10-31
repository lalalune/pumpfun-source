//! Captured account admission of Pump `sell_v2`, `buy_v2` and
//! `buy_exact_quote_in_v2`: which accounts each handler refuses, with which
//! code, and which one wins when several are wrong.
//!
//! `sell_v2.rs`, `buy_v2.rs` and `v2_token_quote.rs` take the recipients as
//! booleans and leave the rest of admission out. This model stops where they
//! start: it answers `Pass` when the trade goes on to price, and the amounts
//! then belong to those models. Recovered from
//! `evidence/original/pump/deployed.so` and checked against it on LiteSVM by
//! `tests/test_v2_account_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Admission runs in four stages:
//!
//! 1. Accounts load in field order. `user_volume_accumulator` is skipped.
//! 2. `user_volume_accumulator` is created or loaded.
//! 3. Field constraints run in field order. All six quote accounts are seeded
//!    PDAs of the ATA program, so they are checked by address on every route.
//! 4. The handler runs its curve and amount gates, its two recipient lists,
//!    then the quote accounts. A native route skips the quote accounts.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 base mints,
//! frozen accounts, a non-empty `sharing_config`, and order inside a slot
//! beyond the pairs the test runs.

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
pub const MINT_MISMATCH: u32 = 6004;
pub const COMPLETE: u32 = 6005;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const NOT_ENOUGH_TOKENS_TO_SELL: u32 = 6023;
pub const BUY_NOT_ENOUGH_QUOTE: u32 = 6041;
pub const NOT_AUTHORIZED_BUYBACK: u32 = 6057;
pub const BUYBACK_RECIPIENT_MISSING: u32 = 6062;
/// System program `AccountAlreadyInUse`, from the `init_if_needed` create.
pub const ALREADY_IN_USE: u32 = 0;
/// SPL Token `MintMismatch` and `OwnerMismatch`, at the transfer.
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Handler {
    Sell,
    Buy,
    BuyExactQuote,
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
    /// The other token program, the accounts beside it left as they were.
    OtherInterface,
    /// The other token program, the quote accounts moved with it.
    OtherInterfaceMoved,
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
    /// Listed in `Global`, the quote account moved with it.
    #[default]
    Listed,
    Unlisted,
    /// The default key.
    Zero,
}

#[derive(Clone, Copy, Default, Debug)]
pub struct Gates {
    pub complete: bool,
    /// Sell `amount`, buy `amount`, or exact-quote `min_tokens_out` is zero.
    pub zero_amount: bool,
    /// Exact-quote `spendable_quote_in` is zero.
    pub zero_quote: bool,
    /// More than the user's balance (sell), or more than the curve holds on a
    /// Mayhem buy.
    pub over_amount: bool,
}

#[derive(Clone, Copy, Debug)]
pub struct Request {
    pub handler: Handler,
    /// `bonding_curve.quote_mint` is the default key. wSOL curves are token routes.
    pub native: bool,
    pub global: Slot,
    pub base_mint: Slot,
    pub quote_mint: Slot,
    /// A native curve passed a valid quote mint other than wSOL, with every
    /// quote account derived from that mint.
    pub native_other_mint: bool,
    pub base_token_program: ProgramSlot,
    pub quote_token_program: ProgramSlot,
    pub associated_token_program_ok: bool,
    pub fee_recipient: Slot,
    pub fee_payee: Payee,
    pub fee_quote: Slot,
    pub buyback: Slot,
    pub buyback_payee: Payee,
    pub buyback_quote: Slot,
    pub bonding_curve: Slot,
    pub curve_base: Slot,
    pub curve_quote: Slot,
    pub user_unsigned: bool,
    pub user_base: Slot,
    pub user_quote: Slot,
    pub creator_vault: Slot,
    pub vault_quote: Slot,
    pub sharing_config: Slot,
    pub global_volume: Slot,
    pub accumulator: Slot,
    pub accumulator_shape: Accumulator,
    pub accumulator_quote: Slot,
    pub fee_config: Slot,
    pub fee_config_wrong_bump: bool,
    /// The user is `Global.whitelist_pda`.
    pub whitelisted: bool,
    pub fee_config_truncated: bool,
    pub fee_program_ok: bool,
    pub system_program_ok: bool,
    pub event_authority_ok: bool,
    pub program_ok: bool,
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
    /// Admitted and priced like the expected accounts, but a transfer fails
    /// with this SPL Token code, unless pricing stops first.
    Transfer(u32),
    /// Admitted and priced, but after the native fee payment to the default
    /// key, the system program's account fails the rent check on LiteSVM.
    NativeFeeToSystemProgram,
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

fn program(p: ProgramSlot) -> Result<(), Stop> {
    if p == ProgramSlot::Invalid {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
}

fn buys(r: &Request) -> bool {
    r.handler != Handler::Sell
}

fn load_stage(r: &Request) -> Result<(), Stop> {
    load_typed(&r.global)?;
    load_decoded(&r.base_mint)?;
    load_decoded(&r.quote_mint)?;
    program(r.base_token_program)?;
    program(r.quote_token_program)?;
    if !r.associated_token_program_ok {
        return Err(code(INVALID_PROGRAM_ID));
    }
    load_decoded(&r.bonding_curve)?;
    load_decoded(&r.curve_base)?;
    if r.user_unsigned {
        return Err(code(NOT_SIGNER));
    }
    load_decoded(&r.user_base)?;
    // `sell_v2` has no global volume accumulator slot.
    if buys(r) {
        load_typed(&r.global_volume)?;
    }
    load_typed(&r.fee_config)?;
    if r.fee_config_truncated {
        return Err(code(DID_NOT_DESERIALIZE));
    }
    if !r.fee_program_ok || !r.system_program_ok || !r.program_ok {
        return Err(code(INVALID_PROGRAM_ID));
    }
    Ok(())
}

/// `init_if_needed`, ahead of every other constraint.
fn accumulator_stage(r: &Request) -> Result<(), Stop> {
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

/// A quote account field: seeded on its owner slot, the quote program and the
/// quote mint, then `mut`.
fn quote_seeds(r: &Request, s: &Slot, owner_moved: bool) -> Result<(), Stop> {
    let derived_elsewhere = r.quote_mint.wrong_address || r.quote_token_program == ProgramSlot::OtherInterface;
    if s.wrong_address || owner_moved || derived_elsewhere {
        return Err(code(CONSTRAINT_SEEDS));
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
    quote_seeds(r, &r.fee_quote, r.fee_recipient.wrong_address)?;
    if r.buyback.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    quote_seeds(r, &r.buyback_quote, r.buyback.wrong_address)?;
    // The curve PDA is derived from the base mint passed.
    if r.bonding_curve.wrong_address || r.base_mint.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.bonding_curve.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.native_other_mint {
        return Err(code(MINT_MISMATCH));
    }
    if r.base_token_program == ProgramSlot::OtherInterface {
        return Err(code(CONSTRAINT_TOKEN_PROGRAM));
    }
    // `associated_token::*` with no mint check: a right address of the wrong
    // mint goes on to the transfer.
    if r.curve_base.wrong_authority {
        return Err(code(CONSTRAINT_TOKEN_OWNER));
    }
    if r.curve_base.wrong_address {
        return Err(code(NOT_ASSOCIATED));
    }
    if r.curve_base.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    quote_seeds(r, &r.curve_quote, false)?;
    if r.user_base.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.user_base.wrong_mint {
        return Err(code(CONSTRAINT_TOKEN_MINT));
    }
    if r.user_quote.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    if r.creator_vault.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if r.creator_vault.read_only {
        return Err(code(CONSTRAINT_MUT));
    }
    quote_seeds(r, &r.vault_quote, false)?;
    if r.sharing_config.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if buys(r) && r.global_volume.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    quote_seeds(r, &r.accumulator_quote, false)?;
    if r.fee_config.wrong_address {
        return Err(code(CONSTRAINT_SEEDS));
    }
    if !r.event_authority_ok {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

fn gate_stage(r: &Request) -> Result<(), Stop> {
    let g = &r.gates;
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
        Handler::BuyExactQuote => {
            if g.zero_amount {
                return Err(code(BUY_ZERO_AMOUNT));
            }
            if g.zero_quote {
                return Err(code(BUY_NOT_ENOUGH_QUOTE));
            }
        }
    }
    Ok(())
}

fn recipient_stage(r: &Request) -> Result<(), Stop> {
    // The default key fills empty list entries, so it counts as a fee recipient.
    if r.fee_payee == Payee::Unlisted {
        return Err(code(NOT_AUTHORIZED));
    }
    match r.buyback_payee {
        Payee::Listed => Ok(()),
        Payee::Unlisted => Err(code(NOT_AUTHORIZED_BUYBACK)),
        Payee::Zero => Err(code(BUYBACK_RECIPIENT_MISSING)),
    }
}

/// `buy_v2::admit_associated_token_account`. The address was checked by seeds.
fn associated(s: &Slot, allow_create: bool) -> Result<(), Stop> {
    if s.missing {
        return if allow_create { Ok(()) } else { Err(code(NOT_INITIALIZED)) };
    }
    if s.wrong_owner {
        return Err(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    if s.short {
        return Err(Stop::InvalidAccountData);
    }
    if s.wrong_mint {
        return Err(code(MINT_MISMATCH));
    }
    Ok(())
}

fn quote_stage(r: &Request) -> Result<(), Stop> {
    if r.native {
        return Ok(());
    }
    if r.quote_token_program == ProgramSlot::OtherInterfaceMoved {
        return Err(code(NOT_INITIALIZED));
    }
    associated(&r.curve_quote, false)?;
    // `check_token_account`: a missing account is simply not the program's.
    let u = &r.user_quote;
    if u.missing || u.wrong_owner {
        return Err(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    associated(u, false)?;
    if u.wrong_authority {
        return Err(code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    associated(&r.vault_quote, true)?;
    associated(&r.accumulator_quote, true)?;
    associated(&r.fee_quote, true)?;
    associated(&r.buyback_quote, true)
}

/// The stored bump is not part of this program's check: the Pump Fees CPI that
/// prices the trade refuses it, and a whitelisted user makes no such CPI.
fn fee_stage(r: &Request) -> Result<(), Stop> {
    if r.fee_config_wrong_bump && !r.whitelisted {
        return Err(code(CONSTRAINT_SEEDS));
    }
    Ok(())
}

/// Faults the handlers do not read, which only the runtime or token program refuses.
fn transfer_stage(r: &Request) -> Outcome {
    if r.curve_base.wrong_mint {
        return Outcome::Transfer(TOKEN_MINT_MISMATCH);
    }
    let selling = r.handler == Handler::Sell;
    if selling && r.user_base.wrong_authority {
        return Outcome::Transfer(TOKEN_OWNER_MISMATCH);
    }
    if selling && !r.native && r.curve_quote.wrong_authority {
        return Outcome::Transfer(TOKEN_OWNER_MISMATCH);
    }
    if r.native && r.fee_payee == Payee::Zero && !r.whitelisted {
        return Outcome::NativeFeeToSystemProgram;
    }
    Outcome::Pass
}

pub fn admit(r: &Request) -> Outcome {
    let stages = load_stage(r)
        .and_then(|()| accumulator_stage(r))
        .and_then(|()| constraint_stage(r))
        .and_then(|()| gate_stage(r))
        .and_then(|()| recipient_stage(r))
        .and_then(|()| quote_stage(r))
        .and_then(|()| fee_stage(r));
    match stages {
        Ok(()) => transfer_stage(r),
        Err(stop) => Outcome::Stop(stop),
    }
}
