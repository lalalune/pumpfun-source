//! Host driver for `trailing_accounts.rs`, used by
//! `tests/test_trailing_accounts_captured.py`. One request per line:
//! `name,remaining,extra,base,rows`.
#[path = "trailing_accounts.rs"]
mod trailing_accounts;

use std::io::{self, BufRead, Write};
use trailing_accounts::{Answer, Run};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<usize>().unwrap();
    let run = Run { name: f[0], remaining: n(1), extra: n(2), base: f[3], rows: n(4) };
    match trailing_accounts::trailing(&run) {
        Answer::Same => "same".to_string(),
        Answer::Bare => "bare".to_string(),
        Answer::Code(code) => code.to_string(),
        Answer::Runtime(name) => name.to_string(),
        Answer::Pass => "ok".to_string(),
        Answer::Open => "open".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
