//! Captured account admission of the six single-curve trades when the base
//! mint is a Token-2022 mint, and on Token-2022 quotes: what a Token-2022
//! account body does to the first stop of `buy`, `buy_exact_sol_in`, `sell`,
//! `buy_v2`, `buy_exact_quote_in_v2`, `sell_v2`, `buy_v3`,
//! `buy_exact_quote_in_v3` and `sell_v3`.
//!
//! A plain Token-2022 account set is admitted exactly like an SPL Token one:
//! one account fault stops at the same place with the same code. This model
//! holds what only a Token-2022 body can add. Each body falls into one class:
//!
//! - It does not load. The account fails where it is first read, so a stop
//!   before that read wins.
//! - It is only read at a transfer. Every admission and pricing stop wins, as
//!   does anything earlier in the same Token-2022 transfer.
//! - It breaks the quote mint's extension read (`UnsupportedQuoteMint`), which
//!   the v2 and v3 trades run once admission is done, ahead of pricing.
//! - Nothing reads it.
//!
//! `plain` is the captured outcome of the faults on valid accounts, and
//! `probe` the same with a wrong owner on this slot, which shows whether the
//! trade gets as far as reading it. They are inputs: the order of
//! admission belongs to the admission models and amounts to the accounting
//! models. This model only decides how the body joins that order. Recovered
//! from `evidence/original/pump/deployed.so` and checked against it on LiteSVM
//! by `tests/test_token2022_admission_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): two bad bodies in one
//! trade, three or more faults, and extensions other than the ones named here.

pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// Token-2022 codes seen at a transfer.
pub const TOKEN_FROZEN: u32 = 17;
pub const TOKEN_MEMO_REQUIRED: u32 = 36;
pub const TOKEN_CPI_GUARD: u32 = 42;
pub const TOKEN_PAUSED: u32 = 67;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Family {
    Legacy,
    V2,
    V3,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Side {
    Buy,
    Sell,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Slot {
    BaseMint,
    QuoteMint,
    CurveBase,
    UserBase,
    CurveQuote,
    UserQuote,
    /// A token account that only receives: fee, buyback or creator vault.
    Payee,
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Body {
    // No read fails on these.
    Extended,
    BadTlv,
    // Fail the load.
    BadLength,
    WrongType,
    Uninitialized,
    // Read at a transfer.
    Paused,
    HookSet,
    Frozen,
    CpiGuard,
    MemoRequired,
}

/// A captured ending, as far as this model tells them apart.
#[derive(Clone, PartialEq, Eq, Debug)]
pub enum Ending {
    Ok,
    Code(u32),
    Named(String),
}

fn invalid_data() -> Ending {
    Ending::Named("InvalidAccountData".to_string())
}

/// A place in a trade. Ordered, so the earlier stop is the smaller one.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Place {
    Admission,
    Pricing,
    /// The transfer (base first, then quote) and the check inside it.
    Transfer(u8, u8),
    Settlement,
}

const BASE_MOVE: u8 = 1;
const QUOTE_MOVE: u8 = 2;

// Token-2022's order inside one transfer.
const SOURCE_MINT: u8 = 1;
const SOURCE_FROZEN: u8 = 2;
const PAUSED: u8 = 3;
const SOURCE_AUTHORITY: u8 = 4;
const CPI_GUARD: u8 = 5;
const DESTINATION_FROZEN: u8 = 6;
const DESTINATION_MINT: u8 = 7;
const MEMO: u8 = 8;
const HOOK: u8 = 9;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
enum Class {
    Unread,
    Load,
    QuoteExtensions,
    Transfer(u8, u8, u32),
    /// As `Transfer`, ending in `InvalidAccountData`.
    TransferData(u8, u8),
}

/// Which way the account moves tokens in this trade, if it does.
fn is_source(slot: Slot, side: Side) -> Option<bool> {
    match slot {
        Slot::CurveBase | Slot::CurveQuote => Some(side == Side::Sell && slot == Slot::CurveQuote || side == Side::Buy && slot == Slot::CurveBase),
        Slot::UserBase | Slot::UserQuote => Some(side == Side::Sell && slot == Slot::UserBase || side == Side::Buy && slot == Slot::UserQuote),
        Slot::Payee => Some(false),
        Slot::BaseMint | Slot::QuoteMint => None,
    }
}

fn movement(slot: Slot) -> u8 {
    match slot {
        Slot::BaseMint | Slot::CurveBase | Slot::UserBase => BASE_MOVE,
        _ => QUOTE_MOVE,
    }
}

fn class(body: Body, slot: Slot, side: Side) -> Class {
    let source = is_source(slot, side);
    let step = movement(slot);
    match body {
        Body::Extended => Class::Unread,
        Body::BadTlv => {
            if slot == Slot::QuoteMint {
                Class::QuoteExtensions
            } else {
                Class::Unread
            }
        }
        Body::BadLength | Body::WrongType | Body::Uninitialized => Class::Load,
        Body::Paused => Class::Transfer(step, PAUSED, TOKEN_PAUSED),
        Body::HookSet => Class::TransferData(step, HOOK),
        Body::Frozen => {
            let check = if source == Some(true) { SOURCE_FROZEN } else { DESTINATION_FROZEN };
            Class::Transfer(step, check, TOKEN_FROZEN)
        }
        Body::CpiGuard => {
            if source == Some(true) {
                Class::Transfer(step, CPI_GUARD, TOKEN_CPI_GUARD)
            } else {
                Class::Unread
            }
        }
        Body::MemoRequired => {
            if source == Some(false) {
                Class::Transfer(step, MEMO, TOKEN_MEMO_REQUIRED)
            } else {
                Class::Unread
            }
        }
    }
}

/// Where the other fault stops, on the routes where a body can lose to it.
pub fn place_of(family: Family, side: Side, fault: &str) -> Place {
    match fault {
        "curve_base.mint" if side == Side::Sell => Place::Transfer(BASE_MOVE, DESTINATION_MINT),
        "curve_base.mint" => Place::Transfer(BASE_MOVE, SOURCE_MINT),
        "user_base.auth" if side == Side::Sell => Place::Transfer(BASE_MOVE, SOURCE_AUTHORITY),
        "curve_quote.auth" if side == Side::Sell => Place::Transfer(QUOTE_MOVE, SOURCE_AUTHORITY),
        "fee_recipient.zero" => Place::Settlement,
        "buyback.readonly" | "curve_v2.key" if family == Family::Legacy => Place::Settlement,
        "buyback.absent" | "buyback.unlisted" | "buyback.zero" | "curve_v2.absent" | "curve_v2.swapped"
            if family == Family::Legacy && side == Side::Sell =>
        {
            Place::Settlement
        }
        "h.limit" | "h.overflow" | "fee_config.len2511" if family != Family::Legacy => Place::Pricing,
        // The v2 fee CPI checks this seed: after the mint read on a buy, before it on a sell.
        "fee_config.bump" if family == Family::V2 && side == Side::Buy => Place::Pricing,
        _ => Place::Admission,
    }
}

/// The handlers read the quote accounts by hand, in this order, and refuse a
/// wrong one with one code, so `probe` cannot tell two of them apart.
fn hand_read_rank(name: &str) -> u8 {
    match name.split('.').next() {
        Some("curve_quote") => 1,
        Some("user_quote") => 2,
        Some("payee") | Some("buyback_fee_recipient") => 3,
        _ => 0,
    }
}

fn read_first(case: &Case) -> bool {
    let (mine, theirs) = (hand_read_rank(slot_name(case.slot)), hand_read_rank(&case.fault));
    case.plain == Ending::Code(ACCOUNT_TYPE_NOT_SUPPORTED) && mine != 0 && mine < theirs
}

fn slot_name(slot: Slot) -> &'static str {
    match slot {
        Slot::CurveQuote => "curve_quote",
        Slot::UserQuote => "user_quote",
        Slot::Payee => "payee",
        _ => "",
    }
}

/// A missing recipient account is created, which reads the quote mint too.
fn creates_account(family: Family, fault: &str) -> bool {
    family == Family::V2 && fault.starts_with("associated_") && fault.ends_with(".missing")
}

pub struct Case {
    pub family: Family,
    pub side: Side,
    pub slot: Slot,
    pub body: Body,
    /// `-` for none.
    pub fault: String,
    pub plain: Ending,
    pub probe: Ending,
}

fn extension_read(case: &Case) -> Ending {
    if case.plain == Ending::Ok && creates_account(case.family, &case.fault) {
        return invalid_data();
    }
    if case.plain != Ending::Ok && place_of(case.family, case.side, &case.fault) == Place::Admission {
        return case.plain.clone();
    }
    Ending::Code(UNSUPPORTED_QUOTE_MINT)
}

fn at_transfer(case: &Case, step: u8, check: u8, ending: Ending) -> Ending {
    if case.plain == Ending::Ok || place_of(case.family, case.side, &case.fault) > Place::Transfer(step, check) {
        return ending;
    }
    case.plain.clone()
}

/// The ending of a trade with this body in this slot.
pub fn first_stop(case: &Case) -> Ending {
    match class(case.body, case.slot, case.side) {
        Class::Unread => case.plain.clone(),
        Class::Load => {
            if case.probe == case.plain && !read_first(case) {
                return case.plain.clone();
            }
            match case.body {
                Body::Uninitialized => Ending::Named("UninitializedAccount".to_string()),
                _ => invalid_data(),
            }
        }
        Class::QuoteExtensions => extension_read(case),
        Class::Transfer(step, check, code) => at_transfer(case, step, check, Ending::Code(code)),
        Class::TransferData(step, check) => at_transfer(case, step, check, invalid_data()),
    }
}
