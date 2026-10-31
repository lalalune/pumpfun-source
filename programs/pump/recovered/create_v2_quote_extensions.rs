//! Captured check of a `create_v2` quote mint's raw bytes: which Token-2022
//! extensions a quote may carry, and the account the curve gets for it. This is
//! the part `create_v2.rs` lists as unconfirmed.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token, Token-2022 and Associated Token programs by
//! `tests/test_create_v2_quote_extensions_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.

pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
/// SPL Token and Token-2022 `InvalidMint`, from the quote account's creation.
pub const TOKEN_INVALID_MINT: u32 = 2;

const MINT_LEN: usize = 82;
/// Token-2022 reads an account of this length as a multisig.
const MULTISIG_LEN: usize = 355;
const ACCOUNT_LEN: usize = 165;
const MINT_ACCOUNT_TYPE: u8 = 1;
const FEE_CONFIG_LEN: usize = 108;
const TRANSFER_FEE: u16 = 1;
const DEFAULT_ACCOUNT_STATE: u16 = 6;
const TRANSFER_HOOK: u16 = 14;
const PAUSABLE: u16 = 26;
const ACCOUNT_STATE_INITIALIZED: u8 = 1;
const SPL_ATA_SIZE: u64 = 165;
/// A Token-2022 account: the SPL layout, the type byte, ImmutableOwner.
const ATA_SIZE: u64 = 170;

/// Accepted extension kinds: the metadata pair (18, 19) and these token ones.
fn allowed(kind: u16) -> bool {
    matches!(kind, 1 | 4 | 6 | 12 | 14 | 16 | 18 | 19 | 25 | 26)
}

fn body_valid(kind: u16, body: &[u8]) -> bool {
    match kind {
        TRANSFER_FEE => body.len() >= FEE_CONFIG_LEN,
        DEFAULT_ACCOUNT_STATE => body.first() == Some(&ACCOUNT_STATE_INITIALIZED),
        // No hook program may be set.
        TRANSFER_HOOK => body.len() >= 64 && body[32..64].iter().all(|b| *b == 0),
        _ => true,
    }
}

/// The extension kinds of a supported mint, or `None`. A bare 82-byte mint has
/// none. Anything else needs zero padding up to the type byte, and at least one
/// byte after it. The walk stops at kind 0 or with under two bytes left, and
/// refuses a cut header, an entry past the end, a repeated kind, a kind off the
/// list, and the bodies `body_valid` refuses.
pub fn extension_kinds(data: &[u8]) -> Option<Vec<u16>> {
    if data.len() == MINT_LEN {
        return Some(Vec::new());
    }
    if data.len() <= ACCOUNT_LEN + 1
        || data[MINT_LEN..ACCOUNT_LEN].iter().any(|b| *b != 0)
        || data[ACCOUNT_LEN] != MINT_ACCOUNT_TYPE
    {
        return None;
    }
    let tlv = &data[ACCOUNT_LEN + 1..];
    let mut kinds = Vec::new();
    let mut offset = 0;
    loop {
        let rest = &tlv[offset..];
        if rest.len() < 2 {
            return Some(kinds);
        }
        let kind = u16::from_le_bytes([rest[0], rest[1]]);
        if kind == 0 {
            return Some(kinds);
        }
        if rest.len() < 4 {
            return None;
        }
        let size = usize::from(u16::from_le_bytes([rest[2], rest[3]]));
        if size + 4 > rest.len() || !allowed(kind) || kinds.contains(&kind) || !body_valid(kind, &rest[4..size + 4]) {
            return None;
        }
        kinds.push(kind);
        offset += size + 4;
    }
}

/// Size of the curve's quote account for a supported Token-2022 mint.
pub fn quote_account_size(kinds: &[u16]) -> u64 {
    kinds.iter().fold(ATA_SIZE, |size, kind| {
        size + match *kind {
            TRANSFER_FEE => 12,
            TRANSFER_HOOK => 5,
            PAUSABLE => 4,
            _ => 0,
        }
    })
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    IllegalOwner,
}

/// One other failure of the same create, from the rules in `create_v2.rs`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Gate {
    /// Fails ahead of the mint's bytes (quote curve, creator, enable flag).
    Before(u32),
    /// Fails behind them (quote account address).
    After(u32),
    /// The curve's quote account already exists.
    QuoteAccountExists,
    /// Fails behind the creation of the quote account (name, symbol).
    Late(u32),
}

/// Outcome of a create with this mint: the quote account's size. The bytes are
/// only read for Token-2022, after the quote routing and ahead of everything
/// that uses the mint. SPL Token refuses them itself, later, at the creation of
/// the quote account, and so does Token-2022 for a multisig-sized mint.
pub fn check(data: &[u8], spl_program: bool, gate: Option<Gate>) -> Result<u64, Stop> {
    if let Some(Gate::Before(code)) = gate {
        return Err(Stop::Code(code));
    }
    let kinds = if spl_program {
        None
    } else {
        Some(extension_kinds(data).ok_or(Stop::Code(UNSUPPORTED_QUOTE_MINT))?)
    };
    match gate {
        Some(Gate::After(code)) => return Err(Stop::Code(code)),
        Some(Gate::QuoteAccountExists) => return Err(Stop::IllegalOwner),
        _ => {}
    }
    let size = match kinds {
        None if data.len() != MINT_LEN => return Err(Stop::Code(TOKEN_INVALID_MINT)),
        None => SPL_ATA_SIZE,
        Some(_) if data.len() == MULTISIG_LEN => return Err(Stop::Code(TOKEN_INVALID_MINT)),
        Some(kinds) => quote_account_size(&kinds),
    };
    match gate {
        Some(Gate::Late(code)) => Err(Stop::Code(code)),
        _ => Ok(size),
    }
}
