//! stdin/stdout driver for `mayhem_virtual_params.rs`, used by
//! `tests/test_mayhem_virtual_params_captured.py`. One case per line:
//! `<flags>,<vtr>,<vqr>,<rtr>,<rqr>,<supply>,<complete>,<mayhem>,<native>,
//! <initial_real_token_reserves>,<vault_amount>` where `<flags>` is eight
//! `0`/`1` digits in `Accounts` field order. Answers are
//! `ok,<vtr>,<vsr>,<new_vtr>,<new_vsr>,<rtr>,<rsr>` or `error:<code>`.
use std::io::{self, BufRead, Write};

#[path = "mayhem_virtual_params.rs"]
mod mayhem_virtual_params;
use mayhem_virtual_params::*;

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let f: Vec<&str> = line.trim().split(',').collect();
        let bit = |i: usize| f[0].as_bytes()[i] == b'1';
        let n = |i: usize| f[i].parse::<u64>().unwrap();
        let accounts = Accounts {
            global_ok: bit(0),
            token_program_ok: bit(1),
            signed: bit(2),
            seeds_ok: bit(3),
            vault_program_ok: bit(4),
            vault_owner_ok: bit(5),
            vault_address_ok: bit(6),
            curve_ok: bit(7),
        };
        let curve = Curve {
            virtual_token_reserves: n(1),
            virtual_quote_reserves: n(2),
            real_token_reserves: n(3),
            real_quote_reserves: n(4),
            token_total_supply: n(5),
            complete: f[6] == "1",
            is_mayhem_mode: f[7] == "1",
            native_quote: f[8] == "1",
        };
        match set_mayhem_virtual_params(&accounts, &curve, n(9), n(10)) {
            Outcome::Error(code) => writeln!(out, "error:{code}").unwrap(),
            Outcome::Synced(e) => writeln!(
                out,
                "ok,{},{},{},{},{},{}",
                e.virtual_token_reserves,
                e.virtual_sol_reserves,
                e.new_virtual_token_reserves,
                e.new_virtual_sol_reserves,
                e.real_token_reserves,
                e.real_sol_reserves
            )
            .unwrap(),
        }
    }
}
