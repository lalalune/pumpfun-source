//! Host driver for `trade_cpi_order.rs`, used by
//! `tests/test_trade_cpi_order_captured.py`. One request per line:
//! `family,buy,base,curve_quote,recipient,buyback,creator,cashback,vault_rent,
//!  curve_rent,volume_created,token_accounts,fee_cpi,completes`
//! where `family` is `legacy|v2|v2quote|v3|v3quote`. One answer per line: the
//! calls in order, joined by spaces.
#[path = "trade_cpi_order.rs"]
mod trade_cpi_order;

use std::io::{self, BufRead, Write};
use trade_cpi_order::{Family, Trade};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let t = Trade {
        family: match f[0] {
            "legacy" => Family::Legacy,
            "v2" => Family::V2Native,
            "v2quote" => Family::V2Quote,
            "v3" => Family::V3Native,
            "v3quote" => Family::V3Quote,
            other => panic!("unknown family {other}"),
        },
        buy: n(1) != 0,
        base: n(2),
        curve_quote: n(3),
        recipient: n(4),
        buyback: n(5),
        creator: n(6),
        cashback: n(7) != 0,
        vault_rent: n(8),
        curve_rent: n(9),
        volume_account_created: n(10) != 0,
        token_accounts_created: n(11),
        fee_cpi: n(12) != 0,
        completes: n(13) != 0,
    };
    trade_cpi_order::trace(&t).join(" ")
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
