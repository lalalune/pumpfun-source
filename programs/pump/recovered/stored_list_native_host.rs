//! Host driver for `stored_list_native.rs`, used by
//! `tests/test_stored_list_native_captured.py`. One request per line:
//! `native,len,disc,count,fields`. Answers: `pass`, `error:<code>` or `oom`.
#[path = "stored_list_native.rs"]
mod stored_list_native;

use stored_list_native::{typed_load, Answer, Stored};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let stored = Stored { len: n(1), disc_ok: n(2) != 0, count: n(3), fields_ok: n(4) != 0 };
    match typed_load(stored) {
        Answer::Pass => "pass".to_string(),
        Answer::Error(code) => format!("error:{code}"),
        Answer::OutOfMemory => "oom".to_string(),
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
