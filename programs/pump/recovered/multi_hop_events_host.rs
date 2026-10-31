//! stdin/stdout driver for `multi_hop_events.rs`, used by
//! `tests/test_multi_hop_events_captured.py`. The line format is the one
//! `multi_hop_token2022_host.rs` parses. Answers are `error:<code or name>`
//! (the same strings as that host, plus `error:model-drift` when the
//! recording loop and the model it extends disagree) or `ok` followed by one
//! `;`-separated record per emitted event: `T` for a hop's trade, `C` for a
//! curve completion, `P` for a post-complete buy.
use std::io::{self, BufRead, Write};

#[path = "multi_hop_events.rs"]
mod multi_hop_events;
use multi_hop_events::mh::{Curve, Mint, Route};
use multi_hop_events::{run_events, Event, MODEL_DRIFT};
use multi_hop_events::mh::{INCORRECT_PROGRAM_ID, INVALID_ACCOUNT_DATA, MISSING_ACCOUNT};

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

fn describe(event: &Event) -> String {
    match event {
        Event::Trade { base_mint, quote_mint, has_creator, mayhem, buy, token_amount, quote_amount, quote_fee,
                       fee_bps, fee, creator_bps, creator_fee, buyback_bps, buyback_fee, virtual_token_reserves,
                       virtual_quote_reserves, real_token_reserves, real_quote_reserves, creator_fee_unclaimed } => format!(
            ";T,{base_mint},{quote_mint},{},{},{buy},{token_amount},{quote_amount},{quote_fee},{fee_bps},{fee},\
             {creator_bps},{creator_fee},{buyback_bps},{buyback_fee},{virtual_token_reserves},{virtual_quote_reserves},\
             {real_token_reserves},{real_quote_reserves},{creator_fee_unclaimed}",
            *has_creator as u8, *mayhem as u8, buy = *buy as u8
        ),
        Event::Complete { curve } => format!(";C,{curve}"),
        Event::Bare => ";B".to_string(),
        Event::Post { curve, base_out, quote_in, fee_bps, fee, creator_bps, creator_fee, buyback_fee,
                      pool_base_before, pool_quote_before, pool_base_after, pool_quote_after } => format!(
            ";P,{curve},{base_out},{quote_in},{fee_bps},{fee},{creator_bps},{creator_fee},{buyback_fee},\
             {pool_base_before},{pool_quote_before},{pool_base_after},{pool_quote_after}"
        ),
    }
}

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let answer = match run_events(&parse(line.trim())) {
            Err(MODEL_DRIFT) => "error:model-drift".to_string(),
            Err(MISSING_ACCOUNT) => "error:MissingAccount".to_string(),
            Err(INCORRECT_PROGRAM_ID) => "error:IncorrectProgramId".to_string(),
            Err(INVALID_ACCOUNT_DATA) => "error:InvalidAccountData".to_string(),
            Err(code) => format!("error:{code}"),
            Ok((_, events)) => {
                let mut text = "ok".to_string();
                for event in &events {
                    text += &describe(event);
                }
                text
            }
        };
        writeln!(out, "{answer}").unwrap();
    }
}
