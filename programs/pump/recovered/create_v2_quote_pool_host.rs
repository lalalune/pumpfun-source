//! Host driver for `create_v2_quote_pool.rs`, used by
//! `tests/test_create_v2_quote_pool_captured.py`. One request per line:
//! `tail,key_ok,owner_ok,len,discriminator_ok,base_key_ok,quote_key_ok,
//!  <base vault>,<quote vault>,adjustment,virtual_tokens,real_tokens,seed`
//! where a vault is `owner_ok,len,state,account_type,amount`. One answer per
//! line: `ok,<reserves>` or `error:<code>`.
#[path = "create_v2_quote_pool.rs"]
mod create_v2_quote_pool;

use create_v2_quote_pool::{Pool, Seed, Vault};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let vault = |i: usize| Vault {
        owner_ok: n(i) != 0,
        len: n(i + 1) as usize,
        state: n(i + 2) as u8,
        account_type: n(i + 3) as u8,
        amount: n(i + 4),
    };
    let pool = Pool {
        tail: n(0) as usize,
        key_ok: n(1) != 0,
        owner_ok: n(2) != 0,
        len: n(3) as usize,
        discriminator_ok: n(4) != 0,
        base_key_ok: n(5) != 0,
        quote_key_ok: n(6) != 0,
        base: vault(7),
        quote: vault(12),
        adjustment: f[17].parse().unwrap(),
    };
    let seed = Seed { initial_virtual_token_reserves: n(18), initial_real_token_reserves: n(19), seed: n(20) };
    match create_v2_quote_pool::reserves(&pool, &seed) {
        Ok(reserves) => format!("ok,{reserves}"),
        Err(code) => format!("error:{code}"),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
