//! Captured Pump rules of `multi_hop_curve_swap` when a route's mints live on
//! Token-2022: what a mint's transfer fee does to the amount each hop prices,
//! the vault that keeps the difference, the buyback in the return value, and
//! the extensions and vault addresses that stop a route.
//! `multi_hop_route.rs` covers the same swap on SPL mints and leaves these out.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_multi_hop_token2022_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): more than one fee tier, a
//! configurable creator fee, curves that need a rent top-up, and account-level
//! checks other than those named here.

pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
pub const TOKEN_MINT_MISMATCH: u32 = 3;
/// A fee is due on a receiving account with no extension to hold it in.
pub const TOKEN_INVALID_STATE: u32 = 13;
pub const TOKEN_ACCOUNT_FROZEN: u32 = 17;
pub const TOKEN_NO_MEMO: u32 = 36;
pub const TOKEN_NON_TRANSFERABLE: u32 = 37;
pub const TOKEN_CPI_GUARD_TRANSFER_BLOCKED: u32 = 42;
pub const TOKEN_PAUSED: u32 = 67;
/// Anchor ConstraintSeeds: a vault that is not the ATA of the mint's program.
pub const CONSTRAINT_SEEDS: u32 = 2006;
pub const MINT_DOES_NOT_MATCH_BONDING_CURVE: u32 = 6004;
pub const ACCOUNT_TYPE_NOT_SUPPORTED: u32 = 6010;
pub const BONDING_CURVE_COMPLETE: u32 = 6005;
pub const BUY_ZERO_AMOUNT: u32 = 6020;
pub const NOT_ENOUGH_TOKENS_TO_BUY: u32 = 6021;
pub const SELL_ZERO_AMOUNT: u32 = 6022;
pub const OVERFLOW: u32 = 6024;
pub const TRUNCATION: u32 = 6025;
pub const DIVISION_BY_ZERO: u32 = 6026;
pub const NOT_ENOUGH_REMAINING_ACCOUNTS: u32 = 6027;
pub const BUY_NOT_ENOUGH_SOL_TO_COVER_FEES: u32 = 6041;
pub const BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT: u32 = 6042;
pub const UNSUPPORTED_QUOTE_MINT: u32 = 6063;
pub const CASHBACK_COIN_NOT_SUPPORTED: u32 = 6094;
pub const DISCONTINUOUS_PATH: u32 = 6098;
pub const HOP_FEES_MISMATCH: u32 = 6106;
pub const MAYHEM_CURVE_NOT_SUPPORTED: u32 = 6108;
/// Not a custom code: the transfer hook program is never passed.
pub const MISSING_ACCOUNT: u32 = u32::MAX;
/// Not a custom code: Token-2022 refuses a destination of the other program.
pub const INCORRECT_PROGRAM_ID: u32 = u32::MAX - 1;
/// Not a custom code: Anchor cannot load a Token-2022 mint with a bad layout.
pub const INVALID_ACCOUNT_DATA: u32 = u32::MAX - 2;

/// Mint id of wrapped SOL; a curve quoted in it holds native lamports.
pub const NATIVE: u8 = 0;

