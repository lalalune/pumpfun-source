//! stdin/stdout driver for `update_creator_fee_config.rs`, used by
//! `tests/test_pump_amm_update_creator_fee_config_captured.py`. One case per line:
//! `<count>,<flags>,<payload_hex>,<config_hex>,<admin_hex>,<timestamp>,<config_lamports>,<admin_lamports>,<rent949>,<admin_data_len>`
//! where `<payload_hex>` is the instruction data after the 8-byte discriminator
//! and `<flags>` is nine `0`/`1` digits: signer, config present, config owner,
//! admin writable, config writable, system program, event authority, program,
//! admin system-owner. Answers are `error:<code>`, `error:<code>,<account>`,
//! `error:InvalidAccountData`, `error:BorshIoError`,
//! `transfer-fail:InvalidArgument,<lamports>`,
//! `transfer-fail:ExternalAccountLamportSpend,<lamports>`,
//! `event-then:MissingAccount,<lamports>,<event_hex>` or
//! `ok,<config_hex>,<event_hex>,<config_lamports>,<admin_lamports>`.
//! Error 1 is the system transfer's insufficient-lamports result and is
//! printed `error:1,<lamports>`.
use std::io::{self, BufRead, Write};

#[path = "update_creator_fee_config.rs"]
mod update_creator_fee_config;
use update_creator_fee_config::*;

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
            config_present: bit(1),
            config_owner_ok: bit(2),
            admin_writable: bit(3),
            config_writable: bit(4),
            system_ok: bit(5),
            event_authority_ok: bit(6),
            program_ok: bit(7),
            admin_system_owner: bit(8),
        };
        let answer = match update_creator_fee_config(
            &unhex(f[2]),
            &accounts,
            &unhex(f[3]),
            unhex(f[4]).try_into().unwrap(),
            f[5].parse().unwrap(),
            f[6].parse().unwrap(),
            f[7].parse().unwrap(),
            f[8].parse().unwrap(),
            f[9].parse().unwrap(),
        ) {
            Outcome::Error { code, site } if site.is_empty() => format!("error:{code}"),
            Outcome::Error { code, site } => format!("error:{code},{site}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::InsufficientLamports { transfer } => format!("error:{INSUFFICIENT_LAMPORTS},{transfer}"),
            Outcome::FromCarriesData { transfer } => format!("transfer-fail:InvalidArgument,{transfer}"),
            Outcome::ExternalAccountLamportSpend { transfer } => {
                format!("transfer-fail:ExternalAccountLamportSpend,{transfer}")
            }
            Outcome::MissingAccountAfterEvent { event, transfer } => {
                format!("event-then:MissingAccount,{transfer},{}", hex(&event))
            }
            Outcome::Ok { config, event, config_lamports, admin_lamports } => {
                format!("ok,{},{},{config_lamports},{admin_lamports}", hex(&config), hex(&event))
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
