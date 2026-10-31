//! Account admission and account creation of Pump `initialize_quote_control`.
//!
//! `quote_control.rs` covers who may call the instruction and what it stores.
//! This model takes the three account slots as the caller passes them, and
//! follows Anchor's `init` path: slots are read by position, `user` and
//! `system_program` load first, the address comes next, and the creation
//! branch depends on the lamports the account already holds. `user` is
//! `mut`, but that constraint runs after `init`, so it only shows when the
//! creation needs no payment.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_quote_control_init_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim. Unconfirmed (outside the checked
//! inputs): accounts holding more than one of the listed shapes at once.

pub const ACCOUNT_IN_USE: u32 = 0;
pub const INSUFFICIENT_FUNDS: u32 = 1;
/// Anchor `ConstraintMut`.
pub const CONSTRAINT_MUT: u32 = 2000;
/// Anchor `ConstraintSeeds`.
pub const CONSTRAINT_SEEDS: u32 = 2006;
/// Anchor `AccountNotEnoughKeys`.
pub const NOT_ENOUGH_KEYS: u32 = 3005;
/// Anchor `InvalidProgramId`.
pub const INVALID_PROGRAM_ID: u32 = 3008;
/// Anchor `AccountNotSigner`.
pub const NOT_SIGNER: u32 = 3010;
/// Anchor `TryingToInitPayerAsProgramAccount`.
pub const INIT_PAYER_AS_PROGRAM_ACCOUNT: u32 = 4101;
/// `initialize_quote_control` allocates 8 + 100 + 50 * 40 bytes.
pub const INIT_LEN: u64 = 2_108;
pub const LAMPORTS_PER_BYTE: u64 = 6_960;

pub fn rent(len: u64) -> u64 {
    (128 + len) * LAMPORTS_PER_BYTE
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Key {
    /// The `quote-control` PDA.
    QuoteControl,
    User,
    System,
    Other(u8),
}

/// One instruction account after the transaction merged its flags.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Meta {
    pub key: Key,
    pub signer: bool,
    pub writable: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Stored {
    pub lamports: u64,
    pub has_data: bool,
    pub system_owned: bool,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Request {
    pub accounts: Vec<Meta>,
    /// What is stored at the `quote-control` PDA.
    pub control: Stored,
    /// What is stored at the payer's key.
    pub user: Stored,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    PrivilegeEscalation,
    InvalidArgument,
    ExternalAccountLamportSpend,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Done {
    /// Lamports `user` paid into the account.
    pub paid: u64,
    pub lamports: u64,
}

/// The `transfer` half of account creation, as the System Program refuses it.
fn pay(user: Stored, amount: u64) -> Result<(), Stop> {
    if user.has_data {
        return Err(Stop::InvalidArgument);
    }
    if user.lamports < amount {
        return Err(Stop::Code(INSUFFICIENT_FUNDS));
    }
    if !user.system_owned {
        return Err(Stop::ExternalAccountLamportSpend);
    }
    Ok(())
}

pub fn initialize(r: &Request) -> Result<Done, Stop> {
    // Slot 0 is taken unread; the `init` field loads with the constraints.
    let control = *r.accounts.first().ok_or(Stop::Code(NOT_ENOUGH_KEYS))?;
    let user = *r.accounts.get(1).ok_or(Stop::Code(NOT_ENOUGH_KEYS))?;
    if !user.signer {
        return Err(Stop::Code(NOT_SIGNER));
    }
    let system = *r.accounts.get(2).ok_or(Stop::Code(NOT_ENOUGH_KEYS))?;
    if system.key != Key::System {
        return Err(Stop::Code(INVALID_PROGRAM_ID));
    }
    if control.key != Key::QuoteControl {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    let needed = rent(INIT_LEN);
    let same = user.key == control.key;
    let paid = if r.control.lamports == 0 {
        // `create_account` with the whole rent.
        if !control.writable || !user.writable {
            return Err(Stop::PrivilegeEscalation);
        }
        if same {
            return Err(Stop::InvalidArgument);
        }
        pay(r.user, needed)?;
        needed
    } else {
        // Top up, then `allocate` and `assign`: whatever the account holds is
        // not read, and the owner is only refused by `allocate`.
        if same {
            return Err(Stop::Code(INIT_PAYER_AS_PROGRAM_ACCOUNT));
        }
        let shortfall = needed.saturating_sub(r.control.lamports);
        if shortfall > 0 {
            if !control.writable || !user.writable {
                return Err(Stop::PrivilegeEscalation);
            }
            pay(r.user, shortfall)?;
        }
        if !control.writable {
            return Err(Stop::PrivilegeEscalation);
        }
        if r.control.has_data || !r.control.system_owned {
            return Err(Stop::Code(ACCOUNT_IN_USE));
        }
        shortfall
    };
    if !user.writable {
        return Err(Stop::Code(CONSTRAINT_MUT));
    }
    Ok(Done { paid, lamports: r.control.lamports + paid })
}
