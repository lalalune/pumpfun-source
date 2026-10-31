//! Captured admission of the six single-curve trades when a trade carries
//! more than the one bad Token-2022 body the admission model
//! (`token2022_admission.rs`) covers: two bad bodies in one trade, a body
//! with two account faults, two bodies with one account fault, and the
//! extension types that model does not name.
//!
//! The class and place tables are the ones of `token2022_admission.rs`,
//! re-stated here so this model stands alone. A body falls into one class:
//!
//! - It does not load. The account fails where it is first read, so a stop
//!   before that read wins.
//! - It is only read at a transfer. Every admission and pricing stop wins,
//!   as does anything earlier in the same Token-2022 transfer.
//! - It breaks the quote mint's extension read (`UnsupportedQuoteMint`),
//!   which the v2 and v3 trades run once admission is done, ahead of
//!   pricing.
//! - Nothing reads it. The extension types beyond the ones the admission
//!   model names all land here on the checked inputs: a transfer-fee
//!   config, a mint close authority, a confidential-transfer mint, a
//!   default account state (set, and set to a value that is not a state),
//!   an interest-bearing config, a permanent delegate, a transfer hook
//!   with no program, a group pointer, a withheld transfer-fee amount on
//!   an account, a confidential-transfer account body, and a transfer-hook
//!   account body with its in-hook flag set. None of them changes an
//!   ending, alone or next to another bad body.
//!
//! Two stopping bodies: the earlier stop wins. Places are ordered
//! admission, the quote extension read, pricing, the transfer (base move
//! first, Token-2022's check order inside it), settlement. The quote move
//! pays each destination in its own transfer, so a quote destination's
//! stop lands in that destination's own sub-transfer: the sub-transfers
//! run in an order the host line supplies per route (on v2 the creator
//! vault first, then the main destination, then the other payees; on v3
//! the main destination first, then the recipient), and the mint and
//! source stops land in the first of them. A load body has
//! no fixed place: the twin probes settle it, as in the admission model —
//! `probe_a` is the second body alone with a wrong owner on the first
//! slot, so it equals the second body's own ending exactly when that body
//! stops before the first slot is read. Two load bodies: exactly one
//! probe can match, and the matching side stops second. Three or more
//! faults: a fault pair is treated as one stop at the earlier of its two
//! places, with its captured ending and probe as the inputs, and two
//! bodies with a fault compare the fault's place against the pair's
//! place; the pair's own captured ending is an input there, not a
//! prediction. Recovered from `evidence/original/pump/deployed.so` and
//! checked against it on LiteSVM by
//! `tests/test_token2022_bodies_multi_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): a load body in a
//! three-or-more-fault trade, the v2 recipient-creation faults
//! (`associated_*.missing`) next to two bodies, body pairs on routes
//! outside the pair routes the admission packet uses, and faults whose
//! place the place table does not name beyond the admission bucket.

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
    // Extension types the admission model does not name. No read fails.
    FeeConfig,
    CloseAuthority,
    ConfidentialMint,
    DefaultState,
    InterestBearing,
    PermanentDelegate,
    HookNone,
    GroupPointer,
    FeeAmount,
    ConfidentialAccount,
    HookAccountOn,
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

fn unconfirmed() -> Ending {
    Ending::Named("unconfirmed".to_string())
}

fn load_ending(body: Body) -> Ending {
    match body {
        Body::Uninitialized => Ending::Named("UninitializedAccount".to_string()),
        _ => invalid_data(),
    }
}

