//! stdin/stdout driver for `idl_authority.rs`, used by
//! `tests/test_idl_authority_captured.py`. One case per line:
//! `<flags>,<owner>,<size>,<lamports>,<discriminator_ok>` where `<flags>` is
//! five `0`/`1` digits in `Case` field order (signed, authority_ok,
//! address_ok, program_signer_ok, authority_writable) and `<owner>` is `s`,
//! `p` or `o`. Answers are `rewritten`, `swept,<lamports>`, `error:<code>`,
//! `escalation`, `invalid-argument`, `invalid-realloc` or `insufficient-rent`.
use std::io::{self, BufRead, Write};

#[path = "idl_authority.rs"]
mod idl_authority;
use idl_authority::*;

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let bit = |i: usize| f[0].as_bytes()[i] == b'1';
        let case = Case {
            signed: bit(0),
            authority_ok: bit(1),
            address_ok: bit(2),
            program_signer_ok: bit(3),
            authority_writable: bit(4),
            owner: match f[1] {
                "s" => Owner::System,
                "p" => Owner::Pump,
                _ => Owner::Other,
            },
            size: f[2].parse().unwrap(),
            lamports: f[3].parse().unwrap(),
            discriminator_ok: f[4] == "1",
        };
        let answer = match admin_set_idl_authority(&case) {
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::Escalation => "escalation".to_string(),
            Outcome::InvalidArgument => "invalid-argument".to_string(),
            Outcome::InvalidRealloc => "invalid-realloc".to_string(),
            Outcome::InsufficientFundsForRent => "insufficient-rent".to_string(),
            Outcome::Swept(lamports) => format!("swept,{lamports}"),
            Outcome::Rewritten => "rewritten".to_string(),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
