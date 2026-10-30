//! Host driver for `creator_fee_distribution.rs`, used by
//! `tests/test_creator_fee_distribution_captured.py`. One request per line:
//! `op,vault,active,creator_fee,curve_creator_is_config,curve_has_quote_mint,
//!  config_mint_matches,shareholders` where `op` is `distribute|minimum` and
//! `shareholders` is `;`-separated `bps:slot` with `slot` one of `-` (no
//! remaining account), `wrong`, `exec` or `lamports/data_len`.
#[path = "creator_fee_distribution.rs"]
mod creator_fee_distribution;

use creator_fee_distribution::{Distribution, Shareholder, Slot};
use std::io::{self, BufRead, Write};

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let n = |i: usize| f[i].parse::<u64>().unwrap();
    let shareholders = f[7]
        .split(';')
        .filter(|s| !s.is_empty())
        .map(|s| {
            let (bps, slot) = s.split_once(':').unwrap();
            let slot = match slot {
                "-" => None,
                "wrong" => Some(Slot::Wrong),
                "exec" => Some(Slot::Executable),
                held => {
                    let (lamports, data_len) = held.split_once('/').unwrap();
                    Some(Slot::Holder { lamports: lamports.parse().unwrap(), data_len: data_len.parse().unwrap() })
                }
            };
            Shareholder { bps: bps.parse().unwrap(), slot }
        })
        .collect();
    let d = Distribution {
        vault_lamports: n(1),
        shareholders,
        active: n(2) != 0,
        creator_fee: n(3),
        curve_creator_is_config: n(4) != 0,
        curve_has_quote_mint: n(5) != 0,
        config_mint_matches: n(6) != 0,
    };
    if f[0] == "minimum" {
        match creator_fee_distribution::minimum(&d) {
            Err(code) => format!("error:{code}"),
            Ok(m) => format!("ok,{},{},{}", m.minimum_required, m.distributable_fees, u8::from(m.can_distribute)),
        }
    } else {
        match creator_fee_distribution::distribute(&d) {
            Err(code) => format!("error:{code}"),
            Ok(r) => {
                let transfers: Vec<String> = r.transfers.iter().map(u64::to_string).collect();
                format!("ok,{},{},{}", r.distributed, u8::from(r.event), transfers.join(";"))
            }
        }
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
