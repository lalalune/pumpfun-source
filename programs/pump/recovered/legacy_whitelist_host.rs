//! Host driver for `legacy_whitelist.rs`, used by
//! `tests/test_legacy_whitelist_captured.py`. One request per line as
//! space-separated `key=value` pairs; `tiers` is `threshold:protocol:creator`
//! entries joined by `;` (`-` for none) and `trailing` is hex (`-` for none).
#[path = "legacy_whitelist.rs"]
mod legacy_whitelist;
#[allow(dead_code)]
#[path = "mayhem_virtual_params.rs"]
mod mayhem_virtual_params;

use legacy_whitelist::*;
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

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

fn case(line: &str) -> Case {
    let map: HashMap<&str, &str> = line.split(' ').map(|kv| kv.split_once('=').unwrap()).collect();
    let n = |k: &str| map[k].parse::<u64>().unwrap();
    let b = |k: &str| n(k) != 0;
    Case {
        op: match map["op"] {
            "sell" => Op::Sell,
            "buy" => Op::Buy,
            _ => Op::BuyExactSolIn,
        },
        amount: n("amount"),
        limit: n("limit"),
        trailing: trailing(map["trailing"]),
        virtual_token_reserves: n("vtr"),
        virtual_quote_reserves: n("vqr"),
        real_token_reserves: n("rtr"),
        real_quote_reserves: n("rqr"),
        token_total_supply: n("supply"),
        complete: b("complete"),
        mayhem: b("mayhem"),
        has_creator: b("creator"),
        curve_creator_bps: n("creator_bps"),
        creator_fee_configurable: b("configurable"),
        mint_supply: n("mint_supply"),
        tiers: tiers(map["tiers"]),
        user_base: n("user_base"),
        curve_base: n("curve_base"),
        fee_recipient_ok: b("fee_recipient_ok"),
        slot1: match map["slot1"] {
            "buyback" => Slot::Buyback,
            "absent" | "short" => Slot::Absent,
            "zero" => Slot::Zero,
            _ => Slot::Other,
        },
    }
}

fn answer(line: &str) -> String {
    match run(&case(line)) {
        Err(Stop::Code(code)) => format!("error:{code}"),
        Err(Stop::Panic) => "panic".to_string(),
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
