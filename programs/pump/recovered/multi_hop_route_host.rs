//! stdin/stdout driver for `multi_hop_route.rs`, used by
//! `tests/test_multi_hop_route_captured.py`. One route per line: the route
//! fields joined by `,` (`hop_fees` and `hops` joined by `:` or `-` when
//! empty), then `|` and the fields of each curve joined by `,`. Answers are
//! `error:<code>` or `ok`, the settled numbers, and one `|` block per curve.
use std::io::{self, BufRead, Write};

#[path = "multi_hop_route.rs"]
mod multi_hop_route;
use multi_hop_route::*;

fn list(s: &str) -> Vec<u64> {
    if s == "-" {
        return vec![];
    }
    s.split(':').map(|x| x.parse().unwrap()).collect()
}

fn parse(line: &str) -> Route {
    let mut blocks = line.split('|');
    let f: Vec<&str> = blocks.next().unwrap().split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let curves = blocks
        .map(|b| {
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
        tier_bps: (n(9), n(10)),
        flat_bps: (n(11), n(12)),
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
