//! Captured reading of the stored shape of Pump's list accounts.
//!
//! `QuoteControl` and pump_fees' `SharingConfig` hold a Borsh `Vec` behind a
//! fixed header, so what they must satisfy depends on the count they state as
//! much as on their length. Anchor-typed slots decode the rows onto the heap;
//! `create_v2` scans `QuoteControl` in place instead, with its own error and no
//! heap limit. `holder_rewards` is not decoded at all: its length only decides
//! whether the System Program will pay from it.
//!
//! A shape that passes leaves the outcome of the same call on an honest account,
//! so the handlers stay with their own models. Row limits are the rows that fit
//! the program's 32 KiB bump heap: the `Vec` starts with 4,096 bytes of capacity
//! and doubles, and old buffers are not reused. A failing decode that stops short
//! of the limit still answers 3003. The limits were read from the captured
//! program, and the distributions fail after the decode, so they hold for these
//! fixtures' heap use only; which allocation fails there is unconfirmed.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_config_length_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

/// Anchor `AccountDiscriminatorNotFound`.
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
/// Anchor `AccountDiscriminatorMismatch`.
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
/// Anchor `AccountDidNotDeserialize`.
pub const DID_NOT_DESERIALIZE: u32 = 3003;
/// `InvalidQuoteControl`.
pub const INVALID_QUOTE_CONTROL: u32 = 6075;

pub const CONTROL_HEADER: u64 = 108;
pub const CONTROL_ROW: u64 = 40;
/// 4,096 / 40 = 102 rows, doubled twice.
pub const CONTROL_ROWS_LIMIT: u64 = 408;
pub const SHARING_HEADER: u64 = 80;
pub const SHARING_ROW: u64 = 34;

/// 4,096 / 34 = 120 rows, doubled twice.
pub const SHARING_ROWS_LIMIT: u64 = 480;
/// Rows the distributions can hold on the heap past the decode: the next
/// allocation after the 480-row buffer fails.
pub const DISTRIBUTION_ROWS_LIMIT: u64 = 240;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Slot {
    Control,
    /// `migrate_bonding_curve_creator`.
    Migrate,
    /// `distribute_creator_fees` and `get_minimum_distributable_fee`.
    Distribute,
    /// The token route of `distribute_creator_fees_v2`, which runs out of heap
    /// ahead of the account constraints.
    QuoteDistribute,
}

impl Slot {
    fn shape(self) -> (u64, u64, u64) {
        match self {
            Slot::Control => (CONTROL_HEADER, CONTROL_ROW, CONTROL_ROWS_LIMIT),
            _ => (SHARING_HEADER, SHARING_ROW, SHARING_ROWS_LIMIT),
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Stored {
    pub len: u64,
    pub disc_ok: bool,
    /// The count stored behind the header.
    pub count: u64,
    /// `status` and `revoked` hold valid Borsh values; always true for
    /// `QuoteControl`, whose header has neither.
    pub fields_ok: bool,
    /// The other account constraints hold, so the handler runs.
    pub admitted: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Answer {
    /// The outcome of an honest account holding `count` rows holds.
    Pass,
    Error(u32),
    /// The heap runs out during the decode: no Anchor code, the VM stops.
    OutOfMemory,
}

/// `Account::try_from` on a program-owned account.
pub fn typed_load(slot: Slot, s: Stored) -> Answer {
    let (header, row, limit) = slot.shape();
    if s.len < 8 {
        return Answer::Error(DISCRIMINATOR_NOT_FOUND);
    }
    if !s.disc_ok {
        return Answer::Error(DISCRIMINATOR_MISMATCH);
    }
    if s.len < header || !s.fields_ok {
        return Answer::Error(DID_NOT_DESERIALIZE);
    }
    let fit = (s.len - header) / row;
    // Rows are read one at a time, so the heap can run out before the bytes do.
    if s.count.min(fit) > limit {
        return Answer::OutOfMemory;
    }
    if s.count > fit {
        return Answer::Error(DID_NOT_DESERIALIZE);
    }
    let reached = slot == Slot::QuoteDistribute || (slot == Slot::Distribute && s.admitted);
    if reached && s.count > DISTRIBUTION_ROWS_LIMIT {
        return Answer::OutOfMemory;
    }
    Answer::Pass
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Scan {
    Found(u64),
    /// The mint is not listed; the caller goes on to the quote chain.
    Missing,
    Error(u32),
}

/// The in-place scan `create_v2` runs on `remaining_accounts[3]`. `first` is
/// the first row holding the mint, wherever it stands in the stored bytes; rows
/// past the stated count are not read.
pub fn control_scan(s: Stored, first: Option<u64>) -> Scan {
    if s.len < CONTROL_HEADER || !s.disc_ok {
        return Scan::Error(INVALID_QUOTE_CONTROL);
    }
    if s.count > (s.len - CONTROL_HEADER) / CONTROL_ROW {
        return Scan::Error(INVALID_QUOTE_CONTROL);
    }
    match first {
        Some(row) if row < s.count => Scan::Found(row),
        _ => Scan::Missing,
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Rewards {
    Pass,
    /// System transfer: "from must not carry data".
    InvalidArgument,
    /// The transfer debits an account System does not own.
    ExternalAccountLamportSpend,
}

/// Paying `amount` out of `holder_rewards`, which is an unchecked account. A
/// zero amount makes no transfer, and the end-of-handler floor stays the rent of
/// zero bytes at any length.
pub fn rewards_payment(system_owned: bool, len: u64, amount: u64) -> Rewards {
    if amount == 0 {
        Rewards::Pass
    } else if len > 0 {
        Rewards::InvalidArgument
    } else if system_owned {
        Rewards::Pass
    } else {
        Rewards::ExternalAccountLamportSpend
    }
}
