//! Host driver for `migrate_pool.rs`, used by `tests/test_migrate_pool_captured.py`.
//! One request per line, the `Migration` fields in order, comma separated: an
//! amount, `0|1` for a flag, or `-` for an account that does not exist.
#[path = "migrate_pool.rs"]
mod migrate_pool;

use migrate_pool::Migration;
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let b = |i: usize| f[i] == "1";
    let o = |i: usize| if f[i] == "-" { None } else { Some(n(i)) };
    let m = Migration {
        curve_tokens: n(0),
        real_quote_reserves: n(1),
        post_complete_quote_in: n(2),
        pool_migration_fee: n(3),
        curve_mayhem: b(4),
        curve_cashback: b(5),
        authority_mint_account: o(6),
        authority_wsol_account: o(7),
        pool_base_account: o(8),
        pool_quote_account: o(9),
        user_lp_account: b(10),
        authority_lamports: n(11),
        pool_lamports: n(12),
        lp_mint_lamports: n(13),
        pool_taken: b(14),
        disable_create: b(15),
        mayhem_enabled: b(16),
        cashback_enabled: b(17),
        boost_enabled: b(18),
        remaining_accounts: n(19) as usize,
        boost_vault_exists: b(20),
        token_2022_base: b(21),
        transfer_fee_bps: n(22) as u16,
    };
    match migrate_pool::migrate(&m) {
        Err(code) => format!("error:{code}"),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{}",
            r.base,
            r.quote,
            r.initial_liquidity,
            r.lp_out,
            r.pool_base_after,
            r.pool_quote_after,
            r.boosted,
            r.user_paid,
            r.withdraw_gain,
            r.wsol_left.map_or("-".to_string(), |v| v.to_string())
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
