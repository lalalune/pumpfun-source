//! Captured `migrate` and `migrate_v2` where one key fills two slots, with the
//! real pump_amm program. Only two inputs can do that on a curve that otherwise
//! passes: `Global.withdraw_authority`, which no seed pins, and the two boost
//! keys in the remaining accounts, which only pump_amm checks.
//!
//! The migration amounts stay with `migrate.rs` and `migrate_v2.rs`. This model
//! holds what the second slot changes: who pays each rent, the lamports the key
//! ends with, and the error. Checked against `evidence/original/pump/deployed.so`,
//! `evidence/original/pump_amm/deployed.so` and the captured token programs by
//! `tests/test_migrate_alias_captured.py`. Not linked into the SBF crate. This is
//! not a byte-identity claim.
//!
//! Unconfirmed (outside the checked inputs): a cluster demotes writable
//! sysvars and builtin programs in a transaction, LiteSVM does not, so `Rent`
//! and the program keys here may fail with 2000 there; a base mint that is also
//! the quote mint, and a curve on the wrapped SOL mint, which fail in fixtures
//! whose cause was not traced.

pub const NOT_MUT: i64 = 2000;
pub const OWNED_BY: i64 = 3007;
pub const WRONG_MINT: i64 = 2014;
pub const WRONG_AUTHORITY: i64 = 2015;
/// System program `ResultWithNegativeLamports`: `pool_authority` ran out.
pub const INSUFFICIENT_LAMPORTS: i64 = 1;
/// Runtime errors, which carry no code.
pub const MISSING_ACCOUNT: i64 = -2;
pub const INVALID_ACCOUNT_DATA: i64 = -3;
pub const LAMPORT_SPEND: i64 = -5;
pub const PRIVILEGE_ESCALATION: i64 = -6;

pub const TOKEN_RENT: u64 = 2_039_280;
pub const TOKEN_2022_RENT: u64 = 2_074_080;
pub const POOL_RENT: u64 = 2_888_400;
pub const LP_MINT_RENT: u64 = 1_461_600;

#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Route {
    /// `migrate`, or `migrate_v2` with no quote mint: the curve pays the fee.
    Native,
    Spl,
    Token2022,
}

/// The slot `Global.withdraw_authority` also names.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Second {
    Wallet,
    User,
    Curve,
    /// `pool_authority` itself: its lamports join the fee.
    Authority,
    Pool,
    LpMint,
    PoolBase,
    PoolQuote,
    /// Closed into the withdraw authority: the temporary token accounts, which
    /// `user` pays on a token route (`lp` false), and the LP account, which
    /// `pool_authority` always pays.
    Closed { lp: bool },
    /// The Pump program: the only key the call runs under, so not writable.
    Pump,
    /// Other executables: lamports cannot land on them.
    Program,
    /// Everything else: an existing account that just gains lamports.
    Bystander,
}

