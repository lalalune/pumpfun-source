//! `distribute_fee_to_holders` on a SOL (wrapped-SOL) quote: the claim
//! authority pays a list of holders straight out of the `holder-rewards` PDA.
//!
//! A pure model of which check stops the call, which lamports move and what
//! the `DistributeFeeToHoldersEvent` reports. Keys are small ids. Checked
//! against the captured program by
//! `tests/test_holder_distribution_captured.py` on the inputs listed there;
//! it is not a byte-identity claim. The token-quote payout path (SPL
//! transfers out of `holder_rewards_token_account`) is out of scope; only
//! its two outcomes without a token account are modelled.

/// Rent-exempt minimum of a zero-length account. The PDA may end at zero or
/// at this floor or above, never in between.
pub const RENT_FLOOR: u64 = 890_880;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Quote {
    /// The wrapped-SOL mint: payouts are lamport transfers.
    Native,
    /// Any other initialized mint, with no holder-rewards token account.
    Token,
    /// `quote_mint` does not exist.
    Missing,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Payee {
    /// A writable wallet, by id.
    Wallet(u8),
    /// The holder-rewards PDA itself.
    Rewards,
    /// A wallet passed read-only, by id.
    Readonly(u8),
}

#[derive(Clone, Debug)]
pub struct Case {
    pub signed: bool,
    /// `holder_reward_claim_authority` matches the Global field.
    pub authority_ok: bool,
    /// `holder_rewards` is the `["holder-rewards", mint]` PDA.
    pub rewards_address_ok: bool,
    pub quote: Quote,
    pub rewards_lamports: u64,
    /// Number of remaining accounts (two are expected per amount).
    pub recipient_accounts: u64,
    pub entries: Vec<(Payee, u64)>,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// The runtime refuses a CPI that would write a read-only account.
    PrivilegeEscalation,
}

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Done {
    pub rewards_lamports: u64,
    /// Lamports received per wallet id, sorted by id.
    pub credits: Vec<(u8, u64)>,
    pub recipients: u64,
    pub total: u64,
}

const NOT_SIGNER: u32 = 3010;
const NOT_INITIALIZED: u32 = 3012;
const NOT_AUTHORIZED: u32 = 6000;
const SEEDS: u32 = 2006;
const INSUFFICIENT_FUNDS: u32 = 1;
const RECIPIENTS_MISMATCH: u32 = 6085;
const RENT_FLOOR_ERROR: u32 = 6086;
const TOKEN_ACCOUNT_MISSING: u32 = 6087;

fn credit(credits: &mut Vec<(u8, u64)>, id: u8, amount: u64) {
    match credits.iter_mut().find(|entry| entry.0 == id) {
        Some(entry) => entry.1 += amount,
        None => credits.push((id, amount)),
    }
}

pub fn distribute(case: &Case) -> Result<Done, Stop> {
    // Account loading, in account order, then the constraints.
    if !case.signed {
        return Err(Stop::Code(NOT_SIGNER));
    }
    if case.quote == Quote::Missing {
        return Err(Stop::Code(NOT_INITIALIZED));
    }
    if !case.authority_ok {
        return Err(Stop::Code(NOT_AUTHORIZED));
    }
    if !case.rewards_address_ok {
        return Err(Stop::Code(SEEDS));
    }
    let count = case.entries.len() as u64;
    if case.recipient_accounts != 2 * count {
        return Err(Stop::Code(RECIPIENTS_MISMATCH));
    }
    let total = case.entries.iter().fold(0u64, |sum, entry| sum.saturating_add(entry.1));
    if case.quote == Quote::Token {
        // An empty list returns before the token account is required.
        if count == 0 {
            return Ok(Done { rewards_lamports: case.rewards_lamports, credits: Vec::new(), recipients: 0, total: 0 });
        }
        return Err(Stop::Code(TOKEN_ACCOUNT_MISSING));
    }
    let mut balance = case.rewards_lamports;
    let mut credits = Vec::new();
    for &(payee, amount) in &case.entries {
        if amount == 0 {
            continue;
        }
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
    if balance != 0 && balance < RENT_FLOOR {
        return Err(Stop::Code(RENT_FLOOR_ERROR));
    }
    credits.sort();
    Ok(Done { rewards_lamports: balance, credits, recipients: count, total })
}
