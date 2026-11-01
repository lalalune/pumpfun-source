//! Host driver for `v2_token_quote.rs`, used by
//! `tests/test_v2_token_quote_captured.py`. One request per line as
//! space-separated `key=value` pairs; tier lists are `threshold:protocol:creator`
//! joined by `/` (`-` when empty) and a transfer fee is
//! `older_bps:older_max:newer_epoch:newer_bps:newer_max` (`-` when absent).
#[allow(dead_code)]
#[path = "mayhem_virtual_params.rs"]
mod mayhem_virtual_params;
#[path = "v2_token_quote.rs"]
mod v2_token_quote;

use std::collections::HashMap;
use std::io::{self, BufRead, Write};
use v2_token_quote::*;

fn tiers(text: &str) -> Vec<(u128, u64, u64)> {
    if text == "-" {
        return Vec::new();
    }
    text.split('/')
        .map(|t| {
            let p: Vec<&str> = t.split(':').collect();
            assert_eq!(p.len(), 3, "tier requires three fields");
            (p[0].parse().unwrap(), p[1].parse().unwrap(), p[2].parse().unwrap())
        })
        .collect()
}

fn numbers(text: &str) -> Vec<u64> {
    text.split(':').map(|v| v.parse().unwrap()).collect()
}

fn transfer_fee(text: &str) -> Option<TransferFee> {
    if text == "-" {
        return None;
    }
    let p = numbers(text);
    assert_eq!(p.len(), 5, "transfer fee requires five fields");
    Some(TransferFee {
        older: Fee { epoch: 0, basis_points: p[0], maximum_fee: p[1] },
        newer: Fee { epoch: p[2], basis_points: p[3], maximum_fee: p[4] },
    })
}

fn case(line: &str) -> Case {
    const FIELDS: &[&str] = &[
        "amount",
        "bad",
        "buyback_bps",
        "buyback_ok",
        "cashback",
        "complete",
        "configurable",
        "creator",
        "curve_base",
        "curve_creator_bps",
        "curve_lamports",
        "curve_quote",
        "epoch",
        "exotic",
        "fee_len",
        "fee_recipient_ok",
        "flat",
        "limit",
        "mayhem",
        "mint_supply",
        "op",
        "partial",
        "rqr",
        "rtr",
        "stable",
        "supply",
        "table",
        "tf",
        "tiers",
        "user_base",
        "user_quote",
        "vault_lamports",
        "vqr",
        "vtr",
        "whitelisted",
    ];
    let mut map = HashMap::new();
    for word in line.split(' ') {
        let (key, value) = word.split_once('=').expect("field must be key=value");
        assert!(FIELDS.contains(&key), "unknown field {key}");
        assert!(map.insert(key, value).is_none(), "duplicate field {key}");
    }
    assert_eq!(map.len(), FIELDS.len(), "missing request field");
    let n = |k: &str| map[k].parse::<u64>().unwrap();
    let b = |k: &str| match map[k] {
        "0" => false,
        "1" => true,
        other => panic!("flag {k} must be 0 or 1, got {other}"),
    };
    let flat = numbers(map["flat"]);
    let exotic = numbers(map["exotic"]);
    assert_eq!(flat.len(), 2, "flat requires two fields");
    assert_eq!(exotic.len(), 3, "exotic requires three fields");
    Case {
        op: match map["op"] {
            "sell" => Op::Sell,
            "buy" => Op::Buy,
            "exact" => Op::BuyExactQuoteIn,
            other => panic!("unknown operation {other}"),
        },
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
        curve_lamports: n("curve_lamports"),
        vault_lamports: n("vault_lamports"),
        table: match map["table"] {
            "tiers" => FeeTable::Tiers,
            "stable" => FeeTable::Stable,
            "flat" => FeeTable::Flat,
            other => panic!("unknown fee table {other}"),
        },
        transfer_fee: transfer_fee(map["tf"]),
        epoch: n("epoch"),
        mint_supply: n("mint_supply"),
        buyback_bps: n("buyback_bps"),
        creator_fee_configurable: b("configurable"),
        whitelisted_user: b("whitelisted"),
        fee_config: FeeConfig {
            flat: (flat[0], flat[1]),
            tiers: tiers(map["tiers"]),
            stable: tiers(map["stable"]),
            exotic: (exotic[0], exotic[1], exotic[2]),
            len: n("fee_len"),
        },
        user_base: n("user_base"),
        curve_base: n("curve_base"),
        user_quote: n("user_quote"),
        curve_quote: n("curve_quote"),
        fee_recipient_ok: b("fee_recipient_ok"),
        buyback_ok: b("buyback_ok"),
        bad: match map["bad"] {
            "curve_key" => BadSlot::CurveKey,
            "user_key" => BadSlot::UserKey,
            "vault_key" => BadSlot::VaultKey,
            "accumulator_key" => BadSlot::AccumulatorKey,
            "recipient_key" => BadSlot::RecipientKey,
            "buyback_key" => BadSlot::BuybackKey,
            "curve_missing" => BadSlot::CurveMissing,
            "user_mint" => BadSlot::UserMint,
            "none" => BadSlot::None,
            // A catchall read a misspelt slot name as "no bad slot", so a case
            // labelled as a wrong account ran the happy path on both sides.
            other => panic!("unknown bad slot {other}"),
        },
    }
}

fn answer(line: &str) -> String {
    match run(&case(line)) {
        Err(FEE_TIERS_EMPTY_PANIC) => "panic".to_string(),
        Err(FEE_CONFIG_INVALID_ACCOUNT_DATA) => "invalid-account-data".to_string(),
        Err(code) => format!("error:{code}"),
        Ok(s) => format!(
            "ok base_moved={} quote={} user_sent={} user_received={} curve_sent={} curve_received={} creator_sent={} creator_received={} recipient_sent={} recipient_received={} buyback_sent={} buyback_received={} vault_rent={} curve_rent={} vtr={} vqr={} rtr={} rqr={} protocol_fee_bps={} protocol_fee={} creator_fee_bps={} creator_fee={} buyback_fee_bps={} quote_transfer_fee={} completes={}",
            s.base_moved,
            s.quote,
            s.user.sent,
            s.user.received,
            s.curve.sent,
            s.curve.received,
            s.creator.sent,
            s.creator.received,
            s.recipient.sent,
            s.recipient.received,
            s.buyback.sent,
            s.buyback.received,
            s.vault_rent,
            s.curve_rent,
            s.virtual_token_reserves,
            s.virtual_quote_reserves,
            s.real_token_reserves,
            s.real_quote_reserves,
            s.protocol_fee_bps,
            s.protocol_fee,
            s.creator_fee_bps,
            s.creator_fee,
            s.buyback_fee_bps,
            s.quote_transfer_fee,
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
