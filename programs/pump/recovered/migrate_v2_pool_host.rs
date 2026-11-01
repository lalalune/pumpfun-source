//! Host driver for `migrate_v2_pool.rs`, used by
//! `tests/test_migrate_v2_pool_captured.py`. One request per line: the route
//! (`sol`, `spl` or `t22`), the quote transfer fee in basis points, then the
//! other `Migration` fields in order, comma separated: an amount, `0|1` for a
//! flag, or `-` for an account that does not exist.
#[path = "migrate_v2_pool.rs"]
mod migrate_v2_pool;

use migrate_v2_pool::{Migration, Quote};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let b = |i: usize| f[i] == "1";
    let o = |i: usize| if f[i] == "-" { None } else { Some(n(i)) };
    let m = Migration {
        quote_route: match f[0] {
            "sol" => Quote::Native,
            "spl" => Quote::Spl,
            "t22" => Quote::Token2022 { fee_bps: n(1) as u16 },
            other => panic!("unknown route {other}"),
        },
        curve_tokens: n(2),
        real_quote_reserves: n(3),
        post_complete_quote_in: n(4),
        pool_migration_fee: n(5),
        curve_mayhem: b(6),
        curve_cashback: b(7),
        authority_mint_account: o(8),
        authority_quote_account: o(9),
        pool_base_account: o(10),
        pool_quote_account: o(11),
        user_lp_account: b(12),
        authority_lamports: n(13),
        pool_lamports: n(14),
        lp_mint_lamports: n(15),
        pool_taken: b(16),
        lp_mint_taken: b(17),
        disable_create: b(18),
        mayhem_enabled: b(19),
        cashback_enabled: b(20),
        boost_enabled: b(21),
        remaining_accounts: n(22) as usize,
        boost_vault_exists: b(23),
        token_2022_base: b(24),
        transfer_fee_bps: n(25) as u16,
    };
    match migrate_v2_pool::migrate(&m) {
        Err(code) => format!("error:{code}"),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{},{},{},{},{},{}",
            r.base,
            r.quote,
            r.initial_liquidity,
            r.lp_out,
            r.pool_base_after,
            r.pool_quote_after,
            r.boosted,
            r.vault_after,
            r.user_paid,
            r.withdraw_gain,
            r.quote_left.map_or("-".to_string(), |v| v.to_string())
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
