//! Captured day-rollover and claim accounting of Pump token incentives:
//! `claim_token_incentives` (volume update with zero new volume, then a claim
//! of every unclaimed token) and `sync_user_volume_accumulator` (the
//! pre-schedule reset of a user's claimed total).
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token and Associated Token programs by
//! `tests/test_token_incentives_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

pub const TRUNCATION: u32 = 6025;
/// SPL Token `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;
/// Days stored in the GlobalVolumeAccumulator arrays.
pub const DAYS: usize = 30;

#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Global {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub total_token_supply: [u64; DAYS],
    pub sol_volumes: [u64; DAYS],
}

#[derive(Clone, Debug, Default, PartialEq, Eq)]
pub struct User {
    pub needs_claim: bool,
    pub total_unclaimed_tokens: u64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
    pub last_update_timestamp: i64,
    pub has_total_claimed_tokens: bool,
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    Panic,
}

/// Timestamps are converted with a checked i64 -> usize cast that panics.
fn time_index(value: i64) -> Result<usize, Stop> {
    usize::try_from(value).map_err(|_| Stop::Panic)
}

fn day_index(g: &Global, timestamp: i64) -> Result<Option<usize>, Stop> {
    let now = time_index(timestamp)?;
    let start = time_index(g.start_time)?;
    let Some(elapsed) = now.checked_sub(start) else { return Ok(None) };
    if g.seconds_in_a_day == 0 {
        return Ok(None);
    }
    Ok(Some(elapsed / time_index(g.seconds_in_a_day)?))
}

fn end_day(g: &Global) -> Result<usize, Stop> {
    let end = time_index(g.end_time)?;
    let start = time_index(g.start_time)?;
    if end < start || g.seconds_in_a_day == 0 {
        return Err(Stop::Panic);
    }
    Ok((end - start) / time_index(g.seconds_in_a_day)?)
}

fn reset_before_start(g: &Global, u: &mut User, now: i64) {
    if u.last_update_timestamp < g.start_time && now < g.start_time {
        u.total_claimed_tokens = 0;
        u.has_total_claimed_tokens = false;
    }
}

fn roll_over(g: &Global, u: &mut User, current_day: usize, now: i64) -> Result<(), Stop> {
    let Some(last_day) = day_index(g, u.last_update_timestamp)? else { return Ok(()) };
    let end = end_day(g)?;
    if last_day < current_day && last_day <= end {
        let sol_volume = *g.sol_volumes.get(last_day).ok_or(Stop::Panic)?;
        let token_supply = g.total_token_supply[last_day];
        if sol_volume > 0 {
            if u.current_sol_volume == 0 {
                return Ok(());
            }
            let tokens = u.current_sol_volume as u128 * token_supply as u128 / sol_volume as u128;
            let tokens = u64::try_from(tokens).map_err(|_| Stop::Code(TRUNCATION))?;
            u.total_unclaimed_tokens = u.total_unclaimed_tokens.checked_add(tokens).ok_or(Stop::Panic)?;
            u.needs_claim = u.total_unclaimed_tokens > 0;
            u.last_update_timestamp = now;
            u.current_sol_volume = 0;
        }
    }
    Ok(())
}

/// Volume update with zero new volume, as `claim_token_incentives` runs it.
pub fn update(g: &Global, u: &mut User, now: i64) -> Result<(), Stop> {
    reset_before_start(g, u, now);
    let Some(current_day) = day_index(g, now)? else { return Ok(()) };
    roll_over(g, u, current_day, now)?;
    if now <= g.end_time {
        // Adding zero still indexes the day bucket and stamps the user.
        if current_day >= DAYS {
            return Err(Stop::Panic);
        }
        u.needs_claim = u.total_unclaimed_tokens > 0 || u.current_sol_volume > 0;
        u.last_update_timestamp = now;
    }
    Ok(())
}

/// Returns the tokens transferred to the user (0 when nothing is claimable).
pub fn claim(g: &Global, u: &mut User, now: i64, vault_balance: u64) -> Result<u64, Stop> {
    update(g, u, now)?;
    let amount = u.total_unclaimed_tokens;
    if amount == 0 {
        return Ok(0);
    }
    if amount > vault_balance {
        return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
    }
    let claimed = u.total_claimed_tokens.checked_add(amount).ok_or(Stop::Panic)?;
    u.last_update_timestamp = now;
    u.has_total_claimed_tokens = claimed > 0;
    u.needs_claim = u.current_sol_volume > 0;
    u.total_claimed_tokens = claimed;
    u.total_unclaimed_tokens = 0;
    Ok(amount)
}

/// `sync_user_volume_accumulator`: only the pre-schedule reset. Returns the
/// claimed total before and after.
pub fn sync(g: &Global, u: &mut User, now: i64) -> (u64, u64) {
    let before = u.total_claimed_tokens;
    reset_before_start(g, u, now);
    (before, u.total_claimed_tokens)
}
