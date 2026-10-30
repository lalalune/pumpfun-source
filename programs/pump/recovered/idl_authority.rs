//! `admin_set_idl_authority`: the admin path that rewrites the authority of
//! Pump's canonical Anchor IDL account, or sweeps the lamports of a
//! system-owned account at that address.
//!
//! A pure model of which check stops the call and what happens to the IDL
//! account. Below 44 bytes the outcome is the LiteSVM one (see
//! `Outcome::InvalidRealloc`). Checked against the captured Pump program by
//! `tests/test_idl_authority_captured.py` on the inputs listed there; that
//! is matching behaviour on those inputs, not a byte-identity claim.

/// Anchor and Pump error numbers.
pub const ACCOUNT_NOT_SIGNER: u32 = 3010;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const CONSTRAINT_ADDRESS: u32 = 2012;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;

/// The handler always reallocates a Pump-owned IDL account to this size.
pub const IDL_SIZE: u64 = 10_240;
/// Discriminator plus authority plus `data_len`: the bytes the handler reads.
pub const HEADER_LEN: u64 = 44;

/// Rent-exempt minimum for `len` data bytes at the default rent.
pub fn rent(len: u64) -> u64 {
    (len + 128) * 6_960
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Owner {
    System,
    Pump,
    Other,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Case {
    pub signed: bool,
    /// `authority` is `global.authority`.
    pub authority_ok: bool,
    /// `idl_account` is `IdlAccount::address(&pump)`.
    pub address_ok: bool,
    /// `program_signer` is Pump's empty-seed PDA.
    pub program_signer_ok: bool,
    /// `authority` is passed writable (the IDL marks it read-only).
    pub authority_writable: bool,
    pub owner: Owner,
    pub size: u64,
    pub lamports: u64,
    /// The first eight bytes are the `IdlAccount` discriminator.
    pub discriminator_ok: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Outcome {
    Error(u32),
    /// The System Program CPI needs `authority` writable.
    Escalation,
    /// `transfer_with_seed` from an account that carries data.
    InvalidArgument,
    /// LiteSVM only: the handler read bytes the realloc had just added.
    InvalidRealloc,
    /// The 10,240-byte account is left below rent exemption.
    InsufficientFundsForRent,
    /// All lamports moved from the IDL address to `authority`; no event.
    Swept(u64),
    /// Resized to `IDL_SIZE`, authority rewritten, lamports kept, event emitted.
    Rewritten,
}

pub fn admin_set_idl_authority(c: &Case) -> Outcome {
    if !c.signed {
        return Outcome::Error(ACCOUNT_NOT_SIGNER);
    }
    if !c.authority_ok {
        return Outcome::Error(NOT_AUTHORIZED);
    }
    if !c.address_ok {
        return Outcome::Error(CONSTRAINT_ADDRESS);
    }
    if !c.program_signer_ok {
        return Outcome::Error(CONSTRAINT_SEEDS);
    }
    match c.owner {
        Owner::System => {
            if !c.authority_writable {
                Outcome::Escalation
            } else if c.size > 0 {
                Outcome::InvalidArgument
            } else {
                Outcome::Swept(c.lamports)
            }
        }
        Owner::Other => Outcome::Error(ACCOUNT_TYPE_NOT_SUPPORTED),
        Owner::Pump => {
            // LiteSVM rejects the first read of bytes the realloc just added:
            // the discriminator read for accounts under 8 bytes, the header
            // read for 8..44 bytes once the discriminator matched.
            // `scripts/pump_idl_authority_surfpool.py` records that Surfpool
            // instead returns 6010 under 8 bytes and succeeds from 8 to 43.
            if c.size < 8 {
                return Outcome::InvalidRealloc;
            }
            if !c.discriminator_ok {
                return Outcome::Error(ACCOUNT_TYPE_NOT_SUPPORTED);
            }
            if c.size < HEADER_LEN {
                return Outcome::InvalidRealloc;
            }
            // The runtime lets an account end below rent exemption only if it
            // already was and its size did not change; a 10,240-byte account
            // below exemption was already below it.
            if c.lamports < rent(IDL_SIZE) && c.size != IDL_SIZE {
                return Outcome::InsufficientFundsForRent;
            }
            Outcome::Rewritten
        }
    }
}
