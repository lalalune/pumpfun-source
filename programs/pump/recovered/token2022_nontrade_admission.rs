//! Captured admission of Token-2022 account bodies outside the trades:
//! `sweep_protocol_fee`, `sweep_creator_fee`, `collect_creator_fee_v2`,
//! `claim_cashback_v2`, `admin_update_token_incentives`,
//! `claim_token_incentives`, `distribute_creator_fees_v2` and
//! `distribute_fee_to_holders`, each on one Token-2022 mint.
//!
//! A route is an ordered list of stops. A stop names a slot, what it looks at
//! and how it ends; the first stop that fires ends the instruction. Slots are 0
//! for the mint and 1, 2 for the two token accounts of the route.
//!
//! Two readers are modelled. `load_mint` and `load_token` read a declared
//! account in Pump. The base comes first, after the short and multisig (355)
//! lengths, so an uninitialized body names itself ahead of a bad tail. The tail
//! must then be a whole layout: 83 to 166 bytes on a mint and exactly 166 on a
//! token account are refused, as is a non-zero mint pad. `open_token` is the captured Token-2022 program
//! reading a slot Pump does not type. It takes 166 bytes and does not check the
//! option tags. A TLV entry running past the account's end passes all three.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token, Token-2022 and Associated Token programs by
//! `tests/test_token2022_nontrade_admission_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim. Unconfirmed: extensions other
//! than the two test entries, a TLV entry that a transfer reads, migrate.

pub const MINT_LEN: usize = 82;
pub const TOKEN_LEN: usize = 165;
pub const MULTISIG_LEN: usize = 355;
/// Offset of the account type byte, on mints and on token accounts.
pub const TYPE_BYTE: usize = 165;
pub const TYPE_MINT: u8 = 1;
pub const TYPE_TOKEN: u8 = 2;

const WRONG_PROGRAM: Ending = Ending::IncorrectProgramId;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ending {
    Ok,
    Code(u32),
    InvalidAccountData,
    UninitializedAccount,
    IncorrectProgramId,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Check {
    /// The declared mint or token account load.
    Load,
    /// The body as the Token-2022 program reads it in a transfer.
    Open,
    /// The account is owned by the other token program.
    Program,
    /// The stored mint is not the instruction's mint.
    Mint,
    /// The stored authority is not the expected one.
    Authority,
    /// The token account is frozen.
    Frozen,
}

use Check::*;
use Ending::*;

type Stop = (usize, Check, Ending);
const LOADED: Ending = Ok; // The ending comes from the body.

const fn code(value: u32) -> Ending {
    Code(value)
}

pub const SWEEP: &[Stop] = &[
    (0, Load, LOADED),
    (1, Program, code(6010)),
    (1, Load, LOADED),
    (1, Mint, code(6004)),
    (2, Program, code(6010)),
    (2, Load, LOADED),
    (2, Mint, code(6004)),
    (1, Frozen, code(17)),
    (0, Program, WRONG_PROGRAM),
    (1, Authority, code(4)),
    (2, Frozen, code(17)),
];
pub const SWEEP_EMPTY: &[Stop] = &[(0, Load, LOADED)];
pub const COLLECT: &[Stop] = &[
    (0, Load, LOADED),
    (1, Load, LOADED),
    (1, Program, WRONG_PROGRAM),
    (2, Program, WRONG_PROGRAM),
    (1, Frozen, code(17)),
    (0, Program, WRONG_PROGRAM),
    (1, Mint, code(3)),
    (1, Authority, code(4)),
    (2, Open, LOADED),
    (2, Frozen, code(17)),
    (2, Mint, code(3)),
];
pub const COLLECT_EMPTY: &[Stop] = &[(0, Load, LOADED), (1, Load, LOADED)];
pub const CASHBACK: &[Stop] = &[
    (0, Program, code(6010)),
    (1, Load, LOADED),
    (2, Program, code(6010)),
    (2, Load, LOADED),
    (2, Authority, code(6076)),
    (0, Load, LOADED),
    (1, Program, WRONG_PROGRAM),
    (1, Frozen, code(17)),
    (1, Mint, code(3)),
    (1, Authority, code(4)),
    (2, Frozen, code(17)),
    (2, Mint, code(3)),
];
pub const CASHBACK_EMPTY: &[Stop] = &[(0, Program, code(6010)), (1, Load, LOADED)];
pub const SCHEDULE: &[Stop] = &[
    (0, Load, LOADED),
    (1, Load, LOADED),
    (1, Mint, code(2014)),
    (1, Authority, code(2015)),
    (1, Program, code(2023)),
];
pub const CLAIM: &[Stop] = &[
    (2, Load, LOADED),
    (0, Load, LOADED),
    (1, Load, LOADED),
    (1, Mint, code(2014)),
    (1, Authority, code(2015)),
    (1, Program, code(2023)),
    (2, Program, code(2023)),
    (2, Authority, code(2015)),
    (2, Frozen, code(17)),
    (0, Program, WRONG_PROGRAM),
    (2, Mint, code(3)),
    (1, Frozen, code(17)),
];
pub const DISTRIBUTE: &[Stop] = &[
    (0, Load, LOADED),
    (1, Load, LOADED),
    (0, Program, code(6054)),
    (1, Program, WRONG_PROGRAM),
    (2, Program, WRONG_PROGRAM),
    (1, Frozen, code(17)),
    (1, Mint, code(3)),
    (1, Authority, code(4)),
    (2, Open, LOADED),
    (2, Frozen, code(17)),
    (2, Mint, code(3)),
];
pub const HOLDER: &[Stop] = &[
    (1, Load, LOADED),
    (0, Load, LOADED),
    (1, Authority, code(2015)),
    (1, Mint, code(2014)),
    (1, Program, code(2021)),
    (2, Program, WRONG_PROGRAM),
    (1, Frozen, code(17)),
    (0, Program, WRONG_PROGRAM),
    (2, Open, LOADED),
    (2, Frozen, code(17)),
    (2, Mint, code(3)),
];
pub const HOLDER_ZERO: &[Stop] =
    &[(1, Load, LOADED), (0, Load, LOADED), (1, Authority, code(2015)), (1, Mint, code(2014)), (1, Program, code(2021))];

pub fn route(name: &str) -> Option<&'static [Stop]> {
    Some(match name {
        "sweep_protocol" | "sweep_creator" => SWEEP,
        "sweep_empty" => SWEEP_EMPTY,
        "collect_v2" => COLLECT,
        "collect_empty" => COLLECT_EMPTY,
        "cashback_v2" => CASHBACK,
        "cashback_empty" => CASHBACK_EMPTY,
        "schedule" => SCHEDULE,
        "claim_incentives" => CLAIM,
        "distribute_v2" => DISTRIBUTE,
        "holder" => HOLDER,
        "holder_zero" => HOLDER_ZERO,
        _ => return None,
    })
}