#[derive(Clone, Debug, Default)]
pub struct Mint {
    pub token2022: bool,
    /// Older bps, older maximum, newer epoch, newer bps, newer maximum.
    pub transfer_fee: Option<(u64, u64, u64, u64, u64)>,
    pub hook: bool,
    pub paused: bool,
    pub non_transferable: bool,
    /// Extension bytes the fee reader refuses; only a quote mint is read.
    pub malformed: bool,
    /// Bytes that do not load as a Token-2022 mint at all.
    pub unreadable: bool,
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct Curve {
    pub virtual_token_reserves: u64,
    pub virtual_quote_reserves: u64,
    pub real_token_reserves: u64,
    pub real_quote_reserves: u64,
    pub creator_fee: u64,
    pub protocol_fees: u64,
    pub post_complete_base_out: u64,
    pub post_complete_quote_in: u64,
    pub has_creator: bool,
    pub cashback: bool,
    pub complete: bool,
    pub mayhem: bool,
    pub base_mint: u8,
    pub quote_mint: u8,
    pub base_vault: u64,
    pub quote_vault: u64,
    pub base_withheld: u64,
    pub quote_withheld: u64,
    pub base_frozen: bool,
    pub quote_frozen: bool,
    /// The vault has no fee extension to hold a withheld fee in.
    pub base_bare: bool,
    pub quote_bare: bool,
    /// The vault is the ATA of the other token program.
    pub base_wrong_program: bool,
    pub quote_wrong_program: bool,
    /// Signed change of the lamports a native curve holds.
    pub lamports: i128,
}

#[derive(Clone, Debug)]
pub struct Route {
    pub amount_in: u64,
    pub hop_fees: Vec<u8>,
    pub remaining_accounts: usize,
    pub source_mint: u8,
    pub destination_mint: u8,
    pub source_balance: u64,
    pub recipient_mint: u8,
    pub pool_migration_fee: u64,
    pub buyback_bps: u64,
    /// (protocol, creator) basis points of the one SOL tier and of the flat fees.
    pub tier_bps: (u64, u64),
    pub flat_bps: (u64, u64),
    pub epoch: u64,
    pub source_frozen: bool,
    pub destination_frozen: bool,
    pub source_cpi_guard: bool,
    pub destination_memo: bool,
    pub destination_bare: bool,
    pub recipient_bare: bool,
    /// The recipient account belongs to the other token program.
    pub recipient_wrong_program: bool,
    pub mints: Vec<Mint>,
    /// Curve index of each hop; a route may visit a curve twice.
    pub hops: Vec<usize>,
    pub curves: Vec<Curve>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct Settled {
    pub amount_out: u64,
    pub buyback_fee: u64,
    pub source: i128,
    pub destination: i128,
    pub destination_withheld: u64,
    pub user_lamports: i128,
    pub recipient: u64,
    pub recipient_withheld: u64,
    pub curves: Vec<Curve>,
}

fn add(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_add(b).ok_or(OVERFLOW)
}
fn sub(a: u64, b: u64) -> Result<u64, u32> {
    a.checked_sub(b).ok_or(OVERFLOW)
}
fn fee(amount: u64, bps: u64) -> Result<u64, u32> {
    u64::try_from((amount as u128 * bps as u128 + 9_999) / 10_000).map_err(|_| OVERFLOW)
}
fn output(amount_in: u64, reserve_in: u64, reserve_out: u64) -> Result<u64, u32> {
    let den = reserve_in as u128 + amount_in as u128;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount_in as u128 * reserve_out as u128 / den).map_err(|_| TRUNCATION)
}
fn buy_quote(c: &Curve, amount: u64) -> Result<u64, u32> {
    let den = (c.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or(OVERFLOW)?;
    if den == 0 {
        return Err(DIVISION_BY_ZERO);
    }
    u64::try_from(amount as u128 * c.virtual_quote_reserves as u128 / den + 1).map_err(|_| TRUNCATION)
}

/// Token-2022 fee on a transfer: the newer entry applies from its epoch on, the
/// rate rounds up and the maximum caps it.
fn transfer_fee(mint: &Mint, epoch: u64, amount: u64) -> u64 {
    let Some((older_bps, older_max, newer_epoch, newer_bps, newer_max)) = mint.transfer_fee else {
        return 0;
    };
    let (bps, max) = if epoch >= newer_epoch { (newer_bps, newer_max) } else { (older_bps, older_max) };
    (((amount as u128 * bps as u128 + 9_999) / 10_000).min(max as u128)) as u64
}

/// (net, protocol fee, creator fee) of a budget: the fees are charged on the
/// first net, and the net is trimmed if they do not fit. Callers price on
/// `budget - fees`, not on the trimmed net.
fn net_quote(p_rate: u64, c_rate: u64, budget: u64) -> Result<(u64, u64, u64), u32> {
    let total = p_rate + c_rate;
    let mut net = if total == 0 { budget } else { (budget as u128 * 10_000 / (10_000 + total as u128)) as u64 };
    if net == 0 {
        return Err(BUY_NOT_ENOUGH_SOL_TO_COVER_FEES);
    }
    let pf = fee(net, p_rate)?;
    let cf = fee(net, c_rate)?;
    let all = net.saturating_add(pf).saturating_add(cf);
    if all > budget {
        net = sub(net, all - budget)?;
        if net == 0 {
            return Err(BUY_SLIPPAGE_BELOW_MIN_TOKENS_OUT);
        }
    }
    Ok((net, pf, cf))
}

struct PostFill {
    base_out: u64,
    quote_in: u64,
    pf: u64,
    cf: u64,
}

/// The crossing fill: the rest of the budget after the curve is filled, priced
/// against the pool on `budget - fees`. The pool base is the vault's real
/// balance, so tokens a transfer fee withheld from it count against the pool.
fn complete_fill(r: &Route, c: &Curve, flag: u8, bps: (u64, u64), rates: (u64, u64), budget: u64) -> Result<Option<(u64, u64, u64, PostFill)>, u32> {
    let quote = buy_quote(c, c.real_token_reserves)?;
    let pf = if flag & 1 != 0 { fee(quote, bps.0)? } else { 0 };
    let cf = if flag & 2 != 0 && c.has_creator { fee(quote, bps.1)? } else { 0 };
    let total = add(add(quote, pf)?, cf)?;
    let remaining = match budget.checked_sub(total) {
        Some(v) if v > 0 => v,
        _ => return Ok(None),
    };
    let pool_base = sub(c.base_vault, c.real_token_reserves)?;
    let mut pool_quote = add(c.real_quote_reserves, quote)?;
    if c.quote_mint == NATIVE {
        pool_quote = sub(pool_quote, r.pool_migration_fee)?;
    }
    if pool_base == 0 {
        return Err(NOT_ENOUGH_TOKENS_TO_BUY);
    }
    if pool_quote == 0 {
        return Err(OVERFLOW);
    }
    let total_bps = rates.0 + rates.1;
    let net = if total_bps == 0 { remaining } else { (remaining as u128 * 10_000 / (10_000 + total_bps as u128)) as u64 };
    if net < 2 {
        return Ok(None);
    }
    let (_, post_pf, post_cf) = net_quote(rates.0, rates.1, remaining)?;
    let quote_in = sub(sub(remaining, post_pf)?, post_cf)?;
    let base_out = output(sub(quote_in, 1)?, pool_quote, pool_base)?;
    if base_out == 0 {
        return Ok(None);
    }
    Ok(Some((quote, pf, cf, PostFill { base_out, quote_in, pf: post_pf, cf: post_cf })))
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Holder {
    Source,
    Destination,
    Recipient,
    /// Curve index, base vault?
    Vault(usize, bool),
}

/// One `transfer_checked`; Pump skips the CPI on a zero amount, so a zero moves
/// nothing whatever the mint or accounts are.
fn transfer(r: &mut Route, s: &mut Settled, mint_id: u8, from: Holder, to: Holder, amount: u64) -> Result<(), u32> {
    if amount == 0 {
        return Ok(());
    }
    let frozen = |r: &Route, h: Holder| match h {
        Holder::Source => r.source_frozen,
        Holder::Destination => r.destination_frozen,
        Holder::Recipient => false,
        Holder::Vault(i, base) => if base { r.curves[i].base_frozen } else { r.curves[i].quote_frozen },
    };
    let balance = match from {
        Holder::Source => r.source_balance,
        Holder::Vault(i, true) => r.curves[i].base_vault,
        Holder::Vault(i, false) => r.curves[i].quote_vault,
        _ => 0,
    };
    let mint = r.mints[mint_id as usize].clone();
    if mint.token2022 && to == Holder::Destination && !r.mints[r.destination_mint as usize].token2022 {
        return Err(INCORRECT_PROGRAM_ID);
    }
    if frozen(r, from) || (!mint.token2022 && frozen(r, to)) {
        return Err(TOKEN_ACCOUNT_FROZEN);
    }
    if balance < amount {
        return Err(TOKEN_INSUFFICIENT_FUNDS);
    }
    if mint.non_transferable {
        return Err(TOKEN_NON_TRANSFERABLE);
    }
    if mint.paused {
        return Err(TOKEN_PAUSED);
    }
    if from == Holder::Source && r.source_cpi_guard {
        return Err(TOKEN_CPI_GUARD_TRANSFER_BLOCKED);
    }
    if frozen(r, to) {
        return Err(TOKEN_ACCOUNT_FROZEN);
    }
    if to == Holder::Destination && r.destination_mint != mint_id {
        return Err(TOKEN_MINT_MISMATCH);
    }
    if to == Holder::Destination && r.destination_memo {
        return Err(TOKEN_NO_MEMO);
    }
    let withheld = transfer_fee(&mint, r.epoch, amount);
    let bare = match to {
        Holder::Destination => r.destination_bare,
        Holder::Recipient => r.recipient_bare,
        Holder::Vault(i, base) => if base { r.curves[i].base_bare } else { r.curves[i].quote_bare },
        Holder::Source => false,
    };
    if bare && withheld > 0 {
        return Err(TOKEN_INVALID_STATE);
    }
    if mint.hook {
        return Err(MISSING_ACCOUNT);
    }
    let received = amount - withheld;
    match from {
        Holder::Source => {
            r.source_balance -= amount;
            s.source -= amount as i128;
        }
        Holder::Vault(i, true) => r.curves[i].base_vault -= amount,
        Holder::Vault(i, false) => r.curves[i].quote_vault -= amount,
        _ => {}
    }
    match to {
        Holder::Destination => {
            s.destination += received as i128;
            s.destination_withheld += withheld;
        }
        Holder::Recipient => {
            s.recipient += received;
            s.recipient_withheld += withheld;
        }
        Holder::Vault(i, true) => {
            r.curves[i].base_vault = r.curves[i].base_vault.saturating_add(received);
            r.curves[i].base_withheld += withheld;
        }
        Holder::Vault(i, false) => {
            r.curves[i].quote_vault = r.curves[i].quote_vault.saturating_add(received);
            r.curves[i].quote_withheld += withheld;
        }
        Holder::Source => {}
    }
    Ok(())
}

struct Hop {
    mint: u8,
    amount: u64,
    buyback: u64,
    vault: (usize, bool),
}

/// The first hop pays from the user; later hops from the last output vault. A
/// vault already holding the input moves nothing, so that hop pays no fee.
fn pay_in(r: &mut Route, s: &mut Settled, mint: u8, previous: Option<(usize, bool)>, to: (usize, bool), amount: u64) -> Result<(), u32> {
    let target = Holder::Vault(to.0, to.1);
    match previous {
        None => transfer(r, s, mint, Holder::Source, target, amount),
        Some(from) if from == to => Ok(()),
        Some((i, base)) => transfer(r, s, mint, Holder::Vault(i, base), target, amount),
    }
}

fn swap_hop(r: &mut Route, s: &mut Settled, idx: usize, current: u8, amount: u64, previous: Option<(usize, bool)>, last: bool, flag: u8) -> Result<Hop, u32> {
    let c = r.curves[idx].clone();
    // The hop's accounts load before anything else in it runs.
    if r.mints[c.base_mint as usize].unreadable || r.mints[c.quote_mint as usize].unreadable {
        return Err(INVALID_ACCOUNT_DATA);
    }
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    // A cashback coin is refused only when the hop charges the creator fee.
    if c.cashback && flag & 2 != 0 {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if c.mayhem {
        return Err(MAYHEM_CURVE_NOT_SUPPORTED);
    }
    let native = c.quote_mint == NATIVE;
    let quote = r.mints[c.quote_mint as usize].clone();
    // Only the quote's fee changes the arithmetic; a native curve never reads it.
    if !native && quote.malformed {
        return Err(UNSUPPORTED_QUOTE_MINT);
    }
    if c.base_wrong_program || c.quote_wrong_program {
        return Err(CONSTRAINT_SEEDS);
    }
    if flag & 1 != 0 {
        // The recipient's owner is compared with this hop's quote program first.
        if (r.mints[r.recipient_mint as usize].token2022 != r.recipient_wrong_program) != quote.token2022 {
            return Err(ACCOUNT_TYPE_NOT_SUPPORTED);
        }
        if r.recipient_mint != c.quote_mint {
            return Err(MINT_DOES_NOT_MATCH_BONDING_CURVE);
        }
    }
    let buy = if current == c.quote_mint {
        true
    } else if current == c.base_mint {
        false
    } else {
        return Err(DISCONTINUOUS_PATH);
    };
    let epoch = r.epoch;
    let quote_cut = |amount: u64| if native { 0 } else { transfer_fee(&quote, epoch, amount) };
    let bps = if native { r.tier_bps } else { r.flat_bps };
    let p_rate = if flag & 1 != 0 { bps.0 } else { 0 };
    let c_rate = if flag & 2 != 0 && c.has_creator { bps.1 } else { 0 };
    let (pf, cf, out, post) = if buy {
        // The hop prices what the vault will receive, not what it is sent.
        let trade = amount - quote_cut(amount);
        let (_, nf_p, nf_c) = net_quote(p_rate, c_rate, trade)?;
        let q = sub(sub(trade, nf_p)?, nf_c)?;
        let base = output(sub(q, 1)?, c.virtual_quote_reserves, c.virtual_token_reserves)?;
        if base == 0 {
            return Err(BUY_ZERO_AMOUNT);
        }
        let reserves = c.real_token_reserves;
        let (base_amount, quote_amount, pf, cf, post) = if base > reserves {
            match complete_fill(r, &c, flag, bps, (p_rate, c_rate), trade)? {
                None => (reserves, q, nf_p, nf_c, None),
                Some((quote, f_p, f_c, post)) => (reserves, quote, f_p, f_c, Some(post)),
            }
        } else {
            (base, q, nf_p, nf_c, None)
        };
        let raw = add(base_amount, post.as_ref().map_or(0, |p| p.base_out))?;
        if native {
            s.user_lamports -= amount as i128;
            r.curves[idx].lamports += amount as i128;
        } else {
            pay_in(r, s, c.quote_mint, previous, (idx, false), amount)?;
        }
        let c2 = &mut r.curves[idx];
        c2.virtual_token_reserves = sub(c2.virtual_token_reserves, base_amount)?;
        c2.real_token_reserves = sub(c2.real_token_reserves, base_amount)?;
        c2.virtual_quote_reserves = add(c2.virtual_quote_reserves, quote_amount)?;
        c2.real_quote_reserves = add(c2.real_quote_reserves, quote_amount)?;
        if last {
            transfer(r, s, c.base_mint, Holder::Vault(idx, true), Holder::Destination, raw)?;
        }
        (pf, cf, raw, post)
    } else {
        let gross = u64::try_from(c.virtual_quote_reserves as u128 * amount as u128 / (c.virtual_token_reserves as u128 + amount as u128)).map_err(|_| TRUNCATION)?;
        let pf = if flag & 1 != 0 { fee(gross, bps.0)? } else { 0 };
        let cf = if flag & 2 != 0 && c.has_creator { fee(gross, bps.1)? } else { 0 };
        let net = sub(sub(gross, pf)?, cf)?;
        if net == 0 {
            return Err(SELL_ZERO_AMOUNT);
        }
        // The next hop is told the amount after the quote fee, though the vault
        // keeps `net`; the last hop sends `net` and the mint withholds the fee.
        let out = net - quote_cut(net);
        pay_in(r, s, c.base_mint, previous, (idx, true), amount)?;
        let c2 = &mut r.curves[idx];
        c2.virtual_token_reserves = add(c2.virtual_token_reserves, amount)?;
        c2.real_token_reserves = add(c2.real_token_reserves, amount)?;
        c2.virtual_quote_reserves = sub(c2.virtual_quote_reserves, gross)?;
        c2.real_quote_reserves = sub(c2.real_quote_reserves, gross)?;
        if last && !native {
            transfer(r, s, c.quote_mint, Holder::Vault(idx, false), Holder::Destination, net)?;
        }
        (pf, cf, out, None)
    };
    let buyback_bps = r.buyback_bps;
    let split = |p: u64| (buyback_bps as u128 * p as u128 / 10_000) as u64;
    let buyback = split(pf);
    let post_buyback = post.as_ref().map_or(0, |p| split(p.pf));
    let c2 = &mut r.curves[idx];
    c2.protocol_fees = add(c2.protocol_fees, pf - buyback)?;
    c2.creator_fee = add(c2.creator_fee, cf)?;
    if let Some(p) = &post {
        c2.post_complete_base_out = p.base_out;
        c2.post_complete_quote_in = p.quote_in;
        c2.protocol_fees = add(c2.protocol_fees, p.pf - post_buyback)?;
        c2.creator_fee = add(c2.creator_fee, p.cf)?;
    }
    let paid = add(buyback, post_buyback)?;
    // The returned buyback is what the recipient receives, not what was sent.
    let received = paid - quote_cut(paid);
    if flag & 1 != 0 {
        if native {
            c2.lamports -= paid as i128;
            s.recipient = add(s.recipient, paid)?;
        } else {
            transfer(r, s, c.quote_mint, Holder::Vault(idx, false), Holder::Recipient, paid)?;
        }
    }
    let c2 = &mut r.curves[idx];
    if native && !buy && last {
        c2.lamports -= out as i128;
        s.user_lamports += out as i128;
    }
    if c2.real_token_reserves == 0 {
        c2.complete = true;
    }
    Ok(if buy {
        Hop { mint: c.base_mint, amount: out, buyback: received, vault: (idx, true) }
    } else {
        Hop { mint: c.quote_mint, amount: out, buyback: received, vault: (idx, false) }
    })
}

pub fn run(route: &Route) -> Result<Settled, u32> {
    let mut r = route.clone();
    if r.amount_in == 0 {
        return Err(BUY_ZERO_AMOUNT);
    }
    let count = r.remaining_accounts / 5;
    if r.remaining_accounts < 5 || count * 5 != r.remaining_accounts {
        return Err(NOT_ENOUGH_REMAINING_ACCOUNTS);
    }
    if r.hop_fees.len() != count || r.hop_fees.iter().any(|&f| f >= 4) {
        return Err(HOP_FEES_MISMATCH);
    }
    let mut s = Settled {
        amount_out: 0,
        buyback_fee: 0,
        source: 0,
        destination: 0,
        destination_withheld: 0,
        user_lamports: 0,
        recipient: 0,
        recipient_withheld: 0,
        curves: vec![],
    };
    let (mut current, mut amount, mut previous, mut total) = (r.source_mint, r.amount_in, None, 0u64);
    for i in 0..count {
        let (idx, flag) = (r.hops[i], r.hop_fees[i]);
        let out = swap_hop(&mut r, &mut s, idx, current, amount, previous, i + 1 == count, flag)?;
        previous = Some(out.vault);
        current = out.mint;
        amount = out.amount;
        total = add(total, out.buyback)?;
    }
    if current != r.destination_mint {
        return Err(DISCONTINUOUS_PATH);
    }
    s.amount_out = amount;
    s.buyback_fee = total;
    s.curves = r.curves;
    Ok(s)
}
