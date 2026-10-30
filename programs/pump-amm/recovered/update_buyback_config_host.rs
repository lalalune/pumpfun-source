//! stdin/stdout driver for `update_buyback_config.rs`, used by
//! `tests/test_pump_amm_update_buyback_config_captured.py`. One case per line:
//! `<fixed>,<flags>,<payload_hex>,<config_hex>,<admin_hex>,<remaining_hex>`
//! where `<payload_hex>` is the instruction data after the 8-byte
//! discriminator, `<flags>` is four `0`/`1` digits in `Accounts` field order
//! after `fixed`, and `<remaining_hex>` is the remaining account keys
//! concatenated. Answers are `error:<code>`, `error:InvalidAccountData`,
//! `error:BorshIoError` or `ok,<config_hex>`.
use std::io::{self, BufRead, Write};

#[path = "update_buyback_config.rs"]
mod update_buyback_config;
use update_buyback_config::*;

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
            fixed: f[0].parse().unwrap(),
            admin_signer: bit(0),
            config_owner_ok: bit(1),
            config_writable: bit(2),
            event_authority_ok: bit(3),
        };
        let remaining: Vec<[u8; 32]> = unhex(f[5]).chunks(32).map(|c| c.try_into().unwrap()).collect();
        let answer = match update_buyback_config(
            &unhex(f[2]),
            &accounts,
            &remaining,
            &unhex(f[3]),
            unhex(f[4]).try_into().unwrap(),
        ) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::Ok(config) => format!("ok,{}", hex(&config)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
