//! stdin/stdout driver for `collect_coin_creator_fee.rs`, used by
//! `tests/test_pump_amm_collect_coin_creator_fee_captured.py`. One case per line:
//! `<payload_hex>,<count>,<token_program>,<mint_owner>,<mint_lamports>,<mint_hex>,
//! <creator_fees>,<creator_lamports>,<authority_ok>,<vault_writable>,<vault_owner>,
//! <vault_lamports>,<vault_ata_ok>,<vault_hex>,<dest_writable>,<dest_owner>,
//! <dest_lamports>,<dest_hex>,<event_ok>,<program_ok>,<creator_hex>,<authority_hex>,
//! <vault_key_hex>,<dest_key_hex>,<mint_key_hex>,<timestamp>`.
//!
//! `token_program` is `0` (neither), `1` (SPL Token) or `2` (Token-2022).
//! Each owner is `0` (other or absent), `1` (SPL Token) or `2` (Token-2022).
//! The `*_ok` and `*_writable` and `creator_fees` fields are `0` or `1`.
//! Answers are `error:<code>`, `error:InvalidAccountData`,
//! `error:UninitializedAccount`, `event-then:MissingAccount,<event_hex>`,
//! `idle` or `ok,<vault_amount>,<dest_amount>,<event_hex>`.
use std::io::{self, BufRead, Write};

#[path = "collect_coin_creator_fee.rs"]
mod collect_coin_creator_fee;
use collect_coin_creator_fee::*;

fn unhex(s: &str) -> Vec<u8> {
    (0..s.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&s[i..i + 2], 16).unwrap())
        .collect()
}

fn hex(b: &[u8]) -> String {
    b.iter().map(|x| format!("{x:02x}")).collect()
}

fn key(s: &str) -> [u8; 32] {
    unhex(s).try_into().unwrap()
}

fn owner(s: &str) -> Owner {
    match s {
        "1" => Owner::SplToken,
        "2" => Owner::Token2022,
        _ => Owner::Other,
    }
}

fn token_program(s: &str) -> TokenProgram {
    match s {
        "1" => TokenProgram::SplToken,
        "2" => TokenProgram::Token2022,
        _ => TokenProgram::Other,
    }
}

fn flag(s: &str) -> bool {
    s == "1"
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let accounts = Accounts {
            count: f[1].parse().unwrap(),
            token_program: token_program(f[2]),
            mint_owner: owner(f[3]),
            mint_lamports: f[4].parse().unwrap(),
            creator_owned_by_fees: flag(f[6]),
            creator_lamports: f[7].parse().unwrap(),
            authority_ok: flag(f[8]),
            vault_writable: flag(f[9]),
            vault_owner: owner(f[10]),
            vault_lamports: f[11].parse().unwrap(),
            vault_ata_ok: flag(f[12]),
            dest_writable: flag(f[14]),
            dest_owner: owner(f[15]),
            dest_lamports: f[16].parse().unwrap(),
            event_ok: flag(f[18]),
            program_ok: flag(f[19]),
        };
        let answer = match collect_coin_creator_fee(
            &unhex(f[0]),
            &accounts,
            &unhex(f[5]),
            &unhex(f[13]),
            &unhex(f[17]),
            key(f[20]),
            key(f[21]),
            key(f[22]),
            key(f[23]),
            key(f[24]),
            f[25].parse().unwrap(),
        ) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::UninitializedAccount => "error:UninitializedAccount".to_string(),
            Outcome::MissingAccount { event } => {
                format!("event-then:MissingAccount,{}", hex(&event))
            }
            Outcome::Idle => "idle".to_string(),
            Outcome::Collected {
                vault_amount,
                dest_amount,
                event,
            } => {
                format!("ok,{vault_amount},{dest_amount},{}", hex(&event))
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
