//! Host driver for `v2_whitelist_native.rs`, used by
//! `tests/test_v2_whitelist_native_captured.py`. One request per line as
//! space-separated `key=value` pairs.
#[allow(dead_code)]
#[path = "mayhem_virtual_params.rs"]
mod mayhem_virtual_params;
#[path = "v2_whitelist_native.rs"]
mod v2_whitelist_native;

use std::collections::HashMap;
use std::io::{self, BufRead, Write};
use v2_whitelist_native::*;

fn case(line: &str) -> Case {
    let map: HashMap<&str, &str> = line.split(' ').map(|kv| kv.split_once('=').unwrap()).collect();
    let n = |k: &str| map[k].parse::<u64>().unwrap();
    let b = |k: &str| n(k) != 0;
    Case {
        op: match map["op"] {
            "sell" => Op::Sell,
            "buy" => Op::Buy,
            _ => Op::BuyExactQuoteIn,
        },
        amount: n("amount"),
        limit: n("limit"),
        partial_fill: b("partial"),
        virtual_token_reserves: n("vtr"),
        virtual_quote_reserves: n("vqr"),
        real_token_reserves: n("rtr"),
        real_quote_reserves: n("rqr"),
        token_total_supply: n("supply"),
        complete: b("complete"),
        mayhem: b("mayhem"),
        user_base: n("user_base"),
        curve_base: n("curve_base"),
        fee_recipient_ok: b("fee_recipient_ok"),
        buyback_ok: b("buyback_ok"),
    }
}

fn answer(line: &str) -> String {
    match run(&case(line)) {
        Err(code) => format!("error:{code}"),
        Ok(s) => format!(
            "ok base_moved={} quote={} vtr={} vqr={} rtr={} rqr={} completes={}",
            s.base_moved,
            s.quote,
            s.virtual_token_reserves,
            s.virtual_quote_reserves,
            s.real_token_reserves,
            s.real_quote_reserves,
            s.completes as u8
        ),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
