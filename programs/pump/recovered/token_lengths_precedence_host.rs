//! Host driver for `token_lengths_precedence.rs`, used by
//! `tests/test_token_lengths_precedence_captured.py`. One request per line:
//! `instruction,slot,twin`, where `twin` is the outcome at the standard
//! length as the harness names it (`ok`, `panic`, `fees`, `rent`, or
//! `<program>:<error>`).
//! Answers: `stands`, `preempts` or `unconfirmed`.
#[path = "token_lengths_precedence.rs"]
mod token_lengths_precedence;

use std::io::{self, BufRead, Write};
use token_lengths_precedence::{precedence, Precedence};

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.splitn(3, ',').collect();
        let answer = match precedence(f[0], f[1], f[2]) {
            Precedence::Stands => "stands",
            Precedence::Preempts => "preempts",
            Precedence::Unconfirmed => "unconfirmed",
        };
        writeln!(out, "{answer}").unwrap();
    }
}
