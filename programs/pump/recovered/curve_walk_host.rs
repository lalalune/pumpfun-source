//! stdin/stdout driver for `curve_walk.rs`, used by
//! `tests/test_curve_walk_captured.py`. The state lives in this process.
//! `start,<has_creator>,<creator_bps>,<supply>,<configurable>,<buyback_bps>,<tiers>,<13 state fields>`
//! begins a walk (`tiers` is `threshold:protocol:creator` joined by `;`) and
//! answers `started`. Later lines are `buy,<amount>,<max>,<trailing hex>`,
//! `exact,<spendable>,<min>,<trailing hex>`, `sell,<amount>,<min>` or `collect`.
//! Each answers `<outcome>|<state fields>|<trade fields>`, where `<outcome>` is
//! `ok`, `error:<code>` or `panic`.
use std::io::{self, BufRead, Write};

#[allow(dead_code, unused_attributes)]
#[path = "constant_product.rs"]
mod constant_product;
#[allow(dead_code)]
#[path = "creator_fee_collect.rs"]
mod creator_fee_collect;
#[path = "curve_walk.rs"]
mod curve_walk;
#[allow(dead_code)]
#[path = "legacy_buy.rs"]
mod legacy_buy;
#[allow(dead_code)]
#[path = "legacy_sell.rs"]
mod legacy_sell;

use curve_walk::{step, Op, Setup, State, Stop};

fn hex(text: &str) -> Vec<u8> {
    (0..text.len()).step_by(2).map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap()).collect()
}

fn state_text(s: &State) -> String {
    format!(
        "{},{},{},{},{},{},{},{},{},{},{},{},{}",
        s.virtual_token_reserves,
        s.virtual_sol_reserves,
        s.real_token_reserves,
        s.real_sol_reserves,
        s.complete as u8,
        s.user_tokens,
        s.curve_tokens,
        s.user_lamports,
        s.curve_lamports,
        s.recipient_lamports,
        s.buyback_lamports,
        s.vault_lamports,
        s.creator_lamports,
    )
}

fn start(f: &[&str]) -> (Setup, State) {
    assert_eq!(f.len(), 20, "unexpected start column count");
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let flag = |i: usize| match f[i] {
        "0" => false,
        "1" => true,
        other => panic!("flag must be 0 or 1, got {other}"),
    };
    let tiers = f[6]
        .split(';')
        .map(|t| {
            let p: Vec<&str> = t.split(':').collect();
            assert_eq!(p.len(), 3, "unexpected tier column count");
            (p[0].parse().unwrap(), p[1].parse().unwrap(), p[2].parse().unwrap())
        })
        .collect();
    let setup = Setup {
        has_creator: flag(1),
        creator_fee_bps: n(2),
        mint_supply: n(3),
        creator_fee_configurable: flag(4),
        buyback_bps: n(5),
        tiers,
    };
    let state = State {
        virtual_token_reserves: n(7),
        virtual_sol_reserves: n(8),
        real_token_reserves: n(9),
        real_sol_reserves: n(10),
        complete: flag(11),
        user_tokens: n(12),
        curve_tokens: n(13),
        user_lamports: n(14),
        curve_lamports: n(15),
        recipient_lamports: n(16),
        buyback_lamports: n(17),
        vault_lamports: n(18),
        creator_lamports: n(19),
    };
    (setup, state)
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    let mut walk: Option<(Setup, State)> = None;
    for line in io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        if f[0] == "start" {
            walk = Some(start(&f));
            writeln!(out, "started").unwrap();
            continue;
        }
        let columns = match f[0] {
            "buy" | "exact" => 4,
            "sell" => 3,
            "collect" => 1,
            other => panic!("unknown op {other}"),
        };
        assert_eq!(f.len(), columns, "unexpected operation column count");
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        let op = match f[0] {
            "buy" => Op::Buy { amount: n(1), max_sol_cost: n(2), trailing: hex(f[3]) },
            "exact" => Op::ExactSolIn { spendable: n(1), min_tokens: n(2), trailing: hex(f[3]) },
            "sell" => Op::Sell { amount: n(1), min_sol_output: n(2) },
            // A catchall read any token -- a typo, a new operation, a column
            // shifted into this one -- as `collect` and answered with real state.
            "collect" => Op::Collect,
            other => panic!("unknown op {other}"),
        };
        let (setup, state) = walk.as_mut().unwrap();
        let (outcome, trade) = match step(state, setup, &op) {
            Err(Stop::Code(code)) => (format!("error:{code}"), None),
            Err(Stop::Panic) => ("panic".to_string(), None),
            Ok(trade) => ("ok".to_string(), trade),
        };
        let trade = trade.map_or(String::new(), |t| {
            format!(
                "{},{},{},{},{},{},{},{},{}",
                t.sol_amount,
                t.token_amount,
                t.is_buy as u8,
                t.fee_bps,
                t.fee,
                t.creator_bps,
                t.creator_fee,
                t.track_volume as u8,
                t.buyback_fee,
            )
        });
        writeln!(out, "{outcome}|{}|{trade}", state_text(state)).unwrap();
    }
}
