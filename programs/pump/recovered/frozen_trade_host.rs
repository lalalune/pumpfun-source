//! Host driver for `frozen_trade.rs`, used by `tests/test_frozen_trade_captured.py`.
//! One request per line: `side,outcome` where `side` is `buy|sell|sell_v2` and `outcome`
//! is `done`, a custom code, or `panic:0|1` (1: the token transfer ran first).
#[path = "frozen_trade.rs"]
mod frozen_trade;

use frozen_trade::{Side, Unfrozen};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let (side, outcome) = line.split_once(',').unwrap();
    let side = match side {
        "sell" => Side::Sell,
        "sell_v2" => Side::SellV2,
        _ => Side::Buy,
    };
    let unfrozen = match outcome {
        "done" => Unfrozen::Done,
        "panic:0" => Unfrozen::Panic { transfer_ran: false },
        "panic:1" => Unfrozen::Panic { transfer_ran: true },
        code => Unfrozen::Code(code.parse().unwrap()),
    };
    match frozen_trade::frozen(side, unfrozen) {
        Unfrozen::Done => "done".to_string(),
        Unfrozen::Code(code) => code.to_string(),
        Unfrozen::Panic { .. } => "panic".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
