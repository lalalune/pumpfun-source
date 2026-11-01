//! stdin/stdout driver for `instruction_data.rs`, used by
//! `tests/test_instruction_data_captured.py`. One case per line:
//! `<data hex>,<repeated slots>[,<signer><is event authority>]...` with the two
//! flags as `0`/`1`. Answers are `passed`, `error:<code>`, `out-of-memory` or
//! `not-enough-keys`.
use std::io::{self, BufRead, Write};

#[path = "instruction_data.rs"]
mod instruction_data;
use instruction_data::*;

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        if f[0].len() % 2 != 0 {
            panic!("odd-length hex {}", f[0]);
        }
        let data: Vec<u8> =
            (0..f[0].len() / 2).map(|i| u8::from_str_radix(&f[0][2 * i..2 * i + 2], 16).unwrap()).collect();
        let accounts: Vec<(bool, bool)> =
            f[2..].iter().map(|s| (s.as_bytes()[0] == b'1', s.as_bytes()[1] == b'1')).collect();
        let answer = match read(&data, &accounts, f[1].parse().unwrap()) {
            Outcome::Passed => "passed".to_string(),
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::OutOfMemory => "out-of-memory".to_string(),
            Outcome::NotEnoughAccountKeys => "not-enough-keys".to_string(),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
