//! Host driver for `sell_v2.rs`, used by `tests/test_sell_v2_captured.py`.
//! One request per line:
//! `vt,vs,rt,rs,complete,has_creator,creator_bps,mint_supply,configurable,
//!  buyback_bps,vault_lamports,user_tokens,fee_recipient_ok,buyback_ok,
//!  amount,min_sol_output,tiers`
//! where `tiers` is `threshold:protocol_bps:creator_bps` joined by `;`.
// sell_v2 never builds the legacy remaining-account slots it does not need.
#[allow(dead_code)]
#[path = "legacy_sell.rs"]
mod legacy_sell;
#[path = "sell_v2.rs"]
mod sell_v2;

use legacy_sell::{Config, Curve, Slot, Stop, Tier};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let curve = Curve {
        virtual_token_reserves: n(0),
        virtual_sol_reserves: n(1),
        real_token_reserves: n(2),
        real_sol_reserves: n(3),
        complete: n(4) != 0,
        has_creator: n(5) != 0,
        creator_fee_bps: n(6),
    };
    let tiers: Vec<Tier> = f[16]
        .split(';')
        .filter(|t| !t.is_empty())
        .map(|t| {
            let p: Vec<&str> = t.split(':').collect();
            Tier { threshold: p[0].parse().unwrap(), protocol_bps: p[1].parse().unwrap(), creator_bps: p[2].parse().unwrap() }
        })
        .collect();
    let config = Config {
        tiers: &tiers,
        mint_supply: n(7),
        creator_fee_configurable: n(8) != 0,
        buyback_bps: n(9),
        vault_lamports: n(10),
        user_tokens: n(11),
        remaining: [Slot::Absent, Slot::Absent],
    };
    let recipients = sell_v2::Recipients { fee_recipient_ok: n(12) != 0, buyback_ok: n(13) != 0 };
    match sell_v2::sell_v2(&curve, &config, &recipients, n(14), n(15)) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Ok((r, rent)) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{},{},{}",
            r.sol_output,
            r.protocol_bps,
            r.protocol_fee,
            r.creator_bps,
            r.creator_fee,
            r.buyback_fee,
            r.vault_top_up,
            r.user_output,
            rent,
            r.curve.virtual_token_reserves,
            r.curve.virtual_sol_reserves,
            r.curve.real_token_reserves,
            r.curve.real_sol_reserves
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
