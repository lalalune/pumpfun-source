//! Host driver for `buy_v2.rs`, used by `tests/test_buy_v2_captured.py`.
//! One request per line:
//! `op,vt,vs,rt,rs,complete,has_creator,curve_creator_bps,supply,configurable,
//!  buyback_bps,vault_lamports,arg0,arg1,trailing_hex,tiers,fee_recipient_ok,
//!  buyback_ok`
//! where `op` is `buy` or `exact`, and `tiers` is `threshold:protocol:creator`
//! joined by `;` (empty for no tiers). The answer has the same shape as
//! `legacy_buy_host.rs`.
#[allow(unused_attributes)]
#[path = "constant_product.rs"]
mod constant_product;
#[allow(dead_code)]
#[path = "legacy_buy.rs"]
mod legacy_buy;
#[path = "buy_v2.rs"]
mod buy_v2;

use buy_v2::{Curve, Recipients};
use legacy_buy::{Config, Stop, Tier};
use std::io::{self, BufRead, Write};

fn hex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let curve = Curve {
        virtual_token_reserves: n(1),
        virtual_sol_reserves: n(2),
        real_token_reserves: n(3),
        real_sol_reserves: n(4),
        complete: n(5) != 0,
        has_creator: n(6) != 0,
        creator_fee_bps: n(7),
    };
    let tiers: Vec<Tier> = f[15]
        .split(';')
        .filter(|t| !t.is_empty())
        .map(|t| {
            let p: Vec<&str> = t.split(':').collect();
            Tier { threshold: p[0].parse().unwrap(), protocol_bps: p[1].parse().unwrap(), creator_bps: p[2].parse().unwrap() }
        })
        .collect();
    let config = Config {
        tiers: &tiers,
        mint_supply: n(8),
        creator_fee_configurable: n(9) != 0,
        buyback_bps: n(10),
        vault_lamports: n(11),
    };
    let recipients = Recipients { fee_recipient_ok: n(16) != 0, buyback_ok: n(17) != 0 };
    let trailing = hex(f[14]);
    let result = match f[0] {
        "buy" => buy_v2::buy_v2(&curve, &config, &recipients, n(12), n(13), &trailing),
        "exact" => buy_v2::buy_exact_quote_in_v2(&curve, &config, &recipients, n(12), n(13), &trailing),
        other => panic!("unknown op {other}"),
    };
    match result {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Ok(fill) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{},{},{}",
            fill.tokens,
            fill.sol_cost,
            fill.protocol_bps,
            fill.protocol_fee,
            fill.creator_bps,
            fill.creator_fee,
            fill.buyback_fee,
            fill.vault_credit,
            fill.curve.virtual_token_reserves,
            fill.curve.virtual_sol_reserves,
            fill.curve.real_token_reserves,
            fill.curve.real_sol_reserves,
            fill.curve.complete as u8,
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
