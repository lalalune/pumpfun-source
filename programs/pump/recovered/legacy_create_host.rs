//! Host driver for `legacy_create.rs`, used by `tests/test_legacy_create_captured.py`.
//! One request per line:
//! `faults,name_bytes,symbol_bytes,uri_bytes,creator_is_zero,vtr,vsr,rtr,supply`
//! where `faults` is `-` or letters from `UACGBM` (see `fault`).
#[path = "legacy_create.rs"]
mod legacy_create;

use legacy_create::{Create, Fault, Global};
use std::io::{self, BufRead, Write};

fn fault(c: char) -> Fault {
    match c {
        'U' => Fault::MintInUse,
        'A' => Fault::MintAuthority,
        'C' => Fault::BondingCurve,
        'G' => Fault::GlobalMissing,
        'B' => Fault::GlobalBadBool,
        'M' => Fault::Metadata,
        other => panic!("unknown fault {other}"),
    }
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let c = Create {
        faults: if f[0] == "-" { Vec::new() } else { f[0].chars().map(fault).collect() },
        name_bytes: n(1) as usize,
        symbol_bytes: n(2) as usize,
        uri_bytes: n(3) as usize,
        creator_is_zero: n(4) != 0,
        global: Global {
            initial_virtual_token_reserves: n(5),
            initial_virtual_sol_reserves: n(6),
            initial_real_token_reserves: n(7),
            token_total_supply: n(8),
        },
    };
    match legacy_create::create(&c) {
        Err(code) => format!("error:{code}"),
        Ok(r) => format!(
            "ok,{},{},{},{},{},{}",
            r.virtual_token_reserves,
            r.virtual_quote_reserves,
            r.real_token_reserves,
            r.token_total_supply,
            r.initial_virtual_quote_reserves,
            r.minted
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
