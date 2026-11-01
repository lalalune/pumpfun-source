//! stdin/stdout driver for `v3_trade_accounting.rs`, used by
//! `tests/test_v3_trade_accounting_captured.py`. One case per line of
//! `key=value` pairs separated by spaces (see `parse`); tier lists are
//! `threshold:protocol_bps:creator_bps` joined by `/`, transfer fees are
//! `older_bps:older_max:newer_epoch:newer_bps:newer_max` or `-`.
//! Answers are `unmodelled`, `error:<code>` or `ok` followed by the
//! `Settled` fields as `key=value`.
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

#[path = "v3_trade_accounting.rs"]
mod v3_trade_accounting;
use v3_trade_accounting::*;

fn tiers(s: &str) -> Vec<(u128, u64, u64)> {
    if s == "-" {
        return vec![];
    }
    s.split('/')
        .map(|t| {
            let v: Vec<&str> = t.split(':').collect();
            (v[0].parse().unwrap(), v[1].parse().unwrap(), v[2].parse().unwrap())
        })
        .collect()
}

fn parse(line: &str) -> Case {
    let m: HashMap<&str, &str> = line.split_whitespace().map(|kv| kv.split_once('=').unwrap()).collect();
    let n = |k: &str| m[k].parse::<u64>().unwrap();
    let b = |k: &str| m[k] == "1";
    let pair = |k: &str| {
        let v: Vec<u64> = m[k].split(':').map(|x| x.parse().unwrap()).collect();
        v
    };
    let flat = pair("flat");
    let exotic = pair("exotic");
    let transfer_fee = match m["tf"] {
        "-" => None,
        s => {
            let v: Vec<u64> = s.split(':').map(|x| x.parse().unwrap()).collect();
            Some(TransferFee {
                older: Fee { epoch: 0, basis_points: v[0], maximum_fee: v[1] },
                newer: Fee { epoch: v[2], basis_points: v[3], maximum_fee: v[4] },
            })
        }
    };
    Case {
        buy: b("buy"),
        amount: n("amount"),
        limit: n("limit"),
        partial_fill: b("partial"),
        virtual_token_reserves: n("vtr"),
        virtual_quote_reserves: n("vqr"),
        real_token_reserves: n("rtr"),
        real_quote_reserves: n("rqr"),
        token_total_supply: n("supply"),
        complete: b("complete"),
        cashback: b("cashback"),
        mayhem: b("mayhem"),
        has_creator: b("creator"),
        curve_creator_fee_bps: n("curve_creator_bps"),
        creator_fee: n("creator_fee"),
        protocol_fees: n("protocol_fees"),
        curve_lamports: n("curve_lamports"),
        native: b("native"),
        table: match m["table"] {
            "tiers" => FeeTable::Tiers,
            "stable" => FeeTable::Stable,
            "flat" => FeeTable::Flat,
            other => panic!("unknown table {other}"),
        },
        transfer_fee,
        epoch: n("epoch"),
        mint_supply: n("mint_supply"),
        buyback_bps: n("buyback_bps"),
        creator_fee_configurable: b("configurable"),
        whitelisted_user: b("whitelisted"),
        fee_config: FeeConfig {
            len: n("fee_len"),
            flat: (flat[0], flat[1]),
            tiers: tiers(m["tiers"]),
            stable: tiers(m["stable"]),
            exotic: (exotic[0], exotic[1], exotic[2]),
        },
        user_base: n("user_base"),
        curve_base: n("curve_base"),
        user_quote: n("user_quote"),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let answer = match run(&parse(line.trim())) {
            Outcome::Unmodelled => "unmodelled".to_string(),
            Outcome::Error(code) => format!("error:{code}"),
            Outcome::Ok(s) => format!(
                "ok user_quote={} curve_quote={} buyback_recipient={} rent_top_up={} base_moved={} vtr={} vqr={} rtr={} rqr={} creator_fee={} protocol_fees={} quote={} protocol_fee_bps={} protocol_fee={} creator_fee_bps={} trade_creator_fee={} buyback_fee_bps={} event_buyback_fee={} quote_transfer_fee={} completes={}",
                s.user_quote, s.curve_quote, s.buyback_recipient, s.rent_top_up, s.base_moved,
                s.virtual_token_reserves, s.virtual_quote_reserves, s.real_token_reserves, s.real_quote_reserves,
                s.creator_fee, s.protocol_fees, s.quote, s.protocol_fee_bps, s.protocol_fee,
                s.creator_fee_bps, s.trade_creator_fee, s.buyback_fee_bps, s.event_buyback_fee, s.quote_transfer_fee, s.completes as u8
            ),
        };
        writeln!(out, "{answer}").unwrap();
    }
}