/// A place in a trade. Ordered, so the earlier stop is the smaller one.
#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Debug)]
pub enum Place {
    Admission,
    /// The quote mint's extension read: after admission, before pricing.
    ExtensionRead,
    Pricing,
    /// The transfer (base first, then quote), the sub-transfer inside the
    /// quote move (0 on the base move, and for a quote mint or source
    /// stop), and the check inside the sub-transfer.
    Transfer(u8, u8, u8),
    Settlement,
    /// No stop at all.
    Never,
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
    Transfer(u8, u8, u8, u32),
    /// As `Transfer`, ending in `InvalidAccountData`.
    TransferData(u8, u8, u8),
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

/// `rank` is the sub-transfer a quote destination's stop lands in; mint
/// and source stops land in the first sub-transfer (rank 0), as does every
/// stop on the base move.
fn class(body: Body, slot: Slot, side: Side, rank: u8) -> Class {
    let source = is_source(slot, side);
    let step = movement(slot);
    let rank = if step == QUOTE_MOVE { rank } else { 0 };
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
        Body::Paused => Class::Transfer(step, rank, PAUSED, TOKEN_PAUSED),
        Body::HookSet => Class::TransferData(step, rank, HOOK),
        Body::Frozen => {
            let check = if source == Some(true) { SOURCE_FROZEN } else { DESTINATION_FROZEN };
            Class::Transfer(step, rank, check, TOKEN_FROZEN)
        }
        Body::CpiGuard => {
            if source == Some(true) {
                Class::Transfer(step, rank, CPI_GUARD, TOKEN_CPI_GUARD)
            } else {
                Class::Unread
            }
        }
        Body::MemoRequired => {
            if source == Some(false) {
                Class::Transfer(step, rank, MEMO, TOKEN_MEMO_REQUIRED)
            } else {
                Class::Unread
            }
        }
        Body::FeeConfig
        | Body::CloseAuthority
        | Body::ConfidentialMint
        | Body::DefaultState
        | Body::InterestBearing
        | Body::PermanentDelegate
        | Body::HookNone
        | Body::GroupPointer
        | Body::FeeAmount
        | Body::ConfidentialAccount
        | Body::HookAccountOn => Class::Unread,
    }
}

