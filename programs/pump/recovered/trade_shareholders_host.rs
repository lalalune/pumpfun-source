//! Host driver for `trade_shareholders.rs`, used by
//! `tests/test_trade_shareholders_captured.py`. One request per line:
//! `op family complete key_ok trade_fails data`, where `op` is
//! `sell|buy|exact`, `family` is `token|t22|native|wl|wl_native`, and `data` is
//! the account's bytes in hex (`-` when empty).
//! Answers `listed <hex>`, `oom`, `refused <code>` or `trade_failed`.
#[path = "trade_shareholders.rs"]
mod trade_shareholders;

use std::io::{self, BufRead, Write};
use trade_shareholders::{encode, trade, Family, Op, Outcome};

fn hex_bytes(text: &str) -> Vec<u8> {
    if text == "-" {
        return Vec::new();
    }
    (0..text.len() / 2).map(|i| u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap()).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(' ').collect();
    let op = match f[0] {
        "sell" => Op::Sell,
        "buy" => Op::Buy,
        _ => Op::ExactQuote,
    };
    let family = match f[1] {
        "token" => Family::Token,
        "t22" => Family::Token2022,
        "native" => Family::Native,
        "wl" => Family::Whitelisted,
        _ => Family::WhitelistedNative,
    };
    match trade(op, family, f[2] == "1", f[3] == "1", f[4] == "1", &hex_bytes(f[5])) {
        Outcome::Listed(rows) => {
            let bytes = encode(&rows);
            format!("listed {}", bytes.iter().map(|b| format!("{b:02x}")).collect::<String>())
        }
        Outcome::OutOfMemory => "oom".to_string(),
        Outcome::Refused(code) => format!("refused {code}"),
        Outcome::TradeFailed => "trade_failed".to_string(),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(&line.unwrap())).unwrap();
    }
}
