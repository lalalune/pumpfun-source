//! Captured reading of the stored shape of pump_fees' `SharingConfig` under
//! native `distribute_creator_fees_v2`.
//!
//! `config_length.rs` reads the stored shapes of the list accounts for the
//! typed readers it covers, and leaves this route out: when it was written,
//! the native route's base model was not on main. That model is
//! `distribution_v2_native_admission.rs` (#3534), so the shape can now be read
//! here the same way.
//!
//! The reader is the same Anchor-typed one as on the other `SharingConfig`
//! slots: an 80-byte header and 34-byte rows behind it, decoded one row at a
//! time onto the 32 KiB bump heap, so more than 480 rows present runs out of
//! memory during the decode, and a count past the rows that fit is 3003. What
//! this route adds is where the second heap limit sits. Past the decode the
//! distributions can hold 240 rows; on `distribute_creator_fees` a failing
//! account constraint answers first, so the limit shows only on admitted
//! calls. Here it does not wait for the constraints: a config whose creator
//! or mint constraint fails still runs out of memory at 241 rows, like the
//! token route of this same instruction in `config_length.rs`. Which
//! allocation fails there is unconfirmed.
//!
//! A shape that passes leaves the outcome of the same call on an honest
//! account, so the handler stays with `creator_fee_distribution.rs` and the
//! admission model. Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_stored_list_native_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

/// Anchor `AccountDiscriminatorNotFound`.
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
/// Anchor `AccountDiscriminatorMismatch`.
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
/// Anchor `AccountDidNotDeserialize`.
pub const DID_NOT_DESERIALIZE: u32 = 3003;

pub const SHARING_HEADER: u64 = 80;
pub const SHARING_ROW: u64 = 34;
/// 4,096 / 34 = 120 rows, doubled twice: the decode's row limit.
pub const DECODE_ROWS_LIMIT: u64 = 480;
/// Rows the handler can hold on the heap past the decode on this route.
pub const HANDLER_ROWS_LIMIT: u64 = 240;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Stored {
    pub len: u64,
    pub disc_ok: bool,
    /// The count stored behind the header.
    pub count: u64,
    /// `status` and `revoked` hold valid Borsh values.
    pub fields_ok: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Answer {
    /// The outcome of an honest account holding `count` rows holds.
    Pass,
    Error(u32),
    /// The heap runs out: no Anchor code, the VM stops.
    OutOfMemory,
}

/// `Account::try_from` on the `sharing_config` slot of native
/// `distribute_creator_fees_v2`, and the allocation that follows the decode.
pub fn typed_load(s: Stored) -> Answer {
    if s.len < 8 {
        return Answer::Error(DISCRIMINATOR_NOT_FOUND);
    }
    if !s.disc_ok {
        return Answer::Error(DISCRIMINATOR_MISMATCH);
    }
    if s.len < SHARING_HEADER || !s.fields_ok {
        return Answer::Error(DID_NOT_DESERIALIZE);
    }
    let fit = (s.len - SHARING_HEADER) / SHARING_ROW;
    // Rows are read one at a time, so the heap can run out before the bytes do.
    if s.count.min(fit) > DECODE_ROWS_LIMIT {
        return Answer::OutOfMemory;
    }
    if s.count > fit {
        return Answer::Error(DID_NOT_DESERIALIZE);
    }
    // Ahead of the account constraints on this route: admission does not
    // gate this limit (checked with a failing creator and a failing mint).
    if s.count > HANDLER_ROWS_LIMIT {
        return Answer::OutOfMemory;
    }
    Answer::Pass
}
