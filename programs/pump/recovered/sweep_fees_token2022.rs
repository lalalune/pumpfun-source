//! Captured accounting of Pump `sweep_protocol_fee` / `sweep_creator_fee` on a
//! Token-2022 quote mint, on top of the recipient and bucket rules in
//! `sweep_fees.rs`: the account admission that rule set assumes, the size of
//! the recipient ATA the payer creates, the transfer fee that lands on the
//! destination, and the order of the failures of the token transfer.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token, Token-2022 and Associated Token programs by
//! `tests/test_sweep_fees_token2022_captured.py`. Not linked into the SBF
//! crate. This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): extensions other than the
//! ones named here, a hook program that is really invoked, and interest-bearing
//! or scaled-amount mints.

use crate::sweep_fees::{self, Bucket, QuoteMint, Recipient, Stop as BaseStop, Sweep as BaseSweep};

pub const NOT_AUTHORIZED: u32 = sweep_fees::NOT_AUTHORIZED;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = sweep_fees::MINT_DOES_NOT_MATCH_BONDING_CURVE;
pub const CONSTRAINT_SEEDS: u32 = sweep_fees::CONSTRAINT_SEEDS;
pub const ACCOUNT_NOT_INITIALIZED: u32 = sweep_fees::ACCOUNT_NOT_INITIALIZED;
/// Anchor `AccountOwnedByWrongProgram`, on the quote mint.
pub const ACCOUNT_OWNED_BY_WRONG_PROGRAM: u32 = 3007;
/// Anchor `InvalidProgramId`, on the quote token program.
pub const INVALID_PROGRAM_ID: u32 = 3008;
/// `AccountTypeNotSupported`: an ATA owned by another program.
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER: u32 = 42;
pub const TOKEN_MINT_PAUSED: u32 = 67;

pub fn rent(len: u64) -> u64 {
    (len + 128) * 6960
}

/// `quote_token_program` as passed.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum TokenProgram {
    Token2022,
    Spl,
    Other,
}

/// Owner of the quote mint account.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum MintOwner {
    Token2022,
    Spl,
    Other,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct TransferFee {
    pub older_bps: u16,
    pub older_max: u64,
    pub newer_epoch: u64,
    pub newer_bps: u16,
    pub newer_max: u64,
}

