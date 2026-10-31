//! Host driver for `quote_recipients.rs`, used by
//! `tests/test_quote_recipients_captured.py`. One request per line:
//! `whitelisted,mayhem,buyback_bps,fee_account,buyback_account,fee_recipient,
//!  fee_recipients,reserved_fee_recipient,reserved_fee_recipients,
//!  buyback_fee_recipients,fee_key,buyback_key`, with keys in hex (lists run
//! together) and accounts `present|absent|wrong`. One answer per line:
//! `ok,<fee paid>,<buyback paid>,<fee account created>,<buyback account created>`
//! or `error:<code>`.
#[path = "quote_recipients.rs"]
mod quote_recipients;

use quote_recipients::{admit, Key, QuoteAccount, Recipients, Trade};
use std::io::{self, BufRead, Write};

fn keys<const N: usize>(hex: &str) -> [Key; N] {
    let mut out = [[0; 32]; N];
    for (i, key) in out.iter_mut().enumerate() {
        for (j, byte) in key.iter_mut().enumerate() {
            *byte = u8::from_str_radix(&hex[(i * 32 + j) * 2..(i * 32 + j) * 2 + 2], 16).unwrap();
        }
    }
    out
}

fn account(text: &str) -> QuoteAccount {
    match text {
        "present" => QuoteAccount::Present,
        "absent" => QuoteAccount::Absent,
        _ => QuoteAccount::WrongAddress,
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let r = Recipients {
        fee_recipient: keys::<1>(f[5])[0],
        fee_recipients: keys(f[6]),
        reserved_fee_recipient: keys::<1>(f[7])[0],
        reserved_fee_recipients: keys(f[8]),
        buyback_fee_recipients: keys(f[9]),
    };
    let t = Trade {
        whitelisted: f[0] == "1",
        mayhem: f[1] == "1",
        buyback_bps: f[2].parse().unwrap(),
        fee_account: account(f[3]),
        buyback_account: account(f[4]),
        fee_key: keys::<1>(f[10])[0],
        buyback_key: keys::<1>(f[11])[0],
    };
    match admit(&r, &t) {
        Ok(s) => format!(
            "ok,{},{},{},{}",
            s.fee_paid as u8, s.buyback_paid as u8, s.fee_account_created as u8, s.buyback_account_created as u8
        ),
        Err(code) => format!("error:{code}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
