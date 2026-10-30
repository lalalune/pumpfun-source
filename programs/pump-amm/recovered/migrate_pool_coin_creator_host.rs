//! stdin/stdout driver for `migrate_pool_coin_creator.rs`, used by
//! `tests/test_pump_amm_migrate_pool_coin_creator_captured.py`. One case per
//! line: `<payload_len>,<count>,<flags>,<pool_hex>,<sharing_hex>,<pool_key_hex>,
//! <sharing_key_hex>,<timestamp>` where `<flags>` is eight `0`/`1` digits in
//! `Accounts` field order after `count`. Answers are `error:<code>`,
//! `error:InvalidAccountData`, `error:BorshIoError`,
//! `event-then:MissingAccount,<event_hex>`, `event-then:BorshIoError,<event_hex>`
//! or `ok,<pool_hex>,<event_hex>`.
use std::io::{self, BufRead, Write};

#[path = "migrate_pool_coin_creator.rs"]
mod migrate_pool_coin_creator;
use migrate_pool_coin_creator::*;

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn key(s: &str) -> [u8; 32] {
    unhex(s).try_into().unwrap()
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let bit = |i: usize| f[2].as_bytes()[i] == b'1';
        let accounts = Accounts {
            count: f[1].parse().unwrap(),
            pool_owner_ok: bit(0),
            pool_writable: bit(1),
            pool_canonical: bit(2),
            pool_seeds_ok: bit(3),
            sharing_owner_ok: bit(4),
            sharing_seeds_ok: bit(5),
            event_seeds_ok: bit(6),
            program_ok: bit(7),
        };
        let answer = match migrate_pool_coin_creator(
            f[0].parse().unwrap(),
            &accounts,
            &unhex(f[3]),
            &unhex(f[4]),
            key(f[5]),
            key(f[6]),
            f[7].parse().unwrap(),
        ) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::MissingAccountAfterEvent(e) => format!("event-then:MissingAccount,{}", hex(&e)),
            Outcome::BorshIoErrorAfterEvent(e) => format!("event-then:BorshIoError,{}", hex(&e)),
            Outcome::Migrated { pool, event } => format!("ok,{},{}", hex(&pool), hex(&event)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
