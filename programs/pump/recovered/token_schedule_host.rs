//! Host driver for `token_schedule.rs`, used by `tests/test_token_schedule_captured.py`.
//! One request per line:
//! `gva,start_time,end_time,seconds_in_a_day,day_number,token_supply_per_day,mint,timestamp`
//! where `gva` (the 544 GVA account bytes) and `mint` are hex. Answers
//! `error:<code>`, `panic`, or `ok,<gva hex>,<event hex>`.
#[path = "token_schedule.rs"]
mod token_schedule;

use std::io::{self, BufRead, Write};
use token_schedule::{Gva, Stop, Update, DAYS};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn word(data: &[u8], offset: usize) -> [u8; 8] {
    data[offset..offset + 8].try_into().unwrap()
}

fn decode(data: &[u8]) -> Gva {
    let array = |offset: usize| -> [u64; DAYS] { std::array::from_fn(|i| u64::from_le_bytes(word(data, offset + 8 * i))) };
    Gva {
        start_time: i64::from_le_bytes(word(data, 8)),
        end_time: i64::from_le_bytes(word(data, 16)),
        seconds_in_a_day: i64::from_le_bytes(word(data, 24)),
        mint: data[32..64].try_into().unwrap(),
        total_token_supply: array(64),
        sol_volumes: array(304),
    }
}

fn encode(head: &[u8], g: &Gva) -> Vec<u8> {
    let mut out = head[..8].to_vec();
    for value in [g.start_time, g.end_time, g.seconds_in_a_day] {
        out.extend_from_slice(&value.to_le_bytes());
    }
    out.extend_from_slice(&g.mint);
    for value in g.total_token_supply.iter().chain(g.sol_volumes.iter()) {
        out.extend_from_slice(&value.to_le_bytes());
    }
    out
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let data = unhex(f[0]);
    let mut gva = decode(&data);
    let update = Update {
        start_time: f[1].parse().unwrap(),
        end_time: f[2].parse().unwrap(),
        seconds_in_a_day: f[3].parse().unwrap(),
        day_number: f[4].parse().unwrap(),
        token_supply_per_day: f[5].parse().unwrap(),
        mint: unhex(f[6]).try_into().unwrap(),
    };
    match token_schedule::update(&mut gva, &update, f[7].parse().unwrap()) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Ok(event) => format!("ok,{},{}", hex(&encode(&data, &gva)), hex(&event)),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
