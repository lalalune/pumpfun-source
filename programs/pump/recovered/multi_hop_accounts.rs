//! Captured account-level rules of `multi_hop_curve_swap`, which
//! `multi_hop_route.rs` lists as unconfirmed: what each named and hop account
//! must look like, which check fires first, what is not checked at all, how a
//! short curve reads, and the rent top-up each hop may charge the user.
//!
//! Every fault is a condition on an account, and the route arithmetic stays in
//! `multi_hop_route.rs`. A hop's checks run after every earlier hop has
//! succeeded, so the hops before a fault are run as a shorter route.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_multi_hop_accounts_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): Token-2022 accounts, a user
//! too poor for anything but a top-up on the first hop, a vault left short by
//! the hop before a fault, and where the authority failures (code 4) fall
//! against a later arithmetic error of the same route. Faults with the same
//! code, and several faults on one account, were not told apart, so their order
//! in the enums is unconfirmed.

use crate::multi_hop_route::{self as route, Route, Settled, NATIVE};

/// `InvalidAccountData`, a runtime error with no custom code. It stands for the
/// answer `invalid-data` of the host.
pub const INVALID_ACCOUNT_DATA: u32 = 0;
/// SPL Token `OwnerMismatch`.
pub const TOKEN_OWNER_MISMATCH: u32 = 4;
pub const SYSTEM_INSUFFICIENT_FUNDS: u32 = 1;
pub const CONSTRAINT_MUT: u32 = 2000;
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const DISCRIMINATOR_NOT_FOUND: u32 = 3001;
pub const DISCRIMINATOR_MISMATCH: u32 = 3002;
pub const DID_NOT_DESERIALIZE: u32 = 3003;
pub const WRONG_OWNER: u32 = 3007;
pub const INVALID_PROGRAM: u32 = 3008;
pub const NOT_SIGNER: u32 = 3010;
pub const NOT_INITIALIZED: u32 = 3012;
pub const MINT_MISMATCH: u32 = route::MINT_DOES_NOT_MATCH_BONDING_CURVE;
pub const TYPE_NOT_SUPPORTED: u32 = 6010;
pub const BUYBACK_NOT_AUTHORIZED: u32 = 6057;
pub const BUYBACK_MISSING: u32 = 6062;
/// Below this length a curve does not deserialize.
pub const CURVE_MIN_LEN: usize = 49;
/// `bonding_curve` account length after a hop, unless it is already longer.
pub const CURVE_LEN: usize = 166;

/// `Rent::minimum_balance(len)`.
pub fn rent(len: usize) -> u64 {
    (128 + len as u64) * 6_960
}

/// Faults on the named accounts, in the order they fire. The first group fails
/// while accounts load, field by field, and the second in the constraint pass.
/// Both come before the arguments and every hop.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum Top {
    GlobalOwner,
    GlobalNoDiscriminator,
    GlobalDiscriminator,
    GlobalBody,
    FeeConfigOwner,
    FeeConfigNoDiscriminator,
    FeeConfigDiscriminator,
    FeeConfigBody,
    AmmConfigNotSigner,
    UserNotSigner,
    AuthorityNotSigner,
    SourceOwner,
    SourceData,
    DestinationOwner,
    DestinationData,
    TokenProgram,
    Token2022Program,
    SystemProgram,
    PumpProgram,
    GlobalAddress,
    FeeConfigAddress,
    AmmConfigAddress,
    UserReadOnly,
    SourceReadOnly,
    DestinationReadOnly,
    RecipientReadOnly,
    EventAuthorityAddress,
}

impl Top {
    pub fn code(self) -> u32 {
        use Top::*;
        match self {
            GlobalOwner | FeeConfigOwner | SourceOwner | DestinationOwner => WRONG_OWNER,
            GlobalNoDiscriminator | FeeConfigNoDiscriminator => DISCRIMINATOR_NOT_FOUND,
            GlobalDiscriminator | FeeConfigDiscriminator => DISCRIMINATOR_MISMATCH,
            GlobalBody | FeeConfigBody => DID_NOT_DESERIALIZE,
            AmmConfigNotSigner | UserNotSigner | AuthorityNotSigner => NOT_SIGNER,
            SourceData | DestinationData => INVALID_ACCOUNT_DATA,
            TokenProgram | Token2022Program | SystemProgram | PumpProgram => INVALID_PROGRAM,
            GlobalAddress | FeeConfigAddress | AmmConfigAddress | EventAuthorityAddress => CONSTRAINT_SEEDS,
            UserReadOnly | SourceReadOnly | DestinationReadOnly | RecipientReadOnly => CONSTRAINT_MUT,
        }
    }
}

