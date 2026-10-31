//! Host driver for `incentive_panics.rs`, used by
//! `tests/test_incentive_panics_captured.py`. One request per line:
//! `claim,now,start,end,seconds,vault,unclaimed,claimed,volume,last_update,days`
//! where `days` is `index:token_supply:sol_volume` joined by `;`,
//! `schedule,now,old_start,old_end,start,end,seconds,day,supply`,
//! `earned,native,total,amount`, `claimed,native,total,amount`, or `sites`.
//! Answers are `ok`, `error:<code>`, or `panic:<line>:<col>:<message>`; `sites`
//! lists the reached and the dead locations as `line:col;...|line:col;...`.
#[path = "incentive_panics.rs"]
mod incentive_panics;

use incentive_panics::{Global, Site, Stop, User, DAYS, DEAD, REACHED};
use std::io::{self, BufRead, Write};

fn text(result: Result<(), Stop>) -> String {
    match result {
        Ok(()) => "ok".to_string(),
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic(Site { line, col, message })) => format!("panic:{line}:{col}:{message}"),
    }
}

fn list(sites: &[(u32, u32)]) -> String {
    sites.iter().map(|(line, col)| format!("{line}:{col}")).collect::<Vec<_>>().join(";")
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let i = |k: usize| f[k].parse::<i64>().unwrap();
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let days = DAYS as usize;
    let empty = Global { start_time: 0, end_time: 0, seconds_in_a_day: 0, total_token_supply: [0; 30], sol_volumes: [0; 30] };
    match f[0] {
        "sites" => format!("{}|{}", list(&REACHED), list(&DEAD)),
        "claim" => {
            let mut g = Global { start_time: i(2), end_time: i(3), seconds_in_a_day: i(4), ..empty };
            for day in f[10].split(';').filter(|d| !d.is_empty()) {
                let p: Vec<u64> = day.split(':').map(|v| v.parse().unwrap()).collect();
                assert!((p[0] as usize) < days);
                g.total_token_supply[p[0] as usize] = p[1];
                g.sol_volumes[p[0] as usize] = p[2];
            }
            let mut u = User {
                total_unclaimed_tokens: n(6),
                total_claimed_tokens: n(7),
                current_sol_volume: n(8),
                last_update_timestamp: i(9),
            };
            text(incentive_panics::claim(&g, &mut u, i(1), n(5)).map(|_| ()))
        }
        "schedule" => {
            let mut g = Global { start_time: i(2), end_time: i(3), ..empty };
            text(incentive_panics::schedule(&mut g, i(4), i(5), i(6), n(7), n(8), i(1)))
        }
        "earned" => text(incentive_panics::record_earned(n(2), n(3), n(1) != 0).map(|_| ()).map_err(Stop::Panic)),
        "claimed" => text(incentive_panics::record_claimed(n(2), n(3), n(1) != 0).map(|_| ()).map_err(Stop::Panic)),
        other => panic!("unknown op {other}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