impl TransferFee {
    /// Withheld from `amount`: the newer schedule from its epoch on, rounded
    /// up, capped at the schedule's maximum.
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
pub enum Hook {
    None,
    /// The extension is there with a default program id.
    Unset,
    Set,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Pausable {
    None,
    Running,
    Paused,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Mint {
    pub owner: MintOwner,
    pub fee: Option<TransferFee>,
    pub hook: Hook,
    pub pausable: Pausable,
    pub non_transferable: bool,
    pub default_frozen: bool,
}

impl Mint {
    fn extended(&self) -> bool {
        self.fee.is_some()
            || self.hook != Hook::None
            || self.pausable != Pausable::None
            || self.non_transferable
            || self.default_frozen
    }

    /// Account size the ATA program asks for: the base account, the account
    /// type byte and ImmutableOwner, then the account side of each extension.
    pub fn ata_len(&self) -> u64 {
        170 + if self.fee.is_some() { 12 } else { 0 }
            + if self.hook != Hook::None { 5 } else { 0 }
            + if self.pausable != Pausable::None { 4 } else { 0 }
            + if self.non_transferable { 4 } else { 0 }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Default)]
pub struct Holding {
    pub balance: u64,
    pub frozen: bool,
    pub fee_extension: bool,
    /// The account's stored owner is the curve (read only for the source).
    pub owner_matches: bool,
    pub memo_required: bool,
    pub cpi_guard: bool,
    pub non_transferable: bool,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ata {
    Missing,
    WrongProgram,
    Truncated,
    Uninitialized,
    WrongMint,
    Held(Holding),
}

pub struct Sweep {
    pub bucket: Bucket,
    pub mayhem: bool,
    pub quote_mint: QuoteMint,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub curve_lamports: u64,
    pub recipient: Recipient,
    pub recipient_lamports: u64,
    pub token_program: TokenProgram,
    pub mint: Mint,
    pub epoch: u64,
    pub curve_ata_address_ok: bool,
    pub recipient_ata_address_ok: bool,
    pub curve_ata: Ata,
    pub recipient_ata: Ata,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    InvalidAccountData,
    UninitializedAccount,
    IncorrectProgramId,
}

#[derive(Debug, Default, PartialEq, Eq)]
pub struct Swept {
    /// Bucket amount: debited from the curve ATA and carried by the event.
    pub amount: u64,
    /// Part of `amount` that stays withheld on the destination.
    pub withheld: u64,
    pub curve_rent_top_up: u64,
    pub recipient_ata_rent: u64,
    pub recipient_ata_len: u64,
    pub buckets: (u64, u64),
}

fn admit(ata: &Ata) -> Result<Option<Holding>, Stop> {
    match ata {
        Ata::Missing => Ok(None),
        Ata::WrongProgram => Err(Stop::Code(ACCOUNT_TYPE_NOT_SUPPORTED)),
        Ata::Truncated => Err(Stop::InvalidAccountData),
        Ata::Uninitialized => Err(Stop::UninitializedAccount),
        Ata::WrongMint => Err(Stop::Code(MINT_DOES_NOT_MATCH_BONDING_CURVE)),
        Ata::Held(held) => Ok(Some(*held)),
    }
}

/// The token program's own checks, in the order the captured program fails them.
fn transfer(s: &Sweep, source: &Holding, destination: &Holding, amount: u64) -> Result<u64, Stop> {
    // SPL Token reads the mint first and only knows the bare layout; it never
    // checks the mint owner.
    if s.token_program == TokenProgram::Spl && s.mint.extended() {
        return Err(Stop::InvalidAccountData);
    }
    if source.frozen {
        return Err(Stop::Code(TOKEN_ACCOUNT_FROZEN));
    }
    if source.balance < amount {
        return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
    }
    if source.non_transferable {
        return Err(Stop::Code(TOKEN_NON_TRANSFERABLE));
    }
    if s.token_program == TokenProgram::Token2022 && s.mint.owner != MintOwner::Token2022 {
        return Err(Stop::IncorrectProgramId);
    }
    if s.mint.pausable == Pausable::Paused {
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
    if destination.memo_required {
        return Err(Stop::Code(TOKEN_NO_MEMO));
    }
    let withheld = s.mint.fee.map_or(0, |fee| fee.withheld(s.epoch, amount));
    if withheld != 0 && !destination.fee_extension {
        return Err(Stop::Code(TOKEN_INVALID_STATE));
    }
    if s.mint.hook == Hook::Set {
        return Err(Stop::InvalidAccountData);
    }
    Ok(withheld)
}

pub fn sweep(s: &Sweep) -> Result<Swept, Stop> {
    if s.mint.owner == MintOwner::Other {
        return Err(Stop::Code(ACCOUNT_OWNED_BY_WRONG_PROGRAM));
    }
    if s.token_program == TokenProgram::Other {
        return Err(Stop::Code(INVALID_PROGRAM_ID));
    }
    // The curve bucket and recipient rules, as on an SPL quote: the ATA
    // balance and existence are decided below.
    let base = sweep_fees::sweep(&BaseSweep {
        bucket: s.bucket,
        native: false,
        mayhem: s.mayhem,
        quote_mint: s.quote_mint,
        real_quote_reserves: 0,
        creator_fee: s.creator_fee,
        protocol_fees: s.protocol_fees,
        curve_lamports: s.curve_lamports,
        recipient: s.recipient,
        recipient_lamports: s.recipient_lamports,
        curve_quote_ata: Some(u64::MAX),
        recipient_quote_ata_exists: true,
    });
    if base == Err(BaseStop::Code(MINT_DOES_NOT_MATCH_BONDING_CURVE)) {
        return Err(Stop::Code(MINT_DOES_NOT_MATCH_BONDING_CURVE));
    }
    if !s.curve_ata_address_ok || !s.recipient_ata_address_ok {
        return Err(Stop::Code(CONSTRAINT_SEEDS));
    }
    let base = base.map_err(|stop| match stop {
        BaseStop::Code(code) => Stop::Code(code),
        other => unreachable!("not on a quote curve: {other:?}"),
    })?;
    let mut out = Swept { amount: base.amount, curve_rent_top_up: base.curve_rent_top_up, buckets: base.buckets, ..Swept::default() };
    if base.amount == 0 {
        return Ok(out);
    }
    let source = admit(&s.curve_ata)?.ok_or(Stop::Code(ACCOUNT_NOT_INITIALIZED))?;
    let destination = match admit(&s.recipient_ata)? {
        Some(held) => held,
        None => {
            // The ATA program's size query reaches the same owner check first.
            if s.token_program == TokenProgram::Token2022 && s.mint.owner != MintOwner::Token2022 {
                return Err(Stop::IncorrectProgramId);
            }
            out.recipient_ata_len = s.mint.ata_len();
            out.recipient_ata_rent = rent(out.recipient_ata_len);
            Holding { frozen: s.mint.default_frozen, fee_extension: true, ..Holding::default() }
        }
    };
    out.withheld = transfer(s, &source, &destination, base.amount)?;
    Ok(out)
}