#[derive(Clone, Copy)]
pub struct Migration {
    pub route: Route,
    pub second: Second,
    pub fee: u64,
    /// Lamports already on the key when it is a system account.
    pub start: u64,
    pub real_quote: u64,
    /// Both boost keys are passed and right, so the call creates the vault.
    pub creates_vault: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Paid {
    pub user_paid: u64,
    /// Lamport change of the withdraw key, across every slot it fills.
    pub key_change: i128,
    /// Wrapped SOL above rent on the pool's quote address: it counts as deposit.
    pub extra_quote: u64,
}

fn quote_rent(route: Route) -> u64 {
    if route == Route::Token2022 { TOKEN_2022_RENT } else { TOKEN_RENT }
}

/// Lamports `pool_authority` holds at once. On the native route it also pays the
/// four token accounts that `user` pays on a token route.
fn authority_need(route: Route) -> u64 {
    let amm = POOL_RENT + LP_MINT_RENT + TOKEN_2022_RENT;
    if route == Route::Native { amm + 2 * TOKEN_RENT + 2 * quote_rent(route) } else { amm }
}

/// Rent the existing lamports of a to-be-created account cover.
fn covered(m: &Migration) -> u64 {
    let rent = match m.second {
        Second::Pool => POOL_RENT,
        Second::LpMint => LP_MINT_RENT,
        Second::PoolBase => TOKEN_RENT,
        Second::PoolQuote => quote_rent(m.route),
        Second::Closed { lp: false } => TOKEN_RENT,
        Second::Closed { lp: true } => TOKEN_2022_RENT,
        _ => 0,
    };
    m.start.min(rent)
}

pub fn run(m: &Migration) -> Result<Paid, i64> {
    if m.second == Second::Pump {
        return Err(NOT_MUT);
    }
    let native = m.route == Route::Native;
    let saved = covered(m);
    let user_saving = !native && matches!(m.second, Second::PoolBase | Second::PoolQuote | Second::Closed { lp: false });
    let authority_saved = if user_saving { 0 } else { saved };
    let extra = if m.second == Second::Authority { m.start } else { 0 };
    if m.fee + extra + authority_saved < authority_need(m.route) {
        return Err(INSUFFICIENT_LAMPORTS);
    }
    match m.second {
        Second::Closed { .. } => return Err(INVALID_ACCOUNT_DATA),
        Second::Program => return Err(LAMPORT_SPEND),
        _ => {}
    }
    let accounts = 2 * TOKEN_RENT + 2 * quote_rent(m.route);
    let vault = if m.creates_vault { quote_rent(m.route) } else { 0 };
    let user_paid = vault + if native { 0 } else { m.fee + accounts - if user_saving { saved } else { 0 } };
    // Everything the temporary accounts return lands on the withdraw key.
    let closes = TOKEN_RENT + quote_rent(m.route) + TOKEN_2022_RENT;
    let kept = POOL_RENT + LP_MINT_RENT + TOKEN_2022_RENT;
    let spent = if native { kept + accounts } else { kept };
    let gain = (m.fee + closes + authority_saved - spent) as i128;
    let own: i128 = match m.second {
        Second::Pool => POOL_RENT as i128 - saved as i128,
        Second::LpMint => LP_MINT_RENT as i128 - saved as i128,
        Second::PoolBase => TOKEN_RENT as i128 - saved as i128,
        Second::PoolQuote if native => (quote_rent(m.route) - saved) as i128 + (m.real_quote - m.fee) as i128,
        Second::PoolQuote => quote_rent(m.route) as i128 - saved as i128,
        Second::Curve if native => -(m.real_quote as i128),
        Second::User => -(user_paid as i128),
        _ => 0,
    };
    let extra_quote = if native && m.second == Second::PoolQuote { m.start.saturating_sub(TOKEN_RENT) } else { 0 };
    Ok(Paid { user_paid, key_change: gain + own, extra_quote })
}

/// What `boost_vault` in the second remaining slot holds when it is not the
/// vault's address.
#[derive(Clone, Copy, PartialEq, Eq)]
pub enum Vault {
    Right,
    /// No data, not owned by a token program.
    Empty,
    /// The Pump program key, which the top call runs under.
    Pump,
    OtherOwner,
    /// A mint: too short for a token account.
    Mint,
    TokenOtherMint,
    TokenOtherAuthority,
}

/// `boost_authority` must be the first remaining key, before the vault is read.
pub fn boost(authority_right: bool, vault: Vault) -> Result<(), i64> {
    if !authority_right {
        return Err(MISSING_ACCOUNT);
    }
    match vault {
        Vault::Right => Ok(()),
        Vault::Empty => Err(MISSING_ACCOUNT),
        Vault::Pump => Err(PRIVILEGE_ESCALATION),
        Vault::OtherOwner => Err(OWNED_BY),
        Vault::Mint => Err(INVALID_ACCOUNT_DATA),
        Vault::TokenOtherMint => Err(WRONG_MINT),
        Vault::TokenOtherAuthority => Err(WRONG_AUTHORITY),
    }
}
