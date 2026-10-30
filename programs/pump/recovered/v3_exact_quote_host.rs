//! stdin/stdout driver for `v3_exact_quote.rs`, used by
//! `tests/test_v3_exact_quote_captured.py`. One case per line of `key=value`
//! pairs separated by spaces, starting with `mode=exact` or `mode=buy` (then
//! `spendable` is `amount` and `min_tokens` is `max_sol_cost`); tier lists are
//! `threshold:protocol_bps:creator_bps` joined by `/`, transfer fees are
//! `older_bps:older_max:newer_epoch:newer_bps:newer_max` or `-`.
//! Answers are `unmodelled`, `error:<code>` or `ok` followed by the `Settled`
//! fields as `key=value`, plus the `post_*` fields for a crossing fill.
use std::collections::HashMap;
use std::io::{self, BufRead, Write};

#[allow(dead_code)]
#[path = "v3_trade_accounting.rs"]
mod v3_trade_accounting;
#[path = "v3_exact_quote.rs"]
mod v3_exact_quote;
use v3_exact_quote::{run, run_buy, ExactQuote};
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

fn parse(line: &str) -> ExactQuote {
    let m: HashMap<&str, &str> = line.split_whitespace().map(|kv| kv.split_once('=').unwrap()).collect();
    let n = |k: &str| m[k].parse::<u64>().unwrap();
    let b = |k: &str| m[k] == "1";
    let list = |k: &str| m[k].split(':').map(|x| x.parse().unwrap()).collect::<Vec<u64>>();
    let flat = list("flat");
    let exotic = list("exotic");
    let transfer_fee = match m["tf"] {
        "-" => None,
        _ => {
            let v = list("tf");
            Some(TransferFee {
                older: Fee { epoch: 0, basis_points: v[0], maximum_fee: v[1] },
                newer: Fee { epoch: v[2], basis_points: v[3], maximum_fee: v[4] },
            })
        }
    };
    ExactQuote {
        case: Case {
            buy: true,
            amount: n("spendable"),
            limit: n("min_tokens"),
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
                _ => FeeTable::Flat,
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
            user_base: 0,
            curve_base: n("curve_base"),
            user_quote: n("user_quote"),
        },
        pool_migration_fee: n("pool_fee"),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let line = line.trim();
        let case = parse(line);
        let answer = match if line.starts_with("mode=buy ") { run_buy(&case) } else { run(&case) } {
            Err(None) => "unmodelled".to_string(),
            Err(Some(code)) => format!("error:{code}"),
            Ok(filled) => {
                let s = filled.settled;
                let mut text = format!(
                    "ok user_quote={} curve_quote={} buyback_recipient={} rent_top_up={} base_moved={} vtr={} vqr={} rtr={} rqr={} creator_fee={} protocol_fees={} quote={} protocol_fee_bps={} protocol_fee={} creator_fee_bps={} trade_creator_fee={} buyback_fee_bps={} event_buyback_fee={} quote_transfer_fee={} completes={}",
                    s.user_quote, s.curve_quote, s.buyback_recipient, s.rent_top_up, s.base_moved,
                    s.virtual_token_reserves, s.virtual_quote_reserves, s.real_token_reserves, s.real_quote_reserves,
                    s.creator_fee, s.protocol_fees, s.quote, s.protocol_fee_bps, s.protocol_fee,
                    s.creator_fee_bps, s.trade_creator_fee, s.buyback_fee_bps, s.event_buyback_fee, s.quote_transfer_fee, s.completes as u8
                );
                if let Some(p) = filled.post {
                    text += &format!(
                        " post_base_out={} post_quote_in={} post_protocol_fee={} post_creator_fee={} post_pool_base={} post_pool_quote={} post_buyback_fee={}",
                        p.base_out, p.quote_in, p.protocol_fee, p.creator_fee, p.pool_base_before, p.pool_quote_before, p.buyback_fee
                    );
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
