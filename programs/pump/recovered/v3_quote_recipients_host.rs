//! stdin/stdout driver for `v3_quote_recipients.rs`, used by
//! `tests/test_v3_quote_recipients_captured.py`. One recipient per line:
//! `zero,listed,whitelisted` as 0/1. Answers are `error:<code>` or
//! `ok,<paid>` with `paid` as 0/1.
use std::io::{self, BufRead, Write};

#[path = "v3_quote_recipients.rs"]
mod v3_quote_recipients;
use v3_quote_recipients::*;

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<u8> = line.trim().split(',').map(|x| x.parse().unwrap()).collect();
        let r = Recipient { zero: f[0] == 1, listed: f[1] == 1, whitelisted: f[2] == 1 };
        let answer = match judge(&r) {
            Err(code) => format!("error:{code}"),
            Ok(s) => format!("ok,{}", s.paid as u8),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
