//! Captured behavior of the token route of Pump `claim_cashback_v2` on a
//! Token-2022 quote mint, on top of the totals and event in
//! `claim_cashback_v2.rs`: the account shapes that model reduces to flags, the
//! transfer fee on the way to the user, and the order of the failures.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token, Token-2022 and Associated Token programs by
//! `tests/test_claim_cashback_v2_token2022_captured.py`. Not linked into the
//! SBF crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): extensions other than the
//! ones named here, a hook program that is really invoked, and interest-bearing
//! or scaled-amount mints.

use crate::claim_cashback_v2::{self, Claim, Claimed, QuoteUser, Stop as BaseStop};

pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = claim_cashback_v2::ACCOUNT_TYPE_NOT_SUPPORTED;
pub const INVALID_QUOTE_TOKEN_PROGRAM: u32 = claim_cashback_v2::INVALID_QUOTE_TOKEN_PROGRAM;
pub const INVALID_CASHBACK_RECIPIENT: u32 = claim_cashback_v2::INVALID_CASHBACK_RECIPIENT;
pub const TOKEN_MINT_MISMATCH: u32 = 3;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER: u32 = 42;
pub const TOKEN_MINT_PAUSED: u32 = 67;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TransferFee {
    pub older_bps: u16,
    pub older_max: u64,
    pub newer_epoch: u64,
    pub newer_bps: u16,
    pub newer_max: u64,
}

impl TransferFee {
    pub fn withheld(&self, epoch: u64, amount: u64) -> u64 {
        let (bps, max) = if epoch >= self.newer_epoch {
            (self.newer_bps, self.newer_max)
        } else {
            (self.older_bps, self.older_max)
        };
        let fee = (u128::from(amount) * u128::from(bps)).div_ceil(10_000);
        fee.min(u128::from(max)) as u64
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Mint {
    pub owner_matches_program: bool,
    /// Owned by the token program but too short to read as a mint.
    pub truncated: bool,
    pub fee: Option<TransferFee>,
    pub hook_set: bool,
    pub paused: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Holding {
    pub balance: u64,
    pub frozen: bool,
    pub fee_extension: bool,
    /// The stored token owner is the UVA (source) or `user` (destination).
    pub owner_matches: bool,
    pub mint_matches: bool,
    pub memo_required: bool,
    pub cpi_guard: bool,
    pub non_transferable: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ata {
    Missing,
    /// Well-formed data under the other token program.
    WrongProgram(Holding),
    Truncated,
    Uninitialized,
    Held(Holding),
}

pub struct ClaimToken2022<'a> {
    pub user: [u8; 32],
    /// `quote_token_program` is SPL Token or Token-2022.
    pub token_program_ok: bool,
    pub mint: Mint,
    pub epoch: u64,
    pub uva_ata_address_ok: bool,
    pub uva_ata: Ata,
    pub user_ata: Ata,
    pub uva_lamports: u64,
    pub uva_data: &'a [u8],
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    UninitializedAccount,
    IncorrectProgramId,
    /// A checked add on a claimed total overflowed (`expect`).
    Panic,
}

#[derive(Debug, PartialEq, Eq)]
pub struct ClaimedToken2022 {
    pub claimed: Claimed,
    pub withheld: u64,
}

fn parsed(ata: &Ata) -> Result<Holding, Stop> {
    match ata {
        Ata::Missing | Ata::Truncated => Err(Stop::InvalidAccountData),
        Ata::Uninitialized => Err(Stop::UninitializedAccount),
        Ata::WrongProgram(held) | Ata::Held(held) => Ok(*held),
    }
}

fn transfer(c: &ClaimToken2022, source: &Holding, destination: &Holding) -> Result<u64, Stop> {
    let amount = source.balance;
    if source.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if source.non_transferable {
        return Err(Stop::Code(TOKEN_NON_TRANSFERABLE));
    }
    if !source.mint_matches {
        return Err(Stop::Code(TOKEN_MINT_MISMATCH));
    }
    if c.mint.paused {
        return Err(Stop::Code(TOKEN_MINT_PAUSED));
    }
    if !source.owner_matches {
        return Err(Stop::Code(TOKEN_OWNER_MISMATCH));
    }
    if source.cpi_guard {
        return Err(Stop::Code(TOKEN_CPI_GUARD_TRANSFER));
    }
    if destination.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if !destination.mint_matches {
        return Err(Stop::Code(TOKEN_MINT_MISMATCH));
    }
    if destination.memo_required {
        return Err(Stop::Code(TOKEN_NO_MEMO));
    }
    let withheld = c.mint.fee.map_or(0, |fee| fee.withheld(c.epoch, amount));
    if withheld != 0 && !destination.fee_extension {
        return Err(Stop::Code(TOKEN_INVALID_STATE));
    }
    if c.mint.hook_set {
        return Err(Stop::InvalidAccountData);
    }
    Ok(withheld)
}

/// In order, after the Anchor UVA load: UVA ATA address (2006), token program
/// (6064), mint owner (6010); no UVA ATA or an empty one is a no-op. Pump then
/// checks the user's account itself (owner program 6010, parse, stored owner
/// 6076, any mint is left to the token program) and parses the mint before
/// the transfer. The claimed total only moves after a good transfer, so a
/// token failure wins over the panic on an overflowing total.
pub fn claim(c: &ClaimToken2022, timestamp: i64) -> Result<ClaimedToken2022, Stop> {
    if !c.uva_ata_address_ok {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    let settle = |balance: Option<u64>| {
        claim_cashback_v2::claim(
            &Claim {
                user: c.user,
                native: false,
                token_program_ok: c.token_program_ok,
                mint_owner_ok: c.mint.owner_matches_program,
                uva_quote_balance: balance,
                quote_user: QuoteUser::User,
                uva_lamports: c.uva_lamports,
                uva_data: c.uva_data,
            },
            timestamp,
        )
    };
    let to_stop = |stop: BaseStop| match stop {
        BaseStop::Code(code) => Stop::Code(code),
        BaseStop::Panic => Stop::Panic,
    };
    if !c.token_program_ok || !c.mint.owner_matches_program || c.uva_ata == Ata::Missing {
        let claimed = settle(None).map_err(to_stop)?;
        return Ok(ClaimedToken2022 { claimed, withheld: 0 });
    }
    let source = parsed(&c.uva_ata)?;
    if source.balance == 0 {
        let claimed = settle(None).map_err(to_stop)?;
        return Ok(ClaimedToken2022 { claimed, withheld: 0 });
    }
    if matches!(c.user_ata, Ata::Missing | Ata::WrongProgram(_)) {
        return Err(Stop::Code(ACCOUNT_TYPE_NOT_SUPPORTED));
    }
    let destination = parsed(&c.user_ata)?;
    if !destination.owner_matches {
        return Err(Stop::Code(INVALID_CASHBACK_RECIPIENT));
    }
    if c.mint.truncated {
        return Err(Stop::InvalidAccountData);
    }
    if matches!(c.uva_ata, Ata::WrongProgram(_)) {
        return Err(Stop::IncorrectProgramId);
    }
    let withheld = transfer(c, &source, &destination)?;
    let claimed = settle(Some(source.balance)).map_err(to_stop)?;
    Ok(ClaimedToken2022 { claimed, withheld })
}
