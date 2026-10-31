//! Host driver for `migrate_funds.rs`, used by
//! `tests/test_migrate_funds_captured.py`. One request per line: the line of
//! `migrate_host.rs`, then `;` and `curve_len,curve_lamports,creator_fee,
//! protocol_fees,base_balance`. Answers are `borsh`, `error:<code>`,
//! `after-pool:<code>:<base>:<boost>`, `invalid-data`, `lamports`, `below-rent`,
//! `noop,<user_paid>` or `ok,<quote>,<mayhem>,<cashback>,<creator_fee_bps>,
//! <can_edit>,<holder>,<boost>,<curve_lamports>,<base>,<user_paid>,<creator>`.
#[allow(dead_code)]
#[path = "migrate.rs"]
mod migrate;
#[path = "migrate_funds.rs"]
mod migrate_funds;

use migrate::{AmmConfig, Fault, Migrate, Outcome, Stop};
use migrate_funds::{Failure, Funds};
use std::io::{self, BufRead, Write};

fn fault(c: char) -> Fault {
    match c {
        'W' => Fault::WithdrawAuthority,
        'R' => Fault::WithdrawReadonly,
        'Q' => Fault::CurveQuoteMint,
        'P' => Fault::Pool,
        'C' => Fault::AmmGlobalConfig,
        'S' => Fault::WsolMint,
        'L' => Fault::LpMint,
        'E' => Fault::AmmEventAuthority,
        'T' => Fault::Rent,
        other => panic!("unknown fault {other}"),
    }
}

fn answer(line: &str) -> String {
    let (line, funds) = line.split_once(';').unwrap();
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let m = Migrate {
        faults: if f[0] == "-" { Vec::new() } else { f[0].chars().map(fault).collect() },
        complete: n(1) as u8,
        virtual_token_reserves: n(2),
        virtual_quote_reserves: n(3),
        real_token_reserves: n(4),
        real_quote_reserves: n(5),
        post_complete_quote_in: n(6),
        pool_migration_fee: n(7),
        is_mayhem_mode: n(8) != 0,
        is_cashback_coin: n(9) != 0,
        creator_fee_bps: n(10),
        can_edit_creator_fee: n(11) != 0,
        is_holder_reward: n(12) != 0,
        amm_config: if f[13] == "-" {
            None
        } else {
            let c: Vec<u64> = f[13].split(':').map(|x| x.parse().unwrap()).collect();
            Some(AmmConfig { len: c[0] as usize, discriminator_ok: c[1] != 0, boost_byte: c[2] as u8 })
        },
        remaining_accounts: n(14) as usize,
        curve_slack: n(15),
    };
    let g: Vec<u64> = funds.split(',').map(|x| x.parse().unwrap()).collect();
    let funds = Funds {
        curve_len: g[0] as usize,
        curve_lamports: g[1],
        creator_fee: g[2],
        protocol_fees: g[3],
        base_balance: g[4],
        has_creator: true,
    };
    match migrate_funds::run(m, funds) {
        Err(Failure::Stop(Stop::Code(code))) => format!("error:{code}"),
        Err(Failure::Stop(Stop::InvalidBool)) => "borsh".to_string(),
        Err(Failure::InvalidData) => "invalid-data".to_string(),
        Err(Failure::Lamports) => "lamports".to_string(),
        Err(Failure::BelowRent) => "below-rent".to_string(),
        Err(Failure::AfterPool(code, base, boost)) => format!("after-pool:{code}:{base}:{}", boost as u8),
        Ok(done) => match done.outcome {
            Outcome::AlreadyMigrated => format!("noop,{}", done.user_paid),
            Outcome::Migrated { pool: p, init_boost, curve_lamports } => format!(
                "ok,{},{},{},{},{},{},{},{},{},{},{}",
                p.quote_amount_in,
                p.is_mayhem_mode as u8,
                p.is_cashback_coin as u8,
                p.creator_fee_bps,
                p.can_edit_creator_fee as u8,
                p.is_holder_reward as u8,
                init_boost as u8,
                curve_lamports,
                done.base_amount_in,
                done.user_paid,
                done.creator as u8
            ),
        },
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
