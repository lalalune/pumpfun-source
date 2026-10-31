//! Host driver for `token2022_base.rs`, used by
//! `tests/test_token2022_base_captured.py`. One request per line as
//! space-separated `key=value` pairs; `tiers` is `threshold:protocol:creator`
//! entries joined by `;` (`-` for none) and `trailing` is hex (`-` for none).
#[allow(unused_attributes)]
#[path = "constant_product.rs"]
mod constant_product;
#[allow(dead_code)]
#[path = "legacy_buy.rs"]
mod legacy_buy;
#[allow(dead_code)]
#[path = "buy_v2.rs"]
mod buy_v2;
#[allow(dead_code)]
#[path = "sell_v2.rs"]
mod sell_v2;
#[path = "token2022_base.rs"]
mod token2022_base;
#[allow(dead_code)]
#[path = "legacy_sell.rs"]
mod legacy_sell;

use legacy_buy::Tier;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};
use token2022_base::*;

fn tiers(text: &str) -> Vec<Tier> {
    if text == "-" {
        return Vec::new();
    }
    text.split(';')
        .map(|entry| {
            let parts: Vec<&str> = entry.split(':').collect();
            Tier {
                threshold: parts[0].parse().unwrap(),
                protocol_bps: parts[1].parse().unwrap(),
                creator_bps: parts[2].parse().unwrap(),
            }
        })
        .collect()
}

fn trailing(text: &str) -> Vec<u8> {
    if text == "-" {
        return Vec::new();
    }
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn program(text: &str) -> Program {
    if text == "t22" {
        Program::Token2022
    } else {
        Program::Spl
    }
}

fn case(line: &str) -> Case {
    let map: HashMap<&str, &str> = line.split(' ').map(|kv| kv.split_once('=').unwrap()).collect();
    let n = |k: &str| map[k].parse::<u64>().unwrap();
    let b = |k: &str| n(k) != 0;
    Case {
        family: if map["family"] == "legacy" { Family::Legacy } else { Family::V2 },
        op: match map["op"] {
            "sell" => Op::Sell,
            "buy" => Op::Buy,
            _ => Op::BuyExact,
        },
        amount: n("amount"),
        limit: n("limit"),
        trailing: trailing(map["trailing"]),
        virtual_token_reserves: n("vtr"),
        virtual_sol_reserves: n("vqr"),
        real_token_reserves: n("rtr"),
        real_sol_reserves: n("rqr"),
        complete: b("complete"),
        has_creator: b("creator"),
        curve_creator_bps: n("creator_bps"),
        creator_fee_configurable: b("configurable"),
        mint_supply: n("mint_supply"),
        buyback_bps: n("buyback_bps"),
        vault_lamports: n("vault"),
        user_tokens: n("user_base"),
        tiers: tiers(map["tiers"]),
        recipient_ok: map["recipient"] == "regular",
        buyback_ok: b("buyback_ok"),
        owner: program(map["mint_owner"]),
        program: program(map["program"]),
        ata: program(map["ata"]),
        extension: match map["ext"] {
            "fee" => Extension::TransferFee { bps: n("fee_bps") as u16, maximum: n("fee_max") },
            "hook" => Extension::TransferHook,
            "nontransfer" => Extension::NonTransferable,
            "pause1" => Extension::Paused,
            _ => Extension::Inert,
        },
    }
}

fn answer(line: &str) -> String {
    match run(&case(line)) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
        Err(Stop::MissingAccount) => "missing".to_string(),
        Ok(s) => format!(
            "ok tokens={} sol_amount={} protocol_bps={} protocol_fee={} creator_bps={} creator_fee={} buyback_fee={} vault_credit={} user_delta={} vtr={} vqr={} rtr={} rqr={} completes={} buyback_bps={} withheld={}",
            s.tokens,
            s.sol_amount,
            s.protocol_bps,
            s.protocol_fee,
            s.creator_bps,
            s.creator_fee,
            s.buyback_fee,
            s.vault_credit,
            s.user_delta,
            s.virtual_token_reserves,
            s.virtual_sol_reserves,
            s.real_token_reserves,
            s.real_sol_reserves,
            s.completes as u8,
            s.buyback_bps,
            s.withheld,
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
