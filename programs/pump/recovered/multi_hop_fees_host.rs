//! stdin/stdout driver for `multi_hop_fees.rs`, used by
//! `tests/test_multi_hop_fees_captured.py`. One route per line: the fee fields
//! joined by `;` (tiers `threshold:protocol:creator` joined by `/` or `-` when
//! empty), then `$`, the route fields joined by `,` (`hop_fees` and `hops` joined
//! by `:` or `-` when empty), then `|` and the fields of each curve joined by
//! `,`. Answers are `error:<code>` or `ok`, the settled numbers, and one `|`
//! block per curve.
use std::io::{self, BufRead, Write};

#[path = "multi_hop_fees.rs"]
mod multi_hop_fees;
use multi_hop_fees::*;

fn list(s: &str) -> Vec<u64> {
    if s == "-" {
        return vec![];
    }
    s.split(':').map(|x| x.parse().unwrap()).collect()
}

fn tiers(s: &str) -> Vec<Tier> {
    if s == "-" {
        return vec![];
    }
    s.split('/')
        .map(|t| {
            let v: Vec<u128> = t.split(':').map(|x| x.parse().unwrap()).collect();
            (v[0], v[1] as u64, v[2] as u64)
        })
        .collect()
}

fn parse(line: &str) -> Route {
    let (fees, line) = line.split_once('$').unwrap();
    let g: Vec<&str> = fees.split(';').collect();
    let bps = list(g[3]);
    let exotic = list(g[4]);
    let creator_bps = list(g[7]);
    let mut blocks = line.split('|');
    let f: Vec<&str> = blocks.next().unwrap().split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let curves = blocks
        .enumerate()
        .map(|(i, b)| {
            let v: Vec<u64> = b.split(',').map(|x| x.parse().unwrap()).collect();
            Curve {
                virtual_token_reserves: v[0],
                virtual_quote_reserves: v[1],
                real_token_reserves: v[2],
                real_quote_reserves: v[3],
                creator_fee: v[4],
                protocol_fees: v[5],
                has_creator: v[6] == 1,
                cashback: v[7] == 1,
                complete: v[8] == 1,
                mayhem: v[9] == 1,
                creator_fee_bps: creator_bps[i],
                base_mint: v[10] as u8,
                quote_mint: v[11] as u8,
                base_vault: v[12],
                quote_vault: v[13],
                ..Curve::default()
            }
        })
        .collect();
    Route {
        amount_in: n(0),
        hop_fees: list(f[1]).iter().map(|&x| x as u8).collect(),
        remaining_accounts: n(2) as usize,
        source_mint: n(3) as u8,
        destination_mint: n(4) as u8,
        source_balance: n(5),
        recipient_mint: n(6) as u8,
        pool_migration_fee: n(7),
        buyback_bps: n(8),
        fee_config: FeeConfig { len: g[0].parse().unwrap(), tiers: tiers(g[1]), stable: tiers(g[2]), flat: (bps[0], bps[1]), exotic: (exotic[0], exotic[1], exotic[2]) },
        creator_fee_configurable: g[5] == "1",
        mint_supply: g[6].parse().unwrap(),
        hops: list(f[13]).iter().map(|&x| x as usize).collect(),
        curves,
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let answer = match run(&parse(line.trim())) {
            Err(code) => format!("error:{code}"),
            Ok(s) => {
                let mut text = format!("ok,{},{},{},{},{},{}", s.amount_out, s.buyback_fee, s.source, s.destination, s.user_lamports, s.recipient);
                for c in &s.curves {
                    text += &format!(
                        "|{},{},{},{},{},{},{},{},{},{},{},{}",
                        c.virtual_token_reserves, c.virtual_quote_reserves, c.real_token_reserves, c.real_quote_reserves,
                        c.creator_fee, c.protocol_fees, c.post_complete_base_out, c.post_complete_quote_in,
                        c.complete as u8, c.base_vault, c.quote_vault, c.lamports
                    );
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
