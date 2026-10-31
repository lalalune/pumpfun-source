//! Captured panic sites of the Pump volume accumulator: which source location
//! and message abort `claim_token_incentives`,
//! `admin_update_token_incentives`, `claim_cashback_v2` and the v2 cashback
//! trades. `token_incentives.rs` and `token_schedule.rs` end such a case in a
//! plain `Panic`; this file names the site the original logs.
//!
//! Checked against `evidence/original/pump/deployed.so` by
//! `tests/test_incentive_panics_captured.py`, which also reads the location
//! table out of the ELF. Not linked into the SBF crate. This is not a
//! byte-identity claim.
//!
//! `DEAD` lists the locations of the file no input reaches. The only caller of
//! the volume update passes a volume of zero, so neither sum can overflow, and
//! a time range accepted by the size check always has a day index and at most
//! 30 days. Unconfirmed: this comes from reading the checks above those sites
//! and from every case here missing them, not from a proof over the ELF.

/// Days stored in the GlobalVolumeAccumulator arrays.
pub const DAYS: u64 = 30;
pub const TRUNCATION: u32 = 6025;
pub const START_TIME_IN_THE_PAST: u32 = 6031;
pub const END_TIME_IN_THE_PAST: u32 = 6032;
pub const END_TIME_BEFORE_START_TIME: u32 = 6033;
pub const TIME_RANGE_TOO_LARGE: u32 = 6034;
pub const END_TIME_BEFORE_CURRENT_DAY: u32 = 6035;
pub const SUPPLY_UPDATE_FOR_FINISHED_RANGE: u32 = 6036;
pub const DAY_INDEX_AFTER_END_INDEX: u32 = 6037;
pub const DAY_IN_ACTIVE_RANGE: u32 = 6038;
/// SPL Token `InsufficientFunds`.
pub const TOKEN_INSUFFICIENT_FUNDS: u32 = 1;

/// Line, column and message of a panic in `volume_accumulator.rs`.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Site {
    pub line: u32,
    pub col: u32,
    pub message: String,
}

fn site(line: u32, col: u32, message: &str) -> Site {
    Site { line, col, message: message.to_string() }
}

fn out_of_bounds(line: u32, col: u32, index: u64) -> Site {
    site(line, col, &format!("index out of bounds: the len is {DAYS} but the index is {index}"))
}

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    Panic(Site),
}

impl From<Site> for Stop {
    fn from(site: Site) -> Stop {
        Stop::Panic(site)
    }
}

/// Reached locations of the file, by line and column.
pub const REACHED: [(u32, u32); 15] = [
    (78, 17), (108, 14), (136, 14), (164, 22), (170, 22), (186, 22), (192, 22), (317, 13), (331, 14), (346, 13),
    (376, 18), (381, 18), (425, 14), (429, 43), (436, 28),
];
/// Locations no case reaches; see the header. Lines 8 and 19 are the two
/// `#[account]` expansions, not handler code.
pub const DEAD: [(u32, u32); 6] = [(8, 1), (19, 1), (53, 14), (390, 18), (397, 17), (431, 14)];

#[derive(Clone, Debug)]
pub struct Global {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub total_token_supply: [u64; DAYS as usize],
    pub sol_volumes: [u64; DAYS as usize],
}

#[derive(Clone, Debug, Default)]
pub struct User {
    pub total_unclaimed_tokens: u64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
    pub last_update_timestamp: i64,
}

fn time_index(value: i64) -> Result<u64, Site> {
    u64::try_from(value).map_err(|_| site(436, 28, "SVM is 64-bit: TryFromIntError(())"))
}

fn day_index(g: &Global, timestamp: i64) -> Result<Option<u64>, Site> {
    let now = time_index(timestamp)?;
    let start = time_index(g.start_time)?;
    let Some(elapsed) = now.checked_sub(start) else { return Ok(None) };
    if g.seconds_in_a_day == 0 {
        return Ok(None);
    }
    Ok(Some(elapsed / time_index(g.seconds_in_a_day)?))
}

fn end_day(g: &Global) -> Result<u64, Site> {
    let end = time_index(g.end_time)?;
    let start = time_index(g.start_time)?;
    if end < start || g.seconds_in_a_day == 0 {
        return Err(site(425, 14, "end_time should be bigger than start_time"));
    }
    Ok((end - start) / time_index(g.seconds_in_a_day)?)
}

fn roll_over(g: &Global, u: &mut User, current_day: u64, now: i64) -> Result<(), Stop> {
    let Some(last_day) = day_index(g, u.last_update_timestamp)? else { return Ok(()) };
    let end = end_day(g)?;
    if last_day < current_day && last_day <= end {
        if last_day >= DAYS {
            return Err(out_of_bounds(78, 17, last_day).into());
        }
        let sol_volume = g.sol_volumes[last_day as usize];
        if sol_volume > 0 && u.current_sol_volume > 0 {
            let supply = g.total_token_supply[last_day as usize];
            let tokens = u.current_sol_volume as u128 * supply as u128 / sol_volume as u128;
            let tokens = u64::try_from(tokens).map_err(|_| Stop::Code(TRUNCATION))?;
            u.total_unclaimed_tokens =
                u.total_unclaimed_tokens.checked_add(tokens).ok_or_else(|| site(108, 14, "Unexpected overflow"))?;
            u.last_update_timestamp = now;
            u.current_sol_volume = 0;
        }
    }
    Ok(())
}

