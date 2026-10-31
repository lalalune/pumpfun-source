//! Scope excludes exact-drain/no-post-completion cases not exercised by the adapter.
//! The events `multi_hop_curve_swap` emits, recorded alongside the settlement
//! `multi_hop_token2022.rs` already models: one `TradeEvent` per hop, a
//! `CompleteEvent` when a hop's fill drains the curve, and a
//! `PostCompleteBuyEvent` when the crossing remainder buys from the pool.
//! `tests/test_multi_hop_token2022_captured.py` compares state only and says
//! so; `tests/test_multi_hop_events_captured.py` compares these events too.
//!
//! The hop loop below repeats the Token-2022 model's loop with recording
//! added, because the model's hop internals are private. The repetition is
//! guarded: `run_events` also runs the original model and answers
//! `MODEL_DRIFT` unless both settle identically (same error, or the same
//! `Settled`), so a copy that diverges from the model it extends fails every
//! route instead of quietly disagreeing with the captured program.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_multi_hop_events_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.
//!
//! Unconfirmed (미확인, outside the checked inputs): the events of a route
//! that fails after an earlier hop (they are in the failed transaction's logs
//! but commit nothing), and a `CompleteEvent` for a buy that drains a curve
//! whose real reserves were already zero.

#[path = "multi_hop_token2022.rs"]
pub mod mh;
pub use mh::{Curve, Mint, Route, Settled};
use mh::*;

/// The recording loop and the model it extends settled differently.
pub const MODEL_DRIFT: u32 = u32::MAX - 100;

/// One emitted event, in the order the program emits it. Keys, the user, the
/// timestamp and the fields the fixtures hold at zero (the fee recipient, the
/// volume accumulator, cashback, holder rewards, the shareholder list) are
/// left to the test, which knows the fixture; every number the hop actually
/// computed is here.
#[derive(Debug, PartialEq, Eq)]
pub enum Event {
    Trade {
        base_mint: u8,
        quote_mint: u8,
        has_creator: bool,
        mayhem: bool,
        buy: bool,
        token_amount: u64,
        quote_amount: u64,
        /// The transfer fee the hop deducted from its quote leg: from the
        /// amount in on a buy, from the net quote on a sell. The captured
        /// program appends it to `TradeEvent` past the IDL type's last field.
        quote_fee: u64,
        fee_bps: u64,
        fee: u64,
        creator_bps: u64,
        creator_fee: u64,
        buyback_bps: u64,
        /// What the buyback recipient receives for this hop, minus the post
        /// fill's share on the `Post` event: the buyback moves in one
        /// transfer, so the mint's transfer fee lands on the combined amount
        /// and the trade event carries the residual.
        buyback_fee: u64,
        virtual_token_reserves: u64,
        virtual_quote_reserves: u64,
        real_token_reserves: u64,
        real_quote_reserves: u64,
        /// The curve's creator-fee balance after the hop, post fill included:
        /// the fill's own `creator_fee` field above stays fill-only.
        creator_fee_unclaimed: u64,
    },
    Complete {
        curve: usize,
    },
    /// A self-CPI whose entire data is the Anchor event tag, made by a
    /// native hop that pays a nonzero buyback in lamports, just before its
    /// trade event. It has no `Program data:` log line and carries no event
    /// payload; what the call does inside the program is not modelled, only
    /// its presence, position and condition are pinned.
    Bare,
    Post {
        curve: usize,
        base_out: u64,
        quote_in: u64,
        fee_bps: u64,
        fee: u64,
        creator_bps: u64,
        creator_fee: u64,
        buyback_fee: u64,
        pool_base_before: u64,
        pool_quote_before: u64,
        pool_base_after: u64,
        pool_quote_after: u64,
    },
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

fn transfer_fee(mint: &Mint, epoch: u64, amount: u64) -> u64 {
    let Some((older_bps, older_max, newer_epoch, newer_bps, newer_max)) = mint.transfer_fee else {
        return 0;
    };
    let (bps, max) = if epoch >= newer_epoch { (newer_bps, newer_max) } else { (older_bps, older_max) };
    (((amount as u128 * bps as u128 + 9_999) / 10_000).min(max as u128)) as u64
}

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
    Vault(usize, bool),
}

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

