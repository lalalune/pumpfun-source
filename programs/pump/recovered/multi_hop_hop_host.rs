//! Host driver for `multi_hop_hop.rs`, used by `tests/test_multi_hop_hop_captured.py`.
//! One request per line:
//! `buy,native,amount_in,hop_fees,remaining,vtr,vqr,rtr,rqr,complete,mayhem,
//!  cashback,has_creator,creator_fee,protocol_fees,fee_config_len,table_empty,
//!  protocol_bps,creator_bps,buyback_bps,user_base,curve_quote_tokens`
//! where `hop_fees` is `-` (empty) or flag digits joined by `:`.
#[path = "multi_hop_hop.rs"]
mod multi_hop_hop;

use multi_hop_hop::{Hop, Outcome};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let h = Hop {
        buy: n(0) != 0,
        native: n(1) != 0,
        amount_in: n(2),
        hop_fees: if f[3] == "-" { Vec::new() } else { f[3].split(':').map(|x| x.parse().unwrap()).collect() },
        remaining_accounts: n(4) as usize,
        virtual_token_reserves: n(5),
        virtual_quote_reserves: n(6),
        real_token_reserves: n(7),
        real_quote_reserves: n(8),
        complete: n(9) != 0,
        mayhem: n(10) != 0,
        cashback: n(11) != 0,
        has_creator: n(12) != 0,
        creator_fee: n(13),
        protocol_fees: n(14),
        fee_config_len: n(15) as usize,
        fee_table_empty: n(16) != 0,
        fee_bps: (n(17), n(18)),
        buyback_bps: n(19),
        user_base: n(20),
        curve_quote_tokens: n(21),
    };
    match multi_hop_hop::run(&h) {
        Outcome::Error(code) => format!("error:{code}"),
        Outcome::Unmodelled => "unmodelled".to_string(),
        Outcome::Ok(s) => format!(
            "ok,{},{},{},{},{},{},{},{},{}",
            s.virtual_token_reserves,
            s.virtual_quote_reserves,
            s.real_token_reserves,
            s.real_quote_reserves,
            s.creator_fee,
            s.protocol_fees,
            s.base,
            s.output,
            s.buyback
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
