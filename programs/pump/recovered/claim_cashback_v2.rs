//! Captured behavior of Pump `claim_cashback_v2` on its two routes: native
//! (the quote mint is the wrapped-SOL mint; UVA lamports above rent go to the
//! user) and SPL token (the UVA's quote token balance goes to the user's quote
//! token account).
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token and Associated Token programs by
//! `tests/test_claim_cashback_v2_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const INVALID_QUOTE_TOKEN_PROGRAM: u32 = 6064;
pub const INVALID_CASHBACK_RECIPIENT: u32 = 6076;
/// Default-rent cost of one byte: `Rent::minimum_balance(len) == (128 + len) * 6960`.
pub const LAMPORTS_PER_BYTE: u64 = 6_960;
const CLAIM_EVENT: [u8; 8] = [226, 214, 246, 33, 7, 242, 147, 229];

const OFF_CASHBACK_EARNED: usize = 74;
const OFF_TOTAL_CASHBACK_CLAIMED: usize = 82;
const OFF_TOTAL_STABLE_CASHBACK_CLAIMED: usize = 98;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum QuoteUser {
    /// A token account of the quote mint owned by `user`.
    User,
    /// A token account owned by someone else.
    Stranger,
    /// No account (system-owned, empty).
    Absent,
}

pub struct Claim<'a> {
    pub user: [u8; 32],
    /// `quote_mint` is the wrapped-SOL mint.
    pub native: bool,
    /// `quote_token_program` is SPL Token or Token-2022.
    pub token_program_ok: bool,
    /// The quote mint is owned by `quote_token_program`.
    pub mint_owner_ok: bool,
    /// Balance of the UVA's quote token account (`None`: not created).
    pub uva_quote_balance: Option<u64>,
    pub quote_user: QuoteUser,
    pub uva_lamports: u64,
    pub uva_data: &'a [u8],
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// A checked add on a claimed total overflowed (`expect`).
    Panic,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Claimed {
    /// Lamports moved from the UVA to `user` (native route).
    pub lamports: u64,
    /// Quote tokens moved from the UVA token account to the user's (token route).
    pub tokens: u64,
    pub uva_data: Vec<u8>,
    pub event: Option<Vec<u8>>,
}

fn u64_at(data: &[u8], offset: usize) -> u64 {
    u64::from_le_bytes(data[offset..offset + 8].try_into().unwrap())
}

fn add_at(data: &mut [u8], offset: usize, amount: u64) -> Result<(), Stop> {
    let total = u64_at(data, offset).checked_add(amount).ok_or(Stop::Panic)?;
    data[offset..offset + 8].copy_from_slice(&total.to_le_bytes());
    Ok(())
}

/// The handler after the Anchor account checks (UVA load, seeds, mut), which
/// match `claim_cashback` and are not repeated here.
///
/// Native route: the token program, mint and token accounts are not checked.
/// The claim is the UVA lamports above `Rent::minimum_balance(uva data length)`
/// and is added to `total_cashback_claimed`.
///
/// Token route, in order: token program (6064); mint owner (6010); a missing
/// or empty UVA token account is a no-op; the user's quote account must be
/// owned by the token program (6010) and by `user` (6076). The whole UVA
/// token balance moves and is added to `total_stable_cashback_claimed`; the
/// UVA's spare lamports stay.
///
/// A zero claim emits nothing. An overflowing total aborts the program
/// (unlike `claim_cashback`, which returns error6024). On both routes the
/// event reports the native totals `total_cashback_claimed` and
/// `cashback_earned`.
pub fn claim(c: &Claim, timestamp: i64) -> Result<Claimed, Stop> {
    let mut data = c.uva_data.to_vec();
    let none = |data: Vec<u8>| Ok(Claimed { lamports: 0, tokens: 0, uva_data: data, event: None });
    let (lamports, tokens) = if c.native {
        let minimum = (128 + data.len() as u64) * LAMPORTS_PER_BYTE;
        let amount = c.uva_lamports.saturating_sub(minimum);
        if amount == 0 {
            return none(data);
        }
        add_at(&mut data, OFF_TOTAL_CASHBACK_CLAIMED, amount)?;
        (amount, 0)
    } else {
        if !c.token_program_ok {
            return Err(Stop::Code(INVALID_QUOTE_TOKEN_PROGRAM));
        }
        if !c.mint_owner_ok {
            return Err(Stop::Code(ACCOUNT_TYPE_NOT_SUPPORTED));
        }
        let amount = match c.uva_quote_balance {
            None | Some(0) => return none(data),
            Some(amount) => amount,
        };
        match c.quote_user {
            QuoteUser::Absent => return Err(Stop::Code(ACCOUNT_TYPE_NOT_SUPPORTED)),
            QuoteUser::Stranger => return Err(Stop::Code(INVALID_CASHBACK_RECIPIENT)),
            QuoteUser::User => {}
        }
        add_at(&mut data, OFF_TOTAL_STABLE_CASHBACK_CLAIMED, amount)?;
        (0, amount)
    };
    let mut event = Vec::with_capacity(72);
    event.extend_from_slice(&CLAIM_EVENT);
    event.extend_from_slice(&c.user);
    event.extend_from_slice(&(lamports + tokens).to_le_bytes());
    event.extend_from_slice(&timestamp.to_le_bytes());
    event.extend_from_slice(&u64_at(&data, OFF_TOTAL_CASHBACK_CLAIMED).to_le_bytes());
    event.extend_from_slice(&u64_at(&data, OFF_CASHBACK_EARNED).to_le_bytes());
    Ok(Claimed { lamports, tokens, uva_data: data, event: Some(event) })
}
