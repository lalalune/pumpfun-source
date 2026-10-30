//! Host driver for `claim_cashback.rs`, used by `tests/test_claim_cashback_captured.py`.
//! One request per line:
//! `user,user_writable,uva_lamports,uva_owned_by_pump,uva_is_user_pda,uva_writable,uva_data,timestamp`
//! where `user` and `uva_data` are hex and the flags are `0|1`. Answers
//! `error:<code>` or `ok,<amount>,<uva hex>,<event hex or ->`.
#[path = "claim_cashback.rs"]
mod claim_cashback;

use claim_cashback::Claim;
use std::io::{self, BufRead, Write};

fn unhex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let flag = |i: usize| f[i] == "1";
    let data = unhex(f[6]);
    let c = Claim {
        user: unhex(f[0]).try_into().unwrap(),
        user_writable: flag(1),
        uva_lamports: f[2].parse().unwrap(),
        uva_owned_by_pump: flag(3),
        uva_is_user_pda: flag(4),
        uva_writable: flag(5),
        uva_data: &data,
    };
    match claim_cashback::claim(&c, f[7].parse().unwrap()) {
        Err(code) => format!("error:{code}"),
        Ok(r) => format!("ok,{},{},{}", r.amount, hex(&r.uva_data), r.event.map_or("-".to_string(), |e| hex(&e))),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
