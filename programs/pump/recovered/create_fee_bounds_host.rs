//! stdin/stdout driver for `create_fee_bounds.rs`, used by
//! `tests/test_create_fee_bounds_captured.py`. One case per line:
//! `<source>,<requested>,<configurable>,<max_bps>` where `<source>` is `sol`,
//! `whitelisted`, `controlled` or `nested` and `<configurable>` is 0 or 1.
//! Answers are `ok,<stored_bps>` or `error,<code>`.
use std::io::{self, BufRead, Write};

#[path = "create_fee_bounds.rs"]
mod create_fee_bounds;
use create_fee_bounds::*;

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let source = match f[0] {
            "sol" => QuoteSource::Sol,
            "whitelisted" => QuoteSource::Whitelisted,
            "controlled" => QuoteSource::Controlled,
            "nested" => QuoteSource::Nested,
            other => panic!("unknown source {other}"),
        };
        let gate = FeeGate { configurable: f[2] == "1", max_bps: f[3].parse().unwrap() };
        match stored_creator_fee(source, f[1].parse().unwrap(), gate) {
            Ok(bps) => writeln!(out, "ok,{bps}").unwrap(),
            Err(code) => writeln!(out, "error,{code}").unwrap(),
        }
    }
}