#[derive(Clone, Debug)]
pub struct Slot {
    pub data: Vec<u8>,
    /// Owned by the route's token program.
    pub right_program: bool,
    pub expected_mint: Vec<u8>,
    pub expected_authority: Vec<u8>,
}

fn tag_ok(data: &[u8], at: usize) -> bool {
    u32::from_le_bytes([data[at], data[at + 1], data[at + 2], data[at + 3]]) <= 1
}

fn type_ok(data: &[u8], base: usize, wanted: u8) -> bool {
    data.len() == base || data[TYPE_BYTE] == wanted
}

pub fn load_mint(data: &[u8]) -> Ending {
    let n = data.len();
    if n < MINT_LEN || n == MULTISIG_LEN {
        return InvalidAccountData;
    }
    if !tag_ok(data, 0) || !tag_ok(data, 46) || data[45] > 1 {
        return InvalidAccountData;
    }
    if data[45] == 0 {
        return UninitializedAccount;
    }
    if n == MINT_LEN {
        return Ok;
    }
    if n <= TYPE_BYTE + 1 || data[MINT_LEN..TYPE_BYTE].iter().any(|b| *b != 0) || data[TYPE_BYTE] != TYPE_MINT {
        return InvalidAccountData;
    }
    Ok
}

pub fn load_token(data: &[u8]) -> Ending {
    let n = data.len();
    if n < TOKEN_LEN || n == MULTISIG_LEN {
        return InvalidAccountData;
    }
    if !tag_ok(data, 72) || !tag_ok(data, 109) || !tag_ok(data, 129) || data[108] > 2 {
        return InvalidAccountData;
    }
    if data[108] == 0 {
        return UninitializedAccount;
    }
    if n == TYPE_BYTE + 1 || !type_ok(data, TOKEN_LEN, TYPE_TOKEN) {
        return InvalidAccountData;
    }
    Ok
}

pub fn open_token(data: &[u8]) -> Ending {
    let n = data.len();
    if n < TOKEN_LEN || n == MULTISIG_LEN {
        return InvalidAccountData;
    }
    if data[108] == 0 || data[108] > 2 {
        return UninitializedAccount;
    }
    if !type_ok(data, TOKEN_LEN, TYPE_TOKEN) {
        return InvalidAccountData;
    }
    Ok
}

fn fired(index: usize, slot: &Slot, check: Check, ending: Ending) -> Option<Ending> {
    let stored = |at: usize, wanted: &[u8]| slot.data.len() >= at + 32 && slot.data[at..at + 32] != *wanted;
    let found = match check {
        Load => {
            let read = if index == 0 { load_mint(&slot.data) } else { load_token(&slot.data) };
            return (read != Ok).then_some(read);
        }
        Open => {
            let read = open_token(&slot.data);
            return (read != Ok).then_some(read);
        }
        Program => !slot.right_program,
        Mint => stored(0, &slot.expected_mint),
        Authority => stored(32, &slot.expected_authority),
        Frozen => slot.data.len() > 108 && slot.data[108] == 2,
    };
    found.then_some(ending)
}

pub fn ending(stops: &[Stop], slots: &[Slot]) -> Ending {
    for (index, check, stop) in stops {
        if let Some(found) = slots.get(*index).and_then(|slot| fired(*index, slot, *check, *stop)) {
            return found;
        }
    }
    Ok
}
