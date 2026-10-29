//! Bonding-curve creator assignment: `set_creator`, `set_metaplex_creator`
//! and `migrate_bonding_curve_creator`.
//!
//! A pure model of which creator ends up in the bonding curve, which event
//! is emitted and which check stops the call. Keys are small ids
//! (`DEFAULT` is the all-zero key). Checked against the captured program by
//! `tests/test_creator_assignment_captured.py` on the inputs listed there;
//! it is not a byte-identity claim.

/// The all-zero key.
pub const DEFAULT: u8 = 0;
/// Size the curve is written back at; shorter accounts fail on write.
pub const CURVE_LEN: u64 = 166;
/// Shortest curve that still deserializes (discriminator..complete flag).
pub const CURVE_READ_MIN: u64 = 49;
/// Shortest curve whose `creator` (offset 49) is read; shorter reads as unset.
pub const CREATOR_READ_MIN: u64 = 81;
/// Shortest curve whose `is_holder_reward` flag (offset 124) is read.
pub const HOLDER_REWARD_READ_MIN: u64 = 125;
/// Shortest curve whose `creator_fee` (offset 125) is read; it is read
/// together with `protocol_fees`, so both must be present.
pub const CREATOR_FEE_READ_MIN: u64 = 141;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Load {
    Ok,
    Missing,
    WrongOwner,
    BadDiscriminator,
    BadData,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub signed: bool,
    pub authority_ok: bool,
    pub metadata: Load,
    pub metadata_address_ok: bool,
    /// Metaplex `creators`: `None` or the creator keys in order.
    pub creators: Option<Vec<u8>>,
    pub curve_len: u64,
    pub curve_address_ok: bool,
    pub curve_creator: u8,
    pub holder_reward: bool,
    pub creator_fee: u64,
    pub argument: u8,
    pub sharing: Load,
    pub sharing_address_ok: bool,
    pub sharing_mint_ok: bool,
    pub sharing_admin: u8,
    /// Id of the sharing-config PDA key.
    pub sharing_key: u8,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Event {
    None,
    SetCreator,
    SetMetaplexCreator,
    Migrate { old: u8 },
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Done {
    pub creator: u8,
    pub event: Event,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    BorshRead,
    BorshWrite,
    Panic,
}

fn load(state: Load) -> Result<(), Stop> {
    match state {
        Load::Ok => Ok(()),
        Load::Missing => Err(Stop::Code(3012)),
        Load::WrongOwner => Err(Stop::Code(3007)),
        Load::BadDiscriminator => Err(Stop::Code(3002)),
        Load::BadData => Err(Stop::Code(3003)),
    }
}

/// Metaplex metadata is Borsh-decoded: a bad key byte or short data is an IO error.
fn load_metadata(state: Load) -> Result<(), Stop> {
    match state {
        Load::BadDiscriminator | Load::BadData => Err(Stop::BorshRead),
        other => load(other),
    }
}

fn load_curve(case: &Case) -> Result<(), Stop> {
    if case.curve_len < CURVE_READ_MIN {
        return Err(Stop::InvalidAccountData);
    }
    Ok(())
}

/// The stored creator as the program reads it.
fn stored_creator(case: &Case) -> u8 {
    if case.curve_len >= CREATOR_READ_MIN {
        case.curve_creator
    } else {
        DEFAULT
    }
}

fn write_curve(case: &Case, done: Done) -> Result<Done, Stop> {
    if case.curve_len < CURVE_LEN {
        return Err(Stop::BorshWrite);
    }
    Ok(done)
}

fn seeds(ok: bool) -> Result<(), Stop> {
    if ok {
        Ok(())
    } else {
        Err(Stop::Code(2006))
    }
}

/// The first Metaplex creator, verified or not. An empty list panics.
fn first_creator(creators: &[u8]) -> Result<u8, Stop> {
    creators.first().copied().ok_or(Stop::Panic)
}

/// `set_creator`: the set-creator authority fills an unset creator. When the
/// metadata lists creators the first one wins over the argument.
pub fn set_creator(case: &Case) -> Result<Done, Stop> {
    if !case.signed {
        return Err(Stop::Code(3010));
    }
    load_metadata(case.metadata)?;
    load_curve(case)?;
    if !case.authority_ok {
        return Err(Stop::Code(6000));
    }
    seeds(case.metadata_address_ok)?;
    seeds(case.curve_address_ok)?;
    let done = if case.curve_creator != DEFAULT {
        Done { creator: case.curve_creator, event: Event::None }
    } else {
        match &case.creators {
            Some(list) => Done { creator: first_creator(list)?, event: Event::SetMetaplexCreator },
            None => Done { creator: case.argument, event: Event::SetCreator },
        }
    };
    write_curve(case, done)
}

/// `set_metaplex_creator`: unsigned; copies the first Metaplex creator into
/// an unset curve creator. No creators list leaves the curve alone.
pub fn set_metaplex_creator(case: &Case) -> Result<Done, Stop> {
    load_metadata(case.metadata)?;
    load_curve(case)?;
    seeds(case.metadata_address_ok)?;
    seeds(case.curve_address_ok)?;
    let unchanged = Done { creator: case.curve_creator, event: Event::None };
    let done = match (&case.creators, case.curve_creator != DEFAULT) {
        (_, true) | (None, _) => unchanged,
        (Some(list), false) => Done { creator: first_creator(list)?, event: Event::SetMetaplexCreator },
    };
    write_curve(case, done)
}

/// `migrate_bonding_curve_creator`: when the curve creator is the sharing
/// config's admin, the creator becomes the sharing-config PDA, unless the
/// coin is a holder-reward coin or unswept creator fees remain. Status and
/// `admin_revoked` are not consulted.
pub fn migrate_bonding_curve_creator(case: &Case) -> Result<Done, Stop> {
    load_curve(case)?;
    load(case.sharing)?;
    seeds(case.curve_address_ok)?;
    seeds(case.sharing_address_ok)?;
    if !case.sharing_mint_ok {
        return Err(Stop::Code(6004));
    }
    let old = stored_creator(case);
    if old != case.sharing_admin {
        return Err(Stop::Code(6053));
    }
    if case.holder_reward && case.curve_len >= HOLDER_REWARD_READ_MIN {
        return Err(Stop::Code(6083));
    }
    if case.creator_fee != 0 && case.curve_len >= CREATOR_FEE_READ_MIN {
        return Err(Stop::Code(6095));
    }
    let done = Done { creator: case.sharing_key, event: Event::Migrate { old } };
    write_curve(case, done)
}
