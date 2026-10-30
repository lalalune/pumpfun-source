//! `distribute_fee_to_holders` with a `holder_rewards_token_account`: SPL
//! Token and Token-2022 payouts out of the holder-rewards ATA, and the
//! wrapped-SOL source that is closed into the PDA before lamport payouts.
//!
//! A pure model of which check stops the call, which token amounts and
//! lamports move, which recipient ATAs are created (the claim authority pays
//! their rent) and what `DistributeFeeToHoldersEvent` reports. Keys are small
//! ids. Checked against the captured Pump, SPL Token, Token-2022 and
//! Associated Token programs by
//! `tests/test_holder_distribution_token_captured.py` on the inputs listed
//! there; it is not a byte-identity claim. Mints carry no extensions, and
//! `holder_rewards_token_account` is always the PDA's own ATA. The SOL path
//! without a source account is `holder_distribution.rs`.

/// Rent-exempt minimum of a zero-length account (the PDA floor).
pub const RENT_FLOOR: u64 = 890_880;
/// Rent of a 165-byte SPL Token account.
pub const TOKEN_ACCOUNT_RENT: u64 = 2_039_280;
/// Rent of a 170-byte Token-2022 ATA (the ATA program adds ImmutableOwner).
pub const TOKEN_2022_ACCOUNT_RENT: u64 = 2_074_080;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Program {
    Token,
    Token2022,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Source {
    /// Token-account owner is the holder-rewards PDA.
    pub authority_ok: bool,
    /// Token-account mint is `quote_mint`.
    pub mint_ok: bool,
    /// Token account is owned by `quote_token_program`.
    pub program_ok: bool,
    pub amount: u64,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Payee {
    Wallet(u8),
    /// The holder-rewards PDA (its ATA is the source account).
    Rewards,
    /// A wallet passed read-only.
    Readonly(u8),
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Ata {
    /// The recipient ATA already exists with a zero balance.
    Exists,
    /// The recipient ATA address holds no account yet.
    Empty,
    /// The second account is not the recipient's ATA.
    Wrong,
}

#[derive(Clone, Debug)]
pub struct Case {
    pub signed: bool,
    pub authority_ok: bool,
    /// `quote_mint` is wrapped SOL (always on SPL Token here).
    pub native: bool,
    pub program: Program,
    /// The program that owns the quote mint account.
    pub mint_program: Program,
    pub source: Option<Source>,
    pub rewards_lamports: u64,
    pub recipient_accounts: u64,
    pub entries: Vec<(Payee, u64, Ata)>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    PrivilegeEscalation,
    /// A token CPI saw a mint owned by the other token program.
    IncorrectProgramId,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Done {
    pub rewards_lamports: u64,
    /// Lamports the claim authority paid for created ATAs.
    pub authority_paid: u64,
    /// Final source balance; `None` once a wrapped-SOL source is closed.
    pub source_amount: Option<u64>,
    /// Per wallet id: token units (token path) or lamports (SOL path).
    pub credits: Vec<(u8, u64)>,
    /// Wallet ids whose ATA was created, sorted.
    pub created: Vec<u8>,
    pub recipients: u64,
    pub total: u64,
}

const INSUFFICIENT_FUNDS: u32 = 1;
const CONSTRAINT_TOKEN_MINT: u32 = 2014;
const CONSTRAINT_TOKEN_OWNER: u32 = 2015;
const CONSTRAINT_TOKEN_PROGRAM: u32 = 2021;
const NOT_SIGNER: u32 = 3010;
const NOT_AUTHORIZED: u32 = 6000;
const OVERFLOW: u32 = 6024;
const RECIPIENTS_MISMATCH: u32 = 6085;
const RENT_FLOOR_ERROR: u32 = 6086;
const TOKEN_ACCOUNT_MISSING: u32 = 6087;

fn credit(credits: &mut Vec<(u8, u64)>, id: u8, amount: u64) {
    match credits.iter_mut().find(|entry| entry.0 == id) {
        Some(entry) => entry.1 += amount,
        None => credits.push((id, amount)),
    }
}

fn wallet_id(payee: Payee) -> Option<u8> {
    match payee {
        Payee::Wallet(id) | Payee::Readonly(id) => Some(id),
        Payee::Rewards => None,
    }
}

pub fn distribute(case: &Case) -> Result<Done, Stop> {
    if !case.signed {
        return Err(Stop::Code(NOT_SIGNER));
    }
    if !case.authority_ok {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    // token::authority, then token::mint, then token::token_program.
    if let Some(source) = case.source {
        if !source.authority_ok {
            return Err(Stop::Code(CONSTRAINT_TOKEN_OWNER));
        }
        if !source.mint_ok {
            return Err(Stop::Code(CONSTRAINT_TOKEN_MINT));
        }
        if !source.program_ok {
            return Err(Stop::Code(CONSTRAINT_TOKEN_PROGRAM));
        }
    }
    let count = case.entries.len() as u64;
    if case.recipient_accounts != 2 * count {
        return Err(Stop::Code(RECIPIENTS_MISMATCH));
    }
    let mut total = 0u64;
    let mut credits = Vec::new();
    let mut created = Vec::new();
    if case.native {
        // The wrapped-SOL source is closed into the PDA before any payout:
        // its rent and its wrapped lamports both land there.
        let mut balance = case.rewards_lamports;
        if let Some(source) = case.source {
            balance += TOKEN_ACCOUNT_RENT + source.amount;
        }
        for &(payee, amount, _) in &case.entries {
            if amount != 0 {
                if let Payee::Readonly(_) = payee {
                    return Err(Stop::PrivilegeEscalation);
                }
                if balance < amount {
                    return Err(Stop::Code(INSUFFICIENT_FUNDS));
                }
                if let Payee::Wallet(id) = payee {
                    balance -= amount;
                    credit(&mut credits, id, amount);
                }
            }
            total = total.checked_add(amount).ok_or(Stop::Code(OVERFLOW))?;
        }
        if balance != 0 && balance < RENT_FLOOR {
            return Err(Stop::Code(RENT_FLOOR_ERROR));
        }
        credits.sort();
        return Ok(Done { rewards_lamports: balance, authority_paid: 0, source_amount: None, credits, created, recipients: count, total });
    }
    let rent = match case.program {
        Program::Token => TOKEN_ACCOUNT_RENT,
        Program::Token2022 => TOKEN_2022_ACCOUNT_RENT,
    };
    let mut authority_paid = 0u64;
    let mut held = case.source.map(|source| source.amount);
    for &(payee, amount, ata) in &case.entries {
        // A token quote needs the source for every entry, even a zero one.
        let source = held.ok_or(Stop::Code(TOKEN_ACCOUNT_MISSING))?;
        if ata == Ata::Wrong {
            return Err(Stop::Code(RECIPIENTS_MISMATCH));
        }
        let id = wallet_id(payee);
        // Read-only wallets are fine here: only their ATA is written.
        if let Some(id) = id {
            if ata == Ata::Empty && !created.contains(&id) {
                // The ATA program initialises the account through the quote
                // token program, which must own the mint.
                if case.mint_program != case.program {
                    return Err(Stop::IncorrectProgramId);
                }
                created.push(id);
                authority_paid += rent;
            }
        }
        if amount != 0 {
            // Token-2022 checks the mint owner on transfer_checked; legacy
            // SPL Token does not.
            if case.program == Program::Token2022 && case.mint_program != Program::Token2022 {
                return Err(Stop::IncorrectProgramId);
            }
            if source < amount {
                return Err(Stop::Code(INSUFFICIENT_FUNDS));
            }
            // Paying the PDA is a self-transfer: it checks the balance and
            // moves nothing.
            if let Some(id) = id {
                held = Some(source - amount);
                credit(&mut credits, id, amount);
            }
        }
        total = total.checked_add(amount).ok_or(Stop::Code(OVERFLOW))?;
    }
    credits.sort();
    created.sort();
    Ok(Done { rewards_lamports: case.rewards_lamports, authority_paid, source_amount: held, credits, created,
              recipients: count, total })
}
