//! Host driver for `config_length.rs`, used by
//! `tests/test_config_length_captured.py`. One request per line:
//! `typed,slot,len,disc,count,fields,admitted`, `scan,len,disc,count,first` or
//! `rewards,system_owned,len,amount`, where `slot` is
//! `control|migrate|distribute|quote` and `first` is a row or `-`.
//! Answers: `pass`, `error:<code>`, `oom`, `found:<row>`, `missing`, `argument`
//! or `spend`.
#[path = "config_length.rs"]
mod config_length;

use config_length::{control_scan, rewards_payment, typed_load, Answer, Rewards, Scan, Slot, Stored};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    match f[0] {
        "typed" => {
            let slot = match f[1] {
                "control" => Slot::Control,
                "migrate" => Slot::Migrate,
                "distribute" => Slot::Distribute,
                _ => Slot::QuoteDistribute,
            };
            let stored = Stored { len: n(2), disc_ok: n(3) != 0, count: n(4), fields_ok: n(5) != 0, admitted: n(6) != 0 };
            match typed_load(slot, stored) {
                Answer::Pass => "pass".to_string(),
                Answer::Error(code) => format!("error:{code}"),
                Answer::OutOfMemory => "oom".to_string(),
            }
        }
        "scan" => {
            let stored = Stored { len: n(1), disc_ok: n(2) != 0, count: n(3), fields_ok: true, admitted: true };
            match control_scan(stored, f[4].parse::<u64>().ok()) {
                Scan::Found(row) => format!("found:{row}"),
                Scan::Missing => "missing".to_string(),
                Scan::Error(code) => format!("error:{code}"),
            }
        }
        _ => match rewards_payment(n(1) != 0, n(2), n(3)) {
            Rewards::Pass => "pass".to_string(),
            Rewards::InvalidArgument => "argument".to_string(),
            Rewards::ExternalAccountLamportSpend => "spend".to_string(),
        },
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