/// Faults on the five accounts of a hop, in the order they fire. `Late` ones
/// run after the rent top-up and the curve flags, the others before.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord)]
pub enum HopFault {
    BaseMintOwner,
    BaseMintData,
    QuoteMintOwner,
    QuoteMintData,
    CurveOwner,
    /// A wrong discriminator reads like a curve shorter than 49 bytes.
    CurveData,
    BaseVaultOwner,
    BaseVaultData,
    /// Also a `base_mint` that is not the curve's: the seeds use it.
    CurveAddress,
    CurveReadOnly,
    /// `quote_mint` is not the curve's, the fixture passes a real one.
    QuoteMint,
    BaseVaultReadOnly,
    QuoteVaultReadOnly,
    BaseVaultAddress,
    QuoteVaultAddress,
    // The rest of the quote vault is only read on a token quote.
    QuoteVaultSystemOwned,
    QuoteVaultOwner,
    QuoteVaultData,
    QuoteVaultMint,
    // The recipient is read only on a hop that pays the buyback.
    RecipientOwner,
    RecipientData,
    RecipientMint,
    RecipientNoOwner,
    RecipientNotListed,
    RecipientAddress,
}

impl HopFault {
    fn late(self) -> bool {
        self >= HopFault::BaseVaultAddress
    }

    /// `None` when the hop never looks at this condition.
    fn code(self, native: bool, charges_buyback: bool) -> Option<u32> {
        use HopFault::*;
        Some(match self {
            BaseMintOwner | QuoteMintOwner | CurveOwner | BaseVaultOwner => WRONG_OWNER,
            BaseMintData | QuoteMintData | CurveData | BaseVaultData => INVALID_ACCOUNT_DATA,
            CurveReadOnly | BaseVaultReadOnly | QuoteVaultReadOnly => CONSTRAINT_MUT,
            CurveAddress | BaseVaultAddress | QuoteVaultAddress => CONSTRAINT_SEEDS,
            QuoteMint => MINT_MISMATCH,
            QuoteVaultSystemOwned | QuoteVaultOwner | QuoteVaultData | QuoteVaultMint if native => return None,
            QuoteVaultSystemOwned => NOT_INITIALIZED,
            QuoteVaultOwner => TYPE_NOT_SUPPORTED,
            QuoteVaultData => INVALID_ACCOUNT_DATA,
            QuoteVaultMint => MINT_MISMATCH,
            RecipientOwner | RecipientData | RecipientMint | RecipientNoOwner | RecipientNotListed | RecipientAddress
                if !charges_buyback =>
            {
                return None
            }
            RecipientOwner => TYPE_NOT_SUPPORTED,
            RecipientData => INVALID_ACCOUNT_DATA,
            RecipientMint => MINT_MISMATCH,
            RecipientNoOwner => BUYBACK_MISSING,
            RecipientNotListed => BUYBACK_NOT_AUTHORIZED,
            RecipientAddress => CONSTRAINT_SEEDS,
        })
    }
}

/// The token owner field of an account is wrong; only SPL Token looks at it,
/// when an input or output is actually drawn from the account.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Authority {
    /// `source_authority` is a signer, but `source` is not its account.
    Source,
    BaseVault(usize),
    QuoteVault(usize),
}

#[derive(Clone, Debug)]
pub struct Case {
    pub route: Route,
    pub top: Vec<Top>,
    /// (hop index, fault).
    pub hop: Vec<(usize, HopFault)>,
    pub authority: Vec<Authority>,
    /// Length and lamports of each entry of `route.curves`.
    pub curve_len: Vec<usize>,
    pub curve_lamports: Vec<u64>,
    pub user_lamports: u64,
}

/// What a hop reads from a curve of `len` bytes: a field past the end is zero,
/// and the two fee buckets are read as a pair. A token-quoted curve cut before
/// its quote mint reads as native.
pub fn read_curve(c: &route::Curve, len: usize) -> route::Curve {
    let mut c = c.clone();
    if len < 81 {
        c.has_creator = false;
    }
    if len < 82 {
        c.mayhem = false;
    }
    if len < 83 {
        c.cashback = false;
    }
    if len < 115 {
        c.quote_mint = NATIVE;
    }
    if len < 141 {
        c.creator_fee = 0;
        c.protocol_fees = 0;
    }
    c
}

/// Rent top-up of a hop: rent of the account beyond what its lamports hold over
/// the quote a native curve owes.
fn top_up(c: &route::Curve, len: usize, lamports: u64) -> Result<u64, u32> {
    let owed = if c.quote_mint == NATIVE {
        c.real_quote_reserves
            .checked_add(c.creator_fee)
            .and_then(|v| v.checked_add(c.protocol_fees))
            .ok_or(route::OVERFLOW)?
    } else {
        0
    };
    Ok(rent(len.max(CURVE_LEN)).saturating_sub(lamports.saturating_sub(owed)))
}

/// The mint held after each hop, as far as the route is continuous.
fn walk(r: &Route) -> Vec<(bool, u8)> {
    let mut current = r.source_mint;
    r.hops
        .iter()
        .map(|&i| {
            let c = &r.curves[i];
            let buy = current == c.quote_mint;
            current = if buy { c.base_mint } else { c.quote_mint };
            (buy, current)
        })
        .collect()
}

