use crate::PumpError;
use anchor_lang::prelude::*;

// layout-pad(4): aligns the next Source site with the original line



#[account]
#[derive(Debug)]
pub struct GlobalVolumeAccumulator {
    pub start_time: i64,
    pub end_time: i64,
    pub seconds_in_a_day: i64,
    pub mint: Pubkey,
    pub total_token_supply: [u64;30],
    pub sol_volumes: [u64;30],
}

#[account]
#[derive(Default)]
pub struct UserVolumeAccumulator{pub user:Pubkey,pub needs_claim:bool,pub total_unclaimed_tokens:u64,pub total_claimed_tokens:u64,pub current_sol_volume:u64,pub last_update_timestamp:i64,pub has_total_claimed_tokens:bool,pub cashback_earned:u64,pub total_cashback_claimed:u64,pub stable_cashback_earned:u64,pub total_stable_cashback_claimed:u64}
// Captured main-Pump worker: 0x7bfd8. Claim passes zero new volume, while
// the recovered worker retains the original generic update signature.


























impl UserVolumeAccumulator {
    fn add_sol_volume(&mut self, sol_volume: u64, now: i64) {
        self.current_sol_volume = self.current_sol_volume.checked_add(sol_volume)
            .expect("Overflowing user accumulator sol volume");
        self.needs_claim = self.total_unclaimed_tokens > 0 || self.current_sol_volume > 0;
        self.last_update_timestamp = now;
    }
}

fn roll_over(
    global: &GlobalVolumeAccumulator,
    user: &mut UserVolumeAccumulator,
    current_day: usize,
    now: i64,
) -> Result<()> {
    if let Some(last_update_day) = day_index(global, user.last_update_timestamp) {
        let end_day = end_day(global);
        if last_update_day < current_day && last_update_day <= end_day {
// layout-pad(9): aligns the next Source site with the original line








            let sol_volume =
                global.sol_volumes[last_update_day];
            let token_supply = global.total_token_supply[last_update_day];
            if sol_volume > 0 {
                if user.current_sol_volume == 0 {
                    return Ok(());
                }
                let tokens = match u64::try_from(
                    (user.current_sol_volume as u128) * (token_supply as u128) / (sol_volume as u128),
                ) {
                    Ok(tokens) => tokens,
// layout-pad(15): aligns the next Source site with the original line














                    Err(_) => return Err(error!(PumpError::Truncation)),
                };
                user.total_unclaimed_tokens = user
                    .total_unclaimed_tokens
                    .checked_add(tokens)
            .expect("Unexpected overflow");
                user.needs_claim = user.total_unclaimed_tokens > 0;
                user.last_update_timestamp = now;
                user.current_sol_volume = 0;
            }
        }
    }
    Ok(())
}
// layout-pad(14): aligns the next Source site with the original line













#[inline]
pub fn record_claim(user: &mut UserVolumeAccumulator, timestamp: i64) {
    let claimed = user
            .total_claimed_tokens
            .checked_add(user.total_unclaimed_tokens)
            .unwrap();
    user.last_update_timestamp = timestamp;
    user.has_total_claimed_tokens = claimed > 0;
    user.needs_claim = user.current_sol_volume > 0;
    user.total_claimed_tokens = claimed;
    user.total_unclaimed_tokens = 0;
}

// layout-pad(13): aligns the next Source site with the original line












#[inline(never)]
pub fn record_cashback_earned(user: &mut UserVolumeAccumulator, amount: u64, native: bool) -> Result<()> {
    if native {
        user.cashback_earned =
            user
                .cashback_earned
                .checked_add(amount)
                    .expect("Overflowing cashback earned");
    } else {
        user.stable_cashback_earned =
            user
                .stable_cashback_earned
                .checked_add(amount)
                    .expect("Overflowing stable cashback earned");
    }
    Ok(())
}

// layout-pad(4): aligns the next Source site with the original line



#[inline(never)]
pub fn record_cashback_claim(user: &mut UserVolumeAccumulator, amount: u64, native: bool) -> Result<()> {
    if native {
        user.total_cashback_claimed =
            user
                .total_cashback_claimed
                .checked_add(amount)
                    .expect("Overflowing total cashback claimed");
    } else {
        user.total_stable_cashback_claimed =
            user
                .total_stable_cashback_claimed
                .checked_add(amount)
                    .expect("Overflowing total stable cashback claimed");
    }
    Ok(())
}

// layout-pad(53): aligns the next Source site with the original line

#[inline(never)]
pub fn update(
    global: &mut GlobalVolumeAccumulator,
    user: &mut UserVolumeAccumulator,
    now: i64,
    volume: u64,
    key: &Pubkey,
) -> Result<()> {
    user.user = *key;
    if user.last_update_timestamp < global.start_time && now < global.start_time {
        user.total_claimed_tokens = 0;
        user.has_total_claimed_tokens = false;
    }
    let result = match day_index(global, now) {
        Some(current_day) => roll_over(global, user, current_day, now).map(|()| Some(current_day)),
        None => return Ok(()),
    };
    if let Ok(Some(current_day)) = result {
        if now <= global.end_time {
            global.add_sol_volume(current_day, volume);
            user.add_sol_volume(volume, now);
        }
    }
    result.map(|_| ())
}


























// Captured state-update worker at 0x7c720, called by the scheduler's outer handler.
#[inline(never)]
pub fn update_schedule(
    accumulator: &mut GlobalVolumeAccumulator,
    start_time: i64,
    end_time: i64,
    seconds_in_a_day: i64,
    mint: &Pubkey,
    day_number: u64,
    token_supply_per_day: u64,
    timestamp: i64,
) -> Result<()> {
    accumulator.seconds_in_a_day = seconds_in_a_day;
    accumulator.mint = *mint;
    if start_time != 0 && end_time != 0 {
        update_time_range(accumulator, start_time, end_time, timestamp)?;
    }
    if token_supply_per_day > 0 {
        update_token_supply(accumulator, day_number, token_supply_per_day, timestamp)?;
    }
    Ok(())
}

