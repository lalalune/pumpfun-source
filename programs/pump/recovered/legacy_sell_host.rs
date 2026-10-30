//! Host driver for `legacy_sell.rs`, used by `tests/test_legacy_sell_captured.py`.
//! One request per line:
//! `vt,vs,rt,rs,complete,has_creator,curve_creator_bps,supply,configurable,
//!  buyback_bps,vault_lamports,user_tokens,slot0,slot1,amount,min_sol_output,tiers`
//! where slots are `absent|curve_v2|buyback|zero|other` and `tiers` is
//! `threshold:protocol:creator` joined by `;` (empty for no tiers).
#[path = "legacy_sell.rs"]
mod legacy_sell;

use legacy_sell::{Config, Curve, Slot, Stop, Tier};
use std::io::{self, BufRead, Write};

fn slot(text: &str) -> Slot {
    match text {
        "absent" => Slot::Absent,
        "curve_v2" => Slot::CurveV2,
        "buyback" => Slot::Buyback,
        "zero" => Slot::Zero,
        "other" => Slot::Other,
        _ => panic!("unknown slot {text}"),
    }
}

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
        remaining: [slot(f[12]), slot(f[13])],
    };
    match legacy_sell::sell(&curve, &config, n(14), n(15)) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Ok(fill) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{},{}",
            fill.sol_output,
            fill.protocol_bps,
            fill.protocol_fee,
            fill.creator_bps,
            fill.creator_fee,
            fill.buyback_fee,
            fill.vault_top_up,
            fill.user_output,
            fill.curve.virtual_token_reserves,
            fill.curve.virtual_sol_reserves,
            fill.curve.real_token_reserves,
            fill.curve.real_sol_reserves,
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
