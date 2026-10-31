//! stdin/stdout driver for `create_config.rs`, used by
//! `tests/test_pump_amm_create_config_captured.py`. One case per line:
//! `<count>,<flags>,<payload_hex>,<admin_hex>,<timestamp>,<config_lamports>,<config_data_len>,<config_system_owned>,<admin_lamports>,<rent>`
//! where `<payload_hex>` is the instruction data after the 8-byte
//! discriminator and `<flags>` is seven `0`/`1` digits in `Accounts` field
//! order after `count`. Answers are `error:<code>`, `error:<code>,<site>`,
//! `error:PrivilegeEscalation`, `event-then:MissingAccount,<event_hex>` or
//! `ok,<config_hex>,<event_hex>,<config_lamports>,<admin_lamports>`.
use std::io::{self, BufRead, Write};

#[path = "create_config.rs"]
mod create_config;
use create_config::*;

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
            admin_writable: bit(1),
            config_writable: bit(2),
            config_seeds_ok: bit(3),
            system_program_ok: bit(4),
            event_authority_ok: bit(5),
            program_ok: bit(6),
            config_lamports: f[5].parse().unwrap(),
            config_data_len: f[6].parse().unwrap(),
            config_system_owned: f[7] == "1",
            admin_lamports: f[8].parse().unwrap(),
            rent: f[9].parse().unwrap(),
        };
        let answer = match create_config(&unhex(f[2]), &accounts, unhex(f[3]).try_into().unwrap(), f[4].parse().unwrap()) {
            Outcome::Error { code, site } if site.is_empty() => format!("error:{code}"),
            Outcome::Error { code, site } => format!("error:{code},{site}"),
            Outcome::PrivilegeEscalation => "error:PrivilegeEscalation".to_string(),
            Outcome::MissingAccountAfterEvent(event) => format!("event-then:MissingAccount,{}", hex(&event)),
            Outcome::Created { config, event, config_lamports, admin_lamports } => {
                format!("ok,{},{},{config_lamports},{admin_lamports}", hex(&config), hex(&event))
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