#[inline]
fn day_index(accumulator: &GlobalVolumeAccumulator, timestamp: i64) -> Option<usize> {
    time_index(timestamp)
        .checked_sub(time_index(accumulator.start_time))
        .and_then(|elapsed| {
            (accumulator.seconds_in_a_day != 0).then(|| elapsed / time_index(accumulator.seconds_in_a_day))
        })
}

#[inline]
fn update_token_supply(
    accumulator: &mut GlobalVolumeAccumulator,
    day_number: u64,
    token_supply_per_day: u64,
    timestamp: i64,
) -> Result<()> {
    if timestamp < accumulator.start_time {
        return update_token_supply_before_start(accumulator, day_number, token_supply_per_day);
    }
// layout-pad(5): aligns the next Source site with the original line




    require!(timestamp <= accumulator.end_time, PumpError::SupplyUpdateForFinishedRange);
    update_token_supply_after_start(accumulator, day_number, token_supply_per_day, timestamp)
}

#[inline]
fn update_token_supply_before_start(
    accumulator: &mut GlobalVolumeAccumulator,
    day_number: u64,
    token_supply_per_day: u64,
) -> Result<()> {
    let end = end_day(accumulator);
    if day_number < 30 {
        require_gte!(end, day_number as usize, PumpError::DayIndexAfterEndIndex);
        set_token_supply(
            accumulator,
            day_number as usize,
            token_supply_per_day,
        );
    } else {
        for index in 0..=end {
            accumulator.total_token_supply[index] = token_supply_per_day;
        }
    }
    Ok(())
}

#[inline]
fn update_token_supply_after_start(
    accumulator: &mut GlobalVolumeAccumulator,
    day_number: u64,
    token_supply_per_day: u64,
    timestamp: i64,
) -> Result<()> {
    let current = day_index(accumulator, timestamp)
            .expect("current_timestamp should be bigger than start_time");
    let end = end_day(accumulator);
    if day_number < 30 {
// layout-pad(3): aligns the next Source site with the original line


        require_gte!(end, day_number as usize, PumpError::DayIndexAfterEndIndex);
        require_gte!(day_number as usize, current, PumpError::DayInActiveRange);
        set_token_supply(
            accumulator,
            day_number as usize,
            token_supply_per_day,
        );
    } else {
        for index in current..=end {
            accumulator.total_token_supply[index] = token_supply_per_day;
        }
    }
    Ok(())
}

#[inline]
fn update_time_range(
    accumulator: &mut GlobalVolumeAccumulator,
    start_time: i64, end_time: i64,
    timestamp: i64,
) -> Result<()> {
    if start_time != accumulator.start_time {
        require_gt!(start_time, timestamp, PumpError::StartTimeInThePast);
        accumulator.start_time = start_time;
        accumulator.total_token_supply = [0; 30];
        accumulator.sol_volumes = [0; 30];
    }
// layout-pad(5): aligns the next Source site with the original line




    require_gt!(end_time, timestamp, PumpError::EndTimeInThePast);
// layout-pad(1): aligns the next Source site with the original line
    require_gt!(end_time, start_time, PumpError::EndTimeBeforeStartTime);
// layout-pad(1): aligns the next Source site with the original line
    require_gte!(
        accumulator
            .seconds_in_a_day.checked_mul(30)
                .expect("Unexpected overflow")
            - 1,
        end_time
            .checked_sub(start_time)
            // layout-pad(1): aligns the next panic Location with the original line
                .expect("Unexpected overflow"),
        PumpError::TimeRangeTooLarge
    );
    accumulator.end_time = end_time;
    if timestamp > accumulator.start_time {
// layout-pad(3): aligns the next Source site with the original line


        let current = day_index(accumulator, timestamp)
                .expect("current_timestamp should be bigger than start_time");
        let next = current + 1;
        let end = end_day(accumulator);
// layout-pad(1): aligns the next Source site with the original line
        require_gt!(end, current, PumpError::EndTimeBeforeCurrentDay);
        for index in next..=end {
// layout-pad(1): aligns the next Source site with the original line
                accumulator.sol_volumes[index] = 0;
        }
    }
    Ok(())
}


fn set_token_supply(accumulator: &mut GlobalVolumeAccumulator, day: usize, token_supply_per_day: u64) {
    accumulator.total_token_supply[day] = token_supply_per_day;
}
// layout-pad(14): aligns the next Source site with the original line













#[cold]
#[inline(always)]
fn end_day_failure() -> usize {
    None::<usize>
            .expect("end_time should be bigger than start_time")
}
impl GlobalVolumeAccumulator {
    fn add_sol_volume(&mut self, current_index: usize, sol_volume: u64) {
        self.sol_volumes[current_index] = self.sol_volumes[current_index]
            .checked_add(sol_volume)
            .expect("Overflowing sol volume");
    }
}

fn time_index(value: i64) -> usize {
    usize::try_from(value).expect("SVM is 64-bit")
}

#[inline(never)]
pub(crate) fn end_day(global: &GlobalVolumeAccumulator) -> usize {
    let end = time_index(global.end_time);
    let start = time_index(global.start_time);
    if end < start {
        return end_day_failure();
    }
    let divisor = match core::num::NonZeroI64::new(global.seconds_in_a_day) {
        Some(value) => value,
        None => return end_day_failure(),
    };
    (end - start) / time_index(divisor.get())
}
