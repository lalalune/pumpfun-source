//! Host driver for `token_lengths.rs`, used by
//! `tests/test_token_lengths_captured.py`. One request per line:
//! `instruction,slot,kind,program,len,tagged,twin_ok,first_op`, where `kind` is
//! `token|mint`, `program` is `spl|t22`, `tagged` and `twin_ok` are `0|1` and
//! `first_op` is a number or `-`.
//! Answers: `same`, `pump:data`, `pump:<code>`, `ata:owner`, `token:data` or
//! `token:<code>`.
#[path = "token_lengths.rs"]
mod token_lengths;

use std::io::{self, BufRead, Write};
use token_lengths::{answer, read_of, Answer, Kind};

fn run(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let kind = if f[2] == "mint" { Kind::Mint } else { Kind::Token };
    // `-` is the only spelling for "this account has no first instruction".
    // A `.ok()` here read every malformed column as `-` as well, and the
    // answer for that case is `same`, so a broken row looked like a clean one.
    let first_op = match f[7] {
        "-" => None,
        other => Some(other.parse().unwrap()),
    };
    let result = answer(
        read_of(f[0], f[1]),
        f[3] == "t22",
        kind,
        f[4].parse().unwrap(),
        f[5] == "1",
        f[6] == "1",
        first_op,
    );
    match result {
        Answer::Same => "same".to_string(),
        Answer::PumpInvalidData => "pump:data".to_string(),
        Answer::PumpCode(code) => format!("pump:{code}"),
        Answer::AtaIllegalOwner => "ata:owner".to_string(),
        Answer::TokenInvalidData => "token:data".to_string(),
        Answer::TokenCode(code) => format!("token:{code}"),
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        writeln!(out, "{}", run(&line.unwrap())).unwrap();
    }
}
