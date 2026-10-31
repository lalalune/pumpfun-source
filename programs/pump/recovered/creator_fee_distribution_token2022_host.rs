//! Host driver for `creator_fee_distribution_token2022.rs`, used by
//! `tests/test_creator_fee_distribution_token2022_captured.py`. One request per line:
//! `vault_tokens,active,creator_fee,curve_ok,config_mint_ok,quote_ok,initialize_ata,
//!  vault_flags,fee,epoch,hook_set,paused,holders`
//! where `vault_tokens` may be `-`, `vault_flags` is
//! `frozen:owner_mismatch:mint_mismatch:cpi_guard:non_transferable`, `fee` is `-`
//! or `older_bps:older_max:newer_epoch:newer_bps:newer_max`, and `holders` is a
//! `;` list of `bps:wallet:ata:frozen:mint_mismatch:memo:no_fee_extension`
//! (wallet and ata may be `-` when the slot is not passed).
#[path = "creator_fee_distribution_quote.rs"]
#[allow(dead_code)]
mod creator_fee_distribution_quote;
#[path = "creator_fee_distribution_token2022.rs"]
#[allow(dead_code)]
mod creator_fee_distribution_token2022;

use creator_fee_distribution_quote::{Ata, Failure, QuoteDistribution, Shareholder, Wallet};
use creator_fee_distribution_token2022::{Distribution, Holding, TransferFee, Vault};
use std::io::{self, BufRead, Write};

fn fee(text: &str) -> Option<TransferFee> {
    if text == "-" {
        return None;
    }
    let f: Vec<u64> = text.split(':').map(|v| v.parse().unwrap()).collect();
    Some(TransferFee { older_bps: f[0] as u16, older_max: f[1], newer_epoch: f[2], newer_bps: f[3] as u16, newer_max: f[4] })
}

fn list(values: &[u64]) -> String {
    values.iter().map(u64::to_string).collect::<Vec<_>>().join(";")
}

fn answer(line: &str) -> String {
    let f: Vec<&str> = line.split(',').collect();
    let flag = |i: usize| f[i] != "0";
    let v: Vec<bool> = f[7].split(':').map(|x| x != "0").collect();
    let mut shareholders = Vec::new();
    let mut holdings = Vec::new();
    for h in f[12].split(';').filter(|h| !h.is_empty()) {
        let p: Vec<&str> = h.split(':').collect();
        shareholders.push(Shareholder {
            bps: p[0].parse().unwrap(),
            wallet: match p[1] {
                "ok" => Some(Wallet::Ok),
                "wrong" => Some(Wallet::Wrong),
                "exec" => Some(Wallet::Executable),
                _ => None,
            },
            ata: match p[2] {
                "exists" => Some(Ata::Exists),
                "absent" => Some(Ata::Absent),
                "wrong" => Some(Ata::Wrong),
                _ => None,
            },
        });
        holdings.push(Holding {
            frozen: p[3] != "0",
            mint_mismatch: p[4] != "0",
            memo_required: p[5] != "0",
            no_fee_extension: p[6] != "0",
        });
    }
    let d = Distribution {
        base: QuoteDistribution {
            vault_tokens: if f[0] == "-" { None } else { Some(f[0].parse().unwrap()) },
            shareholders,
            active: flag(1),
            creator_fee: f[2].parse().unwrap(),
            curve_creator_is_config: flag(3),
            config_mint_matches: flag(4),
            quote_mint_matches: flag(5),
            initialize_ata: flag(6),
        },
        vault: Vault { frozen: v[0], owner_mismatch: v[1], mint_mismatch: v[2], cpi_guard: v[3], non_transferable: v[4] },
        holdings,
        fee: fee(f[8]),
        epoch: f[9].parse().unwrap(),
        hook_set: flag(10),
        paused: flag(11),
    };
    match creator_fee_distribution_token2022::distribute(&d) {
        Err(Failure::Custom(code)) => format!("error:{code}"),
        Err(Failure::InvalidAccountData) => "invalid_account_data".to_string(),
        Ok(r) => format!("ok,{},{},{},{}", list(&r.transfers), list(&r.withheld), r.distributed, r.ata_rent),
    }
}

fn main() {
    let stdout = io::stdout();
    let mut out = stdout.lock();
    for line in io::stdin().lock().lines() {
        writeln!(out, "{}", answer(line.unwrap().trim())).unwrap();
    }
}
