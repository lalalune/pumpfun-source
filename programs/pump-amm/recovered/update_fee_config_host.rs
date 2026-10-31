//! stdin/stdout driver for `update_fee_config.rs`, used by
//! `tests/test_pump_amm_update_fee_config_captured.py`. One case per line:
//! `<count>,<flags>,<payload_hex>,<config_hex>,<admin_hex>,<timestamp>`
//! where `<payload_hex>` is the instruction data after the 8-byte
//! discriminator and `<flags>` is five `0`/`1` digits in `Accounts` field
//! order after `count`. Answers are `error:<code>`, `error:6000,<field>`,
//! `error:InvalidAccountData`, `error:BorshIoError`,
//! `event-then:MissingAccount,<event_hex>`,
//! `event-then:BorshIoError,<event_hex>` or `ok,<config_hex>,<event_hex>`.
use std::io::{self, BufRead, Write};

#[path = "update_fee_config.rs"]
mod update_fee_config;
use update_fee_config::*;

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let bit = |i: usize| f[1].as_bytes()[i] == b'1';
        let accounts = Accounts {
            count: f[0].parse().unwrap(),
            admin_signer: bit(0),
            config_owner_ok: bit(1),
            config_writable: bit(2),
            event_authority_ok: bit(3),
            program_ok: bit(4),
        };
        let answer = match update_fee_config(
            &unhex(f[2]),
            &accounts,
            &unhex(f[3]),
            unhex(f[4]).try_into().unwrap(),
            f[5].parse().unwrap(),
        ) {
            Outcome::Error { code, site } if site.is_empty() => format!("error:{code}"),
            Outcome::Error { code, site } => format!("error:{code},{site}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::MissingAccountAfterEvent(event) => format!("event-then:MissingAccount,{}", hex(&event)),
            Outcome::BorshIoErrorAfterEvent(event) => format!("event-then:BorshIoError,{}", hex(&event)),
            Outcome::Ok { config, event } => format!("ok,{},{}", hex(&config), hex(&event)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
