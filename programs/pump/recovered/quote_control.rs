//! QuoteControl registry: `initialize_quote_control`, `add_quote_control_mint`,
//! `remove_quote_control_mint`, `set_quote_control_mint_reserves`,
//! `set_quote_control_admin` and `set_quote_control_reserves_admin`.
//!
//! A pure model of who may call each instruction, how the mint list and the
//! two admin keys change, the account size, and the lamports the signer pays.
//! Keys and mints are small ids (`DEFAULT` is the all-zero key, `NATIVE` the
//! wrapped-SOL mint). Checked against the captured program by
//! `tests/test_quote_control_captured.py` on the inputs listed there; it is
//! not a byte-identity claim.

pub const DEFAULT: u8 = 0;
pub const NATIVE: u8 = 1;
/// discriminator + admin + reserves_admin + reserved + vec length.
pub const HEADER_LEN: u64 = 8 + 32 + 32 + 32 + 4;
/// One `QuoteControlMint`: mint + initial virtual quote reserves.
pub const ENTRY_LEN: u64 = 40;
/// `initialize_quote_control` allocates room for 50 entries, but the list
/// itself is not capped.
pub const INIT_LEN: u64 = HEADER_LEN + 50 * ENTRY_LEN;
pub const LAMPORTS_PER_BYTE: u64 = 6_960;

pub const ACCOUNT_IN_USE: u32 = 0;
pub const INSUFFICIENT_FUNDS: u32 = 1;
pub const ACCOUNT_NOT_INITIALIZED: u32 = 3012;
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_AUTHORIZED: u32 = 6000;
pub const ALREADY_WHITELISTED: u32 = 6067;
pub const NOT_WHITELISTED: u32 = 6068;
pub const NOT_ELIGIBLE: u32 = 6069;

pub fn rent(len: u64) -> u64 {
    (128 + len) * LAMPORTS_PER_BYTE
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Holder {
    Missing,
    System,
    WrongOwner,
    BadDiscriminator,
    Short,
    Control,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Control {
    pub admin: u8,
    pub reserves_admin: u8,
    pub mints: Vec<(u8, u64)>,
    pub len: u64,
    pub lamports: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Op {
    Initialize,
    Add { mint: u8, reserves: u64 },
    Remove { mint: u8 },
    SetReserves { mint: u8, reserves: u64 },
    SetAdmin { new_admin: u8 },
    SetReservesAdmin { new_admin: u8 },
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Done {
    pub control: Control,
    /// Lamports the signer paid into the account.
    pub paid: u64,
    /// The value the event reports as replaced (old reserves or old admin).
    pub old: u64,
}

pub fn serialized_len(entries: usize) -> u64 {
    HEADER_LEN + ENTRY_LEN * entries as u64
}

fn load(holder: Holder) -> Result<(), u32> {
    match holder {
        Holder::Control => Ok(()),
        Holder::Missing => Err(ACCOUNT_NOT_INITIALIZED),
        Holder::System | Holder::WrongOwner => Err(ACCOUNT_OWNED_BY_WRONG_PROGRAM),
        Holder::BadDiscriminator => Err(DISCRIMINATOR_MISMATCH),
        Holder::Short => Err(DID_NOT_DESERIALIZE),
    }
}

fn authorize(allowed: bool) -> Result<(), u32> {
    if allowed {
        Ok(())
    } else {
        Err(NOT_AUTHORIZED)
    }
}

/// `holder`/`control` describe the account before the call; `control.lamports`
/// is its balance even when it is not a QuoteControl.
pub fn apply(
    op: Op,
    signed: bool,
    signer: u8,
    signer_lamports: u64,
    global_authority: u8,
    holder: Holder,
    control: &Control,
) -> Result<Done, u32> {
    if !signed {
        return Err(NOT_SIGNER);
    }
    if op == Op::Initialize {
        // A pre-funded account is topped up before it is allocated, so a
        // short signer fails first even when the account is already in use.
        let paid = rent(INIT_LEN).saturating_sub(control.lamports);
        if paid > signer_lamports {
            return Err(INSUFFICIENT_FUNDS);
        }
        if !matches!(holder, Holder::Missing | Holder::System) {
            return Err(ACCOUNT_IN_USE);
        }
        let fresh = Control {
            admin: DEFAULT,
            reserves_admin: DEFAULT,
            mints: Vec::new(),
            len: INIT_LEN,
            lamports: control.lamports + paid,
        };
        return Ok(Done { control: fresh, paid, old: 0 });
    }
    load(holder)?;
    let is_admin = signer == control.admin;
    let is_global = signer == global_authority;
    let mut next = control.clone();
    let position = |mint: u8| control.mints.iter().position(|entry| entry.0 == mint);
    let mut paid = 0;
    let old = match op {
        Op::Initialize => unreachable!(),
        Op::Add { mint, reserves } => {
            authorize(is_admin || is_global)?;
            if mint == DEFAULT || mint == NATIVE {
                return Err(NOT_ELIGIBLE);
            }
            if position(mint).is_some() {
                return Err(ALREADY_WHITELISTED);
            }
            next.mints.push((mint, reserves));
            let needed = serialized_len(next.mints.len());
            if next.len < needed {
                paid = rent(needed).saturating_sub(next.lamports);
                if paid > signer_lamports {
                    return Err(INSUFFICIENT_FUNDS);
                }
                next.len = needed;
                next.lamports += paid;
            }
            reserves
        }
        Op::Remove { mint } => {
            authorize(is_admin || is_global)?;
            if mint == DEFAULT {
                return Err(NOT_ELIGIBLE);
            }
            let index = position(mint).ok_or(NOT_WHITELISTED)?;
            next.mints.remove(index);
            0
        }
        Op::SetReserves { mint, reserves } => {
            authorize(is_admin || is_global || signer == control.reserves_admin)?;
            let index = position(mint).ok_or(NOT_WHITELISTED)?;
            let old = next.mints[index].1;
            next.mints[index].1 = reserves;
            old
        }
        Op::SetAdmin { new_admin } => {
            authorize(is_global)?;
            next.admin = new_admin;
            control.admin as u64
        }
        Op::SetReservesAdmin { new_admin } => {
            authorize(is_admin || is_global)?;
            next.reserves_admin = new_admin;
            control.reserves_admin as u64
        }
    };
    Ok(Done { control: next, paid, old })
}