/// Where a fault stops, on the routes where a body can lose to it. The
/// admission model's table, unchanged.
pub fn place_of(family: Family, side: Side, fault: &str) -> Place {
    match fault {
        "curve_base.mint" if side == Side::Sell => Place::Transfer(BASE_MOVE, 0, DESTINATION_MINT),
        "curve_base.mint" => Place::Transfer(BASE_MOVE, 0, SOURCE_MINT),
        "user_base.auth" if side == Side::Sell => Place::Transfer(BASE_MOVE, 0, SOURCE_AUTHORITY),
        "curve_quote.auth" if side == Side::Sell => Place::Transfer(QUOTE_MOVE, 0, SOURCE_AUTHORITY),
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
/// wrong one with one code, so a probe cannot tell two of them apart.
fn hand_read_rank(name: &str) -> u8 {
    match name.split('.').next() {
        Some("curve_quote") => 1,
        Some("user_quote") => 2,
        Some("payee") | Some("buyback_fee_recipient") => 3,
        _ => 0,
    }
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

/// The fixed place of a class that stops at one, if it has one.
fn fixed_place(class: Class) -> Option<Place> {
    match class {
        Class::Unread => Some(Place::Never),
        Class::Load => None,
        Class::QuoteExtensions => Some(Place::ExtensionRead),
        Class::Transfer(step, rank, check, _) | Class::TransferData(step, rank, check) => {
            Some(Place::Transfer(step, rank, check))
        }
    }
}

pub struct PairCase {
    pub side: Side,
    pub slot_a: Slot,
    pub body_a: Body,
    /// The sub-transfer rank of slot A (0 unless a quote destination).
    pub rank_a: u8,
    pub slot_b: Slot,
    pub body_b: Body,
    pub rank_b: u8,
    /// Each body's ending on its own. `-` when the model cannot need it.
    pub a_alone: Ending,
    pub b_alone: Ending,
    /// Body B alone with a wrong owner on slot A; body A alone with a
    /// wrong owner on slot B. `-` unless a load body is involved.
    pub probe_a: Ending,
    pub probe_b: Ending,
}

/// The ending of a trade carrying both bodies.
pub fn pair_stop(case: &PairCase) -> Ending {
    let a = class(case.body_a, case.slot_a, case.side, case.rank_a);
    let b = class(case.body_b, case.slot_b, case.side, case.rank_b);
    match (a, b) {
        (Class::Unread, _) => return case.b_alone.clone(),
        (_, Class::Unread) => return case.a_alone.clone(),
        _ => {}
    }
    match (a, b) {
        (Class::Load, Class::Load) => {
            let a_first = case.probe_b == case.a_alone && case.probe_a != case.b_alone;
            let b_first = case.probe_a == case.b_alone && case.probe_b != case.a_alone;
            if b_first {
                return load_ending(case.body_b);
            }
            if a_first {
                return load_ending(case.body_a);
            }
            if case.a_alone == case.b_alone {
                return case.a_alone.clone();
            }
            unconfirmed()
        }
        (Class::Load, _) => {
            if case.probe_a == case.b_alone {
                case.b_alone.clone()
            } else {
                load_ending(case.body_a)
            }
        }
        (_, Class::Load) => {
            if case.probe_b == case.a_alone {
                case.a_alone.clone()
            } else {
                load_ending(case.body_b)
            }
        }
        _ => {
            let (pa, pb) = (fixed_place(a).unwrap(), fixed_place(b).unwrap());
            if pa <= pb {
                case.a_alone.clone()
            } else {
                case.b_alone.clone()
            }
        }
    }
}

pub struct DuoCase {
    pub family: Family,
    pub side: Side,
    pub slot: Slot,
    pub body: Body,
    /// The sub-transfer rank of the body's slot.
    pub rank: u8,
    /// The two faults, as the admission model names them.
    pub fault_f: String,
    pub fault_g: String,
    /// The two faults together on valid accounts, and the same with a
    /// wrong owner on the body's slot.
    pub pair_plain: Ending,
    pub pair_probe: Ending,
}

/// The fault pair read as one stop, as `first_stop` reads a single fault.
fn read_first_duo(case: &DuoCase) -> bool {
    let winner = [case.fault_f.as_str(), case.fault_g.as_str()]
        .iter()
        .map(|name| hand_read_rank(name))
        .filter(|rank| *rank != 0)
        .min();
    let mine = hand_read_rank(slot_name(case.slot));
    case.pair_plain == Ending::Code(ACCOUNT_TYPE_NOT_SUPPORTED)
        && mine != 0
        && winner.is_some()
        && mine < winner.unwrap()
}

/// The ending of a trade carrying one body and two faults.
pub fn duo_stop(case: &DuoCase) -> Ending {
    let place = std::cmp::min(
        place_of(case.family, case.side, &case.fault_f),
        place_of(case.family, case.side, &case.fault_g),
    );
    match class(case.body, case.slot, case.side, case.rank) {
        Class::Unread => case.pair_plain.clone(),
        Class::Load => {
            if case.pair_probe == case.pair_plain && !read_first_duo(case) {
                return case.pair_plain.clone();
            }
            load_ending(case.body)
        }
        Class::QuoteExtensions => {
            if case.pair_plain == Ending::Ok {
                if creates_account(case.family, &case.fault_f) || creates_account(case.family, &case.fault_g) {
                    return invalid_data();
                }
                return Ending::Code(UNSUPPORTED_QUOTE_MINT);
            }
            if place == Place::Admission {
                return case.pair_plain.clone();
            }
            Ending::Code(UNSUPPORTED_QUOTE_MINT)
        }
        Class::Transfer(step, rank, check, code) => {
            at_place(case, place, Place::Transfer(step, rank, check), Ending::Code(code))
        }
        Class::TransferData(step, rank, check) => {
            at_place(case, place, Place::Transfer(step, rank, check), invalid_data())
        }
    }
}

fn at_place(case: &DuoCase, place: Place, mine: Place, ending: Ending) -> Ending {
    if case.pair_plain == Ending::Ok || place > mine {
        return ending;
    }
    if place < mine {
        return case.pair_plain.clone();
    }
    unconfirmed()
}

pub struct TrioCase {
    pub family: Family,
    pub side: Side,
    pub slot_a: Slot,
    pub body_a: Body,
    pub rank_a: u8,
    pub slot_b: Slot,
    pub body_b: Body,
    pub rank_b: u8,
    pub fault: String,
    /// The fault on valid accounts.
    pub fault_plain: Ending,
    /// The two bodies together, captured.
    pub pair_captured: Ending,
}

/// The ending of a trade carrying two bodies and one fault. Neither body
/// may be a load body: a load body's place is set by its probe against a
/// single other stop, and a fault next to a pair is outside the checked
/// inputs.
pub fn trio_stop(case: &TrioCase) -> Ending {
    if case.fault_plain == Ending::Ok {
        return case.pair_captured.clone();
    }
    let (a, b) = (
        fixed_place(class(case.body_a, case.slot_a, case.side, case.rank_a)),
        fixed_place(class(case.body_b, case.slot_b, case.side, case.rank_b)),
    );
    let pair_place = match (a, b) {
        (Some(x), Some(y)) => std::cmp::min(x, y),
        _ => return unconfirmed(),
    };
    let fault_place = place_of(case.family, case.side, &case.fault);
    match pair_place.cmp(&fault_place) {
        std::cmp::Ordering::Less => case.pair_captured.clone(),
        std::cmp::Ordering::Greater => case.fault_plain.clone(),
        std::cmp::Ordering::Equal => unconfirmed(),
    }
}
