//! Host driver for `trade_alias.rs`, used by `tests/test_trade_alias_captured.py`.
//! One request per line:
//! `mode,op,vt,vs,rt,rs,supply,complete,tiers,buyback_bps,vault_lamports,
//!  user_lamports,user_tokens,curve_tokens,arg0,arg1,fee,buyback,buyer_is_curve_ata`
//! where `mode` is `trade|need`, `tiers` is `threshold:protocol:creator;...`,
//! and `fee` and `buyback` are the party names of `party` below.
#[allow(unused_attributes)]
#[path = "constant_product.rs"]
mod constant_product;
#[allow(dead_code)]
#[path = "legacy_buy.rs"]
mod legacy_buy;
#[allow(dead_code)]
#[path = "legacy_sell.rs"]
mod legacy_sell;
#[path = "trade_alias.rs"]
mod trade_alias;

use std::io::{self, BufRead, Write};
use trade_alias::{required_balance, trade, Op, Party, Stop, Trade};

const PLAIN: [&str; 10] = ["uata", "cata", "uva", "gva", "global", "mint", "config", "cv2", "sharing", "wsol"];

fn party(name: &str) -> Party {
    match name {
        "fee" => Party::Fee,
        "buyback" => Party::Buyback,
        "user" => Party::User,
        "curve" => Party::Curve,
        "vault" => Party::Vault,
        "token" => Party::TokenProgram,
        "pump" => Party::PumpProgram,
        "ea" => Party::EventAuthority,
        other => Party::Plain(PLAIN.iter().position(|p| *p == other).unwrap() as u8),
    }
}

fn party_name(p: Party) -> &'static str {
    match p {
        Party::Fee => "fee",
        Party::Buyback => "buyback",
        Party::User => "user",
        Party::Curve => "curve",
        Party::Vault => "vault",
        Party::TokenProgram => "token",
        Party::PumpProgram => "pump",
        Party::EventAuthority => "ea",
        Party::Plain(i) => PLAIN[i as usize],
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let tiers: Vec<(u128, u64, u64)> = f[8]
        .split(';')
        .filter(|s| !s.is_empty())
        .map(|s| {
            let t: Vec<&str> = s.split(':').collect();
            (t[0].parse().unwrap(), t[1].parse().unwrap(), t[2].parse().unwrap())
        })
        .collect();
    let t = Trade {
        op: match f[1] {
            "buy" => Op::Buy,
            "exact" => Op::BuyExact,
            "sell" => Op::Sell,
            "buy2" => Op::BuyV2,
            "exact2" => Op::BuyExactV2,
            "sell2" => Op::SellV2,
            other => panic!("unknown op {other}"),
        },
        reserves: [n(2), n(3), n(4), n(5)],
        supply: n(6),
        complete: n(7) != 0,
        tiers: &tiers,
        buyback_bps: n(9),
        vault_lamports: n(10),
        user_lamports: n(11),
        user_tokens: n(12),
        curve_tokens: n(13),
        args: (n(14), n(15)),
        fee: party(f[16]),
        buyback: party(f[17]),
        buyer_is_curve_ata: n(18) != 0,
    };
    if f[0] == "need" {
        return required_balance(&t).map_or("none".to_string(), |need| need.to_string());
    }
    match trade(&t) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Err(stop) => format!("error:{stop:?}"),
        Ok(s) => {
            let lamports: Vec<String> = s.lamports.iter().map(|(p, d)| format!("{}={d}", party_name(*p))).collect();
            format!(
                "ok,{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
                lamports.join(";"),
                s.user_tokens,
                s.curve_tokens,
                s.reserves[0],
                s.reserves[1],
                s.reserves[2],
                s.reserves[3],
                s.complete as u8,
                s.sol_amount,
                s.token_amount,
                s.protocol_fee,
                s.creator_fee,
                s.buyback_fee,
                t.buyback_bps
            )
        }
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        writeln!(out, "{}", answer(&line)).unwrap();
    }
}
