//! Host driver for `v2_native_cashback.rs`, used by
//! `tests/test_v2_native_cashback_captured.py`. One request per line:
//! `op,cashback,hold,lamports,earned,writable,prior_user,unclaimed,claimed,volume,last,
//!  vault,vt,vs,rt,rs,complete,creator,creator_bps,supply,configurable,buyback,
//!  user_tokens,fee_ok,buyback_ok,amount,limit,trailing,tiers`
//! where `op` is `sell|buy|exact`, `cashback` is `0|1|2`, `hold` is
//! `missing|funded|valid|foreign|baddisc|wrong|sysdata`, `trailing` is hex or
//! `-`, and `tiers` is `threshold:protocol:creator` joined by `;`.
#[path = "buy_v2.rs"]
mod buy_v2;
#[allow(unused_attributes)]
#[allow(dead_code)]
#[path = "constant_product.rs"]
mod constant_product;
#[allow(dead_code)]
#[path = "legacy_buy.rs"]
mod legacy_buy;
#[allow(dead_code)]
#[path = "legacy_sell.rs"]
mod legacy_sell;
#[path = "sell_v2.rs"]
mod sell_v2;
#[path = "v2_native_cashback.rs"]
mod v2_native_cashback;

use std::io::{self, BufRead, Write};
use v2_native_cashback::{Admission, Hold, Op, Stop, Trade};

fn hex(text: &str) -> Vec<u8> {
    if text == "-" || text.is_empty() {
        return Vec::new();
    }
    (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
        .collect()
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let hold = match f[2] {
        "missing" => Hold::Missing,
        "funded" => Hold::Funded(n(3)),
        "valid" => Hold::Valid {
            lamports: n(3),
            earned: n(4),
        },
        "foreign" => Hold::Foreign,
        "baddisc" => Hold::BadDiscriminator,
        "wrong" => Hold::WrongSeeds,
        "sysdata" => Hold::SystemData,
        other => panic!("unknown hold {other}"),
    };
    let tiers: Vec<(u128, u64, u64)> = f[28]
        .split(';')
        .filter(|t| !t.is_empty())
        .map(|t| {
            let p: Vec<&str> = t.split(':').collect();
            (
                p[0].parse().unwrap(),
                p[1].parse().unwrap(),
                p[2].parse().unwrap(),
            )
        })
        .collect();
    let trailing = hex(f[27]);
    let trade = Trade {
        op: match f[0] {
            "sell" => Op::Sell,
            "buy" => Op::Buy,
            "exact" => Op::Exact,
            other => panic!("unknown op {other}"),
        },
        cashback: n(1) as u8,
        admission: Admission {
            hold,
            writable: n(5) != 0,
            prior_user_other: f[6] == "other",
        },
        unclaimed: n(7),
        claimed: n(8),
        volume: n(9),
        last: f[10].parse().unwrap(),
        vault_lamports: n(11),
        virtual_token: n(12),
        virtual_sol: n(13),
        real_token: n(14),
        real_sol: n(15),
        complete: n(16) != 0,
        has_creator: n(17) != 0,
        creator_bps: n(18),
        supply: n(19),
        configurable: n(20) != 0,
        buyback_bps: n(21),
        user_tokens: n(22),
        fee_recipient_ok: n(23) != 0,
        buyback_ok: n(24) != 0,
        amount: n(25),
        limit: n(26),
        trailing: &trailing,
        tiers: &tiers,
    };
    match v2_native_cashback::execute(&trade) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Err(Stop::Privilege) => "privilege".to_string(),
        Err(Stop::Borsh) => "borsh".to_string(),
        Ok(s) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
            s.sol,
            s.tokens,
            s.protocol_bps,
            s.protocol_fee,
            s.creator_bps,
            s.creator_fee,
            s.buyback_fee,
            s.vault_delta,
            s.uva_delta,
            s.earned,
            s.event_creator_bps,
            s.event_creator_fee,
            s.event_cashback_bps,
            s.event_cashback,
            s.event_unclaimed,
            s.event_claimed,
            s.event_volume,
            s.event_last,
            s.virtual_token,
            s.virtual_sol,
            s.real_token,
            s.real_sol,
            s.complete as u8,
            s.user_output,
            s.user_is_signer as u8,
            s.ix_name,
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
