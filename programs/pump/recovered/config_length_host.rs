//! Host driver for `config_length.rs`, used by
//! `tests/test_config_length_captured.py`. One request per line:
//! `typed,slot,len,disc,count,fields,admitted`, `scan,len,disc,count,first` or
//! `rewards,system_owned,len,amount`, where `slot` is
//! `control|migrate|distribute|quote` and `first` is a row or `-`. Any other
//! token is refused: `.ok()` would read a malformed column as "no row", and a
//! catchall would run a different request than the one asked for.
//! Answers: `pass`, `error:<code>`, `oom`, `found:<row>`, `missing`, `argument`
//! or `spend`.
#[path = "config_length.rs"]
mod config_length;

use config_length::{control_scan, rewards_payment, typed_load, Answer, Rewards, Scan, Slot, Stored};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let columns = match f[0] {
        "typed" => 7,
        "scan" => 5,
        "rewards" => 4,
        other => panic!("unknown request {other}"),
    };
    assert_eq!(f.len(), columns, "unexpected column count");
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let flag = |i: usize| match f[i] {
        "0" => false,
        "1" => true,
        other => panic!("flag must be 0 or 1, got {other}"),
    };
    match f[0] {
        "typed" => {
            let slot = match f[1] {
                "control" => Slot::Control,
                "migrate" => Slot::Migrate,
                "distribute" => Slot::Distribute,
                "quote" => Slot::QuoteDistribute,
                other => panic!("unknown slot {other}"),
            };
            let stored = Stored { len: n(2), disc_ok: flag(3), count: n(4), fields_ok: flag(5), admitted: flag(6) };
            match typed_load(slot, stored) {
                Answer::Pass => "pass".to_string(),
                Answer::Error(code) => format!("error:{code}"),
                Answer::OutOfMemory => "oom".to_string(),
            }
        }
        "scan" => {
            let stored = Stored { len: n(1), disc_ok: flag(2), count: n(3), fields_ok: true, admitted: true };
            let first = match f[4] {
                "-" => None,
                row => Some(row.parse::<u64>().expect("first must be a row or -")),
            };
            match control_scan(stored, first) {
                Scan::Found(row) => format!("found:{row}"),
                Scan::Missing => "missing".to_string(),
                Scan::Error(code) => format!("error:{code}"),
            }
        }
        "rewards" => match rewards_payment(flag(1), n(2), n(3)) {
            Rewards::Pass => "pass".to_string(),
            Rewards::InvalidArgument => "argument".to_string(),
            Rewards::ExternalAccountLamportSpend => "spend".to_string(),
        },
        other => panic!("unknown request {other}"),
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in stdin.lock().lines() {
        writeln!(out, "{}", answer(&line.unwrap())).unwrap();
    }
}