fn pay_in(r: &mut Route, s: &mut Settled, mint: u8, previous: Option<(usize, bool)>, to: (usize, bool), amount: u64) -> Result<(), u32> {
    let target = Holder::Vault(to.0, to.1);
    match previous {
        None => transfer(r, s, mint, Holder::Source, target, amount),
        Some(from) if from == to => Ok(()),
        Some((i, base)) => transfer(r, s, mint, Holder::Vault(i, base), target, amount),
    }
}

/// What the hop's own `TradeEvent` reports: the fill alone, never the post
/// fill. `post` carries the crossing remainder for its two own events.
struct Fill {
    buy: bool,
    token_amount: u64,
    quote_amount: u64,
    quote_fee: u64,
    post: Option<PostFill>,
}

fn swap_hop(r: &mut Route, s: &mut Settled, idx: usize, current: u8, amount: u64, previous: Option<(usize, bool)>, last: bool, flag: u8, events: &mut Vec<Event>) -> Result<Hop, u32> {
    let c = r.curves[idx].clone();
    if r.mints[c.base_mint as usize].unreadable || r.mints[c.quote_mint as usize].unreadable {
        return Err(INVALID_ACCOUNT_DATA);
    }
    if c.complete {
        return Err(BONDING_CURVE_COMPLETE);
    }
    if c.cashback && flag & 2 != 0 {
        return Err(CASHBACK_COIN_NOT_SUPPORTED);
    }
    if c.mayhem {
        return Err(MAYHEM_CURVE_NOT_SUPPORTED);
    }
    let native = c.quote_mint == NATIVE;
    let quote = r.mints[c.quote_mint as usize].clone();
    if !native && quote.malformed {
        return Err(UNSUPPORTED_QUOTE_MINT);
    }
    if c.base_wrong_program || c.quote_wrong_program {
        return Err(CONSTRAINT_SEEDS);
    }
    if flag & 1 != 0 {
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
    // The event prints the creator rate whenever the hop's flag asks for it,
    // even on a curve with no creator to charge; the fee itself stays zero.
    let event_c_rate = if flag & 2 != 0 { bps.1 } else { 0 };
    let (pf, cf, out, fill) = if buy {
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
        let fill = Fill { buy: true, token_amount: base_amount, quote_amount, quote_fee: amount - trade, post };
        (pf, cf, raw, fill)
    } else {
        let gross = u64::try_from(c.virtual_quote_reserves as u128 * amount as u128 / (c.virtual_token_reserves as u128 + amount as u128)).map_err(|_| TRUNCATION)?;
        let pf = if flag & 1 != 0 { fee(gross, bps.0)? } else { 0 };
        let cf = if flag & 2 != 0 && c.has_creator { fee(gross, bps.1)? } else { 0 };
        let net = sub(sub(gross, pf)?, cf)?;
        if net == 0 {
            return Err(SELL_ZERO_AMOUNT);
        }
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
        let fill = Fill { buy: false, token_amount: amount, quote_amount: gross, quote_fee: net - out, post: None };
        (pf, cf, out, fill)
    };
    let buyback_bps = r.buyback_bps;
    let split = |p: u64| (buyback_bps as u128 * p as u128 / 10_000) as u64;
    let buyback = split(pf);
    let post_buyback = fill.post.as_ref().map_or(0, |p| split(p.pf));
    let c2 = &mut r.curves[idx];
    c2.protocol_fees = add(c2.protocol_fees, pf - buyback)?;
    c2.creator_fee = add(c2.creator_fee, cf)?;
    if let Some(p) = &fill.post {
        c2.post_complete_base_out = p.base_out;
        c2.post_complete_quote_in = p.quote_in;
        c2.protocol_fees = add(c2.protocol_fees, p.pf - post_buyback)?;
        c2.creator_fee = add(c2.creator_fee, p.cf)?;
    }
    let paid = add(buyback, post_buyback)?;
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
    if native && !fill.buy && last {
        c2.lamports -= out as i128;
        s.user_lamports += out as i128;
    }
    if c2.real_token_reserves == 0 {
        c2.complete = true;
    }
    // The hop settled; record its events in emission order. The trade event
    // reports the fill alone, then completion, then the post fill.
    if native && flag & 1 != 0 && paid > 0 {
        events.push(Event::Bare);
    }
    let settled_curve = r.curves[idx].clone();
    events.push(Event::Trade {
        base_mint: c.base_mint,
        quote_mint: c.quote_mint,
        has_creator: c.has_creator,
        mayhem: c.mayhem,
        buy: fill.buy,
        token_amount: fill.token_amount,
        quote_amount: fill.quote_amount,
        quote_fee: fill.quote_fee,
        fee_bps: p_rate,
        fee: pf,
        creator_bps: event_c_rate,
        creator_fee: cf,
        buyback_bps,
        // The hop's buyback moves in one transfer of the fill and post
        // shares together, so the trade event carries what the recipient
        // received for the hop minus the post event's own share.
        buyback_fee: received - (post_buyback - quote_cut(post_buyback)),
        virtual_token_reserves: settled_curve.virtual_token_reserves,
        virtual_quote_reserves: settled_curve.virtual_quote_reserves,
        real_token_reserves: settled_curve.real_token_reserves,
        real_quote_reserves: settled_curve.real_quote_reserves,
        creator_fee_unclaimed: settled_curve.creator_fee,
    });
    if fill.buy && c.real_token_reserves > 0 && fill.token_amount == c.real_token_reserves {
        events.push(Event::Complete { curve: idx });
    }
    if let Some(p) = &fill.post {
        // The pool the post fill priced against, as `complete_fill` saw it.
        let pool_base_before = c.base_vault - c.real_token_reserves;
        let mut pool_quote_before = c.real_quote_reserves + fill.quote_amount;
        if native {
            pool_quote_before -= r.pool_migration_fee;
        }
        events.push(Event::Post {
            curve: idx,
            base_out: p.base_out,
            quote_in: p.quote_in,
            fee_bps: p_rate,
            fee: p.pf,
            creator_bps: event_c_rate,
            creator_fee: p.cf,
            buyback_fee: post_buyback - quote_cut(post_buyback),
            pool_base_before,
            pool_quote_before,
            pool_base_after: pool_base_before - p.base_out,
            pool_quote_after: pool_quote_before + p.quote_in,
        });
    }
    Ok(if fill.buy {
        Hop { mint: c.base_mint, amount: out, buyback: received, vault: (idx, true) }
    } else {
        Hop { mint: c.quote_mint, amount: out, buyback: received, vault: (idx, false) }
    })
}

fn run_loop(route: &Route, events: &mut Vec<Event>) -> Result<Settled, u32> {
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
        let out = swap_hop(&mut r, &mut s, idx, current, amount, previous, i + 1 == count, flag, events)?;
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

/// Settle `route` and record its events. The settlement is cross-checked
/// against the Token-2022 model on every call; any divergence is
/// `MODEL_DRIFT`, never a silently different answer.
pub fn run_events(route: &Route) -> Result<(Settled, Vec<Event>), u32> {
    let mut events = Vec::new();
    let result = run_loop(route, &mut events);
    let agrees = match (&result, mh::run(route)) {
        (Ok(settled), Ok(plain)) => *settled == plain,
        (Err(mine), Err(theirs)) => *mine == theirs,
        _ => false,
    };
    if !agrees {
        return Err(MODEL_DRIFT);
    }
    result.map(|settled| (settled, events))
}
