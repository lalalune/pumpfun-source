//! stdin/stdout driver for `global_config_toggles.rs`, used by
//! `tests/test_pump_amm_global_config_toggles_captured.py`. One case per line:
//! `<kind>,<count>,<flags>,<payload_hex>,<config_hex>,<admin_hex>,<timestamp>`
//! where `<kind>` is `disable`, `mayhem`, `cashback` or `boost`, `<payload_hex>`
//! is the instruction data after the 8-byte discriminator, and `<flags>` is five
//! `0`/`1` digits in `Accounts` field order after `count`. Answers are
//! `error:<code>`, `error:InvalidAccountData`, `error:BorshIoError`,
//! `event-then:MissingAccount,<event_hex>`, `event-then:BorshIoError,<event_hex>`
//! or `ok,<config_hex>,<event_hex>` (event empty when none is logged).
use std::io::{self, BufRead, Write};

#[path = "global_config_toggles.rs"]
mod global_config_toggles;
use global_config_toggles::*;

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
        let bit = |i: usize| f[2].as_bytes()[i] == b'1';
        let kind = match f[0] {
            "disable" => Kind::Disable,
            "mayhem" => Kind::ToggleMayhemMode,
            "cashback" => Kind::ToggleCashbackEnabled,
            "boost" => Kind::ToggleBoost,
            other => panic!("unknown kind {other}"),
        };
        let accounts = Accounts {
            count: f[1].parse().unwrap(),
            admin_signer: bit(0),
            config_owner_ok: bit(1),
            config_writable: bit(2),
            event_authority_ok: bit(3),
            program_ok: bit(4),
        };
        let answer = match global_config_toggle(
            kind,
            &unhex(f[3]),
            &accounts,
            &unhex(f[4]),
            unhex(f[5]).try_into().unwrap(),
            f[6].parse().unwrap(),
        ) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::MissingAccountAfterEvent(e) => format!("event-then:MissingAccount,{}", hex(&e)),
            Outcome::BorshIoErrorAfterEvent(e) => format!("event-then:BorshIoError,{}", hex(&e)),
            Outcome::Ok { config, event } => format!("ok,{},{}", hex(&config), hex(&event)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
