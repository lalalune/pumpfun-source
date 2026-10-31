//! One case per stdin line, one answer per stdout line, for
//! `tests/test_migrate_faults_captured.py`.
#![allow(dead_code)]

#[path = "migrate_faults.rs"]
mod migrate_faults;

use migrate_faults::{migrate, Extensions, Frozen, Migration};
use std::io::BufRead;

fn balance(field: &str) -> Option<u64> {
    if field == "-" {
        None
    } else {
        Some(field.parse().unwrap())
    }
}

/// `-` for none; ids joined by `+`; 100 above an id sets that extension's option.
fn extensions(field: &str) -> Extensions {
    let mut ext = Extensions::default();
    if field != "-" {
        for id in field.split('+').map(|id| id.parse::<u16>().unwrap()) {
            ext.ids.push(id % 100);
            match id {
                106 => ext.default_frozen = true,
                114 => ext.hook_set = true,
                126 => ext.paused = true,
                _ => {}
            }
        }
    }
    ext
}

fn main() {
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.split(',').collect();
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        let mask = n(16);
        let m = Migration {
            token_2022_base: n(0) == 1,
            base_mint: extensions(f[1]),
            curve_tokens: n(2),
            real_quote_reserves: n(3),
            post_complete_quote_in: n(4),
            pool_migration_fee: n(5),
            curve_mayhem: n(6) == 1,
            curve_cashback: n(7) == 1,
            disable_create: n(8) == 1,
            mayhem_enabled: n(9) == 1,
            cashback_enabled: n(10) == 1,
            boost_enabled: n(11) == 1,
            remaining_accounts: n(17) as usize,
            boost_vault_exists: n(18) == 1,
            authority_mint_account: balance(f[12]),
            authority_wsol_account: balance(f[13]),
            pool_base_account: balance(f[14]),
            pool_quote_account: balance(f[15]),
            frozen: Frozen {
                curve_base: mask & 1 != 0,
                authority_mint: mask & 4 != 0,
                authority_wsol: mask & 8 != 0,
                pool_base: mask & 16 != 0,
                pool_quote: mask & 32 != 0,
                vault: mask & 64 != 0,
            },
            pool_taken: n(19) == 1,
            curve_lamports: n(20),
        };
        match migrate(&m) {
            Ok(o) => println!(
                "ok,{},{},{},{},{},{},{},{},{},{}",
                o.base,
                o.quote,
                o.initial_liquidity,
                o.lp_out,
                o.pool_base_after,
                o.pool_quote_after,
                o.boosted,
                o.user_paid,
                o.withdraw_gain,
                o.wsol_left.map_or("-".to_string(), |v| v.to_string())
            ),
            Err(code) => println!("error:{code}"),
        }
    }
}
