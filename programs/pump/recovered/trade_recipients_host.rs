//! Host driver for `trade_recipients.rs`, used by
//! `tests/test_trade_recipients_captured.py`. One request per line:
//! `route,mayhem,fee_key,buyback_key,fee_recipient,reserved,fee_list,reserved_list,buyback_list`
//! where `route` is `trade|v3|sweep`, keys are 64 hex digits, and lists are
//! `;`-separated keys. One answer per line: `ok,<fee paid>,<buyback paid>` or
//! `error:<code>`.
#[path = "trade_recipients.rs"]
mod trade_recipients;

use std::io::{self, BufRead, Write};
use trade_recipients::{Key, Recipients, Route};

fn key(text: &str) -> Key {
    let mut out = [0; 32];
    for (i, byte) in out.iter_mut().enumerate() {
        *byte = u8::from_str_radix(&text[2 * i..2 * i + 2], 16).unwrap();
    }
    out
}

fn list<const N: usize>(text: &str) -> [Key; N] {
    let keys: Vec<Key> = text.split(';').map(key).collect();
    keys.try_into().unwrap()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let recipients = Recipients {
        fee_recipient: key(f[4]),
        fee_recipients: list(f[6]),
        reserved_fee_recipient: key(f[5]),
        reserved_fee_recipients: list(f[7]),
        buyback_fee_recipients: list(f[8]),
    };
    let route = match f[0] {
        "trade" => Route::Trade,
        "v3" => Route::TradeV3,
        "sweep" => Route::Sweep,
        other => panic!("unknown route {other}"),
    };
    match trade_recipients::admit(&recipients, route, f[1] != "0", &key(f[2]), &key(f[3])) {
        Err(code) => format!("error:{code}"),
        Ok(paid) => format!("ok,{},{}", paid.fee_recipient as u8, paid.buyback as u8),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
