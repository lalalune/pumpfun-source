//! Host driver for `handler_logs.rs`, used by
//! `tests/test_handler_logs_captured.py`. One request per line, op first:
//! `sweep,creator,amount`; `tokens,<token_incentives host line after the op>`;
//! `sync,user_hex,claimed_before,last_update,now,start`;
//! `cashback,lamports,size`; `cashback_token,balance or -`;
//! `collect,executable,lamports,data_len,vault,native or token:<amount>`;
//! `migrate,vt,vq,rt,rq`; `extend,size,kind`; `creator,metaplex,curve_has_creator,has_creators`;
//! `distribute,<creator_fee_distribution host line>,program_hex`;
//! `schedule,gva_hex,start,end,seconds,day,supply,mint_hex,now,key_hex,owner_hex,lamports`.
//! The answer is the expected lines joined by `|`, or `-` for none.
#[path = "creator_fee_distribution.rs"]
#[allow(dead_code)]
mod creator_fee_distribution;
#[path = "handler_logs.rs"]
mod handler_logs;
#[path = "token_incentives.rs"]
#[allow(dead_code)]
mod token_incentives;
#[path = "token_schedule.rs"]
#[allow(dead_code)]
mod token_schedule;

use creator_fee_distribution::{Distribution, Shareholder, Slot};
use handler_logs::{Collect, Dump};
use std::io::{self, BufRead, Write};

fn bytes(hex: &str) -> Vec<u8> {
    (0..hex.len() / 2).map(|i| u8::from_str_radix(&hex[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn key(hex: &str) -> [u8; 32] {
    bytes(hex).try_into().unwrap()
}

fn days(stored: &[u8], offset: usize) -> [u64; 30] {
    std::array::from_fn(|i| u64::from_le_bytes(stored[offset + 8 * i..offset + 8 * i + 8].try_into().unwrap()))
}

fn word(stored: &[u8], offset: usize) -> i64 {
    i64::from_le_bytes(stored[offset..offset + 8].try_into().unwrap())
}

fn tokens(f: &[&str]) -> Vec<String> {
    let i = |k: usize| f[k].parse::<i64>().unwrap();
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let mut g = token_incentives::Global {
        start_time: i(2),
        end_time: i(3),
        seconds_in_a_day: i(4),
        total_token_supply: [0; 30],
        sol_volumes: [0; 30],
    };
    for day in f[10].split(';').filter(|d| !d.is_empty()) {
        let p: Vec<u64> = day.split(':').map(|v| v.parse().unwrap()).collect();
        g.total_token_supply[p[0] as usize] = p[1];
        g.sol_volumes[p[0] as usize] = p[2];
    }
    let mut u = token_incentives::User {
        total_unclaimed_tokens: n(6),
        total_claimed_tokens: n(7),
        current_sol_volume: n(8),
        last_update_timestamp: i(9),
        ..Default::default()
    };
    match token_incentives::claim(&g, &mut u, i(1), n(5)) {
        Ok(amount) => handler_logs::claim_tokens(amount),
        Err(_) => vec![],
    }
}

fn distribute(f: &[&str]) -> Vec<String> {
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let shareholders = f[8]
        .split(';')
        .filter(|s| !s.is_empty())
        .map(|s| {
            let (bps, slot) = s.split_once(':').unwrap();
            let slot = match slot {
                "-" => None,
                "wrong" => Some(Slot::Wrong),
                "exec" => Some(Slot::Executable),
                held => {
                    let (lamports, data_len) = held.split_once('/').unwrap();
                    Some(Slot::Holder { lamports: lamports.parse().unwrap(), data_len: data_len.parse().unwrap() })
                }
            };
            Shareholder { bps: bps.parse().unwrap(), slot }
        })
        .collect();
    let d = Distribution {
        vault_lamports: n(2),
        shareholders,
        active: n(3) != 0,
        creator_fee: n(4),
        curve_creator_is_config: n(5) != 0,
        curve_has_quote_mint: n(6) != 0,
        config_mint_matches: n(7) != 0,
    };
    match creator_fee_distribution::amounts(&d) {
        Err(creator_fee_distribution::EXECUTABLE_RECIPIENT) => handler_logs::unable_to_distribute(&key(f[9])),
        Ok(a) if f[1] == "distribute" && a.available < a.minimum_distributable => {
            handler_logs::insufficient_fees(a.minimum_vault_balance)
        }
        _ => vec![],
    }
}

fn schedule(f: &[&str]) -> Vec<String> {
    let stored = bytes(f[1]);
    let i = |k: usize| f[k].parse::<i64>().unwrap();
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let mut g = token_schedule::Gva {
        start_time: word(&stored, 8),
        end_time: word(&stored, 16),
        seconds_in_a_day: word(&stored, 24),
        mint: stored[32..64].try_into().unwrap(),
        total_token_supply: days(&stored, 64),
        sol_volumes: days(&stored, 304),
    };
    let update = token_schedule::Update {
        start_time: i(2),
        end_time: i(3),
        seconds_in_a_day: i(4),
        day_number: n(5),
        token_supply_per_day: n(6),
        mint: key(f[7]),
    };
    if token_schedule::update(&mut g, &update, i(8)).is_err() {
        return vec![];
    }
    vec![handler_logs::schedule_dump(&Dump {
        start_time: g.start_time,
        end_time: g.end_time,
        seconds_in_a_day: g.seconds_in_a_day,
        mint: &g.mint,
        total_token_supply: &g.total_token_supply,
        sol_volumes: &g.sol_volumes,
        key: &key(f[9]),
        owner: &key(f[10]),
        lamports: n(11),
        stored: &stored,
    })]
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |k: usize| f[k].parse::<u64>().unwrap();
    let lines = match f[0] {
        "sweep" => handler_logs::sweep(n(1) != 0, n(2)),
        "tokens" => tokens(&f),
        "sync" => {
            let before = n(2);
            let reset = f[3].parse::<i64>().unwrap() < f[5].parse::<i64>().unwrap()
                && f[4].parse::<i64>().unwrap() < f[5].parse::<i64>().unwrap();
            handler_logs::sync(&key(f[1]), before, if reset { 0 } else { before })
        }
        "cashback" => handler_logs::cashback_native(n(1), n(2)),
        // `-` is the missing accumulator ATA; a balance is a u64. `.ok()` read
        // every malformed balance as the missing account too, and both answer
        // "No cashback to claim", so a corrupted case looked like a valid one.
        "cashback_token" => handler_logs::cashback_token(match f[1] {
            "-" => None,
            held => Some(held.parse().unwrap()),
        }),
        "collect" => {
            let quote = match f[5].split_once(':') {
                Some((_, amount)) => Collect::Token(amount.parse().unwrap()),
                None => Collect::Native,
            };
            handler_logs::collect(n(1) != 0, n(2), n(3), n(4), quote)
        }
        "extend" => handler_logs::target_size(f[2]).map_or(vec![], |size| handler_logs::extend(n(1), size)),
        "creator" => handler_logs::assign_creator(n(1) != 0, n(2) != 0, n(3) != 0),
        "migrate" => handler_logs::migrate([n(1), n(2), n(3), n(4)]),
        "distribute" => distribute(&f),
        "schedule" => schedule(&f),
        other => panic!("unknown op {other}"),
    };
    if lines.is_empty() {
        "-".to_string()
    } else {
        lines.join("|")
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
