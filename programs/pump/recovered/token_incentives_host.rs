//! Host driver for `token_incentives.rs`, used by
//! `tests/test_token_incentives_captured.py`. One request per line:
//! `op,now,start,end,seconds_in_a_day,vault_balance,needs_claim,unclaimed,
//!  claimed,current_sol_volume,last_update,has_claimed,days`
//! where `op` is `claim|sync` and `days` is `index:token_supply:sol_volume`
//! joined by `;` (unlisted days are zero). Answers are
//! `ok,<amount or claimed-before>,<user fields...>`, `error:<code>`, or `panic`.
#[path = "token_incentives.rs"]
mod token_incentives;

use std::io::{self, BufRead, Write};
use token_incentives::{Global, Stop, User, DAYS};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let i = |k: usize| f[k].parse::<i64>().unwrap();
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let mut g = Global {
        start_time: i(2),
        end_time: i(3),
        seconds_in_a_day: i(4),
        total_token_supply: [0; DAYS],
        sol_volumes: [0; DAYS],
    };
    for day in f[12].split(';').filter(|d| !d.is_empty()) {
        let p: Vec<u64> = day.split(':').map(|v| v.parse().unwrap()).collect();
        g.total_token_supply[p[0] as usize] = p[1];
        g.sol_volumes[p[0] as usize] = p[2];
    }
    let mut u = User {
        needs_claim: n(6) != 0,
        total_unclaimed_tokens: n(7),
        total_claimed_tokens: n(8),
        current_sol_volume: n(9),
        last_update_timestamp: i(10),
        has_total_claimed_tokens: n(11) != 0,
    };
    let first = match f[0] {
        "claim" => match token_incentives::claim(&g, &mut u, i(1), n(5)) {
            Ok(amount) => amount,
            Err(Stop::Code(code)) => return format!("error:{code}"),
            Err(Stop::Panic) => return "panic".to_string(),
        },
        "sync" => token_incentives::sync(&g, &mut u, i(1)).0,
        other => panic!("unknown op {other}"),
    };
    format!(
        "ok,{},{},{},{},{},{},{}",
        first,
        u.needs_claim as u8,
        u.total_unclaimed_tokens,
        u.total_claimed_tokens,
        u.current_sol_volume,
        u.last_update_timestamp,
        u.has_total_claimed_tokens as u8,
    )
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
