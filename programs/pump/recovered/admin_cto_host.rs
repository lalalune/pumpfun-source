//! stdin/stdout driver for `admin_cto.rs`, used by
//! `tests/test_admin_cto_captured.py`. One case per line:
//! `present,flags,payload,curve,global,admin,quote,current,mint,curve_key,sharing,holder,curve_lamports,admin_lamports,timestamp`
//!
//! `flags` is 45 `0`/`1` digits in `Accounts` field order after `present`.
//! Hex fields are raw bytes. Answers are `error:<code>`, `error:InvalidAccountData`,
//! `error:BorshIoError`, `error:MissingAccount`, or `ok,<curve_hex>,<event_hex>,<rent>`.
use std::io::{self, BufRead, Write};

#[path = "admin_cto.rs"]
mod admin_cto;
use admin_cto::*;

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|byte| format!("{byte:02x}")).collect()
}

fn key(text: &str) -> Key {
    unhex(text).try_into().unwrap()
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        if line.is_empty() {
            continue;
        }
        let f: Vec<&str> = line.split(',').collect();
        let bit = |i: usize| f[1].as_bytes()[i] == b'1';
        assert_eq!(f[1].len(), 45, "flag string width");
        let accounts = Accounts {
            present: f[0].parse().unwrap(),
            admin_signer: bit(0),
            admin_writable: bit(1),
            global_owner_ok: bit(2),
            global_seeds_ok: bit(3),
            quote_owner_token_family: bit(4),
            token_program_interface: bit(5),
            quote_owner_matches_token_program: bit(6),
            ata_program_ok: bit(7),
            system_program_ok: bit(8),
            curve_owner_ok: bit(9),
            curve_seeds_ok: bit(10),
            curve_writable: bit(11),
            creator_ata_ok: bit(12),
            creator_ata_writable: bit(13),
            vault_seeds_ok: bit(14),
            vault_writable: bit(15),
            vault_ata_ok: bit(16),
            vault_ata_writable: bit(17),
            holder_vault_writable: bit(18),
            holder_vault_is_dest: bit(19),
            holder_ata_ok: bit(20),
            holder_ata_writable: bit(21),
            amm_program_ok: bit(22),
            amm_config_seeds_ok: bit(23),
            pool_auth_seeds_ok: bit(24),
            pool_seeds_ok: bit(25),
            pool_writable: bit(26),
            amm_event_ok: bit(27),
            coin_auth_seeds_ok: bit(28),
            coin_auth_writable: bit(29),
            coin_ata_ok: bit(30),
            coin_ata_writable: bit(31),
            sharing_seeds_ok: bit(32),
            sharing_writable: bit(33),
            fees_program_ok: bit(34),
            fees_event_ok: bit(35),
            event_seeds_ok: bit(36),
            program_is_pump: bit(37),
            creator_executable: bit(38),
            creator_system_owner: bit(39),
            creator_writable: bit(40),
            sharing_owner_fees: bit(41),
            sharing_nonempty: bit(42),
            pool_owner_amm: bit(43),
            pool_nonempty: bit(44),
        };
        let input = Input {
            payload: &unhex(f[2]),
            curve: &unhex(f[3]),
            global: &unhex(f[4]),
            accounts: &accounts,
            admin: key(f[5]),
            quote: key(f[6]),
            current: key(f[7]),
            mint: key(f[8]),
            curve_key: key(f[9]),
            sharing: key(f[10]),
            holder: key(f[11]),
            curve_lamports: f[12].parse().unwrap(),
            admin_lamports: f[13].parse().unwrap(),
            timestamp: f[14].parse().unwrap(),
        };
        let answer = match admin_cto(&input) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::InvalidAccountData => "error:InvalidAccountData".to_string(),
            Outcome::BorshIoError => "error:BorshIoError".to_string(),
            Outcome::MissingAccount => "error:MissingAccount".to_string(),
            Outcome::Ok { curve, event, rent } => format!("ok,{},{},{rent}", hex(&curve), hex(&event)),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
