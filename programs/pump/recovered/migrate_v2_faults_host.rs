//! One case per stdin line, one answer per stdout line, for
//! `tests/test_migrate_v2_faults_captured.py`.
#![allow(dead_code)]

#[path = "migrate_v2_faults.rs"]
mod migrate_v2_faults;

use migrate_v2_faults::{migrate, Extensions, Frozen, Migration, Route};
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
        let mask = n(18);
        let m = Migration {
            route: match f[0] {
                "sol" => Route::Native,
                "wsol" => Route::WrappedSol,
                "spl" => Route::Spl,
                "t22" => Route::Token2022,
                other => panic!("unknown route {other}"),
            },
            token_2022_base: n(1) == 1,
            base_mint: extensions(f[2]),
            quote_mint: extensions(f[3]),
            curve_tokens: n(4),
            real_quote_reserves: n(5),
            post_complete_quote_in: n(6),
            pool_migration_fee: n(7),
            curve_mayhem: n(8) == 1,
            curve_cashback: n(9) == 1,
            disable_create: n(10) == 1,
            mayhem_enabled: n(11) == 1,
            cashback_enabled: n(12) == 1,
            boost_enabled: n(13) == 1,
            remaining_accounts: n(19) as usize,
            boost_vault_exists: n(20) == 1,
            authority_mint_account: balance(f[14]),
            authority_quote_account: balance(f[15]),
            pool_base_account: balance(f[16]),
            pool_quote_account: balance(f[17]),
            frozen: Frozen {
                curve_base: mask & 1 != 0,
                curve_quote: mask & 2 != 0,
                authority_mint: mask & 4 != 0,
                authority_quote: mask & 8 != 0,
                pool_base: mask & 16 != 0,
                pool_quote: mask & 32 != 0,
                vault: mask & 64 != 0,
            },
            quote_mint_writable: n(21) == 1,
            pool_taken: n(22) == 1,
            user_lamports: n(23),
            curve_quote_missing: n(24),
            curve_lamports: n(25),
        };
        match migrate(&m) {
            Ok(o) => println!(
                "ok,{},{},{},{},{},{},{},{},{},{},{}",
                o.base,
                o.quote,
                o.initial_liquidity,
                o.lp_out,
                o.pool_base_after,
                o.pool_quote_after,
                o.boosted,
                o.vault_after,
                o.user_paid,
                o.withdraw_gain,
                o.quote_left.map_or("-".to_string(), |v| v.to_string())
            ),
            Err(code) => println!("error:{code}"),
        }
    }
}
