//! Captured schedule update of Pump `admin_update_token_incentives`: how the
//! GlobalVolumeAccumulator (GVA) time range, day length, mint and per-day
//! token supply change, and which check fails first.
//!
//! Checked against `evidence/original/pump/deployed.so` and the captured SPL
//! Token and Associated Token programs by
//! `tests/test_token_schedule_captured.py`. Not linked into the SBF crate.
//! This is not a byte-identity claim.

pub const START_TIME_IN_THE_PAST: u32 = 6031;
pub const END_TIME_IN_THE_PAST: u32 = 6032;
pub const END_TIME_BEFORE_START_TIME: u32 = 6033;
pub const TIME_RANGE_TOO_LARGE: u32 = 6034;
pub const END_TIME_BEFORE_CURRENT_DAY: u32 = 6035;
pub const SUPPLY_UPDATE_FOR_FINISHED_RANGE: u32 = 6036;
pub const DAY_INDEX_AFTER_END_INDEX: u32 = 6037;
pub const DAY_IN_ACTIVE_RANGE: u32 = 6038;
/// Days stored in the GVA arrays.
pub const DAYS: usize = 30;
const EVENT: [u8; 8] = [147, 250, 108, 120, 247, 29, 67, 222];

#[derive(Debug, PartialEq, Eq)]
pub enum Stop {
    Code(u32),
    /// The program aborts (an `expect`, a negative time converted to an
    /// index, or a zero day length where a day index is needed).
    Panic,
}

#[derive(Clone)]
pub struct Gva {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub mint: [u8; 32],
    pub total_token_supply: [u64; DAYS],
    pub sol_volumes: [u64; DAYS],
}

pub struct Update {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub day_number: u64,
    pub token_supply_per_day: u64,
    pub mint: [u8; 32],
}

fn index(value: i64) -> Result<u64, Stop> {
    u64::try_from(value).map_err(|_| Stop::Panic)
}

/// Day of `timestamp` in the range; `None` before the start or for a zero day.
fn day_index(g: &Gva, timestamp: i64) -> Result<Option<u64>, Stop> {
    let Some(elapsed) = index(timestamp)?.checked_sub(index(g.start_time)?) else { return Ok(None) };
    if g.seconds_in_a_day == 0 {
        return Ok(None);
    }
    Ok(Some(elapsed / index(g.seconds_in_a_day)?))
}

fn current_day(g: &Gva, timestamp: i64) -> Result<u64, Stop> {
    day_index(g, timestamp)?.ok_or(Stop::Panic)
}

/// Last day of the range; aborts when the range is inverted or the day is zero.
fn end_day(g: &Gva) -> Result<u64, Stop> {
    let (end, start) = (index(g.end_time)?, index(g.start_time)?);
    if end < start || g.seconds_in_a_day == 0 {
        return Err(Stop::Panic);
    }
    Ok((end - start) / index(g.seconds_in_a_day)?)
}

fn slot(array: &mut [u64; DAYS], day: u64) -> Result<&mut u64, Stop> {
    array.get_mut(day as usize).ok_or(Stop::Panic)
}

fn update_time_range(g: &mut Gva, start: i64, end: i64, timestamp: i64) -> Result<(), Stop> {
    if start != g.start_time {
        if start <= timestamp {
            return Err(Stop::Code(START_TIME_IN_THE_PAST));
        }
        // A new start drops every stored day.
        g.start_time = start;
        g.total_token_supply = [0; DAYS];
        g.sol_volumes = [0; DAYS];
    }
    if end <= timestamp {
        return Err(Stop::Code(END_TIME_IN_THE_PAST));
    }
    if end <= start {
        return Err(Stop::Code(END_TIME_BEFORE_START_TIME));
    }
    // Signed: a zero or negative day length always fails here.
    let limit = g.seconds_in_a_day.checked_mul(DAYS as i64).ok_or(Stop::Panic)? - 1;
    if limit < end.checked_sub(start).ok_or(Stop::Panic)? {
        return Err(Stop::Code(TIME_RANGE_TOO_LARGE));
    }
    g.end_time = end;
    if timestamp > g.start_time {
        // Mid-range: volumes of the days after today are cleared.
        let current = current_day(g, timestamp)?;
        let last = end_day(g)?;
        if last <= current {
            return Err(Stop::Code(END_TIME_BEFORE_CURRENT_DAY));
        }
        for day in current + 1..=last {
            *slot(&mut g.sol_volumes, day)? = 0;
        }
    }
    Ok(())
}

/// `day_number` below 30 sets one day; 30 or more sets every day from today
/// (or from day 0 before the start) through the last day.
fn update_token_supply(g: &mut Gva, day_number: u64, supply: u64, timestamp: i64) -> Result<(), Stop> {
    let first = if timestamp < g.start_time {
        0
    } else {
        if timestamp > g.end_time {
            return Err(Stop::Code(SUPPLY_UPDATE_FOR_FINISHED_RANGE));
        }
        current_day(g, timestamp)?
    };
    let last = end_day(g)?;
    if day_number < DAYS as u64 {
        if last < day_number {
            return Err(Stop::Code(DAY_INDEX_AFTER_END_INDEX));
        }
        if day_number < first {
            return Err(Stop::Code(DAY_IN_ACTIVE_RANGE));
        }
        *slot(&mut g.total_token_supply, day_number)? = supply;
    } else {
        for day in first..=last {
            *slot(&mut g.total_token_supply, day)? = supply;
        }
    }
    Ok(())
}

/// The handler after the account checks. The day length and mint are stored
/// first; the time range changes only when both new times are non-zero; the
/// supply changes only when `token_supply_per_day > 0`. Returns the event.
pub fn update(g: &mut Gva, u: &Update, timestamp: i64) -> Result<Vec<u8>, Stop> {
    g.seconds_in_a_day = u.seconds_in_a_day;
    g.mint = u.mint;
    if u.start_time != 0 && u.end_time != 0 {
        update_time_range(g, u.start_time, u.end_time, timestamp)?;
    }
    if u.token_supply_per_day > 0 {
        update_token_supply(g, u.day_number, u.token_supply_per_day, timestamp)?;
    }
    let mut event = Vec::with_capacity(88);
    event.extend_from_slice(&EVENT);
    event.extend_from_slice(&u.start_time.to_le_bytes());
    event.extend_from_slice(&u.end_time.to_le_bytes());
    event.extend_from_slice(&u.day_number.to_le_bytes());
    event.extend_from_slice(&u.token_supply_per_day.to_le_bytes());
    event.extend_from_slice(&u.mint);
    event.extend_from_slice(&u.seconds_in_a_day.to_le_bytes());
    event.extend_from_slice(&timestamp.to_le_bytes());
    Ok(event)
}
