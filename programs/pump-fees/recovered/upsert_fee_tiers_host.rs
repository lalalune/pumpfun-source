//! stdin/stdout driver for `upsert_fee_tiers.rs`, used by
//! `tests/test_pump_fees_upsert_fee_tiers_captured.py`. One case per line:
//! `<count>,<flags>,<payload_hex>,<config_hex>,<admin_hex>,<fee_config_hex>,<timestamp>`
//! where `<payload_hex>` is the instruction data after the 8-byte discriminator,
//! `<flags>` is six `0`/`1` digits in `Accounts` field order after `count`,
//! and `<timestamp>` is the clock's `unix_timestamp` as a signed integer.
//! Answers are `error:<code>`, `error:InvalidAccountData`, `error:BorshIoError`,
//! `error:ProgramFailedToComplete`, `event-then:<name>,<event_hex>` or
//! `ok,<config_hex>,<event_hex>`.
use std::io::{self, BufRead, Write};

#[path = "upsert_fee_tiers.rs"]
mod upsert_fee_tiers;
use upsert_fee_tiers::*;

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len()).step_by(2).map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let fields: Vec<&str> = line.trim().split(',').collect();
        let bit = |index: usize| fields[1].as_bytes()[index] == b'1';
        let accounts = Accounts {
            count: fields[0].parse().unwrap(),
            admin_signer: bit(0),
            config_owner_ok: bit(1),
            config_writable: bit(2),
            seeds_ok: bit(3),
            event_authority_ok: bit(4),
            program_ok: bit(5),
        };
        let answer = match upsert_fee_tiers(
            &unhex(fields[2]),
            &accounts,
            &unhex(fields[3]),
            unhex(fields[4]).try_into().unwrap(),
            unhex(fields[5]).try_into().unwrap(),
            fields[6].parse().unwrap(),
        ) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::ProgramFailedToComplete => "error:ProgramFailedToComplete".to_string(),
            Outcome::MissingAccountAfterEvent(event) => format!("event-then:MissingAccount,{}", hex(&event)),
            Outcome::BorshIoErrorAfterEvent(event) => format!("event-then:BorshIoError,{}", hex(&event)),
            Outcome::Ok { config, event } => format!("ok,{},{}", hex(&config), hex(&event)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
