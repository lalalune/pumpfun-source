//! Host driver for `frozen_v3_trade.rs`, used by
//! `tests/test_frozen_v3_trade_captured.py`.
//! One request per line:
//! `side,account,outcome,invokes,quote_moves,buyback_moves,token_2022` where
//! `side` is `buy|sell`, `account` is `user_base|curve_base|user_quote|
//! curve_quote|recipient`, `outcome` is `done` or a custom code, and the
//! remaining fields are the unfrozen twin's facts (`0`/`1` for the flags).
#[path = "frozen_v3_trade.rs"]
mod frozen_v3_trade;

use frozen_v3_trade::{Account, Side, Twin, Unfrozen};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let fields: Vec<&str> = line.split(',').collect();
    let side = match fields[0] {
        "sell" => Side::Sell,
        _ => Side::Buy,
    };
    let account = match fields[1] {
        "curve_base" => Account::CurveBase,
        "user_quote" => Account::UserQuote,
        "curve_quote" => Account::CurveQuote,
        "recipient" => Account::Recipient,
        _ => Account::UserBase,
    };
    let unfrozen = match fields[2] {
        "done" => Unfrozen::Done,
        code => Unfrozen::Code(code.parse().unwrap()),
    };
    let twin = Twin {
        invokes: fields[3].parse().unwrap(),
        quote_moves: fields[4] == "1",
        buyback_moves: fields[5] == "1",
        token_2022: fields[6] == "1",
    };
    match frozen_v3_trade::frozen(side, account, unfrozen, twin) {
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