/// The first `k` hops as a route of their own. Its last hop pays out, which the
/// real route does not do, so a native sell is put back on the curve.
fn prefix(r: &Route, k: usize) -> Result<Settled, u32> {
    if k == 0 {
        let curves = r.curves.clone();
        return Ok(Settled { amount_out: 0, buyback_fee: 0, source: 0, destination: 0, user_lamports: 0, recipient: 0, curves });
    }
    let steps = walk(r);
    let mut p = r.clone();
    p.hops.truncate(k);
    p.hop_fees.truncate(k);
    p.remaining_accounts = 5 * k;
    p.destination_mint = steps[k - 1].1;
    let mut s = route::run(&p)?;
    let last = r.hops[k - 1];
    if !steps[k - 1].0 && r.curves[last].quote_mint == NATIVE {
        s.user_lamports -= s.amount_out as i128;
        s.curves[last].lamports += s.amount_out as i128;
    }
    Ok(s)
}

/// The hop at which SPL Token is asked to move tokens out of this account. An
/// output left in a vault moves in the next hop, unless that hop takes it there.
fn drawn_at(r: &Route, a: Authority) -> Option<usize> {
    let steps = walk(r);
    let last = steps.len() - 1;
    let onward = |h: usize| if h == last { Some(h) } else { Some(h + 1) };
    match a {
        Authority::Source => (!(steps[0].0 && r.curves[r.hops[0]].quote_mint == NATIVE)).then_some(0),
        Authority::BaseVault(h) => {
            let kept = h != last && !steps[h + 1].0 && r.hops[h + 1] == r.hops[h];
            if steps[h].0 && !kept { onward(h) } else { None }
        }
        Authority::QuoteVault(h) => {
            let c = &r.curves[r.hops[h]];
            let kept = h != last && steps[h + 1].0 && r.hops[h + 1] == r.hops[h];
            if c.quote_mint == NATIVE {
                None
            } else if r.hop_fees[h] & 1 != 0 {
                Some(h)
            } else if !steps[h].0 && !kept {
                onward(h)
            } else {
                None
            }
        }
    }
}

pub fn run(case: &Case) -> Result<Settled, u32> {
    if let Some(t) = case.top.iter().min() {
        return Err(t.code());
    }
    let mut r = case.route.clone();
    if r.amount_in == 0 {
        return Err(route::BUY_ZERO_AMOUNT);
    }
    let count = r.remaining_accounts / 5;
    if r.remaining_accounts < 5 || count * 5 != r.remaining_accounts {
        return Err(route::NOT_ENOUGH_REMAINING_ACCOUNTS);
    }
    if r.hop_fees.len() != count || r.hop_fees.iter().any(|&f| f >= 4) {
        return Err(route::HOP_FEES_MISMATCH);
    }
    for (i, &len) in case.curve_len.iter().enumerate() {
        r.curves[i] = read_curve(&r.curves[i], len);
    }
    let mut paid = vec![0u64; r.curves.len()];
    let mut lens = case.curve_len.clone();
    for k in 0..count {
        let idx = r.hops[k];
        let flag = r.hop_fees[k];
        let before = prefix(&r, k)?;
        let c = before.curves[idx].clone();
        let native = c.quote_mint == NATIVE;
        let mut faults: Vec<HopFault> = case.hop.iter().filter(|(h, _)| *h == k).map(|(_, f)| *f).collect();
        if lens[idx] < CURVE_MIN_LEN {
            faults.push(HopFault::CurveData);
        }
        if case.curve_len[idx] < 115 && case.route.curves[idx].quote_mint != NATIVE {
            faults.push(HopFault::QuoteMint);
        }
        let code = |late: bool| {
            let found = faults.iter().filter(|f| f.late() == late);
            found.filter_map(|f| f.code(native, flag & 1 != 0).map(|e| (*f, e))).min()
        };
        if let Some((_, e)) = code(false) {
            return Err(e);
        }
        let lamports = case.curve_lamports[idx] as i128 + paid[idx] as i128 + before.curves[idx].lamports;
        let need = top_up(&c, lens[idx], u64::try_from(lamports).unwrap_or(0))?;
        let spent: u64 = paid.iter().sum();
        if (case.user_lamports as i128) + before.user_lamports - (spent as i128) < need as i128 {
            return Err(SYSTEM_INSUFFICIENT_FUNDS);
        }
        paid[idx] += need;
        lens[idx] = lens[idx].max(CURVE_LEN);
        if c.complete {
            return Err(route::BONDING_CURVE_COMPLETE);
        }
        if c.cashback && flag & 2 != 0 {
            return Err(route::CASHBACK_COIN_NOT_SUPPORTED);
        }
        if c.mayhem {
            return Err(route::MAYHEM_CURVE_NOT_SUPPORTED);
        }
        if let Some((_, e)) = code(true) {
            return Err(e);
        }
        if case.authority.iter().any(|&a| drawn_at(&r, a) == Some(k)) {
            prefix(&r, k + 1)?;
            return Err(TOKEN_OWNER_MISMATCH);
        }
    }
    let mut s = route::run(&r)?;
    for (i, &top) in paid.iter().enumerate() {
        s.user_lamports -= top as i128;
        s.curves[i].lamports += top as i128;
    }
    Ok(s)
}
