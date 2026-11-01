//! Host driver for `accumulator_length.rs`, used by
//! `tests/test_accumulator_length_captured.py`. One request per line:
//! `user,read,len,lamports,twin` or `global,reads,len`, where `read` is
//! `ignored|load|init|claim|sell|extend`, `reads` is `0|1` and `twin` is the
//! standard-length error code or `-`. Any other token is refused: `.ok()`
//! would read a malformed column as "the twin succeeded".
//! Answers: `same`, `error:<code>` or `paid:<lamports>`.
#[path = "accumulator_length.rs"]
mod accumulator_length;

use accumulator_length::{global_accumulator, user_accumulator, Answer, UserRead};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let columns = match f[0] {
        "user" => 5,
        "global" => 3,
        other => panic!("unknown target {other}"),
    };
    assert_eq!(f.len(), columns, "unexpected column count");
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let result = if f[0] == "global" {
        let reads = match f[1] {
            "0" => false,
            "1" => true,
            other => panic!("reads must be 0 or 1, got {other}"),
        };
        global_accumulator(reads, n(2))
    } else {
        let read = match f[1] {
            "ignored" => UserRead::Ignored,
            "load" => UserRead::Load,
            "init" => UserRead::InitIfNeeded,
            "claim" => UserRead::NativeClaim,
            "sell" => UserRead::CashbackSell,
            "extend" => UserRead::Extend,
            other => panic!("unknown read {other}"),
        };
        let twin = match f[4] {
            "-" => None,
            code => Some(code.parse::<u32>().expect("twin must be an error code or -")),
        };
        user_accumulator(read, n(2), n(3), twin)
    };
    match result {
        Answer::Same => "same".to_string(),
        Answer::Error(code) => format!("error:{code}"),
        Answer::Paid(lamports) => format!("paid:{lamports}"),
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