/// `claim_token_incentives` after the account checks; the answer is the amount.
pub fn claim(g: &Global, u: &mut User, now: i64, vault_balance: u64) -> Result<u64, Stop> {
    if u.last_update_timestamp < g.start_time && now < g.start_time {
        u.total_claimed_tokens = 0;
    }
    let Some(current_day) = day_index(g, now)? else { return claim_unclaimed(u, vault_balance) };
    roll_over(g, u, current_day, now)?;
    if now <= g.end_time && current_day >= DAYS {
        // Adding zero volume still indexes today's bucket.
        return Err(out_of_bounds(429, 43, current_day).into());
    }
    claim_unclaimed(u, vault_balance)
}

fn claim_unclaimed(u: &User, vault_balance: u64) -> Result<u64, Stop> {
    let amount = u.total_unclaimed_tokens;
    if amount == 0 {
        return Ok(0);
    }
    if amount > vault_balance {
        return Err(Stop::Code(TOKEN_INSUFFICIENT_FUNDS));
    }
    u.total_claimed_tokens
        .checked_add(amount)
        .ok_or_else(|| site(136, 14, "called `Option::unwrap()` on a `None` value"))?;
    Ok(amount)
}

fn update_time_range(g: &mut Global, start: i64, end: i64, timestamp: i64) -> Result<(), Stop> {
    if start != g.start_time {
        if start <= timestamp {
            return Err(Stop::Code(START_TIME_IN_THE_PAST));
        }
        g.start_time = start;
    }
    if end <= timestamp {
        return Err(Stop::Code(END_TIME_IN_THE_PAST));
    }
    if end <= start {
        return Err(Stop::Code(END_TIME_BEFORE_START_TIME));
    }
    // The day length is scaled before the range is measured.
    let overflow = || site(376, 18, "Unexpected overflow");
    let limit = g.seconds_in_a_day.checked_mul(DAYS as i64).ok_or_else(overflow)? - 1;
    let size = end.checked_sub(start).ok_or_else(|| site(381, 18, "Unexpected overflow"))?;
    if limit < size {
        return Err(Stop::Code(TIME_RANGE_TOO_LARGE));
    }
    g.end_time = end;
    if timestamp > g.start_time {
        let current = day_index(g, timestamp)?.ok_or_else(|| site(390, 18, "current_timestamp should be bigger than start_time"))?;
        if end_day(g)? <= current {
            return Err(Stop::Code(END_TIME_BEFORE_CURRENT_DAY));
        }
    }
    Ok(())
}

fn update_token_supply(g: &Global, day_number: u64, timestamp: i64) -> Result<(), Stop> {
    if timestamp < g.start_time {
        let end = end_day(g)?;
        if day_number < DAYS {
            if end < day_number {
                return Err(Stop::Code(DAY_INDEX_AFTER_END_INDEX));
            }
        } else if end >= DAYS {
            return Err(out_of_bounds(317, 13, DAYS).into());
        }
        return Ok(());
    }
    if timestamp > g.end_time {
        return Err(Stop::Code(SUPPLY_UPDATE_FOR_FINISHED_RANGE));
    }
    let current = day_index(g, timestamp)?.ok_or_else(|| site(331, 14, "current_timestamp should be bigger than start_time"))?;
    let end = end_day(g)?;
    if day_number < DAYS {
        if end < day_number {
            return Err(Stop::Code(DAY_INDEX_AFTER_END_INDEX));
        }
        if day_number < current {
            return Err(Stop::Code(DAY_IN_ACTIVE_RANGE));
        }
    } else {
        // The fill starts at today, so a late today is the first bad index.
        let first = current.max(DAYS);
        if first <= end {
            return Err(out_of_bounds(346, 13, first).into());
        }
    }
    Ok(())
}

/// `admin_update_token_incentives` after the account checks.
pub fn schedule(g: &mut Global, start: i64, end: i64, seconds: i64, day: u64, supply: u64, timestamp: i64) -> Result<(), Stop> {
    g.seconds_in_a_day = seconds;
    if start != 0 && end != 0 {
        update_time_range(g, start, end, timestamp)?;
    }
    if supply > 0 {
        update_token_supply(g, day, timestamp)?;
    }
    Ok(())
}

/// The running cashback total a v2 trade adds to.
pub fn record_earned(earned: u64, amount: u64, native: bool) -> Result<u64, Site> {
    earned.checked_add(amount).ok_or_else(|| {
        if native {
            site(164, 22, "Overflowing cashback earned")
        } else {
            site(170, 22, "Overflowing stable cashback earned")
        }
    })
}

/// The running total `claim_cashback_v2` adds to.
pub fn record_claimed(claimed: u64, amount: u64, native: bool) -> Result<u64, Site> {
    claimed.checked_add(amount).ok_or_else(|| {
        if native {
            site(186, 22, "Overflowing total cashback claimed")
        } else {
            site(192, 22, "Overflowing total stable cashback claimed")
        }
    })
}
