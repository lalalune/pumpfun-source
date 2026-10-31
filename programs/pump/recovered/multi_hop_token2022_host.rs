//! stdin/stdout driver for `multi_hop_token2022.rs`, used by
//! `tests/test_multi_hop_token2022_captured.py`. One route per line: the route
//! fields joined by `,` (`hop_fees` and `hops` joined by `:` or `-` when
//! empty), `|`, the mints joined by `;` with their fields joined by `:`, then
//! `|` and the fields of each curve joined by `,`. Answers are `error:<code or
//! name>` or `ok`, the settled numbers, and one `|` block per curve.
use std::io::{self, BufRead, Write};

#[path = "multi_hop_token2022.rs"]
mod multi_hop_token2022;
use multi_hop_token2022::*;

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
    let mints = blocks
        .next()
        .unwrap()
        .split(';')
        .map(|m| {
            let v = list(m);
            Mint {
                token2022: v[0] == 1,
                transfer_fee: (v[1] == 1).then_some((v[2], v[3], v[4], v[5], v[6])),
                hook: v[7] == 1,
                paused: v[8] == 1,
                non_transferable: v[9] == 1,
                malformed: v[10] == 1,
                unreadable: v[11] == 1,
            }
        })
        .collect();
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
                base_frozen: v[14] == 1,
                quote_frozen: v[15] == 1,
                base_wrong_program: v[16] == 1,
                quote_wrong_program: v[17] == 1,
                base_bare: v[18] == 1,
                quote_bare: v[19] == 1,
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
        epoch: n(14),
        source_frozen: n(15) == 1,
        destination_frozen: n(16) == 1,
        recipient_wrong_program: n(17) == 1,
        source_cpi_guard: n(18) == 1,
        destination_memo: n(19) == 1,
        destination_bare: n(20) == 1,
        recipient_bare: n(21) == 1,
        mints,
        curves,
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let answer = match run(&parse(line.trim())) {
            Err(MISSING_ACCOUNT) => "error:MissingAccount".to_string(),
            Err(INCORRECT_PROGRAM_ID) => "error:IncorrectProgramId".to_string(),
            Err(INVALID_ACCOUNT_DATA) => "error:InvalidAccountData".to_string(),
            Err(code) => format!("error:{code}"),
            Ok(s) => {
                let mut text = format!(
                    "ok,{},{},{},{},{},{},{},{}",
                    s.amount_out, s.buyback_fee, s.source, s.destination, s.user_lamports, s.recipient, s.destination_withheld, s.recipient_withheld
                );
                for c in &s.curves {
                    text += &format!(
                        "|{},{},{},{},{},{},{},{},{},{},{},{},{},{}",
                        c.virtual_token_reserves, c.virtual_quote_reserves, c.real_token_reserves, c.real_quote_reserves,
                        c.creator_fee, c.protocol_fees, c.post_complete_base_out, c.post_complete_quote_in,
                        c.complete as u8, c.base_vault, c.quote_vault, c.lamports, c.base_withheld, c.quote_withheld
                    );
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
