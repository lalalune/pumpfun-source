//! Host driver for `accumulator_length.rs`, used by
//! `tests/test_accumulator_length_captured.py`. One request per line:
//! `user,read,len,lamports,twin` or `global,reads,len`, where `read` is
//! `ignored|load|init|claim|sell|extend`, `reads` is `0|1` and `twin` is the
//! standard-length error code or `-`.
//! Answers: `same`, `error:<code>` or `paid:<lamports>`.
#[path = "accumulator_length.rs"]
mod accumulator_length;

use accumulator_length::{global_accumulator, user_accumulator, Answer, UserRead};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let result = if f[0] == "global" {
        global_accumulator(n(1) != 0, n(2))
    } else {
        let read = match f[1] {
            "ignored" => UserRead::Ignored,
            "load" => UserRead::Load,
            "init" => UserRead::InitIfNeeded,
            "claim" => UserRead::NativeClaim,
            "sell" => UserRead::CashbackSell,
            _ => UserRead::Extend,
        };
        user_accumulator(read, n(2), n(3), f[4].parse::<u32>().ok())
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
