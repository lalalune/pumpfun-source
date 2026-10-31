//! Host driver for `frozen_v3_exact_quote.rs`, used by
//! `tests/test_frozen_v3_exact_quote_captured.py`.
//! One request per line:
//! `account,outcome,invoked_legs,base_gross,quote_gross,buyback_gross,token_2022`
//! where `account` is `user_base|curve_base|user_quote|curve_quote|
//! recipient`, `outcome` is `done` or a custom code, and the remaining
//! fields are the unfrozen twin's execution record (`0`/`1` for the flag).
#[path = "frozen_v3_exact_quote.rs"]
mod frozen_v3_exact_quote;

use frozen_v3_exact_quote::{Account, Execution, Unfrozen};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let fields: Vec<&str> = line.split(',').collect();
    let account = match fields[0] {
        "curve_base" => Account::CurveBase,
        "user_quote" => Account::UserQuote,
        "curve_quote" => Account::CurveQuote,
        "recipient" => Account::Recipient,
        _ => Account::UserBase,
    };
    let unfrozen = match fields[1] {
        "done" => Unfrozen::Done,
        code => Unfrozen::Code(code.parse().unwrap()),
    };
    let exec = Execution {
        invoked_legs: fields[2].parse().unwrap(),
        base_gross: fields[3].parse().unwrap(),
        quote_gross: fields[4].parse().unwrap(),
        buyback_gross: fields[5].parse().unwrap(),
        token_2022: fields[6] == "1",
    };
    match frozen_v3_exact_quote::frozen(account, unfrozen, exec) {
        Unfrozen::Done => "done".to_string(),
        Unfrozen::Code(code) => code.to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
